```
                        +--------------------------------------------------+
                        |                                                  |
                        |   PYRAMID DETECTION          v2.0                |
                        |   ──────────────────────────────────────────     |
                        |   Binary 3D object classification               |
                        |                                                  |
                        +--------------------------------------------------+
```

## Quickstart

```bash
git clone https://github.com/Malte-Dzierzon/Informatik-Projekt-August-Malte.git
```
```bash
cd Informatik-Projekt-August-Malte
```
```bash
python run.py
```

`run.py` checks the required dependencies, installs missing packages, and starts the selected interface.

If `python` is not recognized on your system, use `python3` on Linux/macOS or `py` on Windows. For an isolated setup, create a virtual environment first: `python -m venv .venv`, then activate it with `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows).

A minimal neural network that classifies 3D objects as pyramids or noise based on their vertices — optimized for low-end hardware, no GPU required.



## What it does

- Trains a binary classifier on procedurally generated 3D vertex data (pyramids vs. noise)
- Handles variable vertex counts per object (4–12 vertices) via dynamic padding
- Saves and resumes training across sessions via a JSON checkpoint system
- Includes an interactive Streamlit dashboard with a 3D Plotly visualizer
- Ships a full-screen terminal UI (TUI) with vim-style navigation, forms, and live training progress


## How it works

The pipeline is split into three stages, one per module:

1. **Data generation** (`pyramid_generator.py`) — A pyramid is defined as 4 base vertices plus an apex (5 points in total). Every sample is randomly scaled, rotated with a random rotation matrix (uniformly distributed over all 3D orientations), and translated into a visible range. Non-pyramids are deliberately generated as near-misses: slanted bases, flat apexes, stacked prisms, or unstructured random point clouds. Samples are padded with `NaN` up to a fixed maximum vertex count so every row has the same shape.

2. **Feature engineering** (`dynamic_input.py`) — Raw X/Y/Z coordinates are transformed into the 10 pairwise distances of the 5 core points. Distances are sorted to remove dependence on vertex order, and `NaN` placeholders become a `-1` sentinel so padding is never interpreted as real geometry. Four explainable features (height, apex balance, base area, center x-offset) are appended, then all features are min-max normalized to `[0, 1]`.

3. **Training** (`nn.py`) — A two-layer network (hidden ReLU, sigmoid output) trained with plain gradient descent (MSE loss, He initialization, configurable train/validation split). Weights and normalization parameters are saved as JSON, so training can be paused and resumed in later sessions.

The same core (`nn.py`) is shared by both interfaces, so a model trained in the web dashboard can be exported and loaded in the terminal UI and vice versa.


## Interfaces

| Option | Description |
| :--- | :--- |
| `1` — Streamlit Web Dashboard | Browser-based UI: dataset generation and CSV import, training curves, and an interactive 3D Plotly visualization |
| `2` — Terminal UI (TUI) | Full-screen terminal app: menus, forms, live training progress, and JSON/Markdown export |

The TUI asks on first launch whether you want Nerd Font icons or plain ASCII art (auto-detected on Linux terminals).


## Stack

`numpy` &nbsp; `scipy` &nbsp; `streamlit` &nbsp; `plotly` &nbsp; `pandas` &nbsp; `python`

NumPy is the only computational core — there is no deep-learning framework and no GPU requirement, which keeps the project runnable on low-end hardware and in constrained environments such as Android (Termux).

```
                        ⠀⠀⠀⠀⠀⠀⣠⣶⣶⢶⣶⣶⣶⣤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣀⡀⠀⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⢰⡿⠃⠀⠀⠀⠀⠀⠉⠙⢻⣦⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣀⠀⢀⣠⣶⠿⠛⠉⠉⠙⣿⡄⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠉⠈⠇⠀⠀⢈⠀⠈⠉⠉⠛⠻⠟⠋⠁⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⢸⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⠃⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠈⣿⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠀⠀⠀⠈⠀⠁⠀⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡟⠀⠀⠀⠀⠀⠀
                        ⠀⣀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⣶⣶⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠃⠀⠀⠀⠀⠀⠀
                        ⠀⠛⠿⢶⣤⣄⠀⢀⣴⡟⠋⠉⠉⠙⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣶⣿⣿⣿⣿⣷⣦⡀⠀⠀⠀⢀⣠⣴⡆⠀
                        ⠀⠀⠀⠀⠈⠉⠀⣾⣿⣧⠀⠀⠀⣠⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⣰⣿⣿⠋⠁⠀⠀⠈⣿⣿⣿⡆⠰⡿⠟⠋⠁⠀⠀
                        ⢠⣴⣦⣤⣤⡀⠀⣿⣿⣿⣶⣶⣶⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⢀⣿⣿⣿⣄⡀⠀⣀⣰⣿⣿⣿⡇⠀⠁⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠉⠉⠁⠀⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠶⠶⠶⠶⠶⠆
                        ⠀⠀⠀⠀⠀⠀⠆⠀⠀⣹⣿⣿⣿⣿⣿⣧⣿⣿⠟⠀⠀⠀⠀⠀⢹⣿⣿⣿⣿⣿⣻⣿⣿⣿⡿⠟⠀⠀⠀⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣾⣍⣛⠿⠿⠿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠙⠿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠻⣷⣶⣶⣶⣶⣤⣤⣤⣤⣤⣴⣶⣶⡶⠿⠟⠛⠛⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢿⣶⠀⠀⠀⠀⠈⠁⠉⠀⣠⣽⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⡀⢀⣤⣤⣤⣤⠀⣸⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠿⠿⠋⠁⠀⠛⠿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
```

---

## License

MIT
