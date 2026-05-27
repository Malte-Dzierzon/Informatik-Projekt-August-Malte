"""
PYRAMIDEN-DATENGENERATOR - Minimalist Version
==============================================
Generiert schnell synthetische Trainingsdaten für Pyramiden-Klassifikation.
Fokus auf mathematische Isolation, Clean-Code und Performance.
"""

import numpy as np
from typing import Tuple, List, Dict


class PyramidGenerator:
    """Generiert Trainings-Daten: Pyramiden (Label=1) vs. andere Formen (Label=0)."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialisiert den Generator mit einem isolierten Zufalls-Zustand."""
        self.rng = np.random.default_rng(seed)
    
    def _generate_pyramid(self) -> Tuple[np.ndarray, int]:
        """Generiert eine Pyramide: 4 Basis-Punkte (3D) + 1 Apex-Punkt (19 Features + Label)."""
        # 4 Eckpunkte der Basis im Raum generieren
        base = self.rng.uniform(0.2, 0.8, (4, 3)).astype(np.float32)
        base[:, 2] *= 0.1  # Z-Ebene (Boden) flach halten
        
        # Berechnung des geometrischen Zentrums der Basis
        base_center = base[:, :2].mean(axis=0)
        apex_xy = base_center + self.rng.uniform(-0.1, 0.1, 2).astype(np.float32)
        apex_z = float(self.rng.uniform(0.5, 1.0))
        
        apex = np.array([apex_xy[0], apex_xy[1], apex_z], dtype=np.float32)
        
        # Ableitung der spezifischen geometrischen Features
        height = np.array([apex_z], dtype=np.float32)
        balance = np.array([np.linalg.norm(apex_xy - base_center)], dtype=np.float32)
        base_area = np.array([np.linalg.norm(base[1] - base[0]) ** 2], dtype=np.float32)
        center_x = np.array([base_center[0]], dtype=np.float32)
        
        # Zusammenführung zum exakt 19-dimensionalen Feature-Vektor
        features = np.concatenate([
            base.flatten(),  # 12 Werte
            apex,            # 3 Werte
            height,          # 1 Wert
            balance,         # 1 Wert
            base_area,       # 1 Wert
            center_x         # 1 Wert
        ], dtype=np.float32)
        
        return features, 1
    
    def _generate_non_pyramid(self) -> Tuple[np.ndarray, int]:
        """Generiert eine mathematische Nicht-Pyramide aus Zufallskoordinaten (Rauschen)."""
        points = self.rng.uniform(0.1, 0.9, (5, 3)).astype(np.float32)
        
        # Struktur-Vektor analog zu den Basis-Features zusammensetzen
        features = np.concatenate([points[:4].flatten(), points[4]], dtype=np.float32)
        
        # Vektor auf die volle Länge von 19 künstlich auffüllen
        padding_size = 19 - len(features)
        padding = self.rng.uniform(0.0, 1.0, padding_size).astype(np.float32)
        features = np.concatenate([features, padding], dtype=np.float32)
        
        return features[:19], 0
    
    def generate_dataset(self, n_pyramids: int = 100, n_non_pyramids: int = 100, 
                         shuffle: bool = True) -> Tuple[np.ndarray, List[Dict]]:
        """Generiert ein balanciertes Klassifikations-Dataset.
        
        Ausgabe-Format: (data_array [n_samples, 20], metadata)
        """
        data = []
        metadata = []
        
        # 1. Pyramiden-Klasse aufbauen
        for i in range(n_pyramids):
            feat, label = self._generate_pyramid()
            label_arr = np.array([label], dtype=np.float32)
            data.append(np.concatenate([feat, label_arr], dtype=np.float32))
            metadata.append({"id": i, "type": "pyramid", "label": 1})
        
        # 2. Alternativ-Klasse aufbauen
        for i in range(n_non_pyramids):
            feat, label = self._generate_non_pyramid()
            label_arr = np.array([label], dtype=np.float32)
            data.append(np.concatenate([feat, label_arr], dtype=np.float32))
            metadata.append({"id": n_pyramids + i, "type": "non_pyramid", "label": 0})
        
        data_matrix = np.array(data, dtype=np.float32)
        
        # 3. Durchmischung (Shuffle), falls aktiviert
        if shuffle and len(data_matrix) > 0:
            idx = self.rng.permutation(len(data_matrix))
            data_matrix = data_matrix[idx]
            metadata = [metadata[i] for i in idx]
        
        return data_matrix, metadata