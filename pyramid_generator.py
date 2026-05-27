"""
PYRAMIDEN-DATENGENERATOR - Minimalist Version
==============================================
Generiert schnell synthetische Trainingsdaten für Pyramiden-Klassifikation.
Optimiert für Klarheit und Geschwindigkeit (nur essenzielle Features).
"""

import numpy as np
from typing import Tuple, List, Dict


class PyramidGenerator:
    """Generiert Trainings-Daten: Pyramiden (Label=1) vs. andere Formen (Label=0)"""
    
    def __init__(self, seed=None):
        if seed is not None:
            np.random.seed(seed)
    
    def _generate_pyramid(self) -> Tuple[np.ndarray, int]:
        """Generiert eine Pyramide: 4 Base-Punkte (3D) + 1 Apex-Punkt (19 Features + Label)"""
        base = np.random.uniform(0.2, 0.8, (4, 3)).astype(np.float32)
        base[:, 2] *= 0.1  # Z nur leicht variieren
        
        base_center = base[:, :2].mean(axis=0)
        apex_xy = base_center + np.random.uniform(-0.1, 0.1, 2)
        apex_z = np.random.uniform(0.5, 1.0)
        apex = np.array([apex_xy[0], apex_xy[1], apex_z], dtype=np.float32)
        
        features = np.concatenate([
            base.flatten(),                    # 12
            apex,                              # 3
            [apex_z],                          # Höhe
            [np.linalg.norm(apex_xy - base_center)],  # Balance
            [np.linalg.norm(base[1] - base[0]) ** 2],  # Base-Fläche
            [base_center[0]],                  # X-Position
        ])
        return features, 1
    
    def _generate_non_pyramid(self) -> Tuple[np.ndarray, int]:
        """Generiert eine Nicht-Pyramide: zufällige Punkte"""
        points = np.random.uniform(0.1, 0.9, (5, 3)).astype(np.float32)
        features = np.concatenate([points[:4].flatten(), points[4]])
        features = np.concatenate([features, np.random.uniform(0, 1, 19 - len(features))])
        return features[:19], 0
    
    def generate_dataset(self, n_pyramids: int = 100, n_non_pyramids: int = 100, 
                        shuffle: bool = True) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generiert ein Klassifikations-Dataset.
        
        Returns: (data_array [n_samples, 20], metadata)
        """
        data = []
        metadata = []
        
        for i in range(n_pyramids):
            feat, label = self._generate_pyramid()
            data.append(np.concatenate([feat, [label]]))
            metadata.append({"id": i, "type": "pyramid", "label": 1})
        
        for i in range(n_non_pyramids):
            feat, label = self._generate_non_pyramid()
            data.append(np.concatenate([feat, [label]]))
            metadata.append({"id": n_pyramids + i, "type": "non_pyramid", "label": 0})
        
        data = np.array(data, dtype=np.float32)
        
        if shuffle:
            idx = np.random.permutation(len(data))
            data = data[idx]
            metadata = [metadata[i] for i in idx]
        
        return data, metadata
