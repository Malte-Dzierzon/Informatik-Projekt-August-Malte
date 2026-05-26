"""
PROZEDURALER PYRAMIDEN-GENERATOR
=================================
Generiert automatisch unendlich viele Pyramiden-Variationen basierend auf mathematischen Formeln.
Pyramide = Quadrat-Basis [0,1]² + Apex-Punkt (Spitze)
"""

import numpy as np
import random
from typing import List, Tuple, Dict
import json


class PyramidGenerator:
    """
    Generiert prozedural Pyramiden mit variabler Basis und Spitze.
    
    Mathematisches Modell:
    - Basis: Quadrat mit 4 Eckpunkten im 2D/3D
    - Apex: Frei wählbarer Punkt über dem Quadrat (als 5. Vertex)
    - Ausgabe: N Pyramiden mit Koordinaten + Label (1 = Pyramide)
    """
    
    def __init__(self, seed=None):
        """
        Initialisiert den Generator.
        
        Args:
            seed: Für reproduzierbare Ergebnisse
        """
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
    
    def generate_base_square_2d(self, offset_x=0.0, offset_y=0.0, scale=1.0) -> List[Tuple[float, float]]:
        """
        Generiert ein 2D Quadrat als Basis für die Pyramide.
        
        Mathematik: 4 Eckpunkte eines Quadrats
        Base: [(0,0), (scale,0), (scale,scale), (0,scale)]
              dann versetzt um (offset_x, offset_y)
        
        Args:
            offset_x: X-Versatz [0, 1)
            offset_y: Y-Versatz [0, 1)
            scale: Skalierung des Quadrats
        
        Returns:
            List von 4 Tupeln: [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        """
        vertices = [
            (offset_x, offset_y),
            (offset_x + scale, offset_y),
            (offset_x + scale, offset_y + scale),
            (offset_x, offset_y + scale)
        ]
        
        # Clamp auf [0, 1]
        vertices = [
            (min(1.0, max(0.0, x)), min(1.0, max(0.0, y)))
            for x, y in vertices
        ]
        
        return vertices
    
    def generate_base_square_3d(self, offset_x=0.0, offset_y=0.0, offset_z=0.0, 
                                 scale=1.0, z_variation=0.1) -> List[Tuple[float, float, float]]:
        """
        Generiert ein 3D Quadrat als Basis (mit leichtem Z-Rauschen).
        
        Args:
            offset_x, offset_y, offset_z: Versätze
            scale: Skalierung
            z_variation: Rauschen in Z-Richtung
        
        Returns:
            List von 4 Tupeln: [(x1,y1,z1), ...]
        """
        vertices_2d = self.generate_base_square_2d(offset_x, offset_y, scale)
        
        vertices_3d = []
        for x, y in vertices_2d:
            z = offset_z + np.random.uniform(-z_variation, z_variation)
            z = max(0.0, min(1.0, z))  # Clamp
            vertices_3d.append((x, y, z))
        
        return vertices_3d
    
    def generate_apex_3d(self, base_center_x=0.5, base_center_y=0.5, 
                        height=0.5, horizontal_offset=0.0) -> Tuple[float, float, float]:
        """
        Generiert den Spitze-Punkt (Apex) einer Pyramide.
        
        Mathematik:
        - Center des Basis-Quadrats: (base_center_x, base_center_y)
        - Spitze versetzt horizontal für "schiefe" Pyramiden: ±horizontal_offset
        - Höhe über dem Quadrat: height
        
        Args:
            base_center_x: Center des Basis-Quadrats (X)
            base_center_y: Center des Basis-Quadrats (Y)
            height: Höhe des Apex über der Basis [0, 1]
            horizontal_offset: Horizontale Versetzung [0, 0.3]
        
        Returns:
            Tuple: (apex_x, apex_y, apex_z)
        """
        # Radius für horizontale Versetzung
        angle = np.random.uniform(0, 2 * np.pi)
        dx = horizontal_offset * np.cos(angle)
        dy = horizontal_offset * np.sin(angle)
        
        apex_x = base_center_x + dx
        apex_y = base_center_y + dy
        apex_z = height
        
        # Clamp
        apex_x = max(0.0, min(1.0, apex_x))
        apex_y = max(0.0, min(1.0, apex_y))
        apex_z = max(0.0, min(1.0, apex_z))
        
        return (apex_x, apex_y, apex_z)
    
    def pyramid_to_feature_vector(self, base_vertices: List, apex: Tuple, 
                                  include_derived_features=True) -> List[float]:
        """
        Konvertiert Pyramiden-Geometrie zu Feature-Vector.
        
        Struktur:
        - Base-Punkte: 4×3 = 12 Werte (x,y,z für jeden Punkt)
        - Apex: 3 Werte (x,y,z)
        - Optional abgeleitete Features: Höhe, Balance, Volume, etc.
        
        Args:
            base_vertices: List von 4 Vertices (3D)
            apex: Apex-Punkt (x,y,z)
            include_derived_features: Zusätzliche Features berechnen
        
        Returns:
            List von Features
        """
        features = []
        
        # Basis-Punkte
        for vertex in base_vertices:
            features.extend(list(vertex))
        
        # Apex
        features.extend(list(apex))
        
        if include_derived_features:
            # Abgeleitete Features
            base_array = np.array(base_vertices)
            apex_array = np.array(apex)
            
            # Höhe (Z des Apex)
            height = apex[2]
            features.append(height)
            
            # Balance: Abstand vom Center
            base_center = base_array[:, :2].mean(axis=0)
            apex_xy = apex_array[:2]
            balance = np.linalg.norm(apex_xy - base_center)
            features.append(balance)
            
            # Base-Area (Quadrat-Seitenlänge)
            p1, p2 = np.array(base_vertices[0][:2]), np.array(base_vertices[1][:2])
            side_length = np.linalg.norm(p2 - p1)
            features.append(side_length)
            
            # Volume-Approximation: base_area * height / 3
            base_area = side_length ** 2
            volume = base_area * height / 3
            features.append(volume)
        
        return features
    
    def generate_pyramid_3d(self, pyramid_id=None, 
                           base_scale_range=(0.3, 1.0),
                           height_range=(0.3, 1.0),
                           horizontal_offset_range=(0.0, 0.3)) -> Tuple[List[float], int]:
        """
        Generiert eine einzelne 3D-Pyramide mit zufälligen Parametern.
        
        Args:
            pyramid_id: Optional eindeutige ID
            base_scale_range: Range für Base-Skalierung
            height_range: Range für Apex-Höhe
            horizontal_offset_range: Range für horizontale Versetzung
        
        Returns:
            Tuple: (feature_vector, label)
                   label=1 für Pyramide
        """
        # Randomisierte Parameter
        base_scale = np.random.uniform(*base_scale_range)
        offset_x = np.random.uniform(0, 1 - base_scale)
        offset_y = np.random.uniform(0, 1 - base_scale)
        offset_z = np.random.uniform(0.0, 0.2)  # Kleine Z-Variation
        height = np.random.uniform(*height_range)
        horizontal_offset = np.random.uniform(*horizontal_offset_range)
        
        # Generiere Base und Apex
        base = self.generate_base_square_3d(
            offset_x=offset_x,
            offset_y=offset_y,
            offset_z=offset_z,
            scale=base_scale,
            z_variation=0.05
        )
        
        base_center_x = offset_x + base_scale / 2
        base_center_y = offset_y + base_scale / 2
        
        apex = self.generate_apex_3d(
            base_center_x=base_center_x,
            base_center_y=base_center_y,
            height=height,
            horizontal_offset=horizontal_offset
        )
        
        # Konvertiere zu Feature-Vector
        feature_vector = self.pyramid_to_feature_vector(base, apex, include_derived_features=True)
        
        return feature_vector, 1  # Label: 1 = Pyramide
    
    def generate_non_pyramid_3d(self) -> Tuple[List[float], int]:
        """
        Generiert einen Non-Pyramid (zufällige Form).
        
        Strategien:
        1. Würfel: 8 Punkte statt Pyramide
        2. Tetraeder: 4 zufällige Punkte
        3. Flache Form: Alle Punkte auf gleicher Z-Ebene
        
        Returns:
            Tuple: (feature_vector, label)
                   label=0 für Nicht-Pyramide
        """
        strategy = np.random.choice([0, 1, 2])
        
        if strategy == 0:  # Würfel (8 Punkte -> Pad auf 5)
            # Generiere 8 Würfel-Punkte
            cube_points = []
            for i in range(8):
                x = (i % 2) * 0.8 + 0.1
                y = ((i // 2) % 2) * 0.8 + 0.1
                z = ((i // 4) % 2) * 0.8 + 0.1
                cube_points.append((x, y, z))
            
            # Nimm erste 4 Punkte + ein extra
            base = cube_points[:4]
            apex = cube_points[4]
        
        elif strategy == 1:  # Flache Form (alle auf gleicher Höhe)
            base = self.generate_base_square_3d(
                offset_x=np.random.uniform(0, 0.2),
                offset_y=np.random.uniform(0, 0.2),
                offset_z=0.5,
                scale=0.8,
                z_variation=0.02
            )
            
            # Apex auch auf gleicher Höhe
            apex = (
                np.random.uniform(0.2, 0.8),
                np.random.uniform(0.2, 0.8),
                0.5
            )
        
        else:  # Tetraeder: 4 zufällige Punkte
            base = [
                (np.random.random(), np.random.random(), np.random.random())
                for _ in range(4)
            ]
            apex = (np.random.random(), np.random.random(), np.random.random())
        
        feature_vector = self.pyramid_to_feature_vector(base, apex, include_derived_features=True)
        
        # Pad auf 19 Features falls zu kurz
        while len(feature_vector) < 19:
            feature_vector.append(np.random.random())
        
        return feature_vector[:19], 0  # Label: 0 = Nicht-Pyramide
    
    def generate_dataset(self, n_pyramids=100, n_non_pyramids=100, 
                        shuffle=True) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generiert ein komplettes Pyramiden-Klassifikations-Dataset.
        
        Args:
            n_pyramids: Anzahl der Pyramiden zu generieren
            n_non_pyramids: Anzahl der Non-Pyramids
            shuffle: Daten mischen
        
        Returns:
            Tuple: (data_array, metadata)
                - data_array: np.array shape (n_samples, 20)
                  [base_4x3 + apex_3 + features_4 + label]
                - metadata: List von Dicts mit Informationen pro Sample
        """
        data = []
        metadata = []
        
        # Generiere Pyramiden
        for i in range(n_pyramids):
            feature_vector, label = self.generate_pyramid_3d()
            feature_vector.append(label)
            data.append(feature_vector)
            
            metadata.append({
                "id": i,
                "type": "pyramid",
                "label": label,
                "n_features": len(feature_vector) - 1
            })
        
        # Generiere Non-Pyramids
        for i in range(n_non_pyramids):
            feature_vector, label = self.generate_non_pyramid_3d()
            feature_vector.append(label)
            data.append(feature_vector)
            
            metadata.append({
                "id": n_pyramids + i,
                "type": "non_pyramid",
                "label": label,
                "n_features": len(feature_vector) - 1
            })
        
        data = np.array(data, dtype=np.float32)
        
        if shuffle:
            indices = np.random.permutation(len(data))
            data = data[indices]
            metadata = [metadata[i] for i in indices]
        
        return data, metadata
    
    def generate_dataset_variable_size(self, n_samples=100, 
                                      min_vertices=4, max_vertices=12,
                                      shuffle=True) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generiert Dataset mit variabler Anzahl von Vertices pro Sample.
        (Feature 4: Dynamischer Input)
        
        Args:
            n_samples: Gesamtanzahl Samples
            min_vertices: Minimale Anzahl Vertices
            max_vertices: Maximale Anzahl Vertices
            shuffle: Daten mischen
        
        Returns:
            Tuple: (data, metadata)
                - data: List von np.arrays unterschiedlicher Länge
                - metadata: Info zu jedem Sample
        """
        data = []
        metadata = []
        
        for i in range(n_samples):
            n_vertices = np.random.randint(min_vertices, max_vertices + 1)
            is_pyramid = np.random.random() > 0.3  # 70% Pyramiden
            
            if is_pyramid:
                feature_vector, label = self.generate_pyramid_3d()
            else:
                feature_vector, label = self.generate_non_pyramid_3d()
            
            # Pad oder Trim zu n_vertices * 3
            target_len = n_vertices * 3
            if len(feature_vector) < target_len:
                feature_vector.extend([0.0] * (target_len - len(feature_vector)))
            elif len(feature_vector) > target_len:
                feature_vector = feature_vector[:target_len]
            
            feature_vector.append(label)
            data.append(np.array(feature_vector, dtype=np.float32))
            
            metadata.append({
                "id": i,
                "n_vertices": n_vertices,
                "label": label,
                "type": "pyramid" if label == 1 else "non_pyramid"
            })
        
        if shuffle:
            indices = np.random.permutation(len(data))
            data = [data[i] for i in indices]
            metadata = [metadata[i] for i in indices]
        
        return data, metadata


# Test
if __name__ == "__main__":
    print("✓ Pyramiden-Generator geladen")
    
    gen = PyramidGenerator(seed=42)
    
    # Test einzelne Pyramide
    pyr, label = gen.generate_pyramid_3d()
    print(f"✓ Einzelne Pyramide: {len(pyr)} Features, Label: {label}")
    
    # Test Dataset
    data, meta = gen.generate_dataset(n_pyramids=10, n_non_pyramids=10)
    print(f"✓ Dataset: {data.shape}, {len(meta)} Metadaten")
    print(f"  - Pyramiden: {sum(1 for m in meta if m['type']=='pyramid')}")
    print(f"  - Non-Pyramids: {sum(1 for m in meta if m['type']=='non_pyramid')}")
    
    # Test Variable-Size Dataset
    var_data, var_meta = gen.generate_dataset_variable_size(n_samples=20, min_vertices=4, max_vertices=8)
    print(f"✓ Variable-Size Dataset: {len(var_data)} Samples")
    print(f"  - Größen: min={min(len(d) for d in var_data)}, max={max(len(d) for d in var_data)}")
