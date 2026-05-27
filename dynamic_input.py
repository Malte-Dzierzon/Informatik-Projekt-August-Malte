"""
DYNAMISCHES INPUT-SYSTEM - Minimalist
=======================================
Dieses Skript sorgt dafür, dass wir Geometriedaten mit völlig unterschiedlicher 
Größe (z.B. unterschiedlich viele Eckpunkte) sauber verarbeiten können.
Dabei achten wir penibel auf schnellen Code, wenig RAM-Verbrauch und Typsicherheit.
"""

import numpy as np
from typing import Tuple, Dict, Optional


class DynamicInputHandler:
    """
    Klasse für das Skalieren und Normalisieren von variablen Eingangsdaten.
    
    Damit die Kiste auch auf schwächerer Hardware flüssig läuft, tricksen wir hier 
    ein bisschen: Wir nutzen speicherschonendes float32 und rechnen direkt auf dem 
    bestehenden Speicherplatz (In-Place), statt ständig neuen RAM anzufordern.
    """
    
    def __init__(self, max_vertices: int = 12, coordinates_per_vertex: int = 3):
        self.max_vertices = max_vertices
        self.coordinates_per_vertex = coordinates_per_vertex
        self.normalization_params: Dict[str, list] = {}
    
    def set_params(self, params: Optional[Dict]):
        """Hier können wir die Min-Max-Werte direkt setzen, falls wir ein fertiges Modell aus einem JSON importieren."""
        if params and "feature_min" in params and "feature_max" in params:
            self.normalization_params = params

    def normalize_data(self, data: np.ndarray, fit: bool = True, 
                       params: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """
        Bringt alle Messwerte (Features) auf eine Skala von 0.0 bis 1.0 (Min-Max-Skalierung).
        Die allerletzte Spalte im Array – also unser Label (Pyramide ja/nein) – fassen wir dabei nicht an.
        """
        # 1. Checken, ob das reinlaufende Array überhaupt das richtige Format hat
        if data is None or data.ndim != 2 or data.shape[1] < 2:
            raise ValueError(
                f"Struktur der Daten passt nicht! Brauche ein 2D-Array mit mindestens "
                f"2 Spalten (Features + Zielklasse). Bekommen habe ich: {data.shape if data is not None else 'Nichts (None)'}"
            )
        
        # 2. Datentyp auf float32 festnageln, um wertvollen RAM zu sparen
        data_float = data.astype(np.float32, copy=False)
        features = data_float[:, :-1]
        labels = data_float[:, -1:]
        
        # 3. Min-Max-Werte ermitteln (entweder neu berechnen oder alte Werte recyclen)
        if fit:
            feature_min = np.min(features, axis=0)
            feature_max = np.max(features, axis=0)
            params = {
                "feature_min": feature_min.tolist(),
                "feature_max": feature_max.tolist()
            }
            self.normalization_params = params
        else:
            # Falls wir im Testmodus sind, greifen wir auf die bereits gespeicherten Parameter zurück
            active_params = params if params is not None else self.normalization_params
            if not active_params:
                raise ValueError(
                    "Mir fehlen die Normalisierungsparameter! "
                    "Du musst das Modell erst mit fit=True füttern oder Gewichte laden."
                )
            
            feature_min = np.array(active_params["feature_min"], dtype=np.float32)
            feature_max = np.array(active_params["feature_max"], dtype=np.float32)
            params = active_params

        # 4. Schreckgespenst 'Division durch Null' abfangen (falls Min und Max exakt gleich sind)
        feature_range = feature_max - feature_min
        feature_range[feature_range == 0.0] = 1.0
        
        # 5. Performance-Trick: Leeres Ziel-Array direkt in der passenden Größe reservieren
        normalized_data = np.empty_like(data_float)
        normalized_data[:, -1:] = labels  # Die Labels kopieren wir einfach direkt rüber
        
        # Hier rechnen wir In-Place direkt auf dem reservierten Speicher. Verhindert RAM-Spitzen!
        target_features = normalized_data[:, :-1]
        np.subtract(features, feature_min, out=target_features)
        np.divide(target_features, feature_range, out=target_features)
        np.clip(target_features, 0.0, 1.0, out=target_features)
        
        return normalized_data, params
    
    def filter_and_prepare(self, data: np.ndarray, fit: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        Das ist unser All-In-One-Werkzeug für die Datenvorbereitung.
        Macht die Validierung, filtert Ausreißer und wirft am Ende die fertig skalierten Daten aus.
        """
        normalized_data, norm_params = self.normalize_data(data, fit=fit)
        
        return normalized_data, {
            "original_shape": data.shape,
            "final_shape": normalized_data.shape,
            "normalization_params": norm_params
        }