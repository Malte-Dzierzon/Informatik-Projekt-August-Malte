#!/usr/bin/env python3
"""
Setup & Run - Automatische Dependency Installation + App Start
===============================================================
Dieses Skript installiert automatisch alle erforderlichen Pakete
und startet dann die Streamlit-Anwendung.

Verwendung:
  python setup_and_run.py
"""

import subprocess
import sys
import importlib.util


def check_and_install_dependencies():
    """Prueft und installiert fehlende Packages"""
    
    # Scipy wurde hier ergaenzt
    required_packages = {
        "streamlit": "streamlit",
        "numpy": "numpy",
        "plotly": "plotly",
        "scipy": "scipy"
    }
    
    missing_packages = []
    
    print("-" * 70)
    print("STATUS: Pruefe erforderliche Packages...")
    print("-" * 70)
    
    for package_name, import_name in required_packages.items():
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            print(f"[ FEHLT ] {package_name}")
            missing_packages.append(package_name)
        else:
            print(f"[ OK    ] {package_name}")
    
    if missing_packages:
        print("\n" + "-" * 70)
        print("INSTALLATION: Starte Download der fehlenden Packages...")
        print("-" * 70)
        
        try:
            # Upgrade pip mit System-Flag
            print("\n>>> Aktualisiere pip...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--break-system-packages"
            ])
            
            # Installiere fehlende Packages mit System-Flag für die normale Umgebung
            for package in missing_packages:
                print(f"\n>>> Installiere {package}...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--break-system-packages"
                ])
            
            print("\nERFOLG: Alle Packages wurden installiert.")
            
        except subprocess.CalledProcessError as e:
            print(f"\nFEHLER: Installation abgebrochen mit Code: {e}")
            sys.exit(1)
    else:
        print("\nSTATUS: Alle Packages sind bereits vorhanden.")
    
    print("-" * 70)


def start_streamlit_app():
    """Startet die Streamlit-App"""
    
    print("START: Streamlit-Anwendung wird geladen...")
    print("-" * 70)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nFEHLER: Fehler beim Starten der Anwendung: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nHINWEIS: Anwendung durch Benutzer beendet.")
        sys.exit(0)


if __name__ == "__main__":
    check_and_install_dependencies()
    start_streamlit_app()