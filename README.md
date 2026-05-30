```
 ____  ____  ____  __  __  __  ____  ____  ____  _  _
(  _ \( ___)(  _ \(  \/  )(  )(  _ \( ___)(  _ \( \( )
 )___/ )__)  )   / )    (  )(  )(_) ))__)  )   / )  (
(__)  (____)(_)\_)(_/\/\_)(__)(____/(____)(_)\_)(_)\_)

 ____  __      __   ____  ____  ____  ____  ____  ____  ____
/ ___)(  )    / _\ / ___)/ ___)(_  _)(  __)(_  _)( ___)(  _ \
( (__  )(    /    \\___ \\___ \  )(   ) _)   )(   )__)  )   /
 \___)(__)   \_/\_/(____/(____/ (__) (__)   (__) (____)(_)\_)

                    v 2 . 0
```

---

```
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⡯⢙⢍⣛⣶⣤⠴⠶⠦⢤⣤⣀⡀⠀⠀⢀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⣨⡾⠋⠁⠀⠀⠀⠀⠀⠀⠉⠙⠷⠛⣫⠍⣻⢍⠹⡆⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠢⡄⠀⢸⠀⣷⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢢⣼⠀⣿⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⡾⠁⠀⠀⣴⣶⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠀⡏⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢀⣴⣶⢿⡷⣆⠀⠀⠿⠿⠟⢀⣀⠀⠀⠀⢰⣿⣿⣦⠀⠀⠀⠀⠀⠀⠀⣿⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣾⣥⠛⡘⢳⡾⡇⠀⠀⠀⡀⠸⣿⠟⠀⠀⠘⠻⠟⠃⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢻⡈⠿⠿⠿⠀⣧⠀⠀⠀⠛⠛⠻⠦⠤⠴⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⡇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⢸⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⣠⡟⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠸⣇⠀⠀⠀⠀⠀⠻⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠛⠉⠉⠙⢷⣾⠋⠀⠀⠀⠀⠀⠀⠀
⠀⣀⣀⣀⣀⣠⣿⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣸⡇⣶⠀⣆⢀⣶⣿⣀⣀⣀⣀⣀⣀⡀⠀
⠈⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠙⠛⠛⠻⠛⠋⠉⠉⠉⠉⠉⠉⠉⠉⠁
```

---

Ein minimales neuronales Netz, das 3D-Objekte anhand ihrer Eckpunkte als Pyramiden oder Rauschen klassifiziert — optimiert für Low-End-Hardware, keine GPU erforderlich.

---

## Documentation

Vollständige Dokumentation, Architektur-Details und mathematische Hintergründe:
**[Kanva Docs](https://your-kanva-link-here)**

---

## Was es macht

- Trainiert einen binären Klassifikator auf prozedural generierten 3D-Eckpunktdaten (Pyramiden vs. Rauschen)
- Verarbeitet variable Punktanzahlen pro Objekt (4–12 Eckpunkte) via dynamisches Padding
- Speichert und setzt Training sessionübergreifend fort — via JSON-Checkpoint-System
- Enthält ein interaktives Streamlit-Dashboard und einen 3D-Plotly-Visualizer

---

## Stack

`numpy` &nbsp; `scipy` &nbsp; `streamlit` &nbsp; `plotly` &nbsp; `pandas`

---

## Quickstart

```bash
pip install -r requirements.txt
python run.py
```

---

```
⠀⠀⠀⠀⢠⡶⠚⢷⣤⡀⠀⠀⠀⠀⠀⣲⡶⠛⠻⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢠⡿⠁⠀⠀⠙⣷⣄⠀⢀⣴⡟⠁⠀⠀⢷⢹⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣾⠃⠀⠠⠶⠚⠛⠛⠛⠛⠋⠀⠀⣀⡀⢸⠈⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢸⣏⡔⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠚⠉⠉⣿⠀⢹⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢾⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢠⣿⢠⣶⡆⠀⠀⠀⠀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀
⢒⡾⠁⠘⠟⠁⠀⠀⠀⠀⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀
⠉⣧⠀⠀⠀⠀⠃⠀⠀⠀⠈⠉⠠⣍⠀⠀⠀⠀⠀⠀⣸⡇⢀⣤⠶⠛⠛⠻⢦⣄
⠀⠸⣧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡟⣴⠟⠁⠀⠀⠀⠀⠀⢻
⠀⠀⠀⠛⣷⡦⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣤⡴⠞⠋⢠⡟⠀⠀⠀⠀⠀⠀⢀⡾
⠀⠀⠀⢰⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠳⣤⡀⢸⠃⠀⠀⠀⠀⢠⡶⠟⠁
⠀⠀⠀⣸⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢷⣹⡄⠀⠀⠀⠀⣼⠀⠀⠀
⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣇⠀⠀⠀⠀⢹⡄⠀⠀
⠀⠀⠀⢸⡀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⡇⠀⠀⠀⠈⣧⠀⠀
⠀⠀⠀⢸⡇⠘⡇⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⢸⣿⠀⠀⠀⠀⢹⡇⠀
⠀⠀⠀⢸⡇⠀⠙⠀⠀⠀⠀⠀⢠⠞⠁⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⢸⡇⠀
⠀⠀⠀⢸⡇⠀⢸⡆⠀⠀⠀⠀⣟⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⠀⠀⠀⠀⣸⠇⠀
⠀⠀⠀⢸⣿⠀⠀⡇⠀⠀⠀⠀⣿⡀⠀⠀⠀⠀⠀⠀⣠⢇⡿⠀⠀⢀⣴⡟⠁⠀
⠀⠀⠀⠘⠿⠶⢶⢧⣦⣦⡴⢾⣥⣽⣤⣤⣤⣤⣤⣤⡿⣯⡤⠴⠶⠛⠋⠀⠀⠀
```

---

## License

MIT
