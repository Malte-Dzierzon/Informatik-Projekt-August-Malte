import csv
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from debug_utils import animated_message, debug_error, debug_generate, debug_info, debug_training
from dynamic_input import DynamicInputHandler
from pyramid_generator import PyramidGenerator

try:
    from InquirerPy import inquirer
except ImportError:
    inquirer = None

APP_HEADER = [
    "⢰⣴⣶⣦⣆⠀⠀⠀⠀⣰⣴⣶⣦⠀⠀⠀⢰⣶⣶⣶⣶⣶⣦⣶⡄⠀⠀⠀⠀⢰⣷⣦⡀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣾⡆⠀⠀⠰⣦⣦⡆⠀⠀⣦⣴⣶⡀⠀⢠⣦⣴⡆",
    "⢸⣿⣿⣿⣿⡀⠀⠀⠀⣿⣿⣿⣿⠀⠀⠀⢸⣿⣿⡟⠛⠛⠛⠛⠃⠀⠀⠀⠀⢸⣿⣿⣿⣆⠀⠀⠀⠀⠀⣰⣿⣿⣿⡇⠀⠀⠀⣿⣿⣿⠀⢀⣿⣿⣿⡇⠀⢸⣿⣿⠃",
    "⢸⣿⣿⣿⣿⡇⠀⠀⢸⣿⣿⣿⣿⠀⠀⠀⢸⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣷⣾⣿⣿⣾⣿⣿⣿⣿⡇⠀⠀⠀⢸⣿⣿⡄⢸⣿⣿⣿⣷⠀⣿⣿⣿⠀",
    "⢸⣿⣿⣿⣿⣿⠀⠀⣿⣿⢿⣿⣿⠀⠀⠀⢸⣿⣿⣃⣀⣀⣀⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠈⣿⣿⡇⣾⣿⣿⣿⣿⣠⣿⣿⡇⠀",
    "⢸⣿⣿⡏⣿⣿⡆⢰⣿⣿⢸⣿⣿⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⣼⣿⣿⠋⠙⣿⣿⣿⣿⣿⠋⠙⣿⣿⣷⠀⠀⠀⠀⢻⣿⣿⣿⣿⡏⣿⣿⣿⣿⣿⠁⠀",
    "⢸⣿⣿⡇⢸⣿⣷⣼⣿⡇⢸⣿⣿⠀⠀⠀⢸⣿⣿⡇⠀⠀⠀⠀⠀⠀⢠⣤⣤⣿⣿⣿⣦⣴⣿⣿⠿⣿⣿⣦⣴⣿⣿⣿⣦⣤⡆⠀⢸⣿⣿⣿⣿⠃⢿⣿⣿⣿⡿⠀⠀",
    "⢸⣿⣿⡇⠈⣿⣿⣿⣿⠀⢸⣿⣿⠀⠀⠀⢸⣿⣿⡇⠀⠀⠀⠀⠀⠀⠘⠛⢛⣻⣿⣿⣿⣿⣿⣿⣶⣿⣿⣿⣿⣿⣿⣿⡛⠛⠃⠀⠀⣿⣿⣿⣿⠀⢸⣿⣿⣿⡇⠀⠀",
    "⢸⣿⣿⡇⠀⢸⣿⣿⡇⠀⢸⣿⣿⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⡇⠀⠰⣾⣿⠿⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠿⣿⣷⠂⠀⠀⢹⣿⣿⡇⠀⠀⣿⣿⣿⠁⠀⠀",
    "⠈⠉⠉⠁⠀⠀⠉⠉⠀⠀⠈⠉⠉⠀⠀⠀⠈⠉⠉⠉⠉⠉⠉⠉⠁⠀⠀⠁⠀⠀⠀⠈⠙⠻⠿⣿⣿⣿⠿⠿⠋⠁⠀⠀⠀⠈⠀⠀⠀⠈⠉⠉⠁⠀⠀⠉⠉⠉⠀⠀⠀",
]

SUBTITLE = "Pyramiden-KI für Termux - Übersicht & Training"

MENU_CHOICES = [
    "Daten laden / generieren",
    "Modell trainieren",
    "Ergebnisse anzeigen",
    "Interaktiven Test starten",
    "Modell exportieren",
    "Beenden",
]

