# 🚀 Quick Start - Neuronales Netz mit erweiterten Features

## Installation & Setup

### 1. Abhängigkeiten installieren
```bash
pip install streamlit plotly pandas numpy
```

### 2. App starten
```bash
streamlit run app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`

---

## Erste Schritte (3 Minuten)

### Variante A: Schnelle Demo mit Sample-Daten

1. **Tab "⚙️ Konfiguration"**
   - Default-Werte sind bereits gut → Nichts ändern nötig

2. **Tab "📊 Trainingsdaten"**
   - Wähle: "Sample-Daten"
   - Klick: "Daten anzeigen"

3. **Tab "🎓 Training"**
   - Klick: "▶️ Training starten"
   - Beobachte die Echtzeit-Ausgabe
   - Nach ~10 Sekunden: Training abgeschlossen ✓

4. **Tab "🔮 Vorhersagen"**
   - Gib Werte ein (z.B. 0.5 für alle)
   - Klick: "🔮 Vorhersage machen"

5. **Tab "💾 Checkpoints"**
   - Klick: "💾 Checkpoint speichern"
   - Gib Namen ein: "demo_v1"
   - Klick: "✓ Speichern bestätigen"

---

### Variante B: Mit automatischem Pyramiden-Generator

1. **Tab "📊 Trainingsdaten"**
   - Wähle: "Pyramiden-Generator (PROZEDURAL)"
   - Anzahl Pyramiden: 100
   - Anzahl Non-Pyramids: 100
   - Klick: "🔄 Daten generieren"

2. **Tab "🎓 Training"**
   - Klick: "▶️ Training starten"
   - Beobachte Live-Training

3. **Tab "💾 Checkpoints"**
   - Speichere einen Checkpoint
   - Notiere dir den Namen

---

## Die 4 Haupt-Features kurz erklärt

### 1️⃣ Checkpoints (Speichern & Fortsetzen)
```
Trainiere → Speichere Checkpoint → 
Later: Lade Checkpoint → Trainiere weiter
(Training-Counter wird automatisch erhöht!)
```

### 2️⃣ Training-Counter
```
Oben rechts im Training-Tab sichtbar:
🔄 Gesamtzahl Trainings-Durchgänge: 5
(Wird mit jedem Training erhöht und in Checkpoints gespeichert)
```

### 3️⃣ Pyramiden-Generator
```
Klick 1x "🔄 Daten generieren" →
Generiert 100+ unterschiedliche Pyramiden automatisch
(Mathematisch unbegrenzte Variationen!)
```

### 4️⃣ Dynamischer Input
```
Egal ob 4, 6, 8, oder 12 Vertices:
System erkennt Padding automatisch → Filtert es heraus
Zeigt "-" für überflüssige Features
```

---

## Workflow: Ein realistisches Szenario

### Szenario: "Ich trainiere ein Modell über 3 Tage"

**Tag 1 - Morgens (10 Minuten):**
1. Generiere 100 Pyramiden-Samples
2. Trainiere mit 500 Epochen
3. Checkpoint speichern: "day1_morning"

**Tag 1 - Abends (10 Minuten):**
1. Lade Checkpoint "day1_morning"
2. Generiere 100 neue Pyramiden (andere Variationen!)
3. Trainiere erneut mit 500 Epochen
   - Training-Counter: 1 → 2
4. Checkpoint speichern: "day1_evening"

**Tag 2 - Morgens:**
1. Lade Checkpoint "day1_evening"
   - Training-Counter: 2 ist wiederhergestellt
2. Trainiere erneut → Training-Counter: 3
3. Checkpoint speichern: "day2"

**Ergebnis:**
- 3 separate Training-Sessions dokumentiert
- Jeder Checkpoint zeigt den exakten State
- Training-Counter = 3 (gesamt)

---

## Häufige Fragen

### F: Wie lange dauert ein Training?
**A:** Mit 500 Epochen und ~200 Samples: ~30-60 Sekunden

### F: Was passiert mit meinen Daten nach dem Trainieren?
**A:** Bleiben im Browser Session (bis Seite neu geladen). Speichere einen Checkpoint zum Persistieren!

