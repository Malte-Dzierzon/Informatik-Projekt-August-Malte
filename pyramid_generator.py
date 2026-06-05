"""
Pyramiden-Datengenerator (einfach erklärbar)
============================================
Eine Pyramide = 4 Eckpunkte auf einer Ebene + 1 Spitze darüber (= 5 Punkte).

Ablauf für eine Pyramide:
  1. 5 Punkte im "Bauplan" erzeugen (Basis flach, Spitze oben)
  2. Mit einer Richtungsmatrix drehen (zufällige Achse + Winkel im Raum)
  3. Verschieben, damit alles im sichtbaren Bereich liegt
  4. In einen langen Zahlenvektor packen (Rest mit NaN auffüllen)
"""

import numpy as np
from typing import Tuple, List, Dict, Optional

PYRAMIDEN_KERNPUNKTE = 5  # immer 4 Basis + 1 Spitze


class PyramidGenerator:

    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Hilfsfunktionen (klein und klar benannt)
    # ------------------------------------------------------------------

    def _dreh_matrix(self) -> np.ndarray:
        """
        Zufällige 3D-Rotation: beliebige Achse im Raum + beliebiger Winkel.
        So kann die Pyramide in jede Richtung kippen (gleichmäßig verteilt).
        """
        achse = self.rng.standard_normal(3).astype(np.float32)
        achse /= np.linalg.norm(achse)
        winkel = float(self.rng.uniform(0, 2 * np.pi))
        c, s = float(np.cos(winkel)), float(np.sin(winkel))
        x, y, z = achse
        # Rodrigues: R = I + sin(θ)·K + (1-cos(θ))·K²
        k = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]], dtype=np.float32)
        return (np.eye(3, dtype=np.float32) + s * k + (1 - c) * (k @ k)).astype(np.float32)

    def _punkte_drehen_und_verschieben(self, punkte: np.ndarray, drehen: bool = True) -> np.ndarray:
        """Drehen mit Zufalls-Richtungsmatrix, dann zufällig verschieben."""
        if drehen:
            skalierung = float(self.rng.uniform(0.75, 1.25))
            punkte = (punkte * skalierung) @ self._dreh_matrix().T
        verschiebung = self.rng.uniform(0.3, 0.7, 3).astype(np.float32)
        return (punkte + verschiebung).astype(np.float32)

    def _in_vektor_packen(
        self,
        punkte: np.ndarray,
        max_vertices: int,
        coords_per_vertex: int,
        hoehe: float,
        balance: float,
        grundflaeche: float,
        mitte_x: float,
    ) -> np.ndarray:
        """5 (oder mehr) Punkte + 4 Extra-Zahlen → ein Trainings-Eintrag."""
        laenge = max_vertices * coords_per_vertex
        coords = np.full(laenge, np.nan, dtype=np.float32)
        coords[: punkte.size] = punkte.reshape(-1)
        extras = np.array([hoehe, balance, grundflaeche, mitte_x], dtype=np.float32)
        return np.concatenate([coords, extras])

    def _zusatzwerte(self, basis: np.ndarray, spitze: np.ndarray) -> Tuple[float, float, float, float]:
        """Einfache Merkmale, die man mündlich erklären kann."""
        mitte = basis.mean(axis=0)
        hoehe = float(np.linalg.norm(spitze - mitte))
        balance = float(np.linalg.norm(spitze[:2] - mitte[:2]))
        kante1 = basis[1] - basis[0]
        kante2 = basis[3] - basis[0]
        grundflaeche = float(np.linalg.norm(np.cross(kante1, kante2)))
        return hoehe, balance, grundflaeche, float(mitte[0])

    # ------------------------------------------------------------------
    # Pyramide (Klasse 1)
    # ------------------------------------------------------------------

    def _generate_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        # Schritt 1: Bauplan – Rechteck als Basis, Spitze darüber
        breite = float(self.rng.uniform(0.15, 0.25))
        tiefe = float(self.rng.uniform(0.15, 0.25))
        hoehe_bauplan = float(self.rng.uniform(0.4, 0.6))

        basis = np.array([
            [breite, tiefe, 0],
            [-breite, tiefe, 0],
            [-breite, -tiefe, 0],
            [breite, -tiefe, 0],
        ], dtype=np.float32)
        # Spitze leicht versetzt → nicht immer perfekt mittig (mehr Variation)
        spitze = np.array([
            self.rng.uniform(-0.08, 0.08),
            self.rng.uniform(-0.08, 0.08),
            hoehe_bauplan,
        ], dtype=np.float32)
        punkte = np.vstack([basis, spitze])

        # Schritt 2+3: immer drehen und verschieben
        punkte = self._punkte_drehen_und_verschieben(punkte, drehen=True)

        basis_out = punkte[:4]
        spitze_out = punkte[4]
        extras = self._zusatzwerte(basis_out, spitze_out)
        return self._in_vektor_packen(punkte, max_vertices, coords_per_vertex, *extras)

    # ------------------------------------------------------------------
    # Keine Pyramide (Klasse 0) – absichtlich "falsche" Formen
    # ------------------------------------------------------------------

    def _generate_non_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        typ = self.rng.choice(["schief", "flach", "viele_punkte", "zufall"])

        if typ == "schief":
            # Sieht aus wie Pyramide, aber Basis-Ecken haben unterschiedliche Höhen
            vektor = self._generate_pyramid(max_vertices, coords_per_vertex)
            punkte = vektor[:15].reshape(5, 3).copy()
            punkte[:4, 2] += self.rng.uniform(-0.05, 0.05, 4)
            vektor[:15] = punkte.reshape(-1)
            return vektor

        if typ == "flach":
            # Spitze liegt in der Basis-Ebene → keine echte Pyramide
            breite = float(self.rng.uniform(0.15, 0.25))
            tiefe = float(self.rng.uniform(0.15, 0.25))
            basis = np.array([
                [breite, tiefe, 0], [-breite, tiefe, 0],
                [-breite, -tiefe, 0], [breite, -tiefe, 0],
            ], dtype=np.float32)
            spitze = basis.mean(axis=0)
            punkte = np.vstack([basis, spitze])
            punkte = self._punkte_drehen_und_verschieben(punkte, drehen=False)
            extras = (0.0, 0.0, 4 * breite * tiefe, float(punkte[:4, 0].mean()))
            return self._in_vektor_packen(punkte, max_vertices, coords_per_vertex, *extras)

        if typ == "viele_punkte" and max_vertices >= 6:
            # Zwei Ebenen übereinander = eher Prisma/Würfel, nicht Pyramide
            anzahl = int(self.rng.integers(6, max_vertices + 1))
            unten = self.rng.uniform(-0.2, 0.2, (anzahl // 2, 3)).astype(np.float32)
            oben = unten.copy()
            oben[:, 2] += float(self.rng.uniform(0.35, 0.55))
            punkte = self._punkte_drehen_und_verschieben(np.vstack([unten, oben]))
            extras = (float(oben[0, 2]), 0.5, 0.2, float(punkte[0, 0]))
            return self._in_vektor_packen(punkte, max_vertices, coords_per_vertex, *extras)

        # Zufällige Punkte ohne Pyramiden-Form
        anzahl = int(self.rng.integers(3, max_vertices + 1))
        punkte = self.rng.uniform(0.2, 0.8, (anzahl, coords_per_vertex)).astype(np.float32)
        extras = (0.3, 0.8, 0.15, 0.5)
        return self._in_vektor_packen(punkte, max_vertices, coords_per_vertex, *extras)

    # ------------------------------------------------------------------
    # Öffentliche API (von app.py genutzt)
    # ------------------------------------------------------------------

    def generate_dataset(
        self,
        max_vertices: int = 12,
        coords_per_vertex: int = 3,
        n_pyramids: int = 100,
        n_non_pyramids: int = 100,
        shuffle: bool = True,
    ) -> Tuple[np.ndarray, List[Dict]]:
        gesamt = n_pyramids + n_non_pyramids
        spalten = max_vertices * coords_per_vertex + 4 + 1
        data = np.empty((gesamt, spalten), dtype=np.float32)

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

        if shuffle and gesamt > 0:
            idx = self.rng.permutation(gesamt)
            data = data[idx]
            meta = [meta[k] for k in idx]

        return data, meta

    def generate_single_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        return self._generate_pyramid(max_vertices, coords_per_vertex)

    def generate_single_non_pyramid(self, max_vertices: int, coords_per_vertex: int) -> np.ndarray:
        return self._generate_non_pyramid(max_vertices, coords_per_vertex)