STATE: Dict[str, Any] = {
    "data": None,
    "model": None,
    "input_handler": DynamicInputHandler(max_vertices=12, coordinates_per_vertex=3),
    "pyramid_generator": PyramidGenerator(seed=42),
    "train_losses": [],
    "test_losses": [],
    "last_validation_result": None,
    "total_training_count": 0,
    "current_test_vector": None,
    "current_soll": None,
}

SPINNER_FRAMES = ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"]
WIDTH = 88


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_line(char: str = "═", width: int = WIDTH) -> None:
    print(char * width)


def boxed(lines: Sequence[str], width: int = WIDTH, title: Optional[str] = None) -> None:
    print(f"╔{'═' * (width - 2)}╗")
    if title:
        print(f"║ {title.ljust(width - 4)} ║")
        print(f"╠{'═' * (width - 2)}╣")
    for line in lines:
        print(f"║ {line.ljust(width - 4)} ║")
    print(f"╚{'═' * (width - 2)}╝")


def split_box(left: Sequence[str], right: Sequence[str], width: int = WIDTH, left_width: int = 42) -> None:
    right_width = width - left_width - 3
    print(f"╔{'═' * (left_width + 1)}╦{'═' * (right_width + 1)}╗")
    max_lines = max(len(left), len(right))
    for i in range(max_lines):
        left_text = left[i] if i < len(left) else ""
        right_text = right[i] if i < len(right) else ""
        print(f"║ {left_text.ljust(left_width - 2)} ║ {right_text.ljust(right_width - 2)} ║")
    print(f"╚{'═' * (left_width + 1)}╩{'═' * (right_width + 1)}╝")


def render_header() -> None:
    clear_screen()
    for line in APP_HEADER:
        print(line.center(WIDTH))
    print()
    boxed([SUBTITLE.center(WIDTH - 4)], width=WIDTH)
    print()
    render_sidebar()


