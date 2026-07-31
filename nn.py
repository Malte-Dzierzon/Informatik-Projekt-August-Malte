"""
Neural Network Core — Shared by Streamlit and Terminal UI.
Minimal NumPy implementation: Input → Hidden(ReLU) → Output(Sigmoid).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(slots=True)
class TrainConfig:
    epochs: int = 1000
    learning_rate: float = 0.1
    val_split: float = 0.2
    seed: int = 42


@dataclass(slots=True)
class TrainResult:
    train_losses: list[float]
    val_losses: list[float]
    final_train_loss: float
    final_val_loss: float


def _expit(z: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid."""
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500.0, 500.0)))


def _he_init(fan_in: int, fan_out: int, rng: np.random.Generator) -> np.ndarray:
    """He initialization for ReLU."""
    return (rng.standard_normal((fan_in, fan_out)) * np.sqrt(2.0 / fan_in)).astype(np.float32)


class NeuralNet:
    """Two-layer MLP: input → hidden(ReLU) → output(Sigmoid)."""

    __slots__ = ("W1", "W2", "b1", "b2", "hidden_size", "input_size")

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        seed: int = 42,
        W1: np.ndarray | None = None,
        b1: np.ndarray | None = None,
        W2: np.ndarray | None = None,
        b2: np.ndarray | None = None,
    ):
        self.input_size = input_size
        self.hidden_size = hidden_size
        rng = np.random.default_rng(seed)

        self.W1 = W1 if W1 is not None else _he_init(input_size, hidden_size, rng)
        self.b1 = b1 if b1 is not None else np.zeros((1, hidden_size), dtype=np.float32)
        self.W2 = W2 if W2 is not None else _he_init(hidden_size, 1, rng)
        self.b2 = b2 if b2 is not None else np.zeros((1, 1), dtype=np.float32)

    def forward(self, X: np.ndarray) -> np.ndarray:
        """Forward pass, returns predictions [N, 1]."""
        z1 = X @ self.W1 + self.b1
        a1 = np.maximum(0.0, z1)          # ReLU
        z2 = a1 @ self.W2 + self.b2
        return _expit(z2)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Binary predictions (0 or 1)."""
        return (self.forward(X) >= 0.5).astype(np.float32)

    def loss(self, X: np.ndarray, y: np.ndarray) -> float:
        """MSE loss."""
        preds = self.forward(X)
        return float(np.mean((preds - y) ** 2))

    def train_step(self, X: np.ndarray, y: np.ndarray, lr: float) -> float:
        """One gradient-descent step, returns loss."""
        n = X.shape[0]
        X_T = X.T

        # Forward
        z1 = X @ self.W1 + self.b1
        a1 = np.maximum(0.0, z1)
        z2 = a1 @ self.W2 + self.b2
        a2 = _expit(z2)

        loss = float(np.mean((a2 - y) ** 2))

        # Backward
        dz2 = (a2 - y) * a2 * (1.0 - a2)
        grad_W2 = (a1.T @ dz2) / n
        grad_b2 = np.mean(dz2, axis=0, keepdims=True)

        dz1 = (dz2 @ self.W2.T) * (z1 > 0.0)
        grad_W1 = (X_T @ dz1) / n
        grad_b1 = np.mean(dz1, axis=0, keepdims=True)

        # Update
        self.W2 -= lr * grad_W2
        self.b2 -= lr * grad_b2
        self.W1 -= lr * grad_W1
        self.b1 -= lr * grad_b1

        return loss

    def save_json(
        self,
        path: str | Path,
        *,
        total_epochs: int = 0,
        last_loss: float = 0.0,
        validation: str = "",
        normalization_params: dict | None = None,
    ) -> None:
        payload = {
            "W1": self.W1.tolist(),
            "b1": self.b1.tolist(),
            "W2": self.W2.tolist(),
            "b2": self.b2.tolist(),
            "config": {
                "input_size": self.input_size,
                "hidden_size": self.hidden_size,
            },
            "stats": {
                "total_epochs": total_epochs,
                "last_loss": last_loss,
                "validation": validation,
            },
            "normalization_params": normalization_params or {},
        }
        Path(path).write_text(json.dumps(payload, indent=2))

    @classmethod
    def load_json(cls, path: str | Path) -> NeuralNet:
        data = json.loads(Path(path).read_text())
        required = ["W1", "b1", "W2", "b2", "config"]
        if not all(k in data for k in required):
            raise ValueError("Invalid model file: missing required keys")
        cfg = data["config"]
        return cls(
            input_size=int(cfg["input_size"]),
            hidden_size=int(cfg["hidden_size"]),
            W1=np.array(data["W1"], dtype=np.float32),
            b1=np.array(data["b1"], dtype=np.float32),
            W2=np.array(data["W2"], dtype=np.float32),
            b2=np.array(data["b2"], dtype=np.float32),
        )


def train_model(
    net: NeuralNet,
    X: np.ndarray,
    y: np.ndarray,
    config: TrainConfig,
) -> TrainResult:
    """Train/validate split + full training loop. Returns losses."""
    rng = np.random.default_rng(config.seed)
    n = len(X)
    idx = rng.permutation(n)
    split = int(n * (1.0 - config.val_split))
    train_idx, val_idx = idx[:split], idx[split:]

    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = (X[val_idx], y[val_idx]) if len(val_idx) > 0 else (X_train, y_train)

    train_losses: list[float] = []
    val_losses: list[float] = []

    for epoch in range(config.epochs):
        loss = net.train_step(X_train, y_train, config.learning_rate)
        train_losses.append(loss)

        val_loss = net.loss(X_val, y_val)
        val_losses.append(val_loss)

    return TrainResult(
        train_losses=train_losses,
        val_losses=val_losses,
        final_train_loss=train_losses[-1],
        final_val_loss=val_losses[-1],
    )