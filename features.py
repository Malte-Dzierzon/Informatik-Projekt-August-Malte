import numpy as np, os, json, random
from datetime import datetime
import pandas as pd

class Checkpoints:
    def __init__(self, path="checkpoints"):
        self.path = path
        os.makedirs(path, exist_ok=True)
    
    def save(self, model, stats, name=None):
        name = name or f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        np.savez(f"{self.path}/{name}.npz", **model)
        with open(f"{self.path}/{name}.json", "w") as f:
            json.dump(stats, f)
        return name
    
    def load(self, name):
        data = np.load(f"{self.path}/{name}.npz")
        with open(f"{self.path}/{name}.json") as f:
            stats = json.load(f)
        return {k: data[k] for k in data.files}, stats
    
    def list(self):
        return [f[:-4] for f in os.listdir(self.path) if f.endswith('.npz')]


class Pyramids:
    def __init__(self, seed=None):
        if seed: np.random.seed(seed)
    
    def pyramid(self):
        base = [[np.random.uniform(0, 1), np.random.uniform(0, 1), np.random.uniform(0, 1)] for _ in range(4)]
        apex = [np.random.uniform(-0.5, 1.5), np.random.uniform(-0.5, 1.5), np.random.uniform(0.5, 2)]
        feats = [x for v in base + [apex] for x in v]
        feats += [np.linalg.norm(np.array(apex) - np.mean(base, axis=0)), 
                  len(base), np.std([np.linalg.norm(v) for v in base])]
        return np.array(feats + [1], dtype=np.float32)
    
    def non_pyramid(self):
        verts = [[np.random.uniform(0, 1), np.random.uniform(0, 1), np.random.uniform(0, 1)] for _ in range(np.random.randint(3, 7))]
        feats = [x for v in verts for x in v]
        feats += [0] * (19 - len(feats))
        return np.array(feats + [0], dtype=np.float32)
    
    def dataset(self, n_pyr=100, n_non=100):
        data = [self.pyramid() for _ in range(n_pyr)] + [self.non_pyramid() for _ in range(n_non)]
        np.random.shuffle(data)
        return np.array(data)


class DynamicInput:
    def filter(self, data, threshold=0.95):
        mask = np.mean(data[:, :-1] == 0, axis=0) < threshold
        return data[:, np.concatenate([[True], mask, [True]])]
    
    def pad(self, data, size=20):
        if data.shape[1] < size:
            pad = np.zeros((data.shape[0], size - data.shape[1]))
            return np.hstack([data[:, :-1], pad, data[:, [-1]]])
        return data[:, :size+1]
