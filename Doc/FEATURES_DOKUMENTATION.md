# 🧠 Neural Network Training - Erweiterte Features

## Übersicht der neuen Funktionalitäten

Dieses Projekt wurde um vier große Features erweitert, die das neuronale Netz für Pyramiden-Klassifikation deutlich leistungsfähiger machen:

---

## 1. 💾 Checkpoint-System (Fortsetzbares Training)

### Feature-Beschreibung
Das Netzwerk kann jederzeit gespeichert und wieder geladen werden. Dies ermöglicht:
- **Unterbrechen und Fortsetzen** von Trainings-Sessions
- **Gewichte und Bias** persistent speichern
- **Trainings-Counter** über Sessions hinweg erhalten
- **Normalisierungs-Parameter** speichern für konsistente Vorhersagen

### Verwendung
1. **Training durchführen** → "Training starten" im "Training" Tab
2. **Modell speichern** → Gehe zu Tab "💾 Checkpoints" → "💾 Checkpoint speichern"
3. **Später fortsetzen** → Checkpoint laden → "Training starten" erneut durchführen
4. Der **Training-Counter wird automatisch erhöht** und angezeigt

### Technische Details
- **Dateiformat**: `.npz` (komprimierte NumPy Arrays) + `.json` Metadaten
- **Gespeicherte Parameter**:
  - W1, b1 (Layer 1 Gewichte/Bias)
  - W2, b2 (Layer 2 Gewichte/Bias)
  - Total Training Count
  - Training History (Train/Test Loss)
  - Normalisierungs-Parameter
- **Speicherort**: `./checkpoints/`

### Code-Integration
```python
# Speichern
manager = CheckpointManager()
manager.save_checkpoint(model_state, training_stats, config)

# Laden
model, stats, config = manager.load_checkpoint("checkpoint_name.npz")

# Aufzählen
checkpoints = manager.list_checkpoints()
```

---

## 2. 🔄 Gesamtzahl Trainings-Durchgänge (Training-Counter)

### Feature-Beschreibung
Zähler für die Gesamtzahl von Trainings-Iterationen über alle Checkpoints hinweg:
- Wird mit jedem Training-Durchlauf erhöht
- Wird in Checkpoints gespeichert
- Wird beim Laden eines Checkpoints wiederhergestellt
- Visuell angezeigt im Training-Tab

### Verwendung
1. Trainiere das Modell mehrfach → Counter erhöht sich
2. Speichere einen Checkpoint → Counter wird mit gespeichert
3. Lade Checkpoint → Counter wird wiederhergestellt
4. Trainiere weiter → Counter wird auf dem neuen Stand weitergezählt

### Anzeige
```
🔄 Gesamtzahl Trainings-Durchgänge: 5
```

---

## 3. 📈 Automatische Pyramiden-Generierung (Prozeduraler Generator)

### Feature-Beschreibung
Generiert mathematisch unbegrenzt viele Pyramiden-Variationen:
- **Basis**: Quadrat im Bereich [0, 1]² (4 Eckpunkte)
- **Apex**: Frei wählbarer Punkt über dem Quadrat (5. Punkt)
- **Variationen**: Unterschiedliche Größen, Positionen, Höhen

### Mathematisches Modell

#### Quadrat-Basis (4 Punkte):
```
Punkt 1: (offset_x, offset_y, z)
Punkt 2: (offset_x + scale, offset_y, z)
Punkt 3: (offset_x + scale, offset_y + scale, z)
Punkt 4: (offset_x, offset_y + scale, z)
```

#### Apex-Punkt:
```
apex_x = center_x + horizontal_offset * cos(angle)
apex_y = center_y + horizontal_offset * sin(angle)
apex_z = height  (über der Basis)
```

#### Feature-Vektor:
```
[base_4_points × 3_coords + apex_3_coords + derived_features]
= [12 + 3 + 4] = 19 Features pro Sample
```

### Verwendung in der App
1. Gehe zu Tab "📊 Trainingsdaten"
2. Wähle "Pyramiden-Generator (PROZEDURAL)"
3. Stelle Anzahl Pyramiden und Non-Pyramids ein
4. Optional: "Variable Eckpunkt-Anzahl" aktivieren
5. Klick "🔄 Daten generieren"

### Code-Integration
```python
from pyramid_generator import PyramidGenerator

gen = PyramidGenerator(seed=42)

# Einzelne Pyramide
feature_vector, label = gen.generate_pyramid_3d()

# Komplettes Dataset
data, metadata = gen.generate_dataset(n_pyramids=100, n_non_pyramids=100)

# Variable-Size Dataset
var_data, var_meta = gen.generate_dataset_variable_size(n_samples=100, 
                                                         min_vertices=4, 
                                                         max_vertices=8)
```

---

## 4. 🎯 Dynamisches Input-System mit Intelligenter Filterung

### Feature-Beschreibung
Das Netzwerk kann nun mit Figuren unterschiedlicher Eckpunkt-Anzahl umgehen:
- **Automatische Padding-Erkennung**: Findet überflüssige "Null-Features"
- **Intelligente Filterung**: Entfernt Padding-Spalten vor dem Training
- **Variable Input-Größe**: Passt sich automatisch an
- **UI-Anzeige**: Zeigt Padding-Features mit "-" an

### Funktionsweise

#### 1. Padding-Erkennung
```
Wenn > 95% der Werte in einer Spalte Null sind:
→ Feature ist Padding und wird gefiltert
```

#### 2. Daten-Verarbeitung Pipeline
```
Original Data
    ↓
Detect Padding Features (95% Null-Threshold)
    ↓
Filter Nicht-Padding Features
    ↓
Normalisierung auf [0, 1]
    ↓
Netzwerk-Input (nur echte Features)
```