def safe_value(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    if isinstance(value, float):
        return f"{value:.5f}"
    return str(value)


def get_data_stats() -> Dict[str, Any]:
    if STATE["data"] is None:
        return {
            "Loaded": "Nein",
            "Rows": "0",
            "Pyramiden": "0",
            "Andere": "0",
            "Features": "0",
            "Vertices": "0",
        }
    data = STATE["data"]
    rows = len(data)
    labels = data[:, -1]
    pyramids = int(np.sum(labels == 1.0))
    other = rows - pyramids
    features = data.shape[1] - 1
    vertices = max(5, (features - 4) // 3)
    return {
        "Loaded": "Ja",
        "Rows": str(rows),
        "Pyramiden": str(pyramids),
        "Andere": str(other),
        "Features": str(features),
        "Vertices": str(vertices),
    }


def get_model_stats() -> Dict[str, Any]:
    if STATE["model"] is None:
        return {
            "Loaded": "Nein",
            "Input": "—",
            "Hidden": "—",
            "Epochs": "0",
            "Loss": "—",
            "Status": "Kein Modell",
        }
    model = STATE["model"]
    return {
        "Loaded": "Ja",
        "Input": str(model.get("input_size", "—")),
        "Hidden": str(model.get("hidden_size", "—")),
        "Epochs": str(STATE["total_training_count"]),
        "Loss": safe_value(STATE["test_losses"][-1] if STATE["test_losses"] else None),
        "Status": STATE["last_validation_result"] or "Keine Validierung",
    }


def render_sidebar() -> None:
    data_stats = get_data_stats()
    model_stats = get_model_stats()
    left = [
        "DATEN-ÜBERSICHT",
        "——————————————",
        f"Geladen: {data_stats['Loaded']}",
        f"Zeilen: {data_stats['Rows']}",
        f"Pyramiden: {data_stats['Pyramiden']}",
        f"Andere: {data_stats['Andere']}",
        f"Merkmale: {data_stats['Features']}",
        f"Vertices: {data_stats['Vertices']}",
    ]
    right = [
        "MODELL-ÜBERSICHT",
        "——————————————",
        f"Geladen: {model_stats['Loaded']}",
        f"Inputs: {model_stats['Input']}",
        f"Hidden: {model_stats['Hidden']}",
        f"Epochen: {model_stats['Epochs']}",
        f"Loss: {model_stats['Loss']}",
        f"Validierung: {model_stats['Status']}",
    ]
    split_box(left, right)
    print()


def animate_progress(message: str, iterations: int = 26) -> None:
    for i in range(iterations):
        frame = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
        sys.stdout.write(f"\r{frame} {message}... ")
        sys.stdout.flush()
        time.sleep(0.05)
    sys.stdout.write("\r" + " " * (len(message) + 6) + "\r")
    sys.stdout.flush()


def ask_menu_choice() -> int:
    if inquirer is not None:
        try:
            selected = inquirer.select(
                message="Wählen Sie eine Aktion:",
                choices=MENU_CHOICES,
                long_instruction="Nutzen Sie die Pfeiltasten und ENTER.",
                pointer="➡",
            ).execute()
            if selected in MENU_CHOICES:
                return MENU_CHOICES.index(selected) + 1
        except Exception:
            pass
    print_line("─")
    for idx, item in enumerate(MENU_CHOICES, start=1):
        print(f"  {idx}. {item}")
    print_line("─")
    while True:
        choice = input("Auswahl [1-6]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(MENU_CHOICES):
            return int(choice)
        print("Ungültige Eingabe. Bitte eine Zahl zwischen 1 und 6 eingeben.")


def prompt_int(prompt: str, default: int) -> int:
    while True:
        value = input(f"{prompt} [{default}]: ").strip()
        if not value:
            return default
        if value.isdigit() and int(value) > 0:
            return int(value)
        print("Bitte eine positive Ganzzahl eingeben.")


def prompt_float(prompt: str, default: float) -> float:
    while True:
        value = input(f"{prompt} [{default}]: ").strip().replace(',', '.')
        if not value:
            return default
        try:
            number = float(value)
            if number > 0.0:
                return number
        except ValueError:
            pass
        print("Bitte eine gültige positive Zahl eingeben.")


def pause() -> None:
    input("\nDrücke ENTER, um zum Menü zurückzukehren...")


def expit(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500.0, 500.0)))


def format_vector_preview(vector: np.ndarray, length: int = 8) -> str:
    preview = [f"{v:.3f}" if not np.isnan(v) else "NaN" for v in vector[:length]]
    if vector.size > length:
        preview.append("...")
    return ", ".join(preview)


def show_dataset_preview(data: np.ndarray) -> None:
    print("DATEN-VORSCHAU")
    print_line("─")
    for idx, row in enumerate(data[:3, :-1], start=1):
        print(f"  Zeile {idx}: {format_vector_preview(row, length=8)}")
    print_line("─")


def update_input_handler_from_data(data: np.ndarray) -> None:
    """Passt den Input-Handler an die Breite des geladenen oder generierten Datensatzes an."""
    if data is None or data.ndim != 2 or data.shape[1] < 2:
        return

    feature_count = data.shape[1] - 1
    coords_per_vertex = STATE["input_handler"].coordinates_per_vertex
    extra_features = 4
    coord_feature_count = max(feature_count - extra_features, 0)
    estimated_vertices = max(5, int(np.ceil(coord_feature_count / coords_per_vertex)))
    STATE["input_handler"].max_vertices = estimated_vertices


def invalidate_model_state() -> None:
    """Entfernt ein ungültiges Modell, wenn sich die Datensatzstruktur geändert hat."""
    if STATE["model"] is not None:
        STATE["model"] = None
        STATE["train_losses"] = []
        STATE["test_losses"] = []
        STATE["last_validation_result"] = None
        STATE["total_training_count"] = 0


def load_data() -> None:
    render_header()
    boxed(["Daten laden / generieren"], width=WIDTH)
    print("  1) Synthetischen Datensatz erzeugen")
    print("  2) CSV-Datei importieren")
    print("  3) Zurück zum Hauptmenü")
    while True:
        choice = input("Auswahl [1-3]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= 3:
            break
        print("Ungültige Eingabe. Bitte eine Zahl zwischen 1 und 3 eingeben.")
    if int(choice) == 1:
        generate_synthetic_dataset()
    elif int(choice) == 2:
        import_csv_dataset()


def generate_synthetic_dataset() -> None:
    render_header()
    boxed(["Synthetischen Datensatz generieren"], width=WIDTH)
    max_vertices = prompt_int("Maximale Eckpunkte", STATE["input_handler"].max_vertices)
    n_pyramids = prompt_int("Anzahl Pyramiden", 100)
    n_non_pyramids = prompt_int("Anzahl andere Formen", 100)

    print()
    boxed(["Datensätze werden generiert"], width=WIDTH)
    animate_progress("Dataset-Aufbau", iterations=26)

    data_matrix, _ = STATE["pyramid_generator"].generate_dataset(
        max_vertices=max_vertices,
        coords_per_vertex=STATE["input_handler"].coordinates_per_vertex,
        n_pyramids=n_pyramids,
        n_non_pyramids=n_non_pyramids,
        shuffle=True,
    )

    STATE["data"] = data_matrix.astype(np.float32)
    update_input_handler_from_data(STATE["data"])
    invalidate_model_state()
    STATE["current_test_vector"] = None
    STATE["current_soll"] = None
    debug_generate("Synthetischen Datensatz erzeugt.")

    render_header()
    boxed(["Datensatz erfolgreich generiert"], width=WIDTH)
    show_dataset_preview(STATE["data"])
    pause()


def import_csv_dataset() -> None:
    render_header()
    boxed(["CSV-Datei importieren"], width=WIDTH)
    path = input("Dateipfad: ").strip()
    if not path:
        boxed(["Keine Datei angegeben. Rückkehr zum Menü."], width=WIDTH)
        pause()
        return
    if not os.path.exists(path):
        boxed(["Datei nicht gefunden. Bitte Pfad überprüfen."], width=WIDTH)
        pause()
        return

    print()
    animate_progress("CSV wird geladen", iterations=20)

    try:
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader if row]
        if not rows:
            raise ValueError("Die CSV-Datei ist leer.")

        first_row = rows[0]
        has_header = any(not cell.replace('.', '', 1).replace('-', '', 1).isdigit() for cell in first_row)
        if has_header:
            rows = rows[1:]

        data = np.array(rows, dtype=np.float32)
        if data.ndim != 2 or data.shape[1] < 2:
            raise ValueError("CSV muss mindestens zwei Spalten besitzen.")

        STATE["data"] = data
        update_input_handler_from_data(STATE["data"])
        invalidate_model_state()
        STATE["current_test_vector"] = None
        STATE["current_soll"] = None
        debug_info("CSV-Datensatz geladen.")

        render_header()
        boxed(["CSV erfolgreich importiert"], width=WIDTH)
        show_dataset_preview(STATE["data"])
    except Exception as exc:
        debug_error("CSV-Import fehlgeschlagen.", exc)
        boxed([f"Fehler beim Einlesen: {exc}"], width=WIDTH)

    pause()


def train_model() -> None:
    if STATE["data"] is None:
        render_header()
        boxed(["Kein Datensatz geladen. Bitte zuerst Daten erstellen oder importieren."], width=WIDTH)
        pause()
        return

    render_header()
    boxed(["Modell trainieren"], width=WIDTH)
    try:
        prepared, _ = STATE["input_handler"].filter_and_prepare(STATE["data"], fit=False)
        detected_inputs = prepared.shape[1] - 1
    except Exception:
        detected_inputs = STATE["data"].shape[1] - 1

    input_size = prompt_int("Input Nodes", detected_inputs)
    hidden_size = prompt_int("Hidden Nodes", 32)
    learning_rate = prompt_float("Lernrate", 0.1)
    epochs = prompt_int("Anzahl Epochen", 1000)

    can_continue = STATE["model"] is not None and STATE["model"].get("input_size") == input_size and STATE["model"].get("hidden_size") == hidden_size
    mode_text = "Bestehendes Modell weitertrainieren" if can_continue else "Neu initialisieren"

    boxed([f"Trainingsmodus: {mode_text}"], width=WIDTH)
    if input("Starten? (j/N): ").strip().lower() != "j":
        pause()
        return

    print()
    animate_progress("Training läuft", iterations=30)

    try:
        prepared_data, _ = STATE["input_handler"].filter_and_prepare(STATE["data"], fit=True)
        X_all = prepared_data[:, :-1]
        y_all = prepared_data[:, -1:]
        actual_input_size = X_all.shape[1]

        rng = np.random.default_rng(42)
        indices = rng.permutation(len(prepared_data))
        split = int(len(indices) * 0.8)
        train_idx = indices[:split]
        val_idx = indices[split:]

        X_train, y_train = X_all[train_idx], y_all[train_idx]
        X_val = X_all[val_idx] if len(val_idx) > 0 else X_train
        y_val = y_all[val_idx] if len(val_idx) > 0 else y_train
        n_train = len(X_train)
        X_train_T = X_train.T

        if can_continue and STATE["model"] is not None:
            W1 = STATE["model"]["W1"].copy()
            b1 = STATE["model"]["b1"].copy()
            W2 = STATE["model"]["W2"].copy()
            b2 = STATE["model"]["b2"].copy()
            train_losses = list(STATE["train_losses"])
            test_losses = list(STATE["test_losses"])
        else:
            rng_init = np.random.default_rng(42)
            W1 = (rng_init.standard_normal((actual_input_size, hidden_size)) * np.sqrt(2.0 / actual_input_size)).astype(np.float32)
            b1 = np.zeros((1, hidden_size), dtype=np.float32)
            W2 = (rng_init.standard_normal((hidden_size, 1)) * np.sqrt(2.0 / hidden_size)).astype(np.float32)
            b2 = np.zeros((1, 1), dtype=np.float32)
            train_losses = []
            test_losses = []

        for epoch in range(1, epochs + 1):
            z1 = X_train @ W1 + b1
            a1 = np.maximum(0.0, z1)
            z2 = a1 @ W2 + b2
            a2 = expit(z2)
            loss = float(np.mean((a2 - y_train) ** 2))
            train_losses.append(loss)

            a1_val = np.maximum(0.0, X_val @ W1 + b1)
            a2_val = expit(a1_val @ W2 + b2)
            val_loss = float(np.mean((a2_val - y_val) ** 2))
            test_losses.append(val_loss)

            dz2 = (a2 - y_train) * a2 * (1.0 - a2)
            grad_W2 = (a1.T @ dz2) / n_train
            grad_b2 = np.mean(dz2, axis=0, keepdims=True)
            dz1 = (dz2 @ W2.T) * (z1 > 0.0)
            grad_W1 = (X_train_T @ dz1) / n_train
            grad_b1 = np.mean(dz1, axis=0, keepdims=True)

            W2 -= learning_rate * grad_W2
            b2 -= learning_rate * grad_b2
            W1 -= learning_rate * grad_W1
            b1 -= learning_rate * grad_b1

            if epoch % max(1, epochs // 8) == 0 or epoch == epochs:
                progress = int((epoch / epochs) * 50)
                bar = "█" * progress + " " * (50 - progress)
                sys.stdout.write(f"\r[{bar}] Epoche {epoch}/{epochs}  Verlust={loss:.5f}  Val={val_loss:.5f}")
                sys.stdout.flush()
        print()

        STATE["model"] = {
            "W1": W1,
            "b1": b1,
            "W2": W2,
            "b2": b2,
            "input_size": actual_input_size,
            "hidden_size": hidden_size,
            "normalization_params": STATE["input_handler"].normalization_params,
        }
        STATE["train_losses"] = train_losses
        STATE["test_losses"] = test_losses
        STATE["total_training_count"] += epochs
        STATE["last_validation_result"] = f"Letzter Val-Loss: {val_loss:.5f}"

        debug_training({
            "Lernrate": learning_rate,
            "Epochen": epochs,
            "Input-Größe": actual_input_size,
            "Hidden-Größe": hidden_size,
            "Train Loss": loss,
            "Val Loss": val_loss,
        })

        render_header()
        boxed(["Training abgeschlossen"], width=WIDTH)
        print(f"  Letzter Verlust: {val_loss:.5f}")
        print(f"  Architektur: {actual_input_size} → {hidden_size} → 1")
    except Exception as exc:
        debug_error("Training fehlgeschlagen.", exc)
        boxed([f"Fehler: {exc}"], width=WIDTH)

    pause()


def show_results() -> None:
    render_header()
    boxed(["Ergebnisse anzeigen"], width=WIDTH)
    if STATE["model"] is None:
        boxed(["Kein Modell verfügbar. Bitte zuerst trainieren oder laden."], width=WIDTH)
        pause()
        return

    model = STATE["model"]
    lines = [
        f"Input: {model['input_size']}",
        f"Hidden: {model['hidden_size']}",
        f"Trainingsläufe: {STATE['total_training_count']}",
        f"Letzter Loss: {STATE['test_losses'][-1]:.5f}" if STATE['test_losses'] else "Letzter Loss: —",
        f"Validierung: {STATE['last_validation_result']}",
    ]
    boxed(lines, width=WIDTH)
    if STATE["train_losses"]:
        print()
        print(f"  Train Loss (erste): {STATE['train_losses'][0]:.5f}")
        print(f"  Train Loss (letzte): {STATE['train_losses'][-1]:.5f}")
    if STATE["test_losses"]:
        print(f"  Val Loss (erste): {STATE['test_losses'][0]:.5f}")
        print(f"  Val Loss (letzte): {STATE['test_losses'][-1]:.5f}")
    print()
    boxed(["Gewichtsschnappschuss"], width=WIDTH)
    print(f"  W1[0,0] = {model['W1'].flat[0]:.5f}")
    print(f"  W2[0,0] = {model['W2'].flat[0]:.5f}")
    print(f"  b1[0] = {model['b1'].flat[0]:.5f}")
    print(f"  b2[0] = {model['b2'].flat[0]:.5f}")
    pause()


def prepare_test_vector(raw_vector: np.ndarray) -> Optional[Dict[str, Any]]:
    raw = np.array(raw_vector, dtype=np.float32).flatten()
    max_len = STATE["input_handler"].max_vertices * STATE["input_handler"].coordinates_per_vertex
    if raw.size < max_len:
        padded = np.full(max_len, np.nan, dtype=np.float32)
        padded[: raw.size] = raw
        raw = padded

    prep = np.zeros((1, raw.size + 1), dtype=np.float32)
    prep[0, : raw.size] = raw
    try:
        norm_matrix, _ = STATE["input_handler"].filter_and_prepare(prep, fit=False)
    except Exception as exc:
        debug_error("Test-Vektor konnte nicht vorbereitet werden.", exc)
        return None
    return {
        "raw": raw,
        "normalized": norm_matrix[0, :-1],
        "input_vector": norm_matrix[0, :-1].reshape(1, -1),
    }


def interactive_test() -> None:
    if STATE["model"] is None:
        render_header()
        boxed(["Kein Modell geladen. Bitte zuerst trainieren oder laden."], width=WIDTH)
        pause()
        return

    render_header()
    boxed(["Interaktiver Test"], width=WIDTH)
    print("  1) Zufälliges Objekt generieren")
    print("  2) Manuelle Koordinaten eingeben")
    print("  3) Zurück zum Menü")
    while True:
        choice = input("Auswahl [1-3]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= 3:
            choice = int(choice)
            break
        print("Ungültige Eingabe. Bitte eine Zahl zwischen 1 und 3 eingeben.")

    if choice == 1:
        print("  1) Pyramide")
        print("  2) Andere Form")
        kind = prompt_int("Objekttyp", 1)
        if kind == 1:
            raw_vector = STATE["pyramid_generator"].generate_single_pyramid(
                STATE["input_handler"].max_vertices,
                STATE["input_handler"].coordinates_per_vertex,
            )
            STATE["current_soll"] = 1.0
        else:
            raw_vector = STATE["pyramid_generator"].generate_single_non_pyramid(
                STATE["input_handler"].max_vertices,
                STATE["input_handler"].coordinates_per_vertex,
            )
            STATE["current_soll"] = 0.0
        STATE["current_test_vector"] = raw_vector
    elif choice == 2:
        raw_vector = prompt_manual_vector()
        if raw_vector is None:
            return
        STATE["current_test_vector"] = raw_vector
        STATE["current_soll"] = None
    else:
        return

    result = prepare_test_vector(STATE["current_test_vector"])
    if result is None:
        boxed(["Die Eingabedaten konnten nicht normiert werden."], width=WIDTH)
        pause()
        return

    model = STATE["model"]
    a1 = np.maximum(0.0, result["input_vector"] @ model["W1"] + model["b1"])
    prediction = float(expit(a1 @ model["W2"] + model["b2"])[0, 0])
    final_class = 1 if prediction >= 0.5 else 0

    render_header()
    boxed(["Testergebnis"], width=WIDTH)
    print(f"  Vorhersage: {'Pyramide' if final_class == 1 else 'Nicht-Pyramide'}")
    print(f"  Wahrscheinlichkeit: {prediction:.4f}")
    if STATE["current_soll"] is not None:
        print(f"  Erwartetes Ergebnis: {int(STATE['current_soll'])}")
    print(f"  Normierte Eingabe (Vorschau): {format_vector_preview(result['normalized'], length=10)}")
    pause()


def prompt_manual_vector() -> Optional[np.ndarray]:
    expected = STATE["input_handler"].max_vertices * STATE["input_handler"].coordinates_per_vertex
    boxed([f"Manuelle Eingabe ({expected} Werte, NaN erlaubt)"], width=WIDTH)
    raw_text = input("Eingabe: ").strip()
    if not raw_text:
        print("Keine Eingabe erhalten.")
        pause()
        return None
    try:
        parts = [item.strip() for item in raw_text.split(",") if item.strip()]
        values: List[float] = []
        for part in parts:
            if part.lower() in ("nan", "x", "_"):
                values.append(np.nan)
            else:
                values.append(float(part.replace(',', '.')))
        if len(values) > expected:
            values = values[:expected]
        if len(values) < expected:
            values.extend([np.nan] * (expected - len(values)))
        return np.array(values, dtype=np.float32)
    except Exception as exc:
        debug_error("Manuelle Testeingabe ungültig.", exc)
        boxed(["Ungültige Eingabe. Bitte nur Zahlen und Kommas verwenden."], width=WIDTH)
        pause()
        return None


def export_model() -> None:
    render_header()
    boxed(["Modell exportieren"], width=WIDTH)
    if STATE["model"] is None:
        boxed(["Kein Modell vorhanden. Bitte zuerst trainieren oder laden."], width=WIDTH)
        pause()
        return

    filename = input("Export-Dateiname [model_export.json]: ").strip() or "model_export.json"
    animate_progress("Exportiere Modell", iterations=18)

    try:
        model = STATE["model"]
        payload = {
            "W1": model["W1"].tolist(),
            "b1": model["b1"].tolist(),
            "W2": model["W2"].tolist(),
            "b2": model["b2"].tolist(),
            "config": {
                "input_size": int(model["input_size"]),
                "hidden_size": int(model["hidden_size"]),
            },
            "stats": {
                "total_epochs": int(STATE["total_training_count"]),
                "last_loss": float(STATE["test_losses"][-1] if STATE["test_losses"] else 0.0),
                "validation": STATE["last_validation_result"],
            },
            "normalization_params": model.get("normalization_params", {}),
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        boxed([f"Modell erfolgreich gespeichert: {filename}"], width=WIDTH)
    except Exception as exc:
        debug_error("Modell-Export fehlgeschlagen.", exc)
        boxed([f"Fehler beim Speichern: {exc}"], width=WIDTH)

    pause()


def exit_program() -> None:
    print("\nBeende Anwendung...")
    sys.exit(0)


def main() -> None:
    while True:
        render_header()
        choice = ask_menu_choice()
        if choice == 1:
            load_data()
        elif choice == 2:
            train_model()
        elif choice == 3:
            show_results()
        elif choice == 4:
            interactive_test()
        elif choice == 5:
            export_model()
        elif choice == 6:
            exit_program()
        else:
            print("Ungültige Auswahl.")
            time.sleep(0.5)


if __name__ == "__main__":
    main()
