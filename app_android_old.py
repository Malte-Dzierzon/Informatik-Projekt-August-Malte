import csv
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import numpy as np

from debug_utils import animated_message, debug_error, debug_generate, debug_info, debug_training
from dynamic_input import DynamicInputHandler
from pyramid_generator import PyramidGenerator

try:
    from InquirerPy import inquirer
except ImportError:
    inquirer = None

APP_HEADER = r"""
  ____  __  __  ____   _   _   _    _  __  __  __  __  _____  
 |  _ \|  \/  |/ __ \ | \ | | | |  | ||  \/  ||  \/  ||  __ \ 
 | |_) | \  / | |  | ||  \| | | |  | || \  / || \  / || |  | |
 |  _ <| |\/| | |  | || . ` | | |  | || |\/| || |\/| || |  | |
 | |_) | |  | | |__| || |\  | | |__| || |  | || |  | || |__| |
 |____/|_|  |_|\____/ |_| \_|  \____/ |_|  |_| |_|  |_||_____/ 
"""

SUBTITLE = "Pyramiden-KI - Terminal Interface für Android/Termux"

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

SPINNER_FRAMES = ["●", "○", "◐", "◓", "◑", "◒"]


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def border_line(width: int = 76, left: str = "╔", right: str = "╗") -> str:
    return f"{left}{'═' * width}{right}"


def section_line(width: int = 76) -> str:
    return f"╠{'═' * width}╣"


def panel_line(text: str, width: int = 76) -> str:
    padded = text[:width].ljust(width)
    return f"║{padded}║"


def print_header() -> None:
    clear_screen()
    print(border_line())
    for line in APP_HEADER.splitlines():
        print(panel_line(line.center(76)))
    print(panel_line(""))
    print(panel_line(SUBTITLE.center(76)))
    print(section_line())
    print_current_status()
    print(section_line())


def print_current_status() -> None:
    data_loaded = "Ja" if STATE["data"] is not None else "Nein"
    model_loaded = "Ja" if STATE["model"] is not None else "Nein"
    validation = STATE["last_validation_result"] or "Keine Validierung"

    print(panel_line(f"Status: Daten geladen = {data_loaded}  |  Modell geladen = {model_loaded}"))
    print(panel_line(f"Trainingsläufe = {STATE['total_training_count']}  |  Validierung = {validation}"))


def horizontal_menu() -> None:
    print(panel_line("Menü:  1) Daten  2) Trainieren  3) Ergebnisse  4) Test  5) Export  6) Beenden"))
    print(section_line())


def slow_print(text: str, delay: float = 0.005) -> None:
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def animate_banner(message: str, rounds: int = 2) -> None:
    for _ in range(rounds):
        for frame in SPINNER_FRAMES:
            sys.stdout.write(f"\r[{frame}] {message}")
            sys.stdout.flush()
            time.sleep(0.07)
    sys.stdout.write("\r" + " " * (len(message) + 6) + "\r")
    sys.stdout.flush()


