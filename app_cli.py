import os
import sys
import time
import json
from typing import Any, Dict, Optional

try:
    from InquirerPy import inquirer
except ImportError:
    inquirer = None

APP_HEADER = r"""
 ██████╗ ██╗   ██╗██████╗  █████╗ ███╗   ███╗██████╗ ██╗
██╔═══██╗██║   ██║██╔══██╗██╔══██╗████╗ ████║██╔══██╗██║
██║   ██║██║   ██║██████╔╝███████║██╔████╔██║██████╔╝██║
██║   ██║██║   ██║██╔═══╝ ██╔══██║██║╚██╔╝██║██╔═══╝ ██║
╚██████╔╝╚██████╔╝██║     ██║  ██║██║ ╚═╝ ██║██║     ██║
 ╚═════╝  ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝
"""

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
    "train_losses": [],
    "test_losses": [],
    "last_validation_result": None,
    "total_training_count": 0,
    "current_test_vector": None,
    "current_soll": None,
}


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_divider(width: int = 72) -> None:
    print("┌" + "─" * width + "┐")


def print_header() -> None:
    clear_screen()
    print(APP_HEADER)
    print("📱  Terminal-Interface für Termux / Android")
    print("✨  Clean, übersichtlich und für mobile Bildschirme optimiert")
    print("" + "─" * 72)
    print_current_status()
    print("" + "─" * 72)


def print_current_status() -> None:
    model_loaded = "Ja" if STATE["model"] else "Nein"
    data_loaded = "Ja" if STATE["data"] is not None else "Nein"
    last_val = STATE["last_validation_result"] or "Keine Validierung"

    print(f"Status:  Daten geladen: {data_loaded}  |  Modell geladen: {model_loaded}")
    print(f"Trainingsläufe: {STATE['total_training_count']}  |  Letzte Validierung: {last_val}")


def pause() -> None:
    input("\nDrücke ENTER, um zum Menü zurückzukehren...")


def ask_menu_choice() -> str:
    if inquirer is not None:
        try:
            return inquirer.select(
                message="Bitte wähle eine Option:",
                choices=MENU_CHOICES,
                long_instruction="Nutze die Pfeiltasten und ENTER.",
                pointer="▶",
            ).execute()
        except Exception:
            pass

    print("\nMenü:")
    for index, option in enumerate(MENU_CHOICES, start=1):
        print(f"  {index}. {option}")

    while True:
        choice = input("Auswahl [1-6]: ")
        if choice.isdigit() and 1 <= int(choice) <= len(MENU_CHOICES):
            return MENU_CHOICES[int(choice) - 1]
        print("Ungültige Eingabe. Bitte erneut versuchen.")


def notify_placeholder(feature_name: str) -> None:
    print(f"\n🔧 Platzhalter: {feature_name}")
    print("Füge hier deinen bestehenden Code aus `app.py` ein, um die Funktionalität zu füllen.")
    pause()


def load_data() -> None:
    print_header()
    print("📥 Daten laden / erstellen")
    print("" + "─" * 72)
    print("1) Synthetischen Datensatz generieren")
    print("2) CSV-Datei importieren")
    print("3) Zurück")

    choice = input("Auswahl [1-3]: ")

    if choice == "1":
        generate_synthetic_dataset()
    elif choice == "2":
        import_csv_dataset()
    else:
        return


def generate_synthetic_dataset() -> None:
    print_header()
    print("🧬 Synthetischen Datensatz generieren")
    print("" + "─" * 72)
    print("Hier wird später dein Pyramiden- und Nicht-Pyramiden-Datengenerator eingebunden.")
    print("Beispiel: STATE['data'] = generated_matrix.astype(np.float32)")
    notify_placeholder("generate_synthetic_dataset")


def import_csv_dataset() -> None:
    print_header()
    print("📄 CSV-Datei importieren")
    print("" + "─" * 72)
    print("Hier kannst du später den CSV-Import aus `app.py` einbauen.")
    print("Beispiel: STATE['data'] = pandas.read_csv(...).to_numpy(dtype=np.float32)")
    notify_placeholder("import_csv_dataset")


def train_model() -> None:
    print_header()
    print("⚙️  Modell trainieren")
    print("" + "─" * 72)
    print("Hier folgt dein Trainingsteil aus `app.py`.")
    print("Beispiel: Daten normalisieren, Gewichte initialisieren, Epochen schleifen.")
    print("Wichtig: Implementiere `STATE['model']`, `STATE['train_losses']` und `STATE['test_losses']`.")
    notify_placeholder("train_model")


def show_results() -> None:
    print_header()
    print("📊 Ergebnisse anzeigen")
    print("" + "─" * 72)

    if STATE["model"] is None:
        print("Kein Modell verfügbar. Bitte zuerst trainieren oder laden.")
        pause()
        return

    print("Aktuelle Modellzusammenfassung:")
    print(f"  - Trainingsläufe: {STATE['total_training_count']}")
    print(f"  - Letzte Validierung: {STATE['last_validation_result']}")
    print(f"  - Train Loss Verlauf Einträge: {len(STATE['train_losses'])}")
    print(f"  - Val Loss Verlauf Einträge: {len(STATE['test_losses'])}")
    print("\nWeitere Details kannst du hier ausgeben: Architektur, Gewichte, Metriken.")
    notify_placeholder("show_results")


def interactive_test() -> None:
    print_header()
    print("🧪 Interaktiver Test")
    print("" + "─" * 72)

    if STATE["model"] is None:
        print("Kein Modell geladen. Bitte zuerst ein Modell trainieren oder laden.")
        pause()
        return

    print("Hier kannst du später ein einzelnes Objekt generieren oder manuelle Koordinaten eingeben.")
    print("Beispiel: Normiere einen Eingabevektor und berechne die Modellvorhersage.")
    notify_placeholder("interactive_test")


def export_model() -> None:
    print_header()
    print("💾 Modell exportieren")
    print("" + "─" * 72)

    if STATE["model"] is None:
        print("Kein Modell vorhanden. Bitte zuerst trainieren oder laden.")
        pause()
        return

    filename = input("Dateiname für den Export (z.B. model_export.json): ").strip()
    if not filename:
        filename = "model_export.json"

    print("Speichere Modell als JSON...")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "model": STATE["model"],
                "train_losses": STATE["train_losses"],
                "test_losses": STATE["test_losses"],
                "last_validation_result": STATE["last_validation_result"],
            }, f, indent=2)
        print(f"✅ Modell erfolgreich gespeichert: {filename}")
    except Exception as exc:
        print(f"❌ Fehler beim Speichern: {exc}")
    pause()


def exit_program() -> None:
    print("\n👋 Danke für die Nutzung. CLI wird beendet.")
    sys.exit(0)


def main() -> None:
    while True:
        print_header()
        choice = ask_menu_choice()

        if choice == MENU_CHOICES[0]:
            load_data()
        elif choice == MENU_CHOICES[1]:
            train_model()
        elif choice == MENU_CHOICES[2]:
            show_results()
        elif choice == MENU_CHOICES[3]:
            interactive_test()
        elif choice == MENU_CHOICES[4]:
            export_model()
        elif choice == MENU_CHOICES[5]:
            exit_program()
        else:
            print("Unbekannte Auswahl. Bitte erneut versuchen.")
            time.sleep(0.5)


if __name__ == "__main__":
    main()
