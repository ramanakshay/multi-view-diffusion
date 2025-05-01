
import pandas as pd
import multiprocessing
import objaverse

objaverse.BASE_PATH = '/scratch/ar8692/multi-view-synthesis/src/data/dataset'
objaverse._VERSIONED_PATH = '/scratch/ar8692/multi-view-synthesis/src/data/dataset/objaverse'

NUM_OBJECTS = 50000

# processes = multiprocessing.cpu_count()
# processes = 32
# print('Number of Processes: ', processes)

df = pd.read_json("hf://datasets/cindyxl/ObjaversePlusPlus/annotated_500k.json")
print('Total Size:', len(df))

# high quality filter + sampling
filtered_df = df[(df['score'] >= 3) &
                 (df['is_multi_object'] == 'false') &
                 (df['is_scene'] == 'false') &
                 (df['is_transparent'] == 'false') &
                 (df['is_single_color'] == 'false')]['UID'].sample(n = NUM_OBJECTS, random_state=21)
print('Filtered Size:', len(filtered_df))

# download objects
uids = list(filtered_df)
objects = objaverse.load_objects(
    uids=uids,
    download_processes=1
)
print('Download Completed!')