### F: Kann ich mehrere Checkpoints vergleichen?
**A:** Ja! Im "💾 Checkpoints" Tab sieht man alle gespeicherten Checkpoints mit Metriken.

### F: Was bedeutet "Dynamic Input"?
**A:** Du kannst Figuren mit unterschiedlicher Anzahl Eckpunkte trainieren. Das System passt sich automatisch an!

### F: Wie viele Features kann das System verarbeiten?
**A:** Aktuell bis 100. Standardmäßig 19 Features (4×3 Basis + 3 Apex + 4 derived)

### F: Kann ich Checkpoints zwischen Computern verschieben?
**A:** Ja! Der `checkpoints/` Ordner enthält alle `.npz` und `.json` Dateien - einfach kopieren!

---

## Tipps für bessere Ergebnisse

### Training-Tipps:
- ✅ Mehrere kleine Trainings mit Checkpoints ist besser als ein großes!
- ✅ Learning Rate: 0.05-0.2 ist meist optimal
- ✅ 500-1000 Epochen für gute Konvergenz
- ✅ Hidden Layer: 16-64 Neuronen empfohlen

### Daten-Tipps:
- ✅ Verwende Generator für unbegrenzte Variationen
- ✅ Verhältnis Pyramiden:Non-Pyramids sollte ausgeglichen sein
- ✅ Mehr Daten = bessere Genauigkeit

### Checkpoint-Tipps:
- ✅ Speichere regelmäßig (nach jedem Training)
- ✅ Gib aussagekräftige Namen: "v1_50-epochs", "v2_more-data"
- ✅ Lösche alte schlechte Checkpoints um Speicher zu sparen

---

## Fehlerbehebung

### Problem: "Keine Trainingsdaten geladen!"
**Lösung:** Gehe zu Tab "📊 Trainingsdaten" und generiere/lade Daten

### Problem: App zeigt "Error loading module checkpoint.py"
**Lösung:** Stelle sicher dass alle `.py` Dateien im gleichen Ordner sind:
- app.py
- checkpoint.py
- pyramid_generator.py
- dynamic_input.py
- matrix.py

### Problem: Training ist sehr langsam
**Lösung:** 
- Reduziere Epochen (z.B. 100 statt 500)
- Verkleinere Hidden Layer (z.B. 16 statt 64)
- Verwende weniger Samples (z.B. 50 statt 500)

### Problem: Checkpoint lässt sich nicht laden
**Lösung:** Checkpoint-Datei könnte beschädigt sein. Lösche die Datei und erstelle einen neuen Checkpoint.

---

## Projektstruktur

```
Informatik-Projekt-August-Malte/
├── app.py                      ← HAUPTDATEI (Streamlit App)
├── checkpoint.py               ← Checkpoint-Management
├── pyramid_generator.py         ← Pyramiden-Generator
├── dynamic_input.py             ← Dynamisches Input-System
├── matrix.py                    ← Matrix-Operationen
├── training.py                  ← Altes Training (legacy)
├── README.md                    ← Projekt-Übersicht
├── FEATURES_DOKUMENTATION.md    ← Detaillierte Doku (THIS)
├── QUICK_START.md              ← Dieser Guide
├── run.bat                      ← Windows Starter
├── checkpoints/                 ← Speicherort Checkpoints
│   ├── checkpoint_*.npz
│   ├── checkpoint_*_metadata.json
│   └── checkpoint_*_history.csv
└── Daten_zum_trainieren/
    └── Trainings_Daten.txt
```

---

## Nächste Schritte

- [ ] Trainiere ein Modell mit 500+ Samples
- [ ] Experimentiere mit verschiedenen Netzwerk-Größen
- [ ] Speichere mehrere Checkpoints
- [ ] Vergleiche Training-Verlauf zwischen Checkpoints
- [ ] Tritt Variable-Size Daten aus
- [ ] Optimiere Hyperparameter

---

## Support & Kontakt

**Fragen?** Siehe [FEATURES_DOKUMENTATION.md](FEATURES_DOKUMENTATION.md) für detaillierte Erklärungen.

**Probleme?** Check die Fehlerbehebungs-Sektion oben.

---

**Version:** 2.0 (Erweitert)  
**Letzte Aktualisierung:** Mai 2026  
**Status:** ✅ Alle 4 Features implementiert und getestet
