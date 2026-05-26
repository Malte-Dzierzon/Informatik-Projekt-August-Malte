"""
CHECKPOINT-SYSTEM FÜR NEURONALES NETZWERK
==========================================
Speichert und lädt Trainingszustände mit Gewichten, Bias, Optimizer-Status und Training-Statistiken.
Ermöglicht Fortsetzbares Training mit exaktem State-Restore.
"""

import json
import numpy as np
import os
from datetime import datetime


class CheckpointManager:
    """
    Verwaltet Checkpoints für neuronale Netze mit persistentem Speicher.
    
    Features:
    - Speichert Gewichte, Bias, Netzwerk-Konfiguration
    - Speichert Training-Counter (Gesamtzahl Trainingsdurchgänge)
    - Speichert Normalisierungs-Parameter für konsistente Input-Verarbeitung
    - Laden und Fortsetzen von Checkpoints
    - Versionierung und Metadaten-Tracking
    """
    
    def __init__(self, checkpoint_dir="checkpoints"):
        """
        Initialisiert CheckpointManager mit Speicherort.
        
        Args:
            checkpoint_dir: Verzeichnis für Checkpoint-Dateien
        """
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def save_checkpoint(self, model_state, training_stats, config, filename=None):
        """
        Speichert einen Checkpoint des aktuellen Netzwerk-Zustands.
        
        Args:
            model_state: Dict mit Gewichten und Bias
                {
                    "W1": np.array, "b1": np.array,
                    "W2": np.array, "b2": np.array,
                    ... (weitere Layer wenn vorhanden)
                }
            training_stats: Dict mit Training-Statistiken
                {
                    "total_training_count": int,
                    "train_errors": list,
                    "test_errors": list,
                    "last_epoch": int,
                    "normalization_params": {
                        "feature_min": list,
                        "feature_max": list
                    }
                }
            config: Dict mit Netzwerk-Konfiguration
                {
                    "input_size": int,
                    "hidden_size": int,
                    "learning_rate": float,
                    "description": str (optional)
                }
            filename: Benutzerdefinierter Dateiname (optional)
                     Falls None: Auto-generiert mit Timestamp
        
        Returns:
            str: Pfad zur gespeicherten Checkpoint-Datei
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"checkpoint_{timestamp}.npz"
        
        filepath = os.path.join(self.checkpoint_dir, filename)
        
        # Prepare data für Speicherung
        save_dict = {}
        
        # Gewichte und Bias speichern
        for key, value in model_state.items():
            if isinstance(value, np.ndarray):
                save_dict[key] = value
        
        # Metadaten speichern (JSON in separater Datei)
        metadata = {
            "config": config,
            "training_stats": {
                "total_training_count": training_stats.get("total_training_count", 0),
                "last_epoch": training_stats.get("last_epoch", 0),
                "final_train_loss": float(training_stats.get("train_errors", [0])[-1]) if training_stats.get("train_errors") else 0.0,
                "final_test_loss": float(training_stats.get("test_errors", [0])[-1]) if training_stats.get("test_errors") else 0.0,
                "normalization_params": training_stats.get("normalization_params", {})
            },
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # Speichere Weights mit np.savez_compressed
        np.savez_compressed(filepath, **save_dict)
        
        # Speichere Metadaten in JSON
        metadata_filepath = filepath.replace(".npz", "_metadata.json")
        with open(metadata_filepath, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Speichere auch Training-History als CSV wenn vorhanden
        if training_stats.get("train_errors") and training_stats.get("test_errors"):
            history_filepath = filepath.replace(".npz", "_history.csv")
            with open(history_filepath, "w") as f:
                f.write("epoch,train_loss,test_loss\n")
                for epoch, (train_loss, test_loss) in enumerate(
                    zip(training_stats["train_errors"], training_stats["test_errors"])
                ):
                    f.write(f"{epoch},{train_loss},{test_loss}\n")
        
        return filepath
    
    def load_checkpoint(self, filename):
        """
        Lädt einen Checkpoint und stellt den Netzwerk-Zustand wieder her.
        
        Args:
            filename: Name der Checkpoint-Datei (z.B. "checkpoint_20240101_120000.npz")
        
        Returns:
            Tuple: (model_state, training_stats, config)
                - model_state: Dict mit Gewichten und Bias
                - training_stats: Dict mit Training-Statistiken
                - config: Dict mit Netzwerk-Konfiguration
        
        Raises:
            FileNotFoundError: Wenn Checkpoint nicht existiert
            ValueError: Wenn Checkpoint beschädigt ist
        """
        filepath = os.path.join(self.checkpoint_dir, filename)
        metadata_filepath = filepath.replace(".npz", "_metadata.json")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Checkpoint nicht gefunden: {filepath}")
        
        if not os.path.exists(metadata_filepath):
            raise FileNotFoundError(f"Checkpoint-Metadaten nicht gefunden: {metadata_filepath}")
        
        try:
            # Lade Gewichte
            weights_data = np.load(filepath)
            model_state = {key: weights_data[key] for key in weights_data.files}
            
            # Lade Metadaten
            with open(metadata_filepath, "r") as f:
                metadata = json.load(f)
            
            training_stats = metadata.get("training_stats", {})
            config = metadata.get("config", {})
            
            return model_state, training_stats, config
            
        except Exception as e:
            raise ValueError(f"Fehler beim Laden des Checkpoints: {str(e)}")
    
    def list_checkpoints(self):
        """
        Listet alle verfügbaren Checkpoints auf.
        
        Returns:
            list: Liste von Dicts mit Checkpoint-Informationen
                [
                    {
                        "filename": str,
                        "timestamp": str,
                        "total_training_count": int,
                        "final_train_loss": float,
                        "final_test_loss": float,
                        "config": dict
                    },
                    ...
                ]
        """
        checkpoints = []
        
        for filename in sorted(os.listdir(self.checkpoint_dir)):
            if filename.endswith("_metadata.json"):
                try:
                    filepath = os.path.join(self.checkpoint_dir, filename)
                    with open(filepath, "r") as f:
                        metadata = json.load(f)
                    
                    checkpoint_info = {
                        "filename": filename.replace("_metadata.json", ".npz"),
                        "timestamp": metadata.get("timestamp", "Unknown"),
                        "total_training_count": metadata.get("training_stats", {}).get("total_training_count", 0),
                        "final_train_loss": metadata.get("training_stats", {}).get("final_train_loss", 0.0),
                        "final_test_loss": metadata.get("training_stats", {}).get("final_test_loss", 0.0),
                        "config": metadata.get("config", {})
                    }
                    checkpoints.append(checkpoint_info)
                except:
                    pass
        
        return sorted(checkpoints, key=lambda x: x["timestamp"], reverse=True)
    
    def delete_checkpoint(self, filename):
        """
        Löscht einen Checkpoint und seine Metadaten.
        
        Args:
            filename: Name der zu löschenden Checkpoint-Datei
        """
        filepath = os.path.join(self.checkpoint_dir, filename)
        metadata_filepath = filepath.replace(".npz", "_metadata.json")
        history_filepath = filepath.replace(".npz", "_history.csv")
        
        for f in [filepath, metadata_filepath, history_filepath]:
            if os.path.exists(f):
                os.remove(f)
    
    def get_checkpoint_info(self, filename):
        """
        Holt detaillierte Informationen über einen Checkpoint.
        
        Args:
            filename: Name der Checkpoint-Datei
        
        Returns:
            dict: Detaillierte Informationen
        """
        filepath = os.path.join(self.checkpoint_dir, filename)
        metadata_filepath = filepath.replace(".npz", "_metadata.json")
        
        if not os.path.exists(metadata_filepath):
            return None
        
        with open(metadata_filepath, "r") as f:
            metadata = json.load(f)
        
        file_size_kb = os.path.getsize(filepath) / 1024
        
        return {
            "filename": filename,
            "size_kb": round(file_size_kb, 2),
            "timestamp": metadata.get("timestamp", "Unknown"),
            "config": metadata.get("config", {}),
            "training_stats": metadata.get("training_stats", {}),
            "version": metadata.get("version", "Unknown")
        }


# Einfache Test-Funktion
if __name__ == "__main__":
    print("✓ Checkpoint-System geladen und bereit")
    
    # Test-Daten
    test_model = {
        "W1": np.random.randn(4, 16).astype(np.float32),
        "b1": np.zeros((1, 16), dtype=np.float32),
        "W2": np.random.randn(16, 1).astype(np.float32),
        "b2": np.zeros((1, 1), dtype=np.float32)
    }
    
    test_stats = {
        "total_training_count": 1,
        "train_errors": [0.5, 0.3, 0.1],
        "test_errors": [0.6, 0.35, 0.15],
        "last_epoch": 3,
        "normalization_params": {"feature_min": [0, 0, 0, 0], "feature_max": [1, 1, 1, 1]}
    }
    
    test_config = {
        "input_size": 4,
        "hidden_size": 16,
        "learning_rate": 0.1,
        "description": "Test Checkpoint"
    }
    
    manager = CheckpointManager()
    saved_path = manager.save_checkpoint(test_model, test_stats, test_config, "test_checkpoint.npz")
    print(f"✓ Test-Checkpoint gespeichert: {saved_path}")
    
    # Test laden
    loaded_model, loaded_stats, loaded_config = manager.load_checkpoint("test_checkpoint.npz")
    print(f"✓ Test-Checkpoint geladen")
    print(f"  - Training-Count: {loaded_stats.get('total_training_count')}")
    print(f"  - Config: {loaded_config}")
