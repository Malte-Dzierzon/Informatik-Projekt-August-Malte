"""
CHECKPOINT-SYSTEM - Vereinfacht & Effizient
============================================
Speichert/lädt neuronale Netze mit Metadaten.
Fokus: Einfachheit und Geschwindigkeit.
"""

import json
import numpy as np
import os
from datetime import datetime


class CheckpointManager:
    """Verwaltet Speicherung und Laden von Modellen"""
    
    def __init__(self, checkpoint_dir="checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def save(self, weights: dict, config: dict, stats: dict, name: str = None) -> str:
        """
        Speichert ein Modell.
        
        Args:
            weights: {'W1': np.array, 'b1': np.array, 'W2', 'b2'}
            config: {'input_size', 'hidden_size', 'learning_rate'}
            stats: {'total_epochs': int, 'final_loss': float}
            name: Optionaler Name (sonst Timestamp)
        
        Returns:
            Pfad der Datei
        """
        if name is None:
            name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filepath = os.path.join(self.checkpoint_dir, f"{name}.npz")
        
        np.savez_compressed(filepath, **weights)
        
        metadata = {
            "config": config,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
        meta_path = filepath.replace(".npz", ".json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        return filepath
    
    def load(self, name: str) -> tuple:
        """
        Lädt ein Modell.
        
        Returns: (weights, config, stats)
        """
        filepath = os.path.join(self.checkpoint_dir, f"{name}.npz")
        meta_path = filepath.replace(".npz", ".json")
        
        weights = dict(np.load(filepath))
        
        with open(meta_path, "r") as f:
            metadata = json.load(f)
        
        return weights, metadata["config"], metadata["stats"]
    
    def list(self) -> list:
        """Listet alle Checkpoints auf"""
        checkpoints = []
        for f in sorted(os.listdir(self.checkpoint_dir)):
            if f.endswith(".json"):
                with open(os.path.join(self.checkpoint_dir, f)) as fp:
                    meta = json.load(fp)
                checkpoints.append({
                    "name": f[:-5],  # Ohne .json
                    "timestamp": meta.get("timestamp", "?"),
                    "config": meta.get("config", {}),
                    "stats": meta.get("stats", {})
                })
        return sorted(checkpoints, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    def delete(self, name: str):
        """Löscht einen Checkpoint"""
        for ext in [".npz", ".json"]:
            f = os.path.join(self.checkpoint_dir, f"{name}{ext}")
            if os.path.exists(f):
                os.remove(f)
