"""
Pyramid Data Generator
======================
A pyramid = 4 base vertices on a plane + 1 apex above (= 5 points).

Pipeline for one pyramid:
  1. Create 5 points in "blueprint" (flat base, apex up)
  2. Rotate with random 3D rotation matrix (random axis + angle)
  3. Translate so everything lies in visible range
  4. Pack into fixed-length vector (pad rest with NaN)
"""

import numpy as np

NUM_CORE_POINTS = 5  # always 4 base + 1 apex


class PyramidGenerator:

    def __init__(self, seed: int | None = None):
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Helpers (small, clearly named)
    # ------------------------------------------------------------------

    def _rotation_matrix(self) -> np.ndarray:
        """
        Random 3D rotation: arbitrary axis in space + arbitrary angle.
        Uniform distribution over SO(3).
        """
        axis = self.rng.standard_normal(3).astype(np.float32)
        axis /= np.linalg.norm(axis)
        angle = float(self.rng.uniform(0, 2 * np.pi))
        c, s = float(np.cos(angle)), float(np.sin(angle))
        x, y, z = axis
        # Rodrigues: R = I + sin(θ)·K + (1-cos(θ))·K²
        k = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]], dtype=np.float32)
        return (np.eye(3, dtype=np.float32) + s * k + (1 - c) * (k @ k)).astype(np.float32)

    def _rotate_and_translate(self, points: np.ndarray, rotate: bool = True) -> np.ndarray:
        """Rotate with random rotation matrix, then random translation."""
        if rotate:
            scale = float(self.rng.uniform(0.75, 1.25))
            points = (points * scale) @ self._rotation_matrix().T
        translation = self.rng.uniform(0.3, 0.7, 3).astype(np.float32)
        return (points + translation).astype(np.float32)

    def _pack_into_vector(
        self,
        points: np.ndarray,
        max_vertices: int,
        coords_per_vertex: int,
        height: float,
        balance: float,
        base_area: float,
        center_x: float,
    ) -> np.ndarray:
        """5 (or more) points + 4 extra features → one training sample."""
        length = max_vertices * coords_per_vertex
        coords = np.full(length, np.nan, dtype=np.float32)
        coords[: points.size] = points.reshape(-1)
        extras = np.array([height, balance, base_area, center_x], dtype=np.float32)
        return np.concatenate([coords, extras])

    def _extra_features(self, base: np.ndarray, apex: np.ndarray) -> tuple[float, float, float, float]:
        """Simple explainable features."""
        center = base.mean(axis=0)
        height = float(np.linalg.norm(apex - center))
        balance = float(np.linalg.norm(apex[:2] - center[:2]))
        edge1 = base[1] - base[0]
        edge2 = base[3] - base[0]
        base_area = float(np.linalg.norm(np.cross(edge1, edge2)))
        return height, balance, base_area, float(center[0])

    # ------------------------------------------------------------------
    # Pyramid (class 1)
    # ------------------------------------------------------------------

    def _generate_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        # Step 1: blueprint – rectangle base, apex above
        width = float(self.rng.uniform(0.15, 0.25))
        depth = float(self.rng.uniform(0.15, 0.25))
        blueprint_height = float(self.rng.uniform(0.4, 0.6))

        base = np.array([
            [width, depth, 0],
            [-width, depth, 0],
            [-width, -depth, 0],
            [width, -depth, 0],
        ], dtype=np.float32)
        # Apex slightly offset → not always perfectly centered (more variation)
        apex = np.array([
            self.rng.uniform(-0.08, 0.08),
            self.rng.uniform(-0.08, 0.08),
            blueprint_height,
        ], dtype=np.float32)
        points = np.vstack([base, apex])

        # Step 2+3: always rotate and translate
        points = self._rotate_and_translate(points, rotate=True)

        base_out = points[:4]
        apex_out = points[4]
        extras = self._extra_features(base_out, apex_out)
        return self._pack_into_vector(points, max_vertices, coords_per_vertex, *extras)

    # ------------------------------------------------------------------
    # Non-Pyramid (class 0) – intentionally "wrong" shapes
    # ------------------------------------------------------------------

    def _generate_non_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        kind = self.rng.choice(["slanted", "flat", "many_points", "random"])

        if kind == "slanted":
            # Looks like pyramid but base corners have different heights
            vec = self._generate_pyramid(max_vertices, coords_per_vertex)
            points = vec[:15].reshape(5, 3).copy()
            points[:4, 2] += self.rng.uniform(-0.05, 0.05, 4)
            vec[:15] = points.reshape(-1)
            return vec

        if kind == "flat":
            # Apex lies in base plane → not a real pyramid
            width = float(self.rng.uniform(0.15, 0.25))
            depth = float(self.rng.uniform(0.15, 0.25))
            base = np.array([
                [width, depth, 0], [-width, depth, 0],
                [-width, -depth, 0], [width, -depth, 0],
            ], dtype=np.float32)
            apex = base.mean(axis=0)
            points = np.vstack([base, apex])
            points = self._rotate_and_translate(points, rotate=False)
            extras = (0.0, 0.0, 4 * width * depth, float(points[:4, 0].mean()))
            return self._pack_into_vector(points, max_vertices, coords_per_vertex, *extras)

        if kind == "many_points" and max_vertices >= 6:
            # Two layers stacked = prism/cube, not pyramid
            count = int(self.rng.integers(6, max_vertices + 1))
            lower = self.rng.uniform(-0.2, 0.2, (count // 2, 3)).astype(np.float32)
            upper = lower.copy()
            upper[:, 2] += float(self.rng.uniform(0.35, 0.55))
            points = self._rotate_and_translate(np.vstack([lower, upper]))
            extras = (float(upper[0, 2]), 0.5, 0.2, float(points[0, 0]))
            return self._pack_into_vector(points, max_vertices, coords_per_vertex, *extras)

        # Random points without pyramid structure
        count = int(self.rng.integers(3, max_vertices + 1))
        points = self.rng.uniform(0.2, 0.8, (count, coords_per_vertex)).astype(np.float32)
        extras = (0.3, 0.8, 0.15, 0.5)
        return self._pack_into_vector(points, max_vertices, coords_per_vertex, *extras)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_dataset(
        self,
        max_vertices: int = 12,
        coords_per_vertex: int = 3,
        n_pyramids: int = 100,
        n_non_pyramids: int = 100,
        shuffle: bool = True,
    ) -> tuple[np.ndarray, list[dict]]:
        total = n_pyramids + n_non_pyramids
        cols = max_vertices * coords_per_vertex + 4 + 1
        data = np.empty((total, cols), dtype=np.float32)

        for i in range(n_pyramids):
            data[i, :-1] = self._generate_pyramid(max_vertices, coords_per_vertex)
            data[i, -1] = 1.0

        for i in range(n_non_pyramids):
            data[n_pyramids + i, :-1] = self._generate_non_pyramid(max_vertices, coords_per_vertex)
            data[n_pyramids + i, -1] = 0.0

        meta = (
            [{"id": i, "type": "pyramid", "label": 1} for i in range(n_pyramids)]
            + [{"id": n_pyramids + i, "type": "non_pyramid", "label": 0} for i in range(n_non_pyramids)]
        )

        if shuffle and total > 0:
            idx = self.rng.permutation(total)
            data = data[idx]
            meta = [meta[k] for k in idx]

        return data, meta

    def generate_single_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        return self._generate_pyramid(max_vertices, coords_per_vertex)

    def generate_single_non_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        return self._generate_non_pyramid(max_vertices, coords_per_vertex)