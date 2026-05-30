"""
DYNAMISCHES INPUT-SYSTEM - Rotationsinvariant & Minimalist
===========================================================
Verarbeitet Geometriedaten mit variabler Vertex-Anzahl und transformiert
X,Y,Z-Koordinaten in rotationsinvariante Punktabstände (Distanzen).
Damit man objekte mit 4 Verteces haben kann, aber auchgleichzeitig welche mit 46, 
ohne dass die KI durcheinander kommt.
"""

import numpy as np
from typing import Tuple, Dict, Optional

from pyramid_generator import PYRAMIDEN_KERNPUNKTE

# ------------------------------------------------------------------
# KONSTANTEN & VORDEFINIERTES FEATURE-SET
# ------------------------------------------------------------------
# C(5,2) = 10 paarweise Abstände zwischen den 5 Kernpunkten
_ANZAHL_DISTANZEN: int = (PYRAMIDEN_KERNPUNKTE * (PYRAMIDEN_KERNPUNKTE - 1)) // 2


class DynamicInputHandler:
    """
    Skaliert, transformiert und normalisiert variable Eingangsdaten.

    Nutzt float32 und In-Place-Operationen für minimalen Speicherverbrauch.
    """

    def __init__(self, max_vertices: int = 12, coordinates_per_vertex: int = 3):
        self.max_vertices = max_vertices
        self.coordinates_per_vertex = coordinates_per_vertex
        self.normalization_params: Dict[str, list] = {}

