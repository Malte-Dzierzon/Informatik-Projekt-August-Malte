"""
PYRAMIDEN-DATENGENERATOR - Projekt-Version (STRIKT & DYNAMISCH)
===============================================================
Generiert synthetische Trainingsdaten nach fester Projektvorgabe:
- Pyramide (Klasse 1): Exakt 5 Punkte (4 Basis-Punkte auf einer Ebene + 1 Spitze).
- Nicht-Pyramide (Klasse 0): Hochgradig dynamische, variable Störobjekte.
"""

import numpy as np
from typing import Tuple, List, Dict, Optional

PYRAMIDEN_KERNPUNKTE = 5  # 4 Basispunkte + 1 Apex

class PyramidGenerator:
    """
    Generiert Daten für das neuronale Netzwerk. Hält sich strikt an die 5-Punkt-Regel
    für Pyramiden und baut dynamische, knifflige Gegenbeispiele für Klasse 0.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialisiert den Generator mit einem isolierten Zufalls-Zustand (RNG)."""
        self.rng = np.random.default_rng(seed)
    
    def _generate_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        """
        Generiert eine strikte Pyramide nach Projektdefinition:
        Exakt 5 Punkte (4 Basis-Punkte auf exakt derselben Z-Ebene + 1 echte Spitze).
        Der Rest bis max_vertices wird mit NaN aufgefüllt (sichere Markierung für "kein Punkt").
        """
        coord_features_len = max_vertices * coords_per_vertex
        # Use NaN padding instead of zero-padding to avoid accidental (0,0,0) points
        coord_block = np.full(coord_features_len, np.nan, dtype=np.float32)
        
        # 1. Zentrum und Radien für eine saubere viereckige Basis definieren
        cx, cy = self.rng.uniform(0.4, 0.6, 2)
        rx, ry = self.rng.uniform(0.15, 0.25, 2)
        z_basis = 0.2  # Absolut flache Ebene für den Boden
        
        # 4 Basis-Punkte (Gegen den Uhrzeigersinn)
        base = np.array([
            [cx + rx, cy + ry, z_basis],  # Punkt 1
            [cx - rx, cy + ry, z_basis],  # Punkt 2
            [cx - rx, cy - ry, z_basis],  # Punkt 3
            [cx + rx, cy - ry, z_basis]   # Punkt 4
        ], dtype=np.float32)
        
        # 2. Die einzelne Spitze (Apex) genau über dem Zentrum setzen
        apex = np.array([
            cx + self.rng.uniform(-0.02, 0.02),
            cy + self.rng.uniform(-0.02, 0.02),
            self.rng.uniform(0.6, 0.85)  # Deutlich höher als die Basis
        ], dtype=np.float32)
        
        # Koordinaten an den Anfang des Blocks schreiben (Exakt 5 Punkte = 15 Werte bei 3D)
        flat_geometry = np.vstack([base, apex]).flatten()
        coord_block[:len(flat_geometry)] = flat_geometry[:coord_features_len]
        
        # 3. Geometrische Zusatzfeatures berechnen
        height = apex[2] - z_basis
        balance = np.linalg.norm(apex[:2] - np.array([cx, cy]))
        base_area = float((rx * 2) * (ry * 2))
        center_x = cx
        
        zusatz_features = np.array([height, balance, base_area, center_x], dtype=np.float32)
        return np.concatenate([coord_block, zusatz_features], dtype=np.float32)
    
    def _generate_non_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        """
        Generiert hochvariable und dynamische Nicht-Pyramiden.
        Erzeugt gezielt "Fallen" für die KI, um echtes Verständnis zu erzwingen.
        """
        coord_features_len = max_vertices * coords_per_vertex
        # Use NaN padding to mark unused points (prevents them from being interpreted as origin)
        coord_block = np.full(coord_features_len, np.nan, dtype=np.float32)
        
        # Zufällige Auswahl eines fiesen Stör-Typs für maximale Variation
        stör_typ = self.rng.choice(["warped_5point", "flat_5point", "dynamic_prism", "pure_chaos"])
        
        if stör_typ == "warped_5point":
            # FALLE 1: Hat 5 Punkte, sieht aus wie eine Pyramide, aber die Basis ist NICHT auf einer Ebene!
            cx, cy = self.rng.uniform(0.4, 0.6, 2)
            rx, ry = self.rng.uniform(0.15, 0.25, 2)
            
            # Z-Koordinaten der Basis leicht verzerren (keine flache Ebene mehr)
            z_warped = self.rng.uniform(0.15, 0.35, 4)
            
            base = np.array([
                [cx + rx, cy + ry, z_warped[0]],
                [cx - rx, cy + ry, z_warped[1]],
                [cx - rx, cy - ry, z_warped[2]],
                [cx + rx, cy - ry, z_warped[3]]
            ], dtype=np.float32)
            
            apex = np.array([cx, cy, self.rng.uniform(0.6, 0.85)], dtype=np.float32)
            flat_geometry = np.vstack([base, apex]).flatten()
            coord_block[:len(flat_geometry)] = flat_geometry[:coord_features_len]
            
        elif stör_typ == "flat_5point":
            # FALLE 2: Hat 5 Punkte, aber die Spitze ist platt auf den Boden gedrückt (2D-Fläche)
            cx, cy = self.rng.uniform(0.4, 0.6, 2)
            rx, ry = self.rng.uniform(0.15, 0.25, 2)
            z_ebene = 0.2
            
            base = np.array([
                [cx + rx, cy + ry, z_ebene], [cx - rx, cy + ry, z_ebene],
                [cx - rx, cy - ry, z_ebene], [cx + rx, cy - ry, z_ebene]
            ], dtype=np.float32)
            
            apex = np.array([cx, cy, z_ebene], dtype=np.float32)  # Keine Höhe!
            flat_geometry = np.vstack([base, apex]).flatten()
            coord_block[:len(flat_geometry)] = flat_geometry[:coord_features_len]
            
        elif stör_typ == "dynamic_prism" and max_vertices >= 6:
            # GEOMETRIE-VARIATION: Ein Prisma/Würfel mit dynamisch vielen Punkten (Nutzt vollen App-Umfang)
            effektive_punkte = self.rng.integers(6, max_vertices + 1)
            half_pts = effektive_punkte // 2
            
            # Erzeuge zwei parallele Platten im Raum
            base_pts = self.rng.uniform(0.2, 0.8, (half_pts, coords_per_vertex)).astype(np.float32)
            if coords_per_vertex >= 3: base_pts[:, 2] = 0.2
                
            top_pts = base_pts.copy()
            if coords_per_vertex >= 3: top_pts[:, 2] = self.rng.uniform(0.6, 0.8)
                
            combined = np.vstack([base_pts, top_pts])
            coord_block[:combined.size] = combined.flatten()[:coord_features_len]
            
        else:
            # PURE DYNAMIK: Völlig zufälliges Polygon-Chaos im erlaubten Raum
            effektive_punkte = self.rng.integers(3, max_vertices + 1)
            anzahl_werte = min(effektive_punkte * coords_per_vertex, coord_features_len)
            coord_block[:anzahl_werte] = self.rng.uniform(0.2, 0.8, anzahl_werte).astype(np.float32)

        # Zusatzfeatures generieren (Weichen bewusst von den echten Pyramidenwerten ab)
        height = self.rng.uniform(0.0, 0.5) if stör_typ == "flat_5point" else self.rng.uniform(0.1, 0.9)
        balance = self.rng.uniform(0.3, 1.5)
        base_area = self.rng.uniform(0.05, 0.5)
        center_x = self.rng.uniform(0.2, 0.8)
        
        zusatz_features = np.array([height, balance, base_area, center_x], dtype=np.float32)
        return np.concatenate([coord_block, zusatz_features], dtype=np.float32)
    
    def generate_dataset(self, max_vertices: int = 12, coords_per_vertex: int = 3, 
                         n_pyramids: int = 100, n_non_pyramids: int = 100, 
                         shuffle: bool = True) -> Tuple[np.ndarray, List[Dict]]:
        """Generiert ein perfekt balanciertes Gesamt-Dataset für das KI-Training."""
        data = []
        metadata = []
        
        # 1. Echte, strikte Pyramiden generieren
        for i in range(n_pyramids):
            feat = self._generate_pyramid(max_vertices, coords_per_vertex)
            label_arr = np.array([1.0], dtype=np.float32)
            data.append(np.concatenate([feat, label_arr], dtype=np.float32))
            metadata.append({"id": i, "type": "pyramid", "label": 1})
        
        # 2. Variable, dynamische Nicht-Pyramiden generieren
        for i in range(n_non_pyramids):
            feat = self._generate_non_pyramid(max_vertices, coords_per_vertex)
            label_arr = np.array([0.0], dtype=np.float32)
            data.append(np.concatenate([feat, label_arr], dtype=np.float32))
            metadata.append({"id": n_pyramids + i, "type": "non_pyramid", "label": 0})
        
        data_matrix = np.array(data, dtype=np.float32)
        
        # 3. Datensatz sauber durchmischen
        if shuffle and len(data_matrix) > 0:
            idx = self.rng.permutation(len(data_matrix))
            data_matrix = data_matrix[idx]
            metadata = [metadata[x] for x in idx]
        
        return data_matrix, metadata

    def generate_single_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        return self._generate_pyramid(max_vertices, coords_per_vertex)

    def generate_single_non_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        return self._generate_non_pyramid(max_vertices, coords_per_vertex)