# Pyramiden-Klassifikation v2.0

Ein minimalistisches, ressourceneffizientes Neuronales Netzwerk zur binären Klassifikation von 3D-Objekten anhand ihrer Eckpunkte.

## Schnellstart & Dokumentation
* **[Quick Start Guide](QUICK_START.md)** – Einrichtung und Start in 5 Minuten.
* **[Feature-Dokumentation](FEATURES_DOKUMENTATION.md)** – Mathematische Hintergründe und Details.
* **Module:** [`app.py`](app.py) (Dashboard) | [`run.py`](run.py) (Starter) | [`pyramid_generator.py`](pyramid_generator.py) | [`dynamic_input.py`](dynamic_input.py)

---

## Abhängigkeiten (Dependencies)
Das Projekt ist für Low-End-Hardware optimiert und benötigt lediglich folgende Kern-Bibliotheken:
* `streamlit` (Web-Oberfläche)
* `numpy` (Matrizen-Berechnungen mit `float32`)
* `scipy` (Stabile Aktivierungsfunktionen)
* `pandas` & `pyarrow` (Performantes Daten-Handling)
* `plotly` (Interaktive 3D-Visualisierung)

---

## Kern-Funktionen

### 1. Checkpoint-System & Tracking
* **Fortsetzbares Training:** Sichert Gewichte, Biases und Metriken in einer strukturierten JSON-Datei.
* **Globaler Counter:** Erfasst die Gesamtzahl aller absolvierten Trainings-Epochen über Sessions hinweg.
* **Protokoll-Export:** Automatischer Download detaillierter Markdown-Reports direkt aus der UI.

### 2. Prozeduraler Pyramiden-Generator
* **Datensynthese:** Erzeugt unbegrenzte geometrische Variationen von Pyramiden (Klasse 1) und mathematischem Rauschen (Klasse 0).
* **Stabilität:** Nutzt einen isolierten Zufallsgenerator (`np.random.default_rng`), um reproduzierbare Datensätze zu garantieren.

### 3. Dynamisches Input-System
* **Flexibilität:** Verarbeitet variable Punkt-Anzahlen (4 bis 12 Eckpunkte) pro Objekt.
* **RAM-Optimierung:** In-Place-Operationen und `float32`-Erzwingung verhindern Speicher-Spitzen.
* **UI-Klarheit:** Automatische Padding-Erkennung; ungenutzte Dimensionen werden in der UI übersichtlich als `-` deklariert.

---

## Datenstruktur (19-D Feature-Vektor)

Das Modell klassifiziert binär zwischen **Klasse 1** (Pyramide: 4 Basispunkte + 1 Spitze) und **Klasse 0** (Keine Pyramide). Der Eingabevektor umfasst exakt 19 Dimensionen:

| Dimensionen | Beschreibung | Typ / Ziel |
| :--- | :--- | :--- |
| **1 – 12** | 4 Basispunkte mit je 3 Koordinaten ($X, Y, Z$) | Raumkoordinaten |
| **13 – 15** | 1 Apex-Punkt (Spitze) mit 3 Koordinaten ($X, Y, Z$) | Raumkoordinaten |
| **16** | Effektive Objekthöhe ($Z$-Achse der Spitze) | Geometrisches Feature |
| **17** | Balance-Wert (Abstand der Spitze zum Basis-Zentrum) | Geometrisches Feature |
| **18** | Quadratische Grundfläche der Basis | Geometrisches Feature |
| **19** | Absolute X-Position des Basis-Zentrums | Geometrisches Feature |
| **20 (Label)** | Zielklasse: `1.0` (Pyramide) oder `0.0` (Andere) | Binäres Target |