"""
PYRAMIDEN-DATENGENERATOR - Dynamische Version (REPARIERT)
=========================================================
Generiert flexibel synthetische Trainingsdaten für die Pyramiden-Klassifikation.
Unterstützt variable Eckpunkte, echtes Zero-Padding für ungenutzte Dimensionen.
"""

import numpy as np
from typing import Tuple, List, Dict, Optional


class PyramidGenerator:
    """
    Generiert maßgeschneiderte Trainings-Daten für das neuronale Netzwerk.
    
    Unterscheidet sauber zwischen echten Pyramiden (Klasse 1) und unregelmäßigen 
    Störobjekten (Klasse 0). Unterstützt dynamisches Auffüllen mit Nullen (Padding).
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialisiert den Generator mit einem isolierten Zufalls-Zustand (RNG)."""
        self.rng = np.random.default_rng(seed)
    
    def _generate_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        """
        Generiert eine mathematisch korrekte Pyramide.
        Feste 5 Eckpunkte (4 Basis + 1 Spitze). Rest wird hart ge-paddet (0.0).
        """
        coord_features_len = max_vertices * coords_per_vertex
        coord_block = np.zeros(coord_features_len, dtype=np.float32)
        
        # Eine Pyramide hat exakt 5 Punkte (wenn max_vertices ausreicht)
        pyr_vertices = min(5, max_vertices)
        base_vertices = pyr_vertices - 1
        
        if base_vertices < 3:
            # Fallback falls max_vertices absurd klein gewählt wurde
            base_vertices = 3
            pyr_vertices = 4

        # 1. Basis-Punkte (Boden) im Raum generieren (Wertebereich 0.2 bis 0.8)
        base = self.rng.uniform(0.2, 0.8, (base_vertices, coords_per_vertex)).astype(np.float32)
        if coords_per_vertex >= 3:
            base[:, 2] = 0.2  # Flacher Boden, leicht angehoben von 0.0, damit es sich vom Padding abhebt
            
        # 2. Berechnung des Zentrums für die Spitze
        base_center = base[:, :2].mean(axis=0)
        apex_xy = base_center + self.rng.uniform(-0.05, 0.05, 2).astype(np.float32)
        
        # Spitze zusammenbauen
        apex = np.zeros(coords_per_vertex, dtype=np.float32)
        apex[0] = apex_xy[0]
        if coords_per_vertex > 1:
            apex[1] = apex_xy[1]
        if coords_per_vertex >= 3:
            apex[2] = self.rng.uniform(0.6, 0.9)  # Klar erkennbare Höhe über dem Boden
            
        # 3. In den Koordinaten-Block schreiben
        flat_base = base.flatten()
        coord_block[:len(flat_base)] = flat_base
        coord_block[len(flat_base):len(flat_base)+coords_per_vertex] = apex
        
        # 4. Geometrische Zusatzfeatures berechnen
        height = apex[2] if coords_per_vertex >= 3 else 1.0
        balance = np.linalg.norm(apex_xy - base_center)
        base_area = np.linalg.norm(base[1] - base[0]) ** 2 if len(base) > 1 else 1.0
        center_x = base_center[0]
        
        zusatz_features = np.array([height, balance, base_area, center_x], dtype=np.float32)
        
        # Zusammenfügen zu einem flachen Feature-Vektor
        return np.concatenate([coord_block, zusatz_features], dtype=np.float32)
    
    def _generate_non_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        """
        Generiert ein unregelmäßiges Störobjekt (Rauschen / andere Form).
        Nutzt den gleichen Wertebereich wie die Pyramide, um Normalisierungsfehler zu vermeiden.
        """
        coord_features_len = max_vertices * coords_per_vertex
        coord_block = np.zeros(coord_features_len, dtype=np.float32)
        
        # Zufällige Punktanzahl für das Störobjekt
        effektive_punkte = self.rng.integers(3, max_vertices + 1) if max_vertices > 3 else max_vertices
        anzahl_werte = effektive_punkte * coords_per_vertex
        
        # Geometrie-Rauschen im exakt GLEICHEN Wertebereich (0.1 bis 0.9) wie die Pyramide!
        # Wichtig: Keine Negativwerte wie -10.0 mehr, das zerschießt die Skalierung der Nullen!
        raw_points = self.rng.uniform(0.1, 0.9, anzahl_werte).astype(np.float32)
        
        coord_block[:anzahl_werte] = raw_points
        
        # Zusatzfeatures generieren, die sich von echten Pyramiden unterscheiden
        height = self.rng.uniform(0.0, 0.5)  # Entweder zu flach oder völlig unproportional
        balance = self.rng.uniform(0.5, 1.5) # Völlig unausbalanciert
        base_area = self.rng.uniform(0.0, 2.0)
        center_x = self.rng.uniform(0.0, 1.0)
        
        zusatz_features = np.array([height, balance, base_area, center_x], dtype=np.float32)
        
        return np.concatenate([coord_block, zusatz_features], dtype=np.float32)
    
    def generate_dataset(self, max_vertices: int = 12, coords_per_vertex: int = 3, 
                         n_pyramids: int = 100, n_non_pyramids: int = 100, 
                         shuffle: bool = True) -> Tuple[np.ndarray, List[Dict]]:
        """Generiert ein perfekt balanciertes Gesamt-Dataset für das Training."""
        data = []
        metadata = []
        
        # 1. Echte Pyramiden
        for i in range(n_pyramids):
            feat = self._generate_pyramid(max_vertices, coords_per_vertex)
            label_arr = np.array([1.0], dtype=np.float32)
            data.append(np.concatenate([feat, label_arr], dtype=np.float32))
            metadata.append({"id": i, "type": "pyramid", "label": 1})
        
        # 2. Andere geometrische Formen
        for i in range(n_non_pyramids):
            feat = self._generate_non_pyramid(max_vertices, coords_per_vertex)
            label_arr = np.array([0.0], dtype=np.float32)
            data.append(np.concatenate([feat, label_arr], dtype=np.float32))
            metadata.append({"id": n_pyramids + i, "type": "non_pyramid", "label": 0})
        
        data_matrix = np.array(data, dtype=np.float32)
        
        # 3. Durchmischen
        if shuffle and len(data_matrix) > 0:
            idx = self.rng.permutation(len(data_matrix))
            data_matrix = data_matrix[idx]
            metadata = [metadata[x] for x in idx]
        
        return data_matrix, metadata

    def generate_single_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        return self._generate_pyramid(max_vertices, coords_per_vertex)

    def generate_single_non_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        return self._generate_non_pyramid(max_vertices, coords_per_vertex)