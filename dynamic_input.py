"""
DYNAMISCHES INPUT-SYSTEM - Minimalist
=======================================
Verarbeitet Input-Daten mit variabler Struktur.
Fokus auf Clean-Code, Ressourceneffizienz und Typsicherheit.
"""

import numpy as np
from typing import Tuple, Dict, Optional


class DynamicInputHandler:
    """Verarbeitet variable Input-Größen und die Min-Max-Normalisierung.
    
    Optimiert für Low-End-Hardware durch speichereffiziente float32-Operationen
    und gezielte In-Place-Speicherallokation.
    """
    
    def __init__(self, max_vertices: int = 12, coordinates_per_vertex: int = 3):
        self.max_vertices = max_vertices
        self.coordinates_per_vertex = coordinates_per_vertex
        self.normalization_params: Dict[str, list] = {}
    
    def set_params(self, params: Optional[Dict]):
        """Setzt die Normalisierungsparameter manuell (z. B. nach einem JSON-Modellimport)."""
        if params and "feature_min" in params and "feature_max" in params:
            self.normalization_params = params

    def normalize_data(self, data: np.ndarray, fit: bool = True, 
                       params: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """Normalisiert alle Feature-Spalten (alle außer der letzten) auf das Intervall [0, 1].
        
        Die Label-Spalte (letzte Spalte des Arrays) bleibt dabei unverändert.
        """
        # 1. Validierung der Eingabestruktur
        if data is None or data.ndim != 2 or data.shape[1] < 2:
            raise ValueError(
                f"Ungültige Datenstruktur. Erwartet wird ein 2D-Array mit mindestens "
                f"2 Spalten (Features + Label). Erhalten: {data.shape if data is not None else 'None'}"
            )
        
        # 2. Datentyp-Standardisierung auf float32 zur RAM-Schonung
        data_float = data.astype(np.float32, copy=False)
        features = data_float[:, :-1]
        labels = data_float[:, -1:]
        
        # 3. Parameter-Logik (Fit oder Transform)
        if fit:
            feature_min = np.min(features, axis=0)
            feature_max = np.max(features, axis=0)
            params = {
                "feature_min": feature_min.tolist(),
                "feature_max": feature_max.tolist()
            }
            self.normalization_params = params
        else:
            # Fallback auf Instanz-Parameter, falls keine Argumente übergeben wurden
            active_params = params if params is not None else self.normalization_params
            if not active_params:
                raise ValueError(
                    "Keine Normalisierungsparameter vorhanden. "
                    "Führen Sie zuerst fit=True aus oder laden Sie ein gültiges Modell."
                )
            
            feature_min = np.array(active_params["feature_min"], dtype=np.float32)
            feature_max = np.array(active_params["feature_max"], dtype=np.float32)
            params = active_params

        # 4. Division durch Null verhindern (falls min == max)
        feature_range = feature_max - feature_min
        feature_range[feature_range == 0.0] = 1.0
        
        # 5. Speicher-Optimierung: Gezielte Pre-Allocation
        normalized_data = np.empty_like(data_float)
        normalized_data[:, -1:] = labels  # Sparendes Kopieren der Labels
        
        # In-Place Operationen auf dem Feature-Slice verhindern RAM-Spitzen
        target_features = normalized_data[:, :-1]
        np.subtract(features, feature_min, out=target_features)
        np.divide(target_features, feature_range, out=target_features)
        np.clip(target_features, 0.0, 1.0, out=target_features)
        
        return normalized_data, params
    
    def filter_and_prepare(self, data: np.ndarray, fit: bool = True) -> Tuple[np.ndarray, Dict]:
        """Bereitet die Geometriedaten vollständig vor.
        
        Kapselt die Validierung, Filterung und die mathematische Skalierung.
        """
        normalized_data, norm_params = self.normalize_data(data, fit=fit)
        
        return normalized_data, {
            "original_shape": data.shape,
            "final_shape": normalized_data.shape,
            "normalization_params": norm_params
        }