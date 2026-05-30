'''
Debug-Utils damit man auch im Terminal sieht was grade auf der Website passiert. 
Außerdem eine cleanen Ladeanimation für die Trainingsphase.

'''


import sys
import time
import traceback

SPINNER_FRAMES = ["|", "/", "-", "\\"]  # Drehbare Zeichen für den Spinner


def animated_message(message: str, repeat: int = 2, delay: float = 0.04) -> None:
    for _ in range(repeat):
        for frame in SPINNER_FRAMES:
            sys.stderr.write(f"\r[{frame}] {message}")  # Schreibe animierten Status ins Terminal
            sys.stderr.flush()
            time.sleep(delay)
    sys.stderr.write("\r" + " " * (len(message) + 6) + "\r")  # Entferne die animierte Zeile danach
    sys.stderr.flush()


def debug_info(message: str) -> None:
    sys.stderr.write(f"[DEBUG] {message}\n")  # Ausgabe einer normalen Debug-Nachricht
    sys.stderr.flush()


def debug_generate(message: str) -> None:
    animated_message(message, repeat=1, delay=0.05)  # Zeige kurze Generierungsanimation
    sys.stderr.write(f"[GENERATE] {message}\n")  # Schreibe Generierungs-Log
    sys.stderr.flush()


def debug_warning(message: str) -> None:
    sys.stderr.write(f"[WARN] {message}\n")  # Schreibe eine Warnmeldung ins Terminal
    sys.stderr.flush()


def debug_error(message: str, exc: Exception | None = None) -> None:
    sys.stderr.write(f"[ERROR] {message}\n")  # Schreibe eine Fehlernachricht
    if exc is not None:
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)  # Drucke die Ausnahme
    animated_message("Fehler protokolliert", repeat=1, delay=0.06)  # Zeige Abschlussanimation


def animated_replace_notice(old: str, new: str) -> None:
    # FILTER: Ignoriere die veraltete Streamlit-Warnung zu use_container_width komplett
    if old == "use_container_width":
        return

    animated_message(f"Ersetze {old} durch {new}", repeat=1, delay=0.03)  # Zeige Austauschhinweis
    sys.stderr.write(f"[INFO] Bitte verwende {new} statt {old}.\n")  # Schreibe Info-Log
    sys.stderr.flush()


def debug_training(results: dict) -> None:
    """Animiert den Abschluss des Trainings und loggt die Ergebnisse strukturiert."""
    # Kurze, stylische Ladeanimation für die Datenverarbeitung
    animated_message("Verarbeite finale Trainingsmetriken...", repeat=2, delay=0.04)  # Zeige Trainingsanimation
    
    sys.stderr.write("[TRAIN] ═══════════ TRAININGSERGEBNISSE ═══════════\n")  # Kopfzeile für Trainingslog
    for key, value in results.items():
        if isinstance(value, float):
            sys.stderr.write(f"[TRAIN]   -> {key}: {value:.4f}\n")  # Formatiere Float-Werte
        else:
            sys.stderr.write(f"[TRAIN]   -> {key}: {value}\n")  # Schreibe nicht-Float-Werte
    sys.stderr.write("[TRAIN] ═══════════════════════════════════════════\n")  # Fußzeile für Trainingslog
    sys.stderr.flush()