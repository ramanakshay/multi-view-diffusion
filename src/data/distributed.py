import glob
import json
import multiprocessing
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Optional
import os
import pickle
import numpy as np

import tyro
import wandb

np.random.seed(42)

@dataclass
class Args:
    workers_per_gpu: int
    """number of workers per gpu"""

    input_models_path: str
    """Path to a json file containing a list of 3D object files"""

    log_to_wandb: bool = False
    """Whether to log the progress to wandb"""

    num_gpus: int = 1
    """number of gpus to use. -1 means all available gpus"""


def worker(
        queue: multiprocessing.JoinableQueue,
        count: multiprocessing.Value,
        gpu: int
) -> None:
    while True:
        item = queue.get()
        if item is None:
            break

        path, elevation = item
        # Perform some operation on the item
        print(item, gpu)
        command = (
            f"export DISPLAY=:0.{gpu} &&"
            f"/scratch/ar8692/multi-view-synthesis/blender-3.2.2-linux-x64/blender -b -P render.py --"
            f" --object_path {path}"
            f" --output_dir {'/scratch/ar8692/multi-view-synthesis/src/data/dataset/views2'}"
            f" --elevation {elevation}"
        )
        subprocess.run(command, shell=True)

        with count.get_lock():
            count.value += 1

        queue.task_done()


if __name__ == "__main__":
    args = tyro.cli(Args)

    queue = multiprocessing.JoinableQueue()
    count = multiprocessing.Value("i", 0)

    if args.log_to_wandb:
        wandb.init(project="objaverse-rendering", entity="multi-view-synthesis")

    # Start worker processes on each of the GPUs
    for gpu_i in range(args.num_gpus):
        for worker_i in range(args.workers_per_gpu):
            worker_i = gpu_i * args.workers_per_gpu + worker_i
            process = multiprocessing.Process(
                target=worker, args=(queue, count, gpu_i)
            )
            process.daemon = True
            process.start()

    # Add items to the queue
    model_paths = []
    for root, _, files in os.walk(args.input_models_path):
        for file in files:
            file_path = os.path.join(root, file)
            model_paths.append(file_path)

    meta_data = {"uid": [], "elevation": []}
    for object_path in model_paths:
        object_uid = os.path.basename(object_path).split(".")[0]
        elevation = np.random.uniform(-5, 30)
        meta_data["uid"].append(object_uid)
        meta_data["elevation"].append(elevation)
        queue.put((object_path, elevation))

    # dump pickle meta_data
    with open('dataset/views/svd_meta.pkl', 'wb') as file:
        pickle.dump(meta_data, file)

    # update the wandb count
    if args.log_to_wandb:
        while True:
            time.sleep(5)
            wandb.log(
                {
                    "count": count.value,
                    "total": len(model_paths),
                    "progress": count.value / len(model_paths),
                }
            )
            if count.value == len(model_paths):
                break

    # Wait for all tasks to be completed
    queue.join()

    # Add sentinels to the queue to stop the worker processes
    for i in range(args.num_gpus * args.workers_per_gpu):
        queue.put(None)