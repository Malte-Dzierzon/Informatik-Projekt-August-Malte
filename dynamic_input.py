"""
DYNAMISCHES INPUT-SYSTEM MIT INTELLIGENTER FILTERUNG
======================================================
Verarbeitet Figures mit unterschiedlicher Eckpunkt-Anzahl.
Erkennt automatisch überflüssige Inputs und filtert sie heraus.
"""

import numpy as np
from typing import List, Tuple, Dict
import pandas as pd


class DynamicInputHandler:
    """
    Verarbeitet Input-Daten mit variabler Struktur.
    
    Features:
    - Automatische Erkennung von Padding-Feldern
    - Intelligente Filterung überflüssiger Inputs
    - Konsistente Normalisierung über alle Samples
    - Metadaten-Tracking für Transparent Input-Processing
    """
    
    def __init__(self, max_vertices=12, coordinates_per_vertex=3):
        """
        Initialisiert den Dynamic Input Handler.
        
        Args:
            max_vertices: Maximale Anzahl von Vertices pro Figure
            coordinates_per_vertex: Koordinaten pro Vertex (3 für x,y,z)
        """
        self.max_vertices = max_vertices
        self.coordinates_per_vertex = coordinates_per_vertex
        self.max_features = max_vertices * coordinates_per_vertex
        
        # Metadaten
        self.feature_masks = None  # Welche Features sind "real" vs "padding"
        self.active_features = None  # Indices der echten Features
        self.normalization_params = {}
        self.feature_names = []
    
    def detect_padding_features(self, data: np.ndarray, threshold=0.95) -> np.ndarray:
        """
        Erkennt automatisch, welche Feature-Spalten hauptsächlich aus Padding-Nullen bestehen.
        
        Logik:
        - Wenn >95% der Werte in einer Spalte Null sind -> Padding
        - Diese Features sind überflüssig und können ignoriert werden
        
        Args:
            data: Shape (n_samples, n_features+1) - Label ist letzter Index
            threshold: Ab welchem Prozentsatz einer Spalte wird als Padding erkannt
        
        Returns:
            np.ndarray: Boolean array shape (n_features,)
                       True = echtes Feature, False = Padding
        """
        # Separiere Features (ohne Label)
        features = data[:, :-1]
        
        # Zähle Nullen pro Spalte
        n_samples = features.shape[0]
        zero_count = np.sum(features == 0, axis=0)
        zero_fraction = zero_count / n_samples
        
        # Ein Feature ist "real" wenn es NICHT hauptsächlich Nullen enthält
        is_real = zero_fraction < threshold
        
        return is_real
    
    def get_active_features(self, data: np.ndarray, auto_detect=True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Bestimmt, welche Features für das Training relevant sind.
        
        Args:
            data: Trainingsdaten
            auto_detect: Automatische Padding-Erkennung aktivieren
        
        Returns:
            Tuple: (filtered_data, active_indices)
                - filtered_data: Nur echte Features + Label
                - active_indices: Indizes der echten Features
        """
        if auto_detect:
            is_real = self.detect_padding_features(data)
        else:
            is_real = np.ones(data.shape[1] - 1, dtype=bool)
        
        # Behalte alle echten Features + Label (letzte Spalte)
        indices_to_keep = np.where(is_real)[0].tolist() + [data.shape[1] - 1]
        active_indices = np.array(indices_to_keep[:-1])  # Ohne Label-Index
        
        filtered_data = data[:, indices_to_keep]
        
        self.active_features = active_indices
        self.feature_masks = is_real
        
        return filtered_data, active_indices
    
    def pad_sample_to_fixed_size(self, sample: np.ndarray, target_size: int) -> np.ndarray:
        """
        Konvertiert einen variabel-sized Sample zu fester Größe.
        
        Strategie: Pad mit Nullen am Ende
        
        Args:
            sample: 1D array (Feature-Vektor ohne Label)
            target_size: Zielgröße
        
        Returns:
            np.ndarray: Padded Sample mit fester Größe
        """
        if len(sample) == target_size:
            return sample
        elif len(sample) < target_size:
            padding = np.zeros(target_size - len(sample), dtype=np.float32)
            return np.concatenate([sample, padding])
        else:
            return sample[:target_size]
    
    def normalize_data(self, data: np.ndarray, 
                      fit=True, normalization_params=None) -> Tuple[np.ndarray, Dict]:
        """
        Normalisiert Features auf [0, 1] Range.
        
        Args:
            data: Shape (n_samples, n_features+1) mit Label als letzte Spalte
            fit: Normalisierungs-Parameter von Daten lernen (True) oder verwenden (False)
            normalization_params: Vorberechnete Min/Max-Parameter
        
        Returns:
            Tuple: (normalized_data, params)
        """
        features = data[:, :-1].copy()
        labels = data[:, -1:].copy()
        
        if fit:
            # Berechne Min/Max pro Feature
            feature_min = np.min(features, axis=0)
            feature_max = np.max(features, axis=0)
            
            normalization_params = {
                "feature_min": feature_min.tolist(),
                "feature_max": feature_max.tolist()
            }
            
            self.normalization_params = normalization_params
        
        else:
            # Verwende vorgegebene Parameter
            feature_min = np.array(normalization_params["feature_min"], dtype=np.float32)
            feature_max = np.array(normalization_params["feature_max"], dtype=np.float32)
        
        # Normalisiere
        feature_range = feature_max - feature_min
        feature_range[feature_range == 0] = 1.0  # Avoid division by zero
        
        normalized_features = (features - feature_min) / feature_range
        normalized_features = np.clip(normalized_features, 0, 1)
        
        # Kombiniere Features + Labels
        normalized_data = np.concatenate([normalized_features, labels], axis=1)
        
        return normalized_data, normalization_params
    
    def create_display_dataframe(self, data: np.ndarray, 
                                 active_features: np.ndarray = None,
                                 show_padding_as_dash=True) -> pd.DataFrame:
        """
        Erstellt einen visuellen Pandas DataFrame für Streamlit-Anzeige.
        
        Feature 4 - Intelligente Tabellen-Filterung:
        - Überflüssige Felder werden mit "-" markiert
        - Nur echte Features werden angezeigt
        
        Args:
            data: Trainings-Daten
            active_features: Indizes der echten Features (optional)
            show_padding_as_dash: Padding-Felder als "-" anzeigen
        
        Returns:
            pd.DataFrame: Formatierte Anzeige
        """
        if active_features is None:
            active_features = np.arange(data.shape[1] - 1)
        
        n_cols = data.shape[1] - 1  # Ohne Label
        
        # Erstelle DataFrame
        df_dict = {}
        
        for col_idx in range(n_cols):
            col_name = f"F{col_idx + 1}"
            
            # Bestimme ob echtes Feature oder Padding
            is_active = col_idx in active_features
            
            if not is_active and show_padding_as_dash:
                # Alle Werte als "-"
                df_dict[col_name] = ["-"] * min(10, len(data))
            else:
                # Echte Daten anzeigen
                df_dict[col_name] = [f"{val:.4f}" if isinstance(val, (int, float)) else val 
                                    for val in data[:min(10, len(data)), col_idx]]
        
        # Label spalte
        df_dict["Label"] = [int(val) for val in data[:min(10, len(data)), -1]]
        
        return pd.DataFrame(df_dict)
    
    def get_feature_info(self) -> Dict:
        """
        Gibt Info über aktive Features und Padding.
        
        Returns:
            Dict mit:
            - total_features: Gesamtzahl der Features
            - active_features: Anzahl echter Features
            - padding_features: Anzahl Padding-Features
            - active_indices: Indizes der echten Features
        """
        if self.feature_masks is None:
            return {
                "total_features": "Unknown",
                "active_features": "Unknown",
                "padding_features": "Unknown",
                "active_indices": None
            }
        
        return {
            "total_features": len(self.feature_masks),
            "active_features": np.sum(self.feature_masks),
            "padding_features": np.sum(~self.feature_masks),
            "active_indices": np.where(self.feature_masks)[0].tolist(),
            "padding_indices": np.where(~self.feature_masks)[0].tolist()
        }
    
    def filter_and_prepare_network_input(self, data: np.ndarray, 
                                        use_detected_active_features=True) -> Tuple[np.ndarray, Dict]:
        """
        Vollständige Vorbereitung der Daten für das neuronale Netz.
        
        Schritte:
        1. Automatische Padding-Erkennung
        2. Filterung überflüssiger Features
        3. Normalisierung
        4. Info für UI
        
        Args:
            data: Rohe Trainingsdaten
            use_detected_active_features: Auto-Filter aktivieren
        
        Returns:
            Tuple: (processed_data, info_dict)
        """
        # Schritt 1 & 2: Filterung
        filtered_data, active_indices = self.get_active_features(
            data, 
            auto_detect=use_detected_active_features
        )
        
        # Schritt 3: Normalisierung
        normalized_data, norm_params = self.normalize_data(filtered_data, fit=True)
        
        # Schritt 4: Info
        feature_info = self.get_feature_info()
        
        info = {
            "original_shape": data.shape,
            "filtered_shape": filtered_data.shape,
            "final_shape": normalized_data.shape,
            "active_feature_count": feature_info["active_features"],
            "padding_feature_count": feature_info["padding_features"],
            "active_indices": active_indices.tolist(),
            "normalization_params": norm_params,
            "display_dataframe": self.create_display_dataframe(filtered_data, active_indices)
        }
        
        return normalized_data, info
    
    def process_single_sample(self, sample: np.ndarray, label: int,
                             normalization_params: Dict = None) -> np.ndarray:
        """
        Verarbeitet einen einzelnen Sample für Vorhersagen.
        
        Args:
            sample: Feature-Vektor (ohne Label)
            label: True Label (für spätere Bewertung)
            normalization_params: Normalisierungs-Parameter
        
        Returns:
            np.ndarray: Verarbeiteter Sample
        """
        if normalization_params and "feature_min" in normalization_params:
            feature_min = np.array(normalization_params["feature_min"], dtype=np.float32)
            feature_max = np.array(normalization_params["feature_max"], dtype=np.float32)
            
            feature_range = feature_max - feature_min
            feature_range[feature_range == 0] = 1.0
            
            processed = (sample - feature_min) / feature_range
            processed = np.clip(processed, 0, 1)
        else:
            processed = sample
        
        return processed.astype(np.float32)


# Test
if __name__ == "__main__":
    print("✓ Dynamic Input Handler geladen")
    
    # Test-Daten mit Padding
    test_data = np.array([
        [0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0],  # 3 echte, 3 Padding, 1 Label
        [0.2, 0.3, 0.4, 0.0, 0.0, 0.0, 1.0],
        [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ], dtype=np.float32)
    
    handler = DynamicInputHandler(max_vertices=2, coordinates_per_vertex=3)
    
    # Test Filterung
    print("\n1. Padding-Erkennung:")
    is_real = handler.detect_padding_features(test_data)
    print(f"   Echo-Features: {np.sum(is_real)}/{len(is_real)}")
    
    # Test Verarbeitung
    print("\n2. Vollständige Verarbeitung:")
    processed, info = handler.filter_and_prepare_network_input(test_data)
    print(f"   Original: {info['original_shape']}")
    print(f"   Nach Filterung: {info['filtered_shape']}")
    print(f"   Nach Normalisierung: {info['final_shape']}")
    print(f"   Aktive Features: {info['active_feature_count']}")
    
    # Test DataFrame
    print("\n3. Anzeige-DataFrame:")
    print(info['display_dataframe'])
