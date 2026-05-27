"""
DYNAMISCHES INPUT-SYSTEM - Minimalist
=======================================
Verarbeitet Input-Daten mit variabler Struktur.
"""

import numpy as np
from typing import Tuple, Dict


class DynamicInputHandler:
    """Verarbeitet variable Input-Größen und Normalisierung"""
    
    def __init__(self, max_vertices=12, coordinates_per_vertex=3):
        self.max_vertices = max_vertices
        self.coordinates_per_vertex = coordinates_per_vertex
        self.normalization_params = {}
    
    def normalize_data(self, data: np.ndarray, fit: bool = True, 
                      params: Dict = None) -> Tuple[np.ndarray, Dict]:
        """Normalisiert Features auf [0, 1]"""
        features = data[:, :-1].copy()
        labels = data[:, -1:].copy()
        
        if fit:
            feature_min = np.min(features, axis=0)
            feature_max = np.max(features, axis=0)
            params = {
                "feature_min": feature_min.tolist(),
                "feature_max": feature_max.tolist()
            }
            self.normalization_params = params
        else:
            feature_min = np.array(params["feature_min"], dtype=np.float32)
            feature_max = np.array(params["feature_max"], dtype=np.float32)
        
        feature_range = feature_max - feature_min
        feature_range[feature_range == 0] = 1.0
        
        normalized = (features - feature_min) / feature_range
        normalized = np.clip(normalized, 0, 1)
        
        return np.concatenate([normalized, labels], axis=1), params
    
    def filter_and_prepare(self, data: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Vorbereitung von Daten: Filterung + Normalisierung"""
        filtered_data, norm_params = self.normalize_data(data, fit=True)
        
        return filtered_data, {
            "original_shape": data.shape,
            "final_shape": filtered_data.shape,
            "normalization_params": norm_params
        }
