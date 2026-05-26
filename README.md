# 🧠 Neuronales Netz zur Erkennung von Pyramiden

Ein intelligentes neuronales Netzwerk zur binären Klassifikation von 2D- und 3D-Objekten. **Mit erweiterten Features für Checkpoints, Pyramiden-Generator und dynamischem Input.**

## ✨ Neue Features (Version 2.0)

### 1. 💾 Checkpoint-System - Fortsetzbares Training
- Speichere und lade Modell-Zustände
- Training-Counter zählt Durchgänge über Sessions hinweg
- Exportiere Gewichte, Bias und Optimierer-Status
- Verwalte mehrere Modell-Varianten

### 2. 📈 Gesamtzahl Trainings-Durchgänge Tracking
- Automatischer Counter für alle Trainingssessions
- Integration mit Checkpoint-System
- Visuelles Tracking in der UI

### 3. 🔄 Pyramiden-Generator - Prozedurales Datengenerierung
- Mathematisch unbegrenzte Pyramiden-Variationen
- Basis: Quadrat [0,1]² + Apex
- Keine festen Limits bei Datensynthese

### 4. 🎯 Dynamisches Input-System
- Variable Eckpunkt-Anzahl pro Figur (4-12 möglich)
- Automatische Padding-Erkennung (>95% Nullen)
- Intelligente Feature-Filterung
- UI zeigt Padding mit "-" an

## 🎯 Projektzielsetzung

Das Modell entscheidet zwischen zwei Ausgaben:
- `1` = **Pyramide** (5 Punkte: 4 Basis + 1 Spitze)
- `0` = **Keine Pyramide** (andere geometrische Formen)

## 📊 Eingabedaten

### Pyramiden-Struktur
- **Basis**: 4 Eckpunkte eines Quadrats im Bereich [0, 1]²
- **Apex**: 1 Spitze-Punkt über dem Quadrat
- **Gesamt**: 5 Punkte × 3 Koordinaten (x,y,z) = 15 Features + 4 abgeleitete = **19 Features**

### Feature-Vektor
```
[x₁, y₁, z₁, x₂, y₂, z₂, x₃, y₃, z₃, x₄, y₄, z₄,  // 4 Basis-Punkte
 xₐ, yₐ, zₐ,                                         // Apex
 height, balance, side_length, volume]               // Abgeleitete Features
```

## 🧮 Modellaufbau

```
Input Layer (19 Features) 
    ↓
Hidden Layer (32 Neuronen, ReLU)
    ↓
Output Layer (1 Neuron, Sigmoid)
    ↓
Binary Classification (0 oder 1)
```

## 🚀 Schnellstart

### Installation
```bash
pip install streamlit plotly pandas numpy
```

### Starten
```bash
streamlit run app.py
```

### Erste Verwendung (3 Minuten)
1. Öffne Tab "📊 Trainingsdaten" → "Pyramiden-Generator"
2. Klick "🔄 Daten generieren" (100 Pyramiden + 100 Non-Pyramids)
3. Gehe zu Tab "🎓 Training" → "▶️ Training starten"
4. Beobachte das Live-Training (~30 Sekunden)
5. Speichere einen Checkpoint im Tab "💾 Checkpoints"

**→ Siehe [QUICK_START.md](QUICK_START.md) für detaillierte Anleitung**

## 📚 Dokumentation

- **[QUICK_START.md](QUICK_START.md)** - Anfänger-Guide (5 Min)
- **[FEATURES_DOKUMENTATION.md](FEATURES_DOKUMENTATION.md)** - Vollständige Feature-Dokumentation
- **[Code-Dokumentation]** - Ausführliche Docstrings in den Python-Dateien

## 🔧 Trainings-Algorithmus

**Architektur**: 2-Layer Neural Network (Input → Hidden → Output)

**Forward Pass**:
$$z^1 = X \cdot W^1 + b^1$$
$$a^1 = \text{ReLU}(z^1) = \max(0, z^1)$$
$$z^2 = a^1 \cdot W^2 + b^2$$
$$a^2 = \sigma(z^2) = \frac{1}{1 + e^{-z^2}}$$

**Loss Function**:
$$L = \frac{1}{n} \sum_{i=1}^{n} (\hat{y}_i - y_i)^2$$

**Backpropagation**: Gradient Descent mit konfigurierbarer Learning Rate

## 📁 Projektstruktur