# ------------------------------------------------------------------
# DYNAMIC INPUT HANDLER
# ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # GEOMETRISCHE TRANSFORMATION
    # ------------------------------------------------------------------

    def _transform_to_distances(self, raw_features: np.ndarray) -> np.ndarray:
        """
        Transformiert rohe X,Y,Z-Koordinaten in rotationsinvariante Abstände.

        Ablauf:
        1. Extrahiert die ersten PYRAMIDEN_KERNPUNKTE (=5) Punkte.
           Hinweis: Vertices 6–max_vertices fließen bewusst nicht in die
           Distanzberechnung ein – die Pyramidendefinition verlangt exakt 5 Punkte.
        2. Berechnet alle C(5,2) = 10 paarweisen Abstände.
           Fehlt ein Punkt (NaN), wird der Sentinel-Wert -1.0 gesetzt.
        3. Sortiert die Abstände für Permutationsinvarianz.
        4. Hängt Zusatzfeatures (ab Index max_vertices * coords_per_vertex) an.
        """
        num_samples = raw_features.shape[0]

        # Koordinatenblock der ersten 5 Punkte extrahieren (= PYRAMIDEN_KERNPUNKTE * 3 Werte)
        coords_len = PYRAMIDEN_KERNPUNKTE * self.coordinates_per_vertex
        if raw_features.shape[1] < coords_len:
            # Fehlende Spalten mit NaN auffüllen
            pad = np.full((num_samples, coords_len - raw_features.shape[1]), np.nan, dtype=np.float32)
            coords_raw = np.hstack([raw_features, pad])
        else:
            coords_raw = raw_features[:, :coords_len]

        # Reshape: [Samples, 5 Punkte, 3 Koordinaten]
        coords = coords_raw.reshape(num_samples, PYRAMIDEN_KERNPUNKTE, self.coordinates_per_vertex)

        # Paarweise Abstände berechnen
        distances = np.empty((num_samples, _ANZAHL_DISTANZEN), dtype=np.float32)
        idx = 0
        for i in range(PYRAMIDEN_KERNPUNKTE):
            for j in range(i + 1, PYRAMIDEN_KERNPUNKTE):
                pi, pj = coords[:, i, :], coords[:, j, :]
                valid = ~(np.isnan(pi).any(axis=1) | np.isnan(pj).any(axis=1))
                # np.where statt explizitem Nullen-Array → kein temporärer Speicher
                diff = np.where(valid[:, None], pi - pj, 0.0).astype(np.float32)
                d = np.linalg.norm(diff, axis=1)
                d[~valid] = -1.0  # Sentinel für fehlende Punkte
                distances[:, idx] = d
                idx += 1

        # Sortieren → Invarianz gegenüber Punkt-Permutationen
        distances_sorted = np.sort(distances, axis=1)

        # Zusatzfeatures ab Index (max_vertices * coords_per_vertex) retten.
        # ACHTUNG: Dieser Index hängt von max_vertices ab und darf NICHT hardcodiert werden!
        geometry_block_end = self.max_vertices * self.coordinates_per_vertex
        if raw_features.shape[1] > geometry_block_end:
            additional = np.nan_to_num(raw_features[:, geometry_block_end:], nan=-1.0)
            return np.hstack([distances_sorted, additional]).astype(np.float32)

        return distances_sorted.astype(np.float32)

    # ------------------------------------------------------------------
    # NORMALISIERUNG
    # ------------------------------------------------------------------

    def set_params(self, params: Optional[Dict]) -> None:
        """Setzt Min-Max-Parameter direkt, z.B. beim Laden eines gespeicherten Modells."""
        if params and "feature_min" in params and "feature_max" in params:
            self.normalization_params = params

    def normalize_data(
        self,
        data: np.ndarray,
        fit: bool = True,
        params: Optional[Dict] = None,
    ) -> Tuple[np.ndarray, Dict]:
        """
        Min-Max-Skalierung auf [0.0, 1.0] für alle Features.
        Die letzte Spalte (Label) bleibt unberührt.

        Args:
            data:   2D-Array [Samples, Features + Label]
            fit:    True  → Min/Max aus Daten berechnen und speichern
                    False → gespeicherte Min/Max-Werte verwenden
            params: Externe Parameter (überschreiben self.normalization_params bei fit=False)
        """
        if data is None or data.ndim != 2 or data.shape[1] < 2:
            raise ValueError(
                f"Ungültige Datenstruktur: Brauche 2D-Array mit ≥2 Spalten "
                f"(Features + Label). Erhalten: {getattr(data, 'shape', 'None')}"
            )

        data_f32 = data.astype(np.float32, copy=False)
        raw_features = data_f32[:, :-1]
        labels       = data_f32[:, -1:]

        # Koordinaten → rotationsinvariante Distanzfeatures
        features = self._transform_to_distances(raw_features)
        features = np.nan_to_num(features, nan=-1.0)

        # Min-Max-Parameter ermitteln oder laden
        if fit:
            feature_min = np.nanmin(features, axis=0)
            feature_max = np.nanmax(features, axis=0)
            active_params: Dict = {
                "feature_min": feature_min.tolist(),
                "feature_max": feature_max.tolist(),
            }
            self.normalization_params = active_params
        else:
            active_params = params if params is not None else self.normalization_params
            if not active_params:
                raise ValueError(
                    "Normalisierungsparameter fehlen! "
                    "Erst mit fit=True trainieren oder ein gespeichertes Modell laden."
                )
            feature_min = np.array(active_params["feature_min"], dtype=np.float32)
            feature_max = np.array(active_params["feature_max"], dtype=np.float32)

        # Division durch Null verhindern (falls Min == Max für ein Feature)
        feature_range = feature_max - feature_min
        feature_range[feature_range == 0.0] = 1.0

        # Ausgabe-Array in-place befüllen → keine RAM-Spitzen durch Zwischenarrays
        out = np.empty((data_f32.shape[0], features.shape[1] + 1), dtype=np.float32)
        out[:, -1:] = labels
        target = out[:, :-1]
        np.subtract(features, feature_min, out=target)
        np.divide(target, feature_range, out=target)
        np.clip(target, 0.0, 1.0, out=target)

        return out, active_params

    # ------------------------------------------------------------------
    # ÖFFENTLICHE API
    # ------------------------------------------------------------------

    def filter_and_prepare(self, data: np.ndarray, fit: bool = True) -> Tuple[np.ndarray, Dict]:
        """All-in-One: Validiert, transformiert und normalisiert die Rohdaten."""
        normalized_data, norm_params = self.normalize_data(data, fit=fit)
        return normalized_data, {
            "original_shape":       data.shape,
            "final_shape":          normalized_data.shape,
            "normalization_params": norm_params,
        }
