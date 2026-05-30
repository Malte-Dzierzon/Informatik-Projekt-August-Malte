import streamlit as st
import numpy as np
import json
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from PIL import Image
import os

from debug_utils import debug_error, debug_info, debug_generate, debug_training
from pyramid_generator import PyramidGenerator
from dynamic_input import DynamicInputHandler

# 1. Pfad zur PNG-Datei im selben Ordner ermitteln
icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
icon_image = Image.open(icon_path)


def expit(z: np.ndarray) -> np.ndarray:
    """Numerisch stabile Sigmoid-Funktion (Clipping verhindert Overflow)."""
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500.0, 500.0)))


st.set_page_config(
    page_title="Pyramiden-Klassifikation", 
    layout="wide",
    page_icon=icon_image
    )

st.markdown("""
    <style>
    h1 { font-size: 2.5rem; margin-bottom: 0rem; }
    .subtitle { font-size: 1.1rem; color: #666; }
    .stButton > button { width: 100%; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>Pyramiden-Klassifikation</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Neuronales Netzwerk zur Erkennung von Pyramiden | Informatik-Projekt</p>", unsafe_allow_html=True)
st.markdown("---")


# ---------------------------------------------------------------------------
# SPEICHER-VERWALTUNG (SESSION STATE)
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "pyramid_generator":     lambda: PyramidGenerator(seed=42),
    "input_handler":         lambda: DynamicInputHandler(max_vertices=12, coordinates_per_vertex=3),
    "model":                 lambda: None,
    "total_training_count":  lambda: 0,
    "train_losses":          lambda: [],
    "test_losses":           lambda: [],
    "last_validation_result": lambda: None,
    "current_test_vector":   lambda: None,
    "current_soll":          lambda: None,
    "ui_object_type":        lambda: "perfect",
}

for _key, _factory in _DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _factory()


# ---------------------------------------------------------------------------
# MODELL-ZENTRALE (SIDEBAR)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='font-size: 1.6rem;'>Modell-Zentrale</h2>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("**JSON-Modell importieren**")
    imported = st.file_uploader(
        "Datei auswählen",
        type="json",
        key="json_uploader_unique",
        label_visibility="collapsed",
    )

    if imported:
        try:
            if "last_loaded_file" not in st.session_state or st.session_state.last_loaded_file != imported.name:
                imported.seek(0)
                data = json.loads(imported.read().decode("utf-8"))

                required_keys = ["W1", "b1", "W2", "b2", "config"]
                if not all(k in data for k in required_keys):
                    st.error("[Strukturfehler] Unvollständige Parameterstruktur im JSON-Dokument.")
                else:
                    st.session_state.model = {
                        "W1": np.array(data["W1"], dtype=np.float32),
                        "b1": np.array(data["b1"], dtype=np.float32),
                        "W2": np.array(data["W2"], dtype=np.float32),
                        "b2": np.array(data["b2"], dtype=np.float32),
                        "input_size":  int(data["config"]["input_size"]),
                        "hidden_size": int(data["config"]["hidden_size"]),
                    }
                    stats = data.get("stats", {})
                    st.session_state.total_training_count = int(stats.get("total_epochs", 0))
                    last_loss = stats.get("last_loss", 0.0)
                    st.session_state.train_losses = [float(last_loss)] if last_loss else []
                    st.session_state.test_losses  = [float(last_loss)] if last_loss else []
                    st.session_state.last_validation_result = stats.get("validation", "Nicht validiert")

                    if "normalization_params" in data:
                        st.session_state.input_handler.set_params(data["normalization_params"])

                    st.session_state.last_loaded_file = imported.name
                    st.success("[System] Modellparameter erfolgreich geladen.")
                    st.rerun()
        except Exception as e:
            debug_error("JSON-Import fehlgeschlagen.", e)
            st.error(f"[Importfehler] Datei-Inhalt ungültig: {str(e)[:50]}")

    st.markdown("---")

    if st.session_state.model is not None:
        model = st.session_state.model

        st.markdown("<h3 style='font-size: 1.2rem;'>Architektur</h3>", unsafe_allow_html=True)
        col_a1, col_a2 = st.columns(2)
        col_a1.metric("Input Nodes",  str(model["input_size"]))
        col_a2.metric("Hidden Nodes", str(model["hidden_size"]))

        st.markdown("---")
        st.markdown("<h3 style='font-size: 1.2rem;'>Status & Validierung</h3>", unsafe_allow_html=True)

        col_x, col_y = st.columns(2)
        formatted_epochs = f"{st.session_state.total_training_count:,}".replace(",", ".")
        col_x.metric("Epochen", formatted_epochs)
        col_y.metric(
            "Loss",
            f"{st.session_state.test_losses[-1]:.5f}" if st.session_state.test_losses else "—",
        )

        val_status = st.session_state.last_validation_result
        if val_status:
            keywords_ok = ("erfolgreich", "perfekt", "verifiziert")
            if any(kw in val_status.lower() for kw in keywords_ok):
                st.success(val_status)
            else:
                st.warning(val_status)

        st.markdown("---")
        st.markdown("<h3 style='font-size: 1.2rem;'>Exporte & Berichte</h3>", unsafe_allow_html=True)

        current_loss = float(st.session_state.test_losses[-1]) if st.session_state.test_losses else 0.0
        export_data = {
            "W1": model["W1"].tolist(), "b1": model["b1"].tolist(),
            "W2": model["W2"].tolist(), "b2": model["b2"].tolist(),
            "config": {"input_size": model["input_size"], "hidden_size": model["hidden_size"]},
            "stats": {
                "total_epochs": int(st.session_state.total_training_count),
                "last_loss":    current_loss,
                "validation":   st.session_state.last_validation_result,
            },
            "normalization_params": st.session_state.input_handler.normalization_params,
        }

        st.download_button(
            label="Download JSON (Gewichte)",
            data=json.dumps(export_data, indent=2),
            file_name=f"model_weights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width="stretch",
        )

        w1_rounded = np.round(model["W1"], 3)
        w2_rounded = np.round(model["W2"].T, 3)

        markdown_report = (
            f"# Modellreport: KI-Pyramiden-Klassifikation\n\n"
            f"## 1. System- & Metadaten\n\n"
            f"| Parameter | Wert |\n"
            f"| :--- | :--- |\n"
            f"| Erstellungsdatum | {datetime.now().strftime('%d.%m.%Y, %H:%M:%S')} Uhr |\n"
            f"| Status Validierung | {st.session_state.last_validation_result} |\n\n"
            f"## 2. Netzwerk-Topologie (Architektur)\n\n"
            f"| Schicht | Anzahl Neuronen | Aktivierungsfunktion |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Eingangsschicht (Input)** | {model['input_size']} | Identische Abbildung |\n"
            f"| **Versteckte Schicht (Hidden)** | {model['hidden_size']} | ReLU |\n"
            f"| **Ausgangsschicht (Output)** | 1 | Sigmoid |\n\n"
            f"## 3. Trainings-Metriken\n\n"
            f"| Metrik | Wert |\n"
            f"| :--- | :--- |\n"
            f"| Absolvierte Epochen gesamt | {formatted_epochs} |\n"
            f"| Letzter Fehlerwert (MSE Loss) | {current_loss:.6f} |\n\n"
            f"## 4. Mathematische Parameter\n\n"
            f"### 4.1 Schicht 1: Input → Hidden (`W1`)\n"
            f"```text\n{np.array2string(w1_rounded, max_line_width=120)}\n```\n\n"
            f"### 4.2 Schicht 2: Hidden → Output (`W2`)\n"
            f"```text\n{np.array2string(w2_rounded, max_line_width=120)}\n```\n"
        )

        st.download_button(
            label="Download Markdown Report (.md)",
            data=markdown_report,
            file_name=f"Modell_Dokumentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            width="stretch",
        )
    else:
        st.info("System wartet auf Modellinitialisierung. Generiere Trainingsdaten oder lade ein bestehendes JSON-Modell.")


# ---------------------------------------------------------------------------
# HAUPTTABS
# ---------------------------------------------------------------------------
tab_data, tab_training, tab_test = st.tabs([
    "Daten-Zentrale",
    "Training & Validierung",
    "Interaktiver Test (3D)",
])


# ---------------------------------------------------------------------------
# TAB 1: DATENSATZ-VERWALTUNG
# ---------------------------------------------------------------------------
with tab_data:
    st.markdown("<h2 style='font-size: 1.5rem;'>Trainingsdaten-Management</h2>", unsafe_allow_html=True)

    st.markdown("###### Maximale Eckpunktanzahl festlegen")
    st.markdown(
        "> **Hinweis zur Datenstruktur:** Alle Objekte werden auf dieselbe Länge gebracht. "
        "Hat ein Objekt weniger Eckpunkte als das Maximum, werden die fehlenden Stellen automatisch "
        "mit `NaN` gefüllt – damit bleibt der Unterschied zu echten Punkten am Ursprung (0, 0, 0) erhalten."
    )

    c_geo1, _ = st.columns(2)
    with c_geo1:
        max_vertices = st.number_input(
            "Maximale Anzahl an Eckpunkten (Vertices)",
            min_value=5,
            value=12,
            step=1,
            key="ui_max_vertices",
        )

    coords_per_vertex = 3

    # Handler synchronisieren, falls sich die UI-Einstellung ändert
    if st.session_state.input_handler.max_vertices != max_vertices:
        st.session_state.input_handler = DynamicInputHandler(
            max_vertices=max_vertices,
            coordinates_per_vertex=coords_per_vertex,
        )

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Variante A: Synthetischen Datensatz generieren**")
        n_pyramids     = st.number_input("Anzahl Pyramiden",     min_value=10, value=100, step=10)
        n_non_pyramids = st.number_input("Anzahl andere Formen", min_value=10, value=100, step=10)

        if st.button("Datensatz erstellen", width="stretch", key="gen_btn"):
            with st.spinner("Geometrie-Matrizen werden berechnet..."):
                data_matrix, _ = st.session_state.pyramid_generator.generate_dataset(
                    max_vertices=max_vertices,
                    coords_per_vertex=coords_per_vertex,
                    n_pyramids=int(n_pyramids),
                    n_non_pyramids=int(n_non_pyramids),
                    shuffle=True,
                )
                st.session_state.data = data_matrix.astype(np.float32)
                debug_generate("Synthetischen Trainingsdatensatz erzeugt.")
                st.success("Datensatz erfolgreich geladen.")
                st.rerun()

    with col2:
        st.markdown("**Variante B: CSV-Datei importieren**")
        uploaded = st.file_uploader("CSV-Datei auswählen", type="csv")
        if uploaded:
            try:
                df_upload = pd.read_csv(uploaded, low_memory=False)
                is_pure_data = all(
                    str(col).replace(".", "", 1).isdigit() or "Unnamed" in str(col)
                    for col in df_upload.columns
                )
                if is_pure_data:
                    uploaded.seek(0)
                    df_upload = pd.read_csv(uploaded, header=None, low_memory=False)
                
                uploaded_matrix = df_upload.to_numpy(dtype=np.float32)
                st.session_state.data = uploaded_matrix
                
                anzahl_zusatz_features = 4
                calculated_features = uploaded_matrix.shape[1] - 1
                calculated_vertices = (calculated_features - anzahl_zusatz_features) // coords_per_vertex
                
                if calculated_vertices >= 5:
                    st.session_state.input_handler = DynamicInputHandler(
                        max_vertices=calculated_vertices,
                        coordinates_per_vertex=coords_per_vertex,
                    )
                    st.session_state.ui_max_vertices = calculated_vertices
                
                st.success(f"CSV erfolgreich importiert ({calculated_vertices} Eckpunkte erkannt).")
                st.rerun()
            except Exception as e:
                debug_error("CSV-Import fehlgeschlagen.", e)
                st.error(f"Fehler beim Einlesen der CSV-Datei: {e}")

    if "data" in st.session_state:
        st.markdown("---")
        data = st.session_state.data
        pyr_rows   = data[data[:, -1] == 1.0]
        other_rows = data[data[:, -1] == 0.0]

        current_num_features = data.shape[1] - 1
        anzahl_zusatz_features = 4
        current_vertices = (current_num_features - anzahl_zusatz_features) // coords_per_vertex

        c1, c2, c3 = st.columns(3)
        c1.metric("Datensätze gesamt",               str(len(data)))
        c2.metric("Anzahl Merkmale (Spalten)",        str(current_num_features))
        c3.metric("Klassenverteilung (Pyr / Andere)", f"{len(pyr_rows)} / {len(other_rows)}")

        st.markdown("### Datenvorschau (vor Normalisierung)")

        col_names: list = []
        feat_counter = 0
        for v in range(current_vertices):
            for c_idx in range(coords_per_vertex):
                if feat_counter < current_num_features:
                    axis = ["X", "Y", "Z"][c_idx % 3]
                    col_names.append(f"P{v + 1}_{axis}")
                    feat_counter += 1
                    
        zusatz_labels = ["Höhe", "Balance", "Grundfläche", "Schwerpunkt X"]
        for label in zusatz_labels:
            if len(col_names) < current_num_features:
                col_names.append(label)
                
        while len(col_names) < current_num_features:
            col_names.append(f"Zusatzmerkmal_{len(col_names) + 1}")
            
        col_names.append("Klasse (Label)")

        view_col1, view_col2 = st.columns(2)
        with view_col1:
            st.markdown("**▪ Klasse 1 – Pyramiden (Vorschau)**")
            if len(pyr_rows) > 0:
                st.dataframe(pd.DataFrame(pyr_rows[:5], columns=col_names).style.format(precision=3, na_rep="NaN"), width="stretch")
            else:
                st.info("Keine Pyramiden im aktuellen Datensatz vorhanden.")

        with view_col2:
            st.markdown("**▪ Klasse 0 – Andere Formen (Vorschau)**")
            if len(other_rows) > 0:
                st.dataframe(pd.DataFrame(other_rows[:5], columns=col_names).style.format(precision=3, na_rep="NaN"), width="stretch")
            else:
                st.info("Keine anderen Formen im aktuellen Datensatz vorhanden.")

# ---------------------------------------------------------------------------
# TAB 2: MODELL-TRAINING
# ---------------------------------------------------------------------------
with tab_training:
    st.markdown("<h2 style='font-size: 1.5rem;'>Modell trainieren</h2>", unsafe_allow_html=True)

    # Eingangsgröße bestimmen (aus geladenen Daten oder Schätzung)
    if "data" in st.session_state:
        try:
            raw_features_only = st.session_state.data[:, :-1]
            detected_inputs = st.session_state.input_handler._transform_to_distances(raw_features_only).shape[1]
        except Exception:
            detected_inputs = st.session_state.data.shape[1] - 1
    else:
        detected_inputs = (max_vertices * (max_vertices - 1)) // 2

    col1, col2, col3 = st.columns(3)
    with col1:
        input_size = st.number_input("Input Nodes ", value=int(detected_inputs), step=1, disabled=True)
    with col2:
        hidden_size = st.number_input("Hidden Nodes", value=32, step=1)
    with col3:
        learning_rate = st.slider("Lernrate(BIOS)", 0.001, 1.0, 0.1)

    epochs = st.number_input("Anzahl Epochen", value=1000, step=100)

    # Prüfen ob das geladene Modell zur aktuellen Architektur passt → Weitertraining möglich
    can_continue = (
        st.session_state.model is not None
        and st.session_state.model["input_size"]  == input_size
        and st.session_state.model["hidden_size"] == hidden_size
    )

    if can_continue:
        train_mode = st.radio(
            "Trainingsmodus:",
            ["Bestehendes Modell weitertrainieren", "Neu starten (Gewichte zurücksetzen)"],
            horizontal=True,
        )
    else:
        st.info("Neue Architektur erkannt oder kein Modell geladen – Gewichte werden neu initialisiert.")
        train_mode = "Neu starten (Gewichte zurücksetzen)"

    if st.button("Training starten", width="stretch"):
        if "data" not in st.session_state:
            st.error("Bitte zuerst Daten laden oder erstellen (Tab: Trainingsdaten).")
        else:
            try:
                raw_data = st.session_state.data
                data_prepared, _ = st.session_state.input_handler.filter_and_prepare(raw_data, fit=True)

                X_all = data_prepared[:, :-1]
                y_all = data_prepared[:, -1:]
                actual_input_size = X_all.shape[1]

                # Fester Zufalls-Seed für reproduzierbare Train/Val-Aufteilung
                split_rng = np.random.default_rng(42)
                shuffled_indices = split_rng.permutation(len(data_prepared))
                split_idx = int(len(data_prepared) * 0.8)
                train_idx, val_idx = shuffled_indices[:split_idx], shuffled_indices[split_idx:]

                X_train, y_train = X_all[train_idx], y_all[train_idx]
                X_val   = X_all[val_idx]  if len(val_idx) > 0 else X_train
                y_val   = y_all[val_idx]  if len(val_idx) > 0 else y_train
                n_train = len(X_train)
                X_train_T = X_train.T  # Einmal transponieren, nicht jede Epoche neu

                if train_mode != "Bestehendes Modell weitertrainieren":
                    st.session_state.total_training_count = 0

                # Gewichte laden oder neu initialisieren (He-Initialisierung für ReLU)
                if train_mode == "Bestehendes Modell weitertrainieren":
                    W1 = st.session_state.model["W1"]
                    b1 = st.session_state.model["b1"]
                    W2 = st.session_state.model["W2"]
                    b2 = st.session_state.model["b2"]
                    train_losses = list(st.session_state.train_losses)
                    test_losses  = list(st.session_state.test_losses)
                else:
                    # He-Initialisierung: Varianz angepasst an Eingangsgröße
                    init_rng = np.random.default_rng(42)
                    W1 = (init_rng.standard_normal((actual_input_size, hidden_size)) * np.sqrt(2.0 / actual_input_size)).astype(np.float32)
                    b1 = np.zeros((1, hidden_size), dtype=np.float32)
                    W2 = (init_rng.standard_normal((hidden_size, 1)) * np.sqrt(2.0 / hidden_size)).astype(np.float32)
                    b2 = np.zeros((1, 1), dtype=np.float32)
                    train_losses = []
                    test_losses  = []

                progress_bar = st.progress(0)
                status_text  = st.empty()

                for epoch in range(int(epochs)):
                    # --- Forward Pass (Training) ---
                    z1 = X_train @ W1 + b1
                    a1 = np.maximum(0.0, z1)        # ReLU
                    z2 = a1 @ W2 + b2
                    a2 = expit(z2)                  # Sigmoid
                    loss = float(np.mean((a2 - y_train) ** 2))
                    train_losses.append(loss)

                    # --- Forward Pass (Validierung) ---
                    a1_val  = np.maximum(0.0, X_val @ W1 + b1)
                    a2_val  = expit(a1_val @ W2 + b2)
                    val_loss = float(np.mean((a2_val - y_val) ** 2))
                    test_losses.append(val_loss)

                    # --- Backpropagation ---
                    # Gradienten separat berechnen (Lernrate erst beim Update anwenden)
                    dz2     = (a2 - y_train) * a2 * (1.0 - a2)
                    grad_W2 = (a1.T @ dz2) / n_train
                    grad_b2 = np.mean(dz2, axis=0, keepdims=True)

                    dz1     = (dz2 @ W2.T) * (z1 > 0.0)   # ReLU-Ableitung
                    grad_W1 = (X_train_T @ dz1) / n_train
                    grad_b1 = np.mean(dz1, axis=0, keepdims=True)

                    # --- Gewichte aktualisieren (Gradient Descent) ---
                    W2 -= learning_rate * grad_W2
                    b2 -= learning_rate * grad_b2
                    W1 -= learning_rate * grad_W1
                    b1 -= learning_rate * grad_b1

                    if epoch % 50 == 0:
                        progress_bar.progress(epoch / int(epochs))
                        status_text.text(
                            f"Epoche {epoch}/{int(epochs)} "
                            f"| Train Loss: {loss:.5f} | Val Loss: {val_loss:.5f}"
                        )

                progress_bar.progress(1.0)
                status_text.text("Training abgeschlossen.")

                validation_msg = f"Modell erfolgreich auf {actual_input_size} Merkmalen trainiert."
                st.session_state.last_validation_result = validation_msg
                st.success(validation_msg)

                st.session_state.model = {
                    "W1": W1, "b1": b1, "W2": W2, "b2": b2,
                    "input_size": actual_input_size, "hidden_size": int(hidden_size),
                }
                st.session_state.train_losses = train_losses
                st.session_state.test_losses  = test_losses
                st.session_state.total_training_count += int(epochs)

                debug_training({
                    "Lernrate":           learning_rate,
                    "Epochen (aktuell)":  int(epochs),
                    "Epochen (gesamt)":   st.session_state.total_training_count,
                    "Train Loss (final)": loss,
                    "Val Loss (final)":   val_loss,
                    "Eingangsgröße":      actual_input_size,
                })
                st.rerun()

            except Exception as e:
                debug_error("Training fehlgeschlagen.", e)
                st.error(f"Fehler während des Trainings: {e}")

    # Loss-Kurven anzeigen (nur wenn Modell und Verlaufsdaten vorhanden)
    if st.session_state.model and st.session_state.train_losses:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=st.session_state.train_losses,
            name="Trainingsfehler (Train Loss)",
            line=dict(color="#1f77b4", width=2),
        ))
        if st.session_state.test_losses:
            fig.add_trace(go.Scatter(
                y=st.session_state.test_losses,
                name="Validierungsfehler (Val Loss)",
                line=dict(color="#ff9f43", width=2),
            ))
        fig.update_layout(
            xaxis_title="Epoche",
            yaxis_title="Fehler (MSE)",
            template="plotly_white",
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# TAB 3: INTERAKTIVER 3D-TEST
# ---------------------------------------------------------------------------
with tab_test:
    st.markdown("<h2 style='font-size: 1.5rem; margin-bottom: 1.5rem;'>Interaktiver 3D-Geometrie-Test</h2>", unsafe_allow_html=True)

    if st.session_state.model is None:
        st.warning("Kein Modell geladen. Bitte zuerst ein Modell trainieren oder importieren.")
    else:
        model = st.session_state.model
        current_input_dim = model["input_size"]
        expected_raw_dim  = (
            st.session_state.input_handler.max_vertices
            * st.session_state.input_handler.coordinates_per_vertex
        )

        test_vector    = None
        soll_ergebnis  = None
        prediction_raw = None
        final_class    = None
        norm_vector    = None

        if st.session_state.current_test_vector is not None:
            test_vector   = np.array(st.session_state.current_test_vector, dtype=np.float32)
            soll_ergebnis = st.session_state.current_soll

        if test_vector is not None:
            # Dummy-Label anhängen, damit filter_and_prepare ein valides 2D-Array erhält
            prep_matrix = np.zeros((1, len(test_vector) + 1), dtype=np.float32)
            prep_matrix[0, :len(test_vector)] = test_vector

            # Normalisierung nachholen falls noch nicht geschehen
            if not st.session_state.input_handler.normalization_params and "data" in st.session_state:
                st.session_state.input_handler.filter_and_prepare(st.session_state.data, fit=True)

            try:
                norm_matrix, _ = st.session_state.input_handler.filter_and_prepare(prep_matrix, fit=False)
                norm_vector = norm_matrix[0, :-1]

                if len(norm_vector) == current_input_dim:
                    X_input = norm_vector.reshape(1, -1)
                    a1 = np.maximum(0.0, X_input @ model["W1"] + model["b1"])
                    prediction_raw = float(expit(a1 @ model["W2"] + model["b2"])[0, 0])
                    final_class = 1 if prediction_raw >= 0.5 else 0
                else:
                    st.error(
                        f"Architektur-Konflikt: Eingabe hat {len(norm_vector)} Merkmale, "
                        f"Modell erwartet {current_input_dim}."
                    )
            except Exception as e:
                debug_error("Vorbereitung des Testvektors fehlgeschlagen.", e)
                st.error(f"Fehler bei der Datenvorbereitung: {e}")

        col_left, col_right = st.columns([1, 1], gap="large")

        # ===================================================================
        # RECHTE SPALTE: Eingabe & Objektgenerierung
        # ===================================================================
        with col_right:
            st.markdown("<h4 style='margin-top:0; color:#444;'>Eingabe & Objektgenerierung</h4>", unsafe_allow_html=True)
            modus = st.radio(
                "Eingabemethode:",
                ["Zufälliges Objekt generieren (Empfohlen)", "Koordinaten manuell eingeben"],
            )

            if "Zufälliges" in modus:
                st.write("Objekttyp auswählen:")
                c_btn1, c_btn2 = st.columns(2)

                with c_btn1:
                    is_p = st.session_state.ui_object_type == "perfect"
                    if st.button("Pyramide (Soll = 1)", type="primary" if is_p else "secondary", width="stretch"):
                        st.session_state.ui_object_type = "perfect"
                        st.rerun()
                with c_btn2:
                    is_a = st.session_state.ui_object_type == "alternative"
                    if st.button("Andere Form (Soll = 0)", type="primary" if is_a else "secondary", width="stretch"):
                        st.session_state.ui_object_type = "alternative"
                        st.rerun()

                if st.button("Objekt generieren & analysieren", width="stretch"):
                    is_pyramid = st.session_state.ui_object_type == "perfect"
                    gen = st.session_state.pyramid_generator
                    raw_vector = (
                        gen.generate_single_pyramid(st.session_state.ui_max_vertices, 3)
                        if is_pyramid
                        else gen.generate_single_non_pyramid(st.session_state.ui_max_vertices, 3)
                    )
                    st.session_state.current_test_vector = raw_vector.astype(np.float32).tolist()
                    st.session_state.current_soll = 1.0 if is_pyramid else 0.0
                    debug_generate("Einzelobjekt für 3D-Test generiert.")
                    st.rerun()

            else:
                st.markdown(f"Gib exakt `{expected_raw_dim}` Zahlen ein. Leere Punkte mit `NaN` auffüllen:")
                default_vals = (
                    [str(round(float(v), 2)) for v in np.random.uniform(0.1, 1.0, 15)]
                    + ["NaN"] * (expected_raw_dim - 15)
                )
                u_input = st.text_area("Eingabevektor:", value=", ".join(default_vals), height=100)

                try:
                    parsed = []
                    for item in (x.strip() for x in u_input.split(",") if x.strip()):
                        parsed.append(np.nan if item.lower() in ("nan", "x") else float(item))

                    if len(parsed) == expected_raw_dim:
                        if st.button("Vorhersage berechnen", width="stretch"):
                            st.session_state.current_test_vector = np.array(parsed, dtype=np.float32).tolist()
                            st.session_state.current_soll = None
                            st.rerun()
                    else:
                        st.caption(f"Benötigt: {expected_raw_dim} Werte – aktuell eingegeben: {len(parsed)}")
                except Exception as e:
                    debug_error("Manuelle Eingabe konnte nicht verarbeitet werden.", e)
                    st.error(f"Ungültige Eingabe: {e}")

        # ===================================================================
        # LINKE SPALTE: Ergebnis & 3D-Visualisierung
        # ===================================================================
        with col_left:
            st.markdown("<h4 style='margin-top:0; color:#444;'>Ergebnis & 3D-Ansicht</h4>", unsafe_allow_html=True)

            if prediction_raw is not None and test_vector is not None and norm_vector is not None:
                col_metric1, col_metric2 = st.columns([3, 2])
                with col_metric1:
                    if final_class == 1:
                        st.success("Pyramide erkannt")
                    else:
                        st.info("Keine Pyramide erkannt")
                with col_metric2:
                    st.metric("Modell-Konfidenz", f"{prediction_raw * 100:.2f} %")

                with st.expander("Technische Details"):
                    if "Zufälliges" in modus and soll_ergebnis is not None:
                        st.caption(f"Erwartetes Ergebnis (Soll): {int(soll_ergebnis)}")
                    feature_preview = [
                        f"Merkmal_{i}: {val:.2f}" if not np.isnan(val) else "Merkmal: NaN"
                        for i, val in enumerate(norm_vector[:15])
                    ]
                    st.caption(", ".join(feature_preview) + " ...")

                # --- 3D-Darstellung ---
                n_pts   = st.session_state.input_handler.max_vertices
                n_coord = st.session_state.input_handler.coordinates_per_vertex
                geometrie = test_vector[:n_pts * n_coord].reshape(-1, n_coord)
                gültige   = geometrie[~np.isnan(geometrie).any(axis=1)]

                if len(gültige) >= 3:
                    x_k, y_k, z_k = gültige[:, 0], gültige[:, 1], gültige[:, 2]
                    mesh_color = "#1f77b4" if final_class == 1 else "#bcbd22"

                    fig_3d = go.Figure()
                    if len(gültige) <= 300:
                        fig_3d.add_trace(go.Mesh3d(
                            x=x_k, y=y_k, z=z_k,
                            opacity=0.35, color=mesh_color, name="Körper", alphahull=0,
                        ))
                    fig_3d.add_trace(go.Scatter3d(
                        x=x_k, y=y_k, z=z_k,
                        mode="markers",
                        marker=dict(size=5, color="#d62728", opacity=0.8),
                        name="Eckpunkte",
                    ))
                    fig_3d.update_layout(
                        scene=dict(
                            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
                            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
                            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
                        ),
                        margin=dict(l=0, r=0, b=0, t=0),
                        height=400,
                    )
                    st.plotly_chart(fig_3d, width="stretch")
                else:
                    st.info("Zu wenige gültige Punkte für die 3D-Darstellung (mind. 3 erforderlich).")
            else:
                st.info("Objekt generieren oder Koordinaten eingeben, um die Analyse zu starten.")