"""
Dynamic Input System — Rotation-Invariant & Minimal
====================================================
Processes geometry data with variable vertex count and transforms
X,Y,Z coordinates into rotation-invariant pairwise distances.
Allows objects with 4 vertices as well as 46, without confusing the model.
"""

import numpy as np

from pyramid_generator import NUM_CORE_POINTS

# ------------------------------------------------------------------
# CONSTANTS & PREDEFINED FEATURE SET
# ------------------------------------------------------------------
# C(5,2) = 10 pairwise distances between the 5 core points
_NUM_DISTANCES: int = (NUM_CORE_POINTS * (NUM_CORE_POINTS - 1)) // 2


class DynamicInputHandler:
    """
    Scales, transforms, and normalizes variable input data.

    Uses float32 and in-place operations for minimal memory footprint.
    """

    def __init__(self, max_vertices: int = 12, coordinates_per_vertex: int = 3):
        self.max_vertices = max_vertices
        self.coordinates_per_vertex = coordinates_per_vertex
        self.normalization_params: dict[str, list] = {}

    # ------------------------------------------------------------------
    # GEOMETRIC TRANSFORMATION
    # ------------------------------------------------------------------

    def _transform_to_distances(self, raw_features: np.ndarray) -> np.ndarray:
        """
        Transforms raw X,Y,Z coordinates into rotation-invariant distances.

        Procedure:
        1. Extract first NUM_CORE_POINTS (=5) points.
           Note: Vertices 6–max_vertices are intentionally excluded from
           distance calculation — pyramid definition requires exactly 5 points.
        2. Compute all C(5,2) = 10 pairwise distances.
           Missing points (NaN) get sentinel value -1.0.
        3. Sort distances for permutation invariance.
        4. Append extra features (from index max_vertices * coords_per_vertex).
        """
        num_samples = raw_features.shape[0]

        # Extract coordinate block of first 5 points (= NUM_CORE_POINTS * 3 values)
        coords_len = NUM_CORE_POINTS * self.coordinates_per_vertex
        if raw_features.shape[1] < coords_len:
            # Pad missing columns with NaN
            pad = np.full((num_samples, coords_len - raw_features.shape[1]), np.nan, dtype=np.float32)
            coords_raw = np.hstack([raw_features, pad])
        else:
            coords_raw = raw_features[:, :coords_len]

        # Reshape: [Samples, 5 Points, 3 Coordinates]
        coords = coords_raw.reshape(num_samples, NUM_CORE_POINTS, self.coordinates_per_vertex)

        # Compute pairwise distances
        distances = np.empty((num_samples, _NUM_DISTANCES), dtype=np.float32)
        idx = 0
        for i in range(NUM_CORE_POINTS):
            for j in range(i + 1, NUM_CORE_POINTS):
                pi, pj = coords[:, i, :], coords[:, j, :]
                valid = ~(np.isnan(pi).any(axis=1) | np.isnan(pj).any(axis=1))
                # np.where instead of explicit zero array → no temporary memory
                diff = np.where(valid[:, None], pi - pj, 0.0).astype(np.float32)
                d = np.linalg.norm(diff, axis=1)
                d[~valid] = -1.0  # Sentinel for missing points
                distances[:, idx] = d
                idx += 1

        # Sort → invariance to point permutations
        distances_sorted = np.sort(distances, axis=1)

        # Preserve extra features from index (max_vertices * coords_per_vertex).
        # IMPORTANT: This index depends on max_vertices and must NOT be hardcoded!
        geometry_block_end = self.max_vertices * self.coordinates_per_vertex
        if raw_features.shape[1] > geometry_block_end:
            additional = np.nan_to_num(raw_features[:, geometry_block_end:], nan=-1.0)
            return np.hstack([distances_sorted, additional]).astype(np.float32)

        return distances_sorted.astype(np.float32)

    # ------------------------------------------------------------------
    # NORMALIZATION
    # ------------------------------------------------------------------

    def set_params(self, params: dict | None) -> None:
        """Set min-max params directly, e.g. when loading a saved model."""
        if params and "feature_min" in params and "feature_max" in params:
            self.normalization_params = params

    def normalize_data(
        self,
        data: np.ndarray,
        fit: bool = True,
        params: dict | None = None,
    ) -> tuple[np.ndarray, dict]:
        """
        Min-max scaling to [0.0, 1.0] for all features.
        Last column (label) is left untouched.

        Args:
            data:   2D array [Samples, Features + Label]
            fit:    True  → compute min/max from data and store
                    False → use stored min/max values
            params: External params (override self.normalization_params when fit=False)
        """
        if data is None or data.ndim != 2 or data.shape[1] < 2:
            raise ValueError(
                f"Invalid data structure: need 2D array with ≥2 columns "
                f"(Features + Label). Got: {getattr(data, 'shape', 'None')}"
            )

        data_f32 = data.astype(np.float32, copy=False)
        raw_features = data_f32[:, :-1]
        labels = data_f32[:, -1:]

        # Coordinates → rotation-invariant distance features
        features = self._transform_to_distances(raw_features)
        features = np.nan_to_num(features, nan=-1.0)

        # Determine or load min-max parameters
        if fit:
            feature_min = np.nanmin(features, axis=0)
            feature_max = np.nanmax(features, axis=0)
            active_params: dict = {
                "feature_min": feature_min.tolist(),
                "feature_max": feature_max.tolist(),
            }
            self.normalization_params = active_params
        else:
            active_params = params if params is not None else self.normalization_params
            if not active_params:
                raise ValueError(
                    "Normalization parameters missing! "
                    "Train first with fit=True or load a saved model."
                )
            feature_min = np.array(active_params["feature_min"], dtype=np.float32)
            feature_max = np.array(active_params["feature_max"], dtype=np.float32)

        # Prevent division by zero (if min == max for a feature)
        feature_range = feature_max - feature_min
        feature_range[feature_range == 0.0] = 1.0

        # Fill output array in-place → no RAM spikes from intermediate arrays
        out = np.empty((data_f32.shape[0], features.shape[1] + 1), dtype=np.float32)
        out[:, -1:] = labels
        target = out[:, :-1]
        np.subtract(features, feature_min, out=target)
        np.divide(target, feature_range, out=target)
        np.clip(target, 0.0, 1.0, out=target)

        return out, active_params

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def filter_and_prepare(self, data: np.ndarray, fit: bool = True) -> tuple[np.ndarray, dict]:
        """All-in-one: validate, transform, and normalize raw data."""
        normalized_data, norm_params = self.normalize_data(data, fit=fit)
        return normalized_data, {
            "original_shape":       data.shape,
            "final_shape":          normalized_data.shape,
            "normalization_params": norm_params,
        }