```
Informatik-Projekt-August-Malte/
├── app.py                           # 🎨 Hauptapplikation (Streamlit)
├── checkpoint.py                    # 💾 Checkpoint-Management
├── pyramid_generator.py              # 🔄 Pyramiden-Generator
├── dynamic_input.py                  # 🎯 Dynamisches Input-System
├── matrix.py                         # 🧮 Matrix-Operationen
├── training.py                       # 📚 Altes Training-Skript (legacy)
├── README.md                         # 📖 Dieser Guide
├── QUICK_START.md                    # 🚀 Anfänger-Guide
├── FEATURES_DOKUMENTATION.md         # 📚 Detaillierte Dokumentation
├── run.bat                           # 🪟 Windows Starter
├── checkpoints/                      # 💾 Gespeicherte Modelle
│   ├── checkpoint_*.npz              # Gewichte & Bias
│   ├── checkpoint_*_metadata.json    # Konfiguration & Stats
│   └── checkpoint_*_history.csv      # Training-History
└── Daten_zum_trainieren/
    └── Trainings_Daten.txt           # Beispiel-Pyramiden-Daten
```

## ⚙️ Konfigurierbare Parameter

| Parameter | Standard | Bereich | Erklärung |
|-----------|----------|---------|-----------|
| Input-Größe | 19 | 2-100 | Anzahl Feature (Auto bei Dynamic Input) |
| Hidden Layer | 32 | 2-1000 | Neuronen im Hidden Layer |
| Learning Rate | 0.1 | 0.001-1.0 | Gradient Descent Schrittgröße |
| Epochen | 500 | 1-10000 | Training-Iterationen |
| Batch-Größe | 4 | 1-100 | Samples pro Update |
| Test-Split | 0.2 | 0.1-0.5 | Test-Daten Anteil |
| Normalisierung | ✓ | - | Features auf [0,1] normalisieren |

## 💡 Empfehlungen für gutes Training

### Parameter
- **Learning Rate**: 0.05 - 0.2 (nicht zu groß, nicht zu klein)
- **Epochen**: 500 - 2000 (mehr = besser, dauert aber länger)
- **Hidden Layer**: 16 - 64 Neuronen (zu groß = Overfitting)
- **Test-Split**: 0.2 - 0.3 (Validierung wichtig!)

### Daten
- **Verhältnis**: ~50:50 Pyramiden zu Non-Pyramids
- **Größe**: Minimum 100 Samples, ideal 500+
- **Vielfalt**: Nutze Generator für diverse Variationen

### Checkpoints
- Speichere nach jedem erfolgreichen Training
- Vergleiche mehrere Versionen
- Nutze fortsetzbares Training für Iterationen

## 🎓 Trainings-Workflow

### Minimal (5 Min)
```
Daten generieren → Training starten → Vorhersage testen
```

### Standard (15 Min)
```
Daten generieren → Parameter tunen → Training → Checkpoint speichern → Vorhersagen
```

### Iterativ (Mehrere Sessions)
```
Session 1: Training → Checkpoint "v1"
    ↓
Session 2: Lade "v1" → Neue Daten → Training → Checkpoint "v2"
    ↓
Session 3: Lade "v2" → Noch mehr Daten → Training → Checkpoint "v3"
    ↓
Vergleiche alle Checkpoints
```

## 📊 Expected Results

Bei korrektem Training sollte man erreichen:
- **Training Loss**: Von ~0.5 auf ~0.01 - 0.05
- **Test Loss**: Ähnlich wie Training Loss (kein Overfitting)
- **Genauigkeit**: >90% bei guten Daten und Training

## 🔍 Debugging

### Problem: Training ist langsam
- Reduziere Epochen
- Verringere Batch-Size
- Nutze weniger Samples

### Problem: Loss sinkt nicht
- Erhöhe Learning Rate (vorsichtig!)
- Vergrößere Hidden Layer
- Generiere mehr / bessere Daten

### Problem: Overfitting (Test Loss > Training Loss)
- Erhöhe Test-Split
- Verringere Hidden Layer Größe
- Verringere Learning Rate
- Aktiviere Normalisierung

## 📦 Abhängigkeiten

```
numpy >= 1.19        # Numerische Operationen
streamlit >= 1.0     # Web UI
plotly >= 5.0        # Interaktive Charts
pandas >= 1.0        # Datenmanipulation
```

## 🔮 Geplante Verbesserungen

- [ ] Mehrere Hidden Layer
- [ ] Dropout Regularisierung
- [ ] Batch Normalization
- [ ] Learning Rate Scheduling
- [ ] GPU Support
- [ ] Modell-Export (ONNX)
- [ ] Hyperparameter Optimization

## 📄 Lizenz

Schulprojekt - Freie Verwendung

## 👥 Autoren

- **Malte** - Hauptentwicklung
- **August** - Mitentwicklung

**Erweiterte Version 2.0**: Mai 2026

---

## 🎯 Quick-Links

- 🚀 [Quick Start Guide](QUICK_START.md)
- 📚 [Features Dokumentation](FEATURES_DOKUMENTATION.md)
- 💻 [Quellcode](app.py)
- 📊 [Checkpoint Manager](checkpoint.py)
- 🔄 [Pyramiden Generator](pyramid_generator.py)
- 🎯 [Dynamic Input Handler](dynamic_input.py)

---

**Status**: ✅ Version 2.0 - Alle Features implementiert  
**Letzte Aktualisierung**: Mai 2026