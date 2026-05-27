# Neuronales Netz zur Erkennung von Pyramiden (v2.0)

Ein kompaktes neuronales Netzwerk zur binären Klassifikation von 2D- und 3D-Objekten anhand ihrer Eckpunkte.

### Direkt-Links zum Projekt
* **[Anfänger-Leitfaden (Quick Start)](QUICK_START.md)** *(Start in 5 Minuten)*
* **[Detaillierte Feature-Dokumentation](FEATURES_DOKUMENTATION.md)**
* **Kern-Module:** [Haupt-App (app.py)](app.py) | [Checkpoint-Manager](checkpoint.py) | [Pyramiden-Generator](pyramid_generator.py) | [Dynamic Input](dynamic_input.py)

---

## Neue Features (Version 2.0)

### 1. Checkpoint-System - Fortsetzbares Training
* Speichere und lade Modell-Zustände (Gewichte, Bias und Optimierer-Status)
* Training-Counter zählt Durchgänge über Sessions hinweg konstant mit
* Ermöglicht den Export und die Verwaltung mehrerer Modell-Varianten

### 2. Gesamtzahl Trainings-Durchgänge Tracking
* Automatischer globaler Counter für alle absolvierten Trainingssessions
* Nahtlose Integration mit dem Checkpoint-System
* Klares visuelles Tracking direkt in der Web-Oberfläche

### 3. Pyramiden-Generator - Prozedurale Datengenerierung
* Mathematisch unbegrenzte Pyramiden-Variationen auf Knopfdruck
* Mathematische Basis: Quadrat im Raum [0,1]² plus ein freier Apex (Spitzenpunkt)
* Keine künstlichen Limits bei der Datensynthese für das Netz

### 4. Dynamisches Input-System
* Variable Eckpunkt-Anzahl pro geometrischer Figur (4 bis 12 Punkte flexibel möglich)
* Automatische Padding-Erkennung (>95% Nullen bei kleineren Objekten)
* Intelligente Feature-Filterung vor der Verarbeitung im Netz
* Die Benutzeroberfläche zeigt aufgefüllte Padding-Werte sauber mit einem "-" an

---

## Projektzielsetzung & Eingabedaten

Das Modell entscheidet über eine binäre Klassifikation zwischen zwei Ausgaben:
* **1 = Pyramide** (5 Punkte: 4 Basis-Punkte + 1 Spitze)
* **0 = Keine Pyramide** (andere geometrische Formen wie Würfel oder flache Vierecke)

### Feature-Vektor (19 Features)
Der Eingabe-Vektor setzt sich aus den reinen Punktkoordinaten sowie mathematisch abgeleiteten Werten zusammen: