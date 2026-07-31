"""
Streamlit Web UI for Pyramid Classification.
Imports core logic from nn.py, pyramid_generator.py, dynamic_input.py.
"""

import json
import logging
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

from dynamic_input import DynamicInputHandler
from nn import NeuralNet, TrainConfig
from pyramid_generator import PyramidGenerator

# ---------------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
icon_image = Image.open(icon_path)

st.set_page_config(
    page_title="Pyramid Classification",
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

st.markdown("<h1>Pyramid Classification</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Neural network for pyramid detection | Informatics Project</p>", unsafe_allow_html=True)
st.markdown("---")


# ---------------------------------------------------------------------------
# SESSION STATE DEFAULTS
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "pyramid_generator":      lambda: PyramidGenerator(seed=42),
    "input_handler":          lambda: DynamicInputHandler(max_vertices=12, coordinates_per_vertex=3),
    "model":                  None,
    "total_training_count":   0,
    "train_losses":           [],
    "test_losses":            [],
    "last_validation_result": None,
    "current_test_vector":    None,
    "expected_label":         None,
    "ui_object_type":         "perfect",
    # NOTE: "ui_max_vertices" is deliberately NOT pre-set here. It is the key of
    # the st.number_input widget below; pre-assigning it via the Session State
    # API triggers Streamlit's warning "The widget with key ... was created with
    # a default value but also had its value set via the Session State API."
}

for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default() if callable(default) else default

# Apply a pending vertex-count change (e.g. detected via CSV import) before the
# widget with key "ui_max_vertices" is instantiated. Streamlit only allows
# assigning to a widget-backed key *before* the widget is created in the run.
_ui_max_vertices_api_set = False
if "ui_max_vertices_pending" in st.session_state:
    st.session_state.ui_max_vertices = st.session_state.pop("ui_max_vertices_pending")
    _ui_max_vertices_api_set = True


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------
def _load_model_from_json(data: dict) -> NeuralNet:
    """Load NeuralNet from JSON dict (already parsed)."""
    required_keys = ["W1", "b1", "W2", "b2", "config"]
    if not all(k in data for k in required_keys):
        raise ValueError("Invalid model file: missing required keys")
    cfg = data["config"]
    return NeuralNet(
        input_size=int(cfg["input_size"]),
        hidden_size=int(cfg["hidden_size"]),
        W1=np.array(data["W1"], dtype=np.float32),
        b1=np.array(data["b1"], dtype=np.float32),
        W2=np.array(data["W2"], dtype=np.float32),
        b2=np.array(data["b2"], dtype=np.float32),
    )


def _export_model_json(net: NeuralNet, norm_params: dict) -> dict:
    """Create export dict from NeuralNet + normalization params."""
    return {
        "W1": net.W1.tolist(), "b1": net.b1.tolist(),
        "W2": net.W2.tolist(), "b2": net.b2.tolist(),
        "config": {"input_size": net.input_size, "hidden_size": net.hidden_size},
        "stats": {
            "total_epochs": int(st.session_state.total_training_count),
            "last_loss":    float(st.session_state.test_losses[-1]) if st.session_state.test_losses else 0.0,
            "validation":   st.session_state.last_validation_result or "",
        },
        "normalization_params": norm_params,
    }


def _format_epochs(n: int) -> str:
    return f"{n:,}".replace(",", ".")


# ---------------------------------------------------------------------------
# SIDEBAR: MODEL MANAGEMENT
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='font-size: 1.6rem;'>Model Center</h2>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("**Import JSON model**")
    uploaded_file = st.file_uploader(
        "Select file",
        type="json",
        key="json_uploader_unique",
        label_visibility="collapsed",
    )

    if uploaded_file:
        try:
            if "last_loaded_file" not in st.session_state or st.session_state.last_loaded_file != uploaded_file.name:
                uploaded_file.seek(0)
                data = json.loads(uploaded_file.read().decode("utf-8"))

                net = _load_model_from_json(data)
                st.session_state.model = net

                stats = data.get("stats", {})
                st.session_state.total_training_count = int(stats.get("total_epochs", 0))
                last_loss = stats.get("last_loss", 0.0)
                st.session_state.train_losses = [float(last_loss)] if last_loss else []
                st.session_state.test_losses  = [float(last_loss)] if last_loss else []
                st.session_state.last_validation_result = stats.get("validation", "Not validated")

                if "normalization_params" in data:
                    st.session_state.input_handler.set_params(data["normalization_params"])

                st.session_state.last_loaded_file = uploaded_file.name
                st.success("[System] Model parameters loaded successfully.")
                st.rerun()
        except Exception as e:
            log.exception("JSON import failed")
            st.error(f"[Import Error] Invalid file contents: {str(e)[:50]}")

    st.markdown("---")

    if st.session_state.model is not None:
        net: NeuralNet = st.session_state.model

        st.markdown("<h3 style='font-size: 1.2rem;'>Architecture</h3>", unsafe_allow_html=True)
        col_a1, col_a2 = st.columns(2)
        col_a1.metric("Input Nodes",  str(net.input_size))
        col_a2.metric("Hidden Nodes", str(net.hidden_size))

        st.markdown("---")
        st.markdown("<h3 style='font-size: 1.2rem;'>Status & Validation</h3>", unsafe_allow_html=True)

        col_x, col_y = st.columns(2)
        col_x.metric("Epochs", _format_epochs(st.session_state.total_training_count))
        col_y.metric(
            "Loss",
            f"{st.session_state.test_losses[-1]:.5f}" if st.session_state.test_losses else "—",
        )

        val_status = st.session_state.last_validation_result
        if val_status:
            keywords_ok = ("successful", "perfect", "verified")
            if any(kw in val_status.lower() for kw in keywords_ok):
                st.success(val_status)
            else:
                st.warning(val_status)

        st.markdown("---")
        st.markdown("<h3 style='font-size: 1.2rem;'>Exports & Reports</h3>", unsafe_allow_html=True)

        export_data = _export_model_json(net, st.session_state.input_handler.normalization_params)

        st.download_button(
            label="Download JSON (weights)",
            data=json.dumps(export_data, indent=2),
            file_name=f"model_weights_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width="stretch",
        )

        w1_rounded = np.round(net.W1, 3)
        w2_rounded = np.round(net.W2.T, 3)

        markdown_report = (
            f"# Model Report: AI Pyramid Classification\n\n"
            f"## 1. System & Metadata\n\n"
            f"| Parameter | Value |\n"
            f"| :--- | :--- |\n"
            f"| Creation date | {datetime.now(timezone.utc).strftime('%d.%m.%Y, %H:%M:%S')} |\n"
            f"| Validation status | {st.session_state.last_validation_result} |\n\n"
            f"## 2. Network Topology (Architecture)\n\n"
            f"| Layer | Neurons | Activation |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Input layer** | {net.input_size} | Identity |\n"
            f"| **Hidden layer** | {net.hidden_size} | ReLU |\n"
            f"| **Output layer** | 1 | Sigmoid |\n\n"
            f"## 3. Training Metrics\n\n"
            f"| Metric | Value |\n"
            f"| :--- | :--- |\n"
            f"| Total epochs completed | {_format_epochs(st.session_state.total_training_count)} |\n"
            f"| Final error value (MSE loss) | {export_data['stats']['last_loss']:.6f} |\n\n"
            f"## 4. Mathematical Parameters\n\n"
            f"### 4.1 Layer 1: Input → Hidden (`W1`)\n"
            f"```text\n{np.array2string(w1_rounded, max_line_width=120)}\n```\n\n"
            f"### 4.2 Layer 2: Hidden → Output (`W2`)\n"
            f"```text\n{np.array2string(w2_rounded, max_line_width=120)}\n```\n"
        )

        st.download_button(
            label="Download Markdown Report (.md)",
            data=markdown_report,
            file_name=f"model_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            width="stretch",
        )
    else:
        st.info("System awaiting model initialization. Generate training data or load an existing JSON model.")


# ---------------------------------------------------------------------------
# MAIN TABS
# ---------------------------------------------------------------------------
tab_data, tab_training, tab_test = st.tabs([
    "Data Center",
    "Training & Validation",
    "Interactive Test (3D)",
])


# ---------------------------------------------------------------------------
# TAB 1: DATASET MANAGEMENT
# ---------------------------------------------------------------------------
with tab_data:
    st.markdown("<h2 style='font-size: 1.5rem;'>Training Data Management</h2>", unsafe_allow_html=True)

    st.markdown("###### Set the maximum vertex count")
    st.markdown(
        "> **Note on data structure:** All objects are padded to the same length. "
        "If an object has fewer vertices than the maximum, the missing slots are automatically "
        "filled with `NaN` – this keeps the difference from real points at the origin (0, 0, 0) intact."
    )

    c_geo1, _ = st.columns(2)
    with c_geo1:
        # If the value was just set through the Session State API (CSV import),
        # pass no widget default to avoid Streamlit's widget-duplication warning.
        # Otherwise the widget keeps its own persisted value (default 12 on the
        # very first run).
        max_vertices = st.number_input(
            "Maximum number of vertices",
            min_value=5,
            value=None if _ui_max_vertices_api_set else st.session_state.get("ui_max_vertices", 12),
            step=1,
            key="ui_max_vertices",
        )
        if max_vertices is None:
            max_vertices = 12

    coords_per_vertex = 3

    # Sync handler if UI setting changed. The widget key "ui_max_vertices"
    # already holds the widget's current value in session state, so it must
    # NOT be assigned here (Streamlit forbids it after widget instantiation).
    if st.session_state.input_handler.max_vertices != max_vertices:
        st.session_state.input_handler = DynamicInputHandler(
            max_vertices=max_vertices,
            coordinates_per_vertex=coords_per_vertex,
        )

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Variant A: Generate synthetic dataset**")
        n_pyramids     = st.number_input("Number of pyramids",     min_value=10, value=100, step=10)
        n_non_pyramids = st.number_input("Number of other shapes", min_value=10, value=100, step=10)

        if st.button("Create dataset", width="stretch", key="gen_btn"):
            with st.spinner("Computing geometry matrices..."):
                data_matrix, _ = st.session_state.pyramid_generator.generate_dataset(
                    max_vertices=max_vertices,
                    coords_per_vertex=coords_per_vertex,
                    n_pyramids=int(n_pyramids),
                    n_non_pyramids=int(n_non_pyramids),
                    shuffle=True,
                )
                st.session_state.data = data_matrix.astype(np.float32)
                log.info("Synthetic training dataset generated.")
                st.success("Dataset loaded successfully.")
                st.rerun()

    with col2:
        st.markdown("**Variant B: Import CSV file**")
        uploaded = st.file_uploader("Select CSV file", type="csv")
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

                extra_features = 4
                calculated_features = uploaded_matrix.shape[1] - 1
                calculated_vertices = (calculated_features - extra_features) // coords_per_vertex

                if calculated_vertices >= 5:
                    st.session_state.input_handler = DynamicInputHandler(
                        max_vertices=calculated_vertices,
                        coordinates_per_vertex=coords_per_vertex,
                    )
                    # Update the widget on the next run: assigning to the
                    # widget-backed key is only allowed before the widget is
                    # instantiated (handled at the top of the script).
                    st.session_state.ui_max_vertices_pending = calculated_vertices

                st.success(f"CSV imported successfully ({calculated_vertices} vertices detected).")
                st.rerun()
            except Exception as e:
                log.exception("CSV import failed")
                st.error(f"Error reading the CSV file: {e}")

    if "data" in st.session_state:
        st.markdown("---")
        data = st.session_state.data
        pyr_rows   = data[data[:, -1] == 1.0]
        other_rows = data[data[:, -1] == 0.0]

        current_num_features = data.shape[1] - 1
        extra_features = 4
        current_vertices = (current_num_features - extra_features) // coords_per_vertex

        c1, c2, c3 = st.columns(3)
        c1.metric("Total samples",                    str(len(data)))
        c2.metric("Number of features (columns)",      str(current_num_features))
        c3.metric("Class distribution (Pyr / Other)", f"{len(pyr_rows)} / {len(other_rows)}")

        st.markdown("### Data preview (before normalization)")

        col_names: list = []
        feat_counter = 0
        for v in range(current_vertices):
            for c_idx in range(coords_per_vertex):
                if feat_counter < current_num_features:
                    axis = ["X", "Y", "Z"][c_idx % 3]
                    col_names.append(f"P{v + 1}_{axis}")
                    feat_counter += 1

        extra_labels = ["Height", "Balance", "Base area", "Centroid X"]
        for label in extra_labels:
            if len(col_names) < current_num_features:
                col_names.append(label)

        while len(col_names) < current_num_features:
            col_names.append(f"extra_feature_{len(col_names) + 1}")

        col_names.append("Class (label)")

        view_col1, view_col2 = st.columns(2)
        with view_col1:
            st.markdown("**▪ Class 1 – Pyramids (preview)**")
            if len(pyr_rows) > 0:
                st.dataframe(pd.DataFrame(pyr_rows[:5], columns=col_names).style.format(precision=3, na_rep="NaN"), width="stretch")
            else:
                st.info("No pyramids in the current dataset.")

        with view_col2:
            st.markdown("**▪ Class 0 – Other shapes (preview)**")
            if len(other_rows) > 0:
                st.dataframe(pd.DataFrame(other_rows[:5], columns=col_names).style.format(precision=3, na_rep="NaN"), width="stretch")
            else:
                st.info("No other shapes in the current dataset.")


# ---------------------------------------------------------------------------
# TAB 2: MODEL TRAINING
# ---------------------------------------------------------------------------
with tab_training:
    st.markdown("<h2 style='font-size: 1.5rem;'>Train Model</h2>", unsafe_allow_html=True)

    # Determine input size from data or estimate
    if "data" in st.session_state:
        try:
            raw_features_only = st.session_state.data[:, :-1]
            detected_inputs = st.session_state.input_handler._transform_to_distances(raw_features_only).shape[1]
        except (ValueError, IndexError, AttributeError):
            detected_inputs = st.session_state.data.shape[1] - 1
    else:
        detected_inputs = (max_vertices * (max_vertices - 1)) // 2

    col1, col2, col3 = st.columns(3)
    with col1:
        input_size = st.number_input("Input Nodes ", value=int(detected_inputs), step=1, disabled=True)
    with col2:
        hidden_size = st.number_input("Hidden Nodes", value=32, step=1)
    with col3:
        learning_rate = st.slider("Learning rate", 0.001, 1.0, 0.1)

    epochs = st.number_input("Number of epochs", value=1000, step=100)

    # Check if existing model matches architecture → continue training possible
    can_continue = (
        st.session_state.model is not None
        and st.session_state.model.input_size  == input_size
        and st.session_state.model.hidden_size == hidden_size
    )

    if can_continue:
        train_mode = st.radio(
            "Training mode:",
            ["Continue training existing model", "Start fresh (reset weights)"],
            horizontal=True,
        )
    else:
        st.info("New architecture detected or no model loaded – weights will be reinitialized.")
        train_mode = "Start fresh (reset weights)"

    if st.button("Start Training", width="stretch"):
        if "data" not in st.session_state:
            st.error("Please load or create data first (tab: Data Center).")
        else:
            try:
                raw_data = st.session_state.data
                data_prepared, _ = st.session_state.input_handler.filter_and_prepare(raw_data, fit=True)

                X_all = data_prepared[:, :-1]
                y_all = data_prepared[:, -1:]
                actual_input_size = X_all.shape[1]

                # Create or reuse NeuralNet
                if train_mode == "Continue training existing model":
                    assert st.session_state.model is not None
                    net = st.session_state.model
                    train_losses = list(st.session_state.train_losses)
                    test_losses  = list(st.session_state.test_losses)
                else:
                    net = NeuralNet(input_size=actual_input_size, hidden_size=hidden_size, seed=42)
                    train_losses = []
                    test_losses  = []
                    st.session_state.total_training_count = 0

                config = TrainConfig(
                    epochs=int(epochs),
                    learning_rate=learning_rate,
                    val_split=0.2,
                    seed=42,
                )

                progress_bar = st.progress(0)
                status_text  = st.empty()

                # Custom training loop with UI updates (using shared train_step)
                n_train = int(len(X_all) * 0.8)
                X_train = X_all[:n_train]
                y_train = y_all[:n_train]
                X_val   = X_all[n_train:]
                y_val   = y_all[n_train:]
                X_train_T = X_train.T

                # Initialize to avoid unbound variable errors
                loss = 0.0
                val_loss = 0.0

                for epoch in range(config.epochs):
                    loss = net.train_step(X_train, y_train, config.learning_rate)
                    train_losses.append(loss)

                    val_loss = net.loss(X_val, y_val)
                    test_losses.append(val_loss)

                    if epoch % 50 == 0:
                        progress_bar.progress(epoch / config.epochs)
                        status_text.text(
                            f"Epoch {epoch}/{config.epochs} "
                            f"| Train Loss: {loss:.5f} | Val Loss: {val_loss:.5f}"
                        )

                progress_bar.progress(1.0)
                status_text.text("Training complete.")

                validation_msg = f"Model successfully trained on {actual_input_size} features."
                st.session_state.last_validation_result = validation_msg
                st.success(validation_msg)

                st.session_state.model = net
                st.session_state.train_losses = train_losses
                st.session_state.test_losses  = test_losses
                st.session_state.total_training_count += config.epochs

                log.info("Training completed", extra={
                    "lr": learning_rate,
                    "epochs": config.epochs,
                    "total_epochs": st.session_state.total_training_count,
                    "train_loss": loss,
                    "val_loss": val_loss,
                    "input_size": actual_input_size,
                })
                st.rerun()

            except Exception as e:
                log.exception("Training failed")
                st.error(f"Error during training: {e}")

    # Loss curves
    if st.session_state.model and st.session_state.train_losses:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=st.session_state.train_losses,
            name="Training error (Train Loss)",
            line=dict(color="#1f77b4", width=2),  # noqa: C408
        ))
        if st.session_state.test_losses:
            fig.add_trace(go.Scatter(
                y=st.session_state.test_losses,
                name="Validation error (Val Loss)",
                line=dict(color="#ff9f43", width=2),  # noqa: C408
            ))
        fig.update_layout(
            xaxis_title="Epoch",
            yaxis_title="Error (MSE)",
            template="plotly_white",
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),  # noqa: C408
        )
        st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# TAB 3: INTERACTIVE 3D TEST
# ---------------------------------------------------------------------------
with tab_test:
    st.markdown("<h2 style='font-size: 1.5rem; margin-bottom: 1.5rem;'>Interactive 3D Geometry Test</h2>", unsafe_allow_html=True)

    if st.session_state.model is None:
        st.warning("No model loaded. Please train or import a model first.")
    else:
        model: NeuralNet = st.session_state.model
        current_input_dim = model.input_size
        expected_raw_dim  = (
            st.session_state.input_handler.max_vertices
            * st.session_state.input_handler.coordinates_per_vertex
        )

        test_vector    = None
        expected_label = None
        prediction_raw = None
        final_class    = None
        norm_vector    = None

        if st.session_state.current_test_vector is not None:
            test_vector    = np.array(st.session_state.current_test_vector, dtype=np.float32)
            expected_label = st.session_state.expected_label

        if test_vector is not None:
            # Dummy label for filter_and_prepare
            prep_matrix = np.zeros((1, len(test_vector) + 1), dtype=np.float32)
            prep_matrix[0, :len(test_vector)] = test_vector

            # Ensure normalization params exist
            if not st.session_state.input_handler.normalization_params and "data" in st.session_state:
                st.session_state.input_handler.filter_and_prepare(st.session_state.data, fit=True)

            try:
                norm_matrix, _ = st.session_state.input_handler.filter_and_prepare(prep_matrix, fit=False)
                norm_vector = norm_matrix[0, :-1]

                if len(norm_vector) == current_input_dim:
                    X_input = norm_vector.reshape(1, -1)
                    prediction_raw = float(model.forward(X_input)[0, 0])
                    final_class = 1 if prediction_raw >= 0.5 else 0
                else:
                    st.error(
                        f"Architecture conflict: input has {len(norm_vector)} features, "
                        f"model expects {current_input_dim}."
                    )
            except Exception as e:
                log.exception("Test vector preparation failed")
                st.error(f"Error preparing data: {e}")

        col_left, col_right = st.columns([1, 1], gap="large")

        # RIGHT COLUMN: Input & Generation
        with col_right:
            st.markdown("<h4 style='margin-top:0; color:#444;'>Input & Object Generation</h4>", unsafe_allow_html=True)
            input_mode = st.radio(
                "Input method:",
                ["Generate random object (recommended)", "Enter coordinates manually"],
            )

            if "Generate random" in input_mode:
                st.write("Select object type:")
                c_btn1, c_btn2 = st.columns(2)

                with c_btn1:
                    is_p = st.session_state.ui_object_type == "perfect"
                    if st.button("Pyramid (expected = 1)", type="primary" if is_p else "secondary", width="stretch"):
                        st.session_state.ui_object_type = "perfect"
                        st.rerun()
                with c_btn2:
                    is_a = st.session_state.ui_object_type == "alternative"
                    if st.button("Other shape (expected = 0)", type="primary" if is_a else "secondary", width="stretch"):
                        st.session_state.ui_object_type = "alternative"
                        st.rerun()

                if st.button("Generate & Analyze Object", width="stretch"):
                    is_pyramid = st.session_state.ui_object_type == "perfect"
                    gen = st.session_state.pyramid_generator
                    raw_vector = (
                        gen.generate_single_pyramid(st.session_state.ui_max_vertices, 3)
                        if is_pyramid
                        else gen.generate_single_non_pyramid(st.session_state.ui_max_vertices, 3)
                    )
                    st.session_state.current_test_vector = raw_vector.astype(np.float32).tolist()
                    st.session_state.expected_label = 1.0 if is_pyramid else 0.0
                    log.info("Single object generated for 3D test.")
                    st.rerun()

            else:
                st.markdown(f"Enter exactly `{expected_raw_dim}` numbers. Fill empty points with `NaN`:")
                default_vals = (
                    [str(round(float(v), 2)) for v in np.random.uniform(0.1, 1.0, 15)]
                    + ["NaN"] * (expected_raw_dim - 15)
                )
                u_input = st.text_area("Input vector:", value=", ".join(default_vals), height=100)

                try:
                    parsed = []
                    for item in (x.strip() for x in u_input.split(",") if x.strip()):
                        parsed.append(np.nan if item.lower() in ("nan", "x") else float(item))

                    if len(parsed) == expected_raw_dim:
                        if st.button("Compute Prediction", width="stretch"):
                            st.session_state.current_test_vector = np.array(parsed, dtype=np.float32).tolist()
                            st.session_state.expected_label = None
                            st.rerun()
                    else:
                        st.caption(f"Required: {expected_raw_dim} values – currently entered: {len(parsed)}")
                except Exception as e:
                    log.exception("Manual input parsing failed")
                    st.error(f"Invalid input: {e}")

        # LEFT COLUMN: Results & 3D Visualization
        with col_left:
            st.markdown("<h4 style='margin-top:0; color:#444;'>Result & 3D View</h4>", unsafe_allow_html=True)

            if prediction_raw is not None and test_vector is not None and norm_vector is not None:
                col_metric1, col_metric2 = st.columns([3, 2])
                with col_metric1:
                    if final_class == 1:
                        st.success("Pyramid detected")
                    else:
                        st.info("No pyramid detected")
                with col_metric2:
                    st.metric("Model Confidence", f"{prediction_raw * 100:.2f} %")

                with st.expander("Technical Details"):
                    if "Generate random" in input_mode and expected_label is not None:
                        st.caption(f"Expected result: {int(expected_label)}")
                    feature_preview = [
                        f"Feature_{i}: {val:.2f}" if not np.isnan(val) else "Feature: NaN"
                        for i, val in enumerate(norm_vector[:15])
                    ]
                    st.caption(", ".join(feature_preview) + " ...")

                # 3D Visualization
                n_pts   = st.session_state.input_handler.max_vertices
                n_coord = st.session_state.input_handler.coordinates_per_vertex
                geometry = test_vector[:n_pts * n_coord].reshape(-1, n_coord)
                valid_points = geometry[~np.isnan(geometry).any(axis=1)]

                if len(valid_points) >= 3:
                    xs, ys, zs = valid_points[:, 0], valid_points[:, 1], valid_points[:, 2]
                    mesh_color = "#1f77b4" if final_class == 1 else "#bcbd22"

                    fig_3d = go.Figure()
                    if len(valid_points) <= 300:
                        fig_3d.add_trace(go.Mesh3d(
                            x=xs, y=ys, z=zs,
                            opacity=0.35, color=mesh_color, name="Surface", alphahull=0,
                        ))
                    fig_3d.add_trace(go.Scatter3d(
                        x=xs, y=ys, z=zs,
                        mode="markers",
                        marker=dict(size=5, color="#d62728", opacity=0.8),  # noqa: C408
                        name="Vertices",
                    ))
                    fig_3d.update_layout(
                        scene=dict(  # noqa: C408
                            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),  # noqa: C408
                            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),  # noqa: C408
                            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),  # noqa: C408
                        ),
                        margin=dict(l=0, r=0, b=0, t=0),  # noqa: C408
                        height=400,
                    )
                    st.plotly_chart(fig_3d, width="stretch")
                else:
                    st.info("Too few valid points for 3D rendering (at least 3 required).")
            else:
                st.info("Generate an object or enter coordinates to start the analysis.")