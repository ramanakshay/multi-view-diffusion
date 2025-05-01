from ldm.base_utils import save_pickle

with open('training_examples/input/model_folders.txt', 'r') as f:
    uids = [line.strip() for line in f if line.strip()]

save_pickle(uids, 'training_examples/uid_set.pkl')
