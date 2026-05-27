# 👥 Developer Guide - Für neue Kollegen

Willkommen! Dieser Guide hilft dir, das Projekt schnell zu verstehen.

---

## 📂 Projektstruktur

```
Informatik-Projekt-August-Malte/
├── app.py                    # 🎯 HAUPTDATEI - Streamlit Web-App
├── pyramid_generator.py      # 📊 Erzeugt Trainingsdaten
├── checkpoint.py             # 💾 Speichert/lädt Modelle
├── dynamic_input.py          # 🔄 Normalisiert Daten
├── matrix.py                 # 🧮 Matrix-Operationen (optional)
├── checkpoints/              # 📁 Gespeicherte Modelle
├── Doc/                      # 📁 Dokumentation
└── REFACTORING.md            # 📝 Was sich geändert hat
```

---

## 🚀 Quick Start

### 1. Setup
```bash
# Python 3.8+
pip install streamlit numpy plotly

# Oder mit venv
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install streamlit numpy plotly
```

### 2. Starten
```bash
streamlit run app.py
```

Browser öffnet automatisch: `http://localhost:8501`

---

## 🧠 Was macht dieses Projekt?

Ein **neuronales Netz** lernt, Pyramiden von anderen 3D-Formen zu unterscheiden.

- **Input**: 19 Features (Koordinaten + abgeleitete Features)
- **Output**: 1 Wert (0 oder 1)
  - `1` = Pyramide erkannt ✅
  - `0` = Andere Form 🔲

---

## 📊 Die 5 Tabs erklärt

### Tab 1: 📊 Daten
**Was**: Trainingsdaten generieren oder hochladen
**Wie**:
- Button "✓ Generieren" → erstellt zufällige Daten
- Oder CSV hochladen
- Zeigt: Anzahl Pyramiden vs. Andere

**Code-Ort**: `app.py` Zeilen ~70-120

### Tab 2: 🎯 Training
**Was**: Modell trainieren
**Parameter**:
- **Input-Größe**: 19 (Standard, nicht ändern)
- **Hidden Layer**: 32 (Neuronen in verstecktem Layer)
- **Learning Rate**: 0.1 (wie schnell es lernt)
- **Epochen**: 500 (wie oft der Datensatz durchgegangen wird)
- **Test-Anteil**: 0.2 (20% der Daten zum Testen)

**Ausgabe**: Graph mit Training vs. Test Loss

**Code-Ort**: `app.py` Zeilen ~150-250

### Tab 3: 💾 Checkpoints
**Was**: Speichern und Laden von Modellen
**Funktionen**:
- 💾 **Speichern**: Modell speichern mit optionalem Namen
- 📂 **Laden**: Altes Modell laden und weiter trainieren
- 🗑️ **Löschen**: Checkpoint entfernen

**Wo gespeichert**: `/checkpoints` Ordner

**Code-Ort**: `app.py` Zeilen ~260-310

### Tab 4: 📈 Stats
**Was**: Netzwerk-Information + Export/Import
**Zeigt**:
- Netzwerk-Architektur (Input → Hidden → Output)
- Gewichte und Bias-Größen
- Training-Counter
- Loss-Wert

**Export/Import**:
- Export als JSON (um Model weiterzugeben)
- Import aus JSON (um Model zu laden)

**Code-Ort**: `app.py` Zeilen ~320-380

### Tab 5: ⚡ Auto-Mode
**Was**: Automatisches Training (generiert Daten + trainiert)
**Wie**:
1. Wähle Parameter
2. Klick "▶️ Auto-Training starten"
3. Das System generiert automatisch Daten
4. Trainiert mehrfach hintereinander
5. Zeigt Loss-Kurve

**Nützlich für**: Schnelle Tests, lange Sessions

**Code-Ort**: `app.py` Zeilen ~390-460

---

## 🔧 Code verstehen

### app.py - Die Main-App

**Struktur**:
```python
# 1. Header & Imports
# 2. Streamlit Config
# 3. Session State Init
# 4. TAB 1: Daten
# 5. TAB 2: Training
# 6. TAB 3: Checkpoints
# 7. TAB 4: Stats
# 8. TAB 5: Auto-Mode
# 9. Footer
```