#### 3. Beispiel
```
Original 19 Features:
[real_1, real_2, real_3, 0, 0, 0, 0, real_4, 0, 0, ..., label]
                        ↓ ↓ ↓ ↓      ↓ ↓
                        Padding (gefiltert)

Nach Filterung: 
[real_1, real_2, real_3, real_4, ..., label]  (z.B. 7 Features)

Input-Size wird automatisch auf 6 angepasst
```

### UI-Anzeige
```
Trainingsdaten-Vorschau:

F1    F2    F3    F4    F5    F6    F7    Label
0.123 0.456 0.789 -     -     -     -     1
0.234 0.567 0.890 -     -     -     -     1
```

Die "-" markieren automatisch gefilterte Padding-Features.

### Verwendung
- **Automatisch aktiviert** bei Training
- Keine spezielle Konfiguration nötig
- Funktioniert transparent im Hintergrund

### Code-Integration
```python
from dynamic_input import DynamicInputHandler

handler = DynamicInputHandler(max_vertices=12)

# Filterung + Normalisierung
processed_data, info = handler.filter_and_prepare_network_input(data)

print(f"Aktive Features: {info['active_feature_count']}")
print(f"Padding-Features: {info['padding_feature_count']}")

# DataFrame für UI
df_display = handler.create_display_dataframe(data)
```

---

## Workflow-Beispiel: Komplettes Training mit allen Features

### Szenario: 3 Training-Sessions

#### Session 1: Initiales Training
```
1. Tab "📊 Trainingsdaten"
   → Pyramiden-Generator
   → 50 Pyramiden + 50 Non-Pyramids
   → "🔄 Daten generieren"

2. Tab "⚙️ Konfiguration"
   → Konfiguriere Parameter
   
3. Tab "🎓 Training"
   → "▶️ Training starten"
   → Training-Counter: 1
   
4. Tab "💾 Checkpoints"
   → "💾 Checkpoint speichern" (Name: "v1_initial")
   → Training-Count: 1 gespeichert
```

#### Session 2: Fortsetzen mit neuen Daten
```
1. Tab "📊 Trainingsdaten"
   → Pyramiden-Generator
   → 75 Pyramiden + 75 Non-Pyramids (mehr Daten!)
   → "🔄 Daten generieren"

2. Tab "💾 Checkpoints"
   → "📂 Laden" (v1_initial)
   → Model + Counter wiederhergestellt
   
3. Tab "🎓 Training"
   → "▶️ Training starten" (mit neuen Daten)
   → Training-Counter: 2 (erhöht!)
   
4. Tab "💾 Checkpoints"
   → "💾 Checkpoint speichern" (Name: "v2_expanded")
   → Training-Count: 2 gespeichert
```

#### Session 3: Variable-Size Figuren
```
1. Tab "📊 Trainingsdaten"
   → Pyramiden-Generator
   → ✓ Variable Eckpunkt-Anzahl aktivieren
   → 100 Samples mit 4-8 Vertices
   
2. Tab "💾 Checkpoints"
   → "📂 Laden" (v2_expanded)
   
3. Tab "🎓 Training"
   → Dynamisches Input-System erkennt automatisch Padding
   → "▶️ Training starten"
   → Training-Counter: 3
```

---

## Dateien und Module

### Neue Module
1. **checkpoint.py** - Checkpoint-Management
   - `CheckpointManager` Klasse
   - Speichern/Laden von Netzwerk-Zuständen

2. **pyramid_generator.py** - Prozeduraler Daten-Generator
   - `PyramidGenerator` Klasse
   - Pyramid/Non-Pyramid Generierung
   - Variable-Size Dataset Support

3. **dynamic_input.py** - Dynamisches Input-System
   - `DynamicInputHandler` Klasse
   - Padding-Erkennung
   - Feature-Filterung

### Veränderte Dateien
- **app.py** - Komplette Überarbeitung mit 5 Tabs

### Verzeichnisse
- **checkpoints/** - Speicherort für Checkpoints (wird automatisch erstellt)

---

## Performance-Tipps

### Für schnelleres Training:
- ✓ Reduziere Epochen-Anzahl
- ✓ Vergrößere Batch-Size
- ✓ Nutze weniger Features (Filterung unterstützt das)

### Für bessere Genauigkeit:
- ✓ Erhöhe Pyramiden/Non-Pyramids Ratio
- ✓ Mehrfaches Training (Checkpoint + Fortsetzen)
- ✓ Experimentiere mit Learning Rate

### Für stabile Training-Progression:
- ✓ Speichere regelmäßig Checkpoints
- ✓ Beobachte Train vs. Test Loss
- ✓ Nutze Normalisierung (Standard: aktiviert)

---

## Technische Anforderungen

```
numpy >= 1.19
streamlit >= 1.0
plotly >= 5.0
pandas >= 1.0
```

Installation:
```bash
pip install streamlit plotly pandas numpy
```

Starten:
```bash
streamlit run app.py
```

---

## Bekannte Limitierungen

- **Max. Vertices**: Begrenzt auf 12 (konfigurierbar)
- **Feature-Größe**: Max. 100 Features im aktuellen Setup
- **Checkpoint-Kompatibilität**: Nur innerhalb gleicher Netzwerk-Architektur

---

## Zukünftige Erweiterungen

Mögliche Verbesserungen:
- [ ] Mehrere Hidden Layer Support
- [ ] Dropout-Regularisierung
- [ ] Batch Normalization
- [ ] Learning Rate Scheduling
- [ ] GPU-Support (CUDA)
- [ ] Model Export (ONNX)
- [ ] Hyperparameter Optimization

---

**Erstellt**: Mai 2026  
**Projekt**: Neuronales Netz - Pyramiden Klassifikation  
**Autoren**: Malte & August