def prompt_option(prompt: str, count: int) -> int:
    while True:
        choice = input(f"{prompt} [1-{count}]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= count:
            return int(choice)
        print("Ungültige Eingabe. Bitte eine Zahl eingeben.")


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


def format_vector_summary(vector: np.ndarray) -> str:
    values = [f"{v:.3f}" if not np.isnan(v) else "NaN" for v in vector[:8]]
    if vector.size > 8:
        values.append("...")
    return ", ".join(values)


def show_dataset_summary(data: np.ndarray) -> None:
    rows = len(data)
    features = data.shape[1] - 1
    pressed = int(np.sum(data[:, -1] == 1.0))
    other = rows - pressed
    vertices = max(5, (features - 4) // 3)

    print(panel_line(f"Datensätze gesamt = {rows}  |  Pyramiden = {pressed}  |  Andere = {other}"))
    print(panel_line(f"Gesamtmerkmale = {features}  |  Erkannte Vertex-Anzahl = {vertices}"))
    print(section_line())
    sample = data[: min(3, rows), :-1]
    for idx, row in enumerate(sample, start=1):
        print(panel_line(f"Zeile {idx}: {format_vector_summary(row)}"))
    print(section_line())


def update_input_handler_from_data(data: np.ndarray) -> None:
    total_features = data.shape[1] - 1
    vertices = max(5, (total_features - 4) // 3)
    handler = STATE["input_handler"]
    handler.max_vertices = vertices
    handler.coordinates_per_vertex = 3


def load_data() -> None:
    print_header()
    print(panel_line("Daten laden / generieren".center(76)))
    print(section_line())
    print(panel_line("1) Synthetischen Datensatz generieren"))
    print(panel_line("2) CSV-Datei importieren"))
    print(panel_line("3) Zurück"))
    print(border_line())

    choice = prompt_option("Auswahl", 3)
    if choice == 1:
        generate_synthetic_dataset()
    elif choice == 2:
        import_csv_dataset()


def generate_synthetic_dataset() -> None:
    print_header()
    print(panel_line("Synthetischen Datensatz generieren".center(76)))
    print(section_line())

    max_vertices = prompt_int("Maximale Eckpunkte", STATE["input_handler"].max_vertices)
    n_pyramids = prompt_int("Anzahl Pyramiden", 100)
    n_non_pyramids = prompt_int("Anzahl andere Formen", 100)

    print(panel_line("Generiere Datensatz, bitte warten..."))
    animate_banner("Dataset-Aufbau wird vorbereitet", rounds=3)

    data_matrix, _ = STATE["pyramid_generator"].generate_dataset(
        max_vertices=max_vertices,
        coords_per_vertex=STATE["input_handler"].coordinates_per_vertex,
        n_pyramids=n_pyramids,
        n_non_pyramids=n_non_pyramids,
        shuffle=True,
    )

    STATE["data"] = data_matrix.astype(np.float32)
    update_input_handler_from_data(STATE["data"])
    STATE["current_test_vector"] = None
    STATE["current_soll"] = None
    debug_generate("Synthetischen Datensatz erzeugt.")

    print(panel_line("Datensatz erfolgreich generiert."))
    show_dataset_summary(STATE["data"])
    pause()


def import_csv_dataset() -> None:
    print_header()
    print(panel_line("CSV-Datei importieren".center(76)))
    print(section_line())

    path = input("Pfad zur CSV-Datei: ").strip()
    if not path:
        print(panel_line("Keine Datei angegeben. Rückkehr zum Menü."))
        pause()
        return

    if not os.path.exists(path):
        print(panel_line("Datei nicht gefunden. Bitte Pfad überprüfen."))
        pause()
        return

    print(panel_line("Lese CSV-Datei ein, bitte warten..."))
    animate_banner("Datei wird analysiert", rounds=2)

    try:
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows: List[List[str]] = [row for row in reader if row]

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
        STATE["current_test_vector"] = None
        STATE["current_soll"] = None
        debug_info("CSV-Datensatz geladen.")

        print(panel_line("CSV erfolgreich importiert."))
        show_dataset_summary(STATE["data"])
    except Exception as exc:
        debug_error("CSV-Import fehlgeschlagen.", exc)
        print(panel_line(f"Fehler beim Einlesen: {exc}"))

    pause()


def train_model() -> None:
    if STATE["data"] is None:
        print_header()
        print(panel_line("Kein Datensatz geladen. Bitte zuerst Daten erstellen oder importieren."))
        pause()
        return

    print_header()
    print(panel_line("Modell trainieren".center(76)))
    print(section_line())

    raw_features = STATE["data"][:, :-1]
    try:
        prepared, _ = STATE["input_handler"].filter_and_prepare(STATE["data"], fit=False)
        detected_inputs = prepared.shape[1] - 1
    except Exception:
        detected_inputs = STATE["data"].shape[1] - 1

    input_size = prompt_int("Eingangsgröße (Input Nodes)", detected_inputs)
    hidden_size = prompt_int("Versteckte Neuronen (Hidden Nodes)", 32)
    learning_rate = prompt_float("Lernrate", 0.1)
    epochs = prompt_int("Anzahl Epochen", 1000)

    can_continue = STATE["model"] is not None and STATE["model"].get("input_size") == input_size and STATE["model"].get("hidden_size") == hidden_size
    mode_text = "Neue Gewichte" if not can_continue else "Weitertrainieren auf bestehendem Modell"

    print(panel_line(f"Aktueller Modus: {mode_text}"))
    start_now = input("Trainieren starten? (j/N): ").strip().lower() == "j"
    if not start_now:
        pause()
        return

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

        print(panel_line("Training startet..."))
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

            if epoch % max(1, epochs // 10) == 0 or epoch == epochs:
                progress = int((epoch / epochs) * 60)
                bar = "█" * progress + " " * (60 - progress)
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
        STATE["last_validation_result"] = f"Trainiert auf {actual_input_size} Merkmalen, letzter Loss {val_loss:.5f}"

        debug_training({
            "Lernrate": learning_rate,
            "Epochen": epochs,
            "Input-Größe": actual_input_size,
            "Hidden-Größe": hidden_size,
            "Letzter Train Loss": loss,
            "Letzter Val Loss": val_loss,
        })

        print(panel_line("Training abgeschlossen."))
        print(panel_line(f"Letzter Validierungsverlust = {val_loss:.5f}"))
    except Exception as exc:
        debug_error("Training fehlgeschlagen.", exc)
        print(panel_line(f"Fehler: {exc}"))

    pause()


def show_results() -> None:
    print_header()
    print(panel_line("Ergebnisse anzeigen".center(76)))
    print(section_line())

    if STATE["model"] is None:
        print(panel_line("Kein Modell verfügbar. Bitte zuerst trainieren oder laden."))
        pause()
        return

    model = STATE["model"]
    print(panel_line(f"Modellarchitektur: Input={model['input_size']}  Hidden={model['hidden_size']}"))
    print(panel_line(f"Gesamttrainings-Epochen: {STATE['total_training_count']}"))
    print(panel_line(f"Letztes Validierungsergebnis: {STATE['last_validation_result']}"))
    print(section_line())
    print(panel_line("Aktuelle Verlustkurven"))
    if STATE["train_losses"]:
        print(panel_line(f"Train Loss (erste) = {STATE['train_losses'][0]:.5f}  zuletzt = {STATE['train_losses'][-1]:.5f}"))
    if STATE["test_losses"]:
        print(panel_line(f"Val Loss (erste)   = {STATE['test_losses'][0]:.5f}  zuletzt = {STATE['test_losses'][-1]:.5f}"))
    print(section_line())
    print(panel_line("Gewichts-Schnappschuss"))
    print(panel_line(f"W1[0][0] = {model['W1'].flat[0]:.5f}  W2[0][0] = {model['W2'].flat[0]:.5f}"))
    print(panel_line(f"Bias b1[0] = {model['b1'].flat[0]:.5f}  Bias b2[0] = {model['b2'].flat[0]:.5f}"))
    print(section_line())
    print(panel_line("Du kannst das Modell exportieren, um die Parameter zu sichern."))
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
    pref = prep.copy()

    try:
        norm_matrix, _ = STATE["input_handler"].filter_and_prepare(pref, fit=False)
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
        print_header()
        print(panel_line("Kein Modell geladen. Bitte zuerst trainieren oder laden."))
        pause()
        return

    print_header()
    print(panel_line("Interaktiver Test".center(76)))
    print(section_line())
    print(panel_line("1) Zufälliges Objekt generieren"))
    print(panel_line("2) Manuelle Koordinaten eingeben"))
    print(panel_line("3) Zurück"))
    print(border_line())

    choice = prompt_option("Auswahl", 3)
    raw_vector: np.ndarray

    if choice == 1:
        print(panel_line("1) Pyramide"))
        print(panel_line("2) Andere Form"))
        kind = prompt_option("Objekttyp", 2)
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
        print(panel_line("Die Eingabedaten konnten nicht normiert werden."))
        pause()
        return

    model = STATE["model"]
    a1 = np.maximum(0.0, result["input_vector"] @ model["W1"] + model["b1"])
    prediction = float(expit(a1 @ model["W2"] + model["b2"])[0, 0])
    final_class = 1 if prediction >= 0.5 else 0

    print(section_line())
    print(panel_line("Vorhersage-Resultat".center(76)))
    print(panel_line(f"Modell-Wahrscheinlichkeit = {prediction:.4f}"))
    print(panel_line(f"Prognose = {'Pyramide' if final_class == 1 else 'Nicht-Pyramide'}"))
    if STATE["current_soll"] is not None:
        print(panel_line(f"Erwartetes Ergebnis = {int(STATE['current_soll'])}"))
    print(panel_line(f"Normierter Input (erste Werte) = {format_vector_summary(result['normalized'])}"))
    pause()


def prompt_manual_vector() -> Optional[np.ndarray]:
    expected = STATE["input_handler"].max_vertices * STATE["input_handler"].coordinates_per_vertex
    print(panel_line("Manuelle Eingabe von Koordinaten".center(76)))
    print(section_line())
    print(panel_line(f"Erwarte {expected} Werte, getrennt durch Kommas. Leere Werte als NaN."))
    print(panel_line("Beispiel: 0.5,0.5,0.2, 0.4,0.4,0.2, ..."))
    raw_text = input("Eingabe: ").strip()
    if not raw_text:
        print(panel_line("Keine Eingabe erhalten."))
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
        print(panel_line("Ungültige Eingabe. Bitte nur Zahlen und Kommas verwenden."))
        pause()
        return None


def export_model() -> None:
    print_header()
    print(panel_line("Modell exportieren".center(76)))
    print(section_line())

    if STATE["model"] is None:
        print(panel_line("Kein Modell vorhanden. Bitte zuerst trainieren oder laden."))
        pause()
        return

    filename = input("Export-Dateiname [model_export.json]: ").strip() or "model_export.json"
    print(panel_line("Schreibe Modellinformationen in die Datei."))
    animate_banner("Export läuft", rounds=2)

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
        print(panel_line(f"Modell erfolgreich gespeichert: {filename}"))
    except Exception as exc:
        debug_error("Modell-Export fehlgeschlagen.", exc)
        print(panel_line(f"Fehler beim Speichern: {exc}"))

    pause()


def exit_program() -> None:
    print("\nProgramm wird beendet.")
    sys.exit(0)


def main() -> None:
    while True:
        print_header()
        horizontal_menu()
        choice = prompt_option("Auswahl", len(MENU_CHOICES))

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
            print("Unbekannte Auswahl. Bitte erneut versuchen.")
            time.sleep(0.5)


if __name__ == "__main__":
    main()