**Key Functions**:
- Forward Pass: `z1 = X @ W1 + b1` → `a1 = max(0, z1)` (ReLU)
- Backprop: Gradient berechnen, Weights updaten
- Loss: `mean((output - target)²)` (MSE)

### pyramid_generator.py - Daten erzeugen

**Struktur**:
```python
class PyramidGenerator:
    _generate_pyramid()      # 1 Pyramide
    _generate_non_pyramid()  # 1 Andere Form
    generate_dataset()       # N Samples
```

**Pyramiden**: Base (4 Punkte) + Apex (1 Punkt)
**Nicht-Pyramiden**: Zufällige Punkte

### checkpoint.py - Speichern/Laden

**Speichert**:
- Gewichte (W1, b1, W2, b2)
- Config (input_size, hidden_size)
- Stats (loss, epochs)

**Dateien**:
- `.npz` - NumPy Binär (komprimiert)
- `.json` - Metadaten

### dynamic_input.py - Daten-Vorbereitung

**Normalisiert** Features auf [0, 1]:
```
normalized = (x - min) / (max - min)
```

---

## 🛠️ Häufige Anpassungen

### Modell größer machen?
**Datei**: `app.py`, Tab "Training"
**Ändere**: `hidden_size` von 32 → 64

### Mehr Daten generieren?
**Datei**: `app.py`, Tab "Daten"
**Ändere**: `n_pyramids` und `n_non_pyramids`

### Bessere Pyramiden-Generierung?
**Datei**: `pyramid_generator.py`
**Methode**: `_generate_pyramid()` anpassen
```python
def _generate_pyramid(self):
    # Hier kann man die Pyramiden-Form ändern
    base = np.random.uniform(...)  # ← Hier
    apex_z = np.random.uniform(...)  # ← Oder hier
```

### Verschiedene Aktivierungsfunktionen?
**Datei**: `app.py`, Training-Loop
**Jetzt**: `a1 = np.maximum(0, z1)` (ReLU)
**Könnte sein**: `a1 = np.tanh(z1)` (Tanh) oder `a1 = 1/(1+np.exp(-z1))` (Sigmoid)

---

## 🧪 Debuggen

### App startet nicht?
```bash
# Syntax-Check
python -m py_compile app.py

# Imports testen
python -c "from checkpoint import CheckpointManager; print('OK')"
```

### Training ist langsam?
- `hidden_size` reduzieren
- `epochs` reduzieren
- `n_pyramids` reduzieren (weniger Daten)

### Modell speichert nicht?
- `/checkpoints` Ordner existiert? (wird automatisch erstellt)
- Festplatte voll?

---

## 📚 Wichtige Konzepte

### Normalisierung
Eingaben auf [0, 1] Bereich skalieren → Netzwerk trainiert besser

### Backpropagation
Prozess, um zu berechnen, wie Gewichte angepasst werden sollen

### Checkpoint
Snapshot des trainierten Modells (Gewichte + Config)

### Epoch
Einmal durch alle Trainingsdaten gehen

### Loss
Fehler des Modells (niedrig = gut)

---

## 🎓 Zum Weiterlesen

- **Matrix.py**: Für Matrix-Operationen (optional, derzeit nicht verwendet)
- **Doc/QUICK_START.md**: Schneller Überblick
- **REFACTORING.md**: Was sich geändert hat (warum, wie)

---

## 💡 Best Practices

✅ **Do**:
- Immer Daten generieren/laden bevor du trainierst
- Checkpoints speichern, bevor du neue Parameter ausprobierst
- Stats-Tab checken, bevor und nach dem Training

❌ **Don't**:
- Nicht alle Parameter auf Zufallswerte setzen
- Nicht vergessen, dass Training Zeit braucht
- Nicht die Datei bearbeiten, während App läuft

---

## 🤝 Support

**Problem?** → Schau `REFACTORING.md` oder Code-Comments
**Feature hinzufügen?** → Schau "Code verstehen" oben
**Fragen?** → Code ist dokumentiert mit Docstrings

---

**Viel Spaß beim Entwickeln!** 🚀
