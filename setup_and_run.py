"""
AUTOMATISCHES SETUP & START-SKRIPT
==================================
Überprüft die Abhängigkeiten und startet das Pyramiden-Dashboard
ordnungsgemäß im nativen Streamlit-Laufzeitmodus.
Fokus auf Clean-Code, professionelle Log-Ausgaben und Pfadsicherheit.
"""

import subprocess
import sys
import os
import importlib.util

# Pip-Paketnamen, die installiert werden müssen
REQUIRED_PACKAGES = [
    "streamlit",
    "numpy",
    "scipy",
    "pandas",
    "plotly",
    "pyarrow"
]

# Mapping, falls der Importname im Code vom Pip-Paketnamen abweicht
IMPORT_MAPPING = {
    "pyarrow": "pyarrow"  # Hier können Abweichungen explizit definiert werden
}


def check_and_install_dependencies():
    """Überprüft die Verfügbarkeit der Bibliotheken und installiert fehlende Pakete."""
    print("[INFO] Überprüfe Projekt-Abhängigkeiten...")
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        import_name = IMPORT_MAPPING.get(package, package)
        
        # Prüfen, ob das Modul im aktuellen Environment auffindbar ist
        if importlib.util.find_spec(import_name) is None:
            missing_packages.append(package)

    if missing_packages:
        print(f"[INFO] Folgende Pakete fehlen und werden installiert: {missing_packages}")
        try:
            # Nutzt den exakt laufenden Python-Interpreter, um Pfad-Konflikte zu vermeiden
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", *missing_packages],
                stdout=subprocess.DEVNULL  # Hält die Konsole sauber
            )
            print("[ERFOLG] Alle Pakete erfolgreich installiert!")
        except subprocess.CalledProcessError as e:
            print(f"[FEHLER] Installation der Pakete fehlgeschlagen: {e}")
            sys.exit(1)
    else:
        print("[ERFOLG] Alle benötigten Bibliotheken sind bereits installiert.")


def start_streamlit_app():
    """Ermittelt die app.py im Skriptverzeichnis und startet das Dashboard."""
    # Bestimme den absoluten Pfad des Skript-Ordners für maximale Aufrufsicherheit
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_app = os.path.join(script_dir, "app.py")
    
    if not os.path.exists(target_app):
        print(f"[FEHLER] Die Hauptdatei '{target_app}' wurde nicht gefunden!")
        print("[INFO] Bitte stelle sicher, dass app.py im selben Ordner wie dieses Skript liegt.")
        sys.exit(1)
        
    python_version = sys.version.split()[0]
    print(f"[INFO] Starte Streamlit-Dashboard unter Python {python_version}...")
    
    # Startet Streamlit prozesssicher als Python-Modul
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", target_app], check=True)
    except KeyboardInterrupt:
        print("\n[STOPP] Dashboard wurde vom Nutzer beendet. Anwendung geschlossen.")
    except subprocess.CalledProcessError as e:
        print(f"\n[FEHLER] Streamlit wurde unerwartet beendet. Fehlercode: {e.returncode}")


if __name__ == "__main__":
    print("=== KI-Pyramiden-Projekt Starter-Zentrale 2026 ===")
    
    # 1. System-Umgebung validieren und absichern
    check_and_install_dependencies()
    print("-" * 50)
    
    # 2. Dashoard-Prozess initialisieren
    start_streamlit_app()