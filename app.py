r"""
STREAMLIT WEB UI FÜR NEURONALES NETZWERK - ERWEITERT
=====================================================
Web-Interface zur Konfiguration und zum Training eines neuronalen Netzwerks
für die binäre Klassifikation von 2D- und 3D-Objekten als Pyramiden.

NEU IN DIESER VERSION:
✓ Checkpoint-System: Speichern/Laden mit Fortsetzbarem Training
✓ Pyramiden-Generator: Prozeduraler Datengenerierung
✓ Dynamisches Input-System: Variable Eckpunkt-Anzahl mit intelligenter Filterung
✓ Training-Counter: Tracking der Gesamtzahl der Trainingsdurchgänge

Starten mit: .\.venv\Scripts\Activate.ps1
streamlit run app.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import json
import os
from datetime import datetime
import math
import random
import plotly.graph_objects as go

# Import neue Module
from checkpoint import CheckpointManager
from pyramid_generator import PyramidGenerator
from dynamic_input import DynamicInputHandler

# ================================================================================================
# SEITE KONFIGURATION & INITIALIZATION
# ================================================================================================

st.set_page_config(
    page_title="Pyramiden Klassifikation",
    page_icon="🔷",
    layout="wide"
)

st.markdown('<h1 class="main-title">Informatik-Projekt-August-Malte</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Neuronales Netz zur Erkennung von Pyramiden</p>', unsafe_allow_html=True)

# Initialisiere Manager
if "checkpoint_manager" not in st.session_state:
    st.session_state.checkpoint_manager = CheckpointManager()
    st.session_state.pyramid_generator = PyramidGenerator(seed=42)
    st.session_state.input_handler = DynamicInputHandler(max_vertices=12, coordinates_per_vertex=3)
    
    # Initialisiere Training-Counter
    if "total_training_count" not in st.session_state:
        st.session_state.total_training_count = 0

# ================================================================================================
# TABS FÜR VERSCHIEDENE FUNKTIONALITÄTEN
# ================================================================================================

tab_config, tab_data, tab_training, tab_checkpoint, tab_predict = st.tabs([
    "Konfiguration",
    "Trainingsdaten",
    "Training",
    "Checkpoints",
    "Vorhersagen"
])


# ================================================================================================
# TAB 1: KONFIGURATION
# ================================================================================================

with tab_config:
    st.header("Netzwerk-Konfiguration")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Netzwerk-Architektur")
        
        input_size = st.number_input(
            "Input-Größe (Anzahl der Koordinaten)",
            min_value=2,
            max_value=100,
            value=19,
            help="Für Pyramiden: 4 Punkte × 3 Koordinaten + Features = 15-19"
        )
        
        hidden_size = st.number_input(
            "Hidden Layer - Größe",
            min_value=2,
            max_value=1000,
            value=32,
            help="Anzahl der Neuronen im Hidden Layer"
        )
    
    with col2:
        st.subheader("Trainings-Parameter")
        
        learning_rate = st.slider(
            "Learning Rate (Lambda)",
            min_value=0.001,
            max_value=1.0,
            value=0.1,
            step=0.01,
            help="Schrittgröße für Gewichtsaktualisierung"
        )
        
        epochs = st.number_input(
            "Epochen (Trainings-Iterationen)",
            min_value=1,
            max_value=10000,
            value=500,
            help="Wie oft das Modell alle Trainingsdaten durchläuft"
        )
    
    col3, col4 = st.columns(2)
    
    with col3:
        batch_size = st.number_input(
            "Batch-Größe",
            min_value=1,
            max_value=100,
            value=4,
            help="Wie viele Samples pro Update"
        )
        
        test_split = st.slider(
            "Test-Daten Anteil",
            min_value=0.1,
            max_value=0.5,
            value=0.2,
            help="Anteil der Daten für Test"
        )
    
    with col4:
        bias = st.slider(
            "Bias-Wert",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            help="Bias für Hidden Layer Neuronen"
        )
        
        normalize = st.checkbox(
            "Normalisierung aktivieren",
            value=True,
            help="Normalisiere Input-Daten auf [0,1]"
        )
    
    # Speichere in Session State
    st.session_state.config = {
        "input_size": input_size,
        "hidden_size": hidden_size,
        "learning_rate": learning_rate,
        "epochs": epochs,
        "batch_size": batch_size,
        "test_split": test_split,
        "bias": bias,
        "normalize": normalize
    }
    
    st.success("✓ Konfiguration aktualisiert")


# ================================================================================================
# TAB 2: TRAININGSDATEN
# ================================================================================================

with tab_data:
    st.header("Trainingsdaten Management")
    st.markdown("---")
    
    data_source = st.radio(
        "Datenquelle wählen",
        ["Pyramiden-Generator (PROZEDURAL)", "CSV-Datei hochladen", "Sample-Daten"],
        help="Wie sollen die Trainingsdaten generiert werden?"
    )
    
    st.markdown("---")
    
    data = None
    data_metadata = None
    
    if data_source == "Pyramiden-Generator (PROZEDURAL)":
        st.subheader("Pyramiden-Generator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            n_pyramids = st.number_input(
                "Anzahl der Pyramiden",
                min_value=10,
                max_value=1000,
                value=100,
                help="Wie viele Pyramiden generieren?"
            )
        
        with col2:
            n_non_pyramids = st.number_input(
                "Anzahl der Non-Pyramids",
                min_value=10,
                max_value=1000,
                value=100,
                help="Wie viele andere Formen?"
            )
        
        use_variable_size = st.checkbox(
            "Variable Eckpunkt-Anzahl",
            value=False,
            help="Feature 4: Unterschiedliche Vertex-Anzahl pro Sample"
        )
        
        if st.button("Daten generieren", use_container_width=True):
            with st.spinner("Generiere Pyramiden..."):
                gen = st.session_state.pyramid_generator
                
                if use_variable_size:
                    data, data_metadata = gen.generate_dataset_variable_size(
                        n_samples=n_pyramids + n_non_pyramids,
                        min_vertices=4,
                        max_vertices=8,
                        shuffle=True
                    )
                    st.info(f"✓ {len(data)} Samples mit variabler Größe generiert")
                else:
                    data, data_metadata = gen.generate_dataset(
                        n_pyramids=n_pyramids,
                        n_non_pyramids=n_non_pyramids,
                        shuffle=True
                    )
                    st.info(f"✓ {len(data)} Samples generiert")
                
                st.session_state.data = data
                st.session_state.data_metadata = data_metadata
    
    elif data_source == "CSV-Datei hochladen":
        st.subheader("CSV-Upload")
        
        uploaded_file = st.file_uploader(
            "CSV-Datei hochladen (Format: features..., label)",
            type="csv"
        )
        
        if uploaded_file is not None:
            try:
                data = np.loadtxt(uploaded_file, delimiter=",")
                st.success(f"✓ Datei geladen: {data.shape[0]} Samples, {data.shape[1]-1} Features")
                st.session_state.data = data
            except Exception as e:
                st.error(f"❌ Fehler beim Laden: {e}")
    
    else:  # Sample-Daten
        st.subheader("Sample-Daten")
        
        sample_pyramids = [
            [1.0, 1.0, 1.0, 0.0] * 5,  # 20 Features
            [0.9, 0.95, 0.95, 0.05] * 5,
            [1.1, 1.05, 1.05, -0.05] * 5,
            [0.85, 0.9, 1.1, 0.1] * 5,
            [1.15, 1.1, 0.9, -0.1] * 5,
        ]
        sample_cubes = [
            [0.5, 0.5, 0.5, 0.5] * 5,  # 20 Features
            [0.55, 0.5, 0.5, 0.5] * 5,
            [0.5, 0.55, 0.5, 0.5] * 5,
            [0.45, 0.5, 0.5, 0.5] * 5,
            [0.5, 0.45, 0.5, 0.5] * 5,
        ]
        
        data = []
        for pyramid in sample_pyramids:
            data.append(pyramid + [1])
        for cube in sample_cubes:
            data.append(cube + [0])
        
        data = np.array(data[:19])  # Nur 19 Features
        st.info("✓ Sample-Daten geladen")
        st.session_state.data = data
    
    # Zeige Daten-Statistik
    if "data" in st.session_state and st.session_state.data is not None:
        data = st.session_state.data
        
        if isinstance(data, list):  # Variable-Size
            st.subheader("Daten-Statistik (Variable-Size)")
            st.metric("Gesamte Samples", len(data))
            st.markdown(f"Größen-Range: {min(len(d) for d in data)} - {max(len(d) for d in data)} Features")
        else:
            st.subheader("Daten-Statistik")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Gesamt Samples", len(data))
            with col2:
                st.metric("Pyramiden (1)", int(data[:, -1].sum()))
            with col3:
                st.metric("Non-Pyramids (0)", len(data) - int(data[:, -1].sum()))
            with col4:
                st.metric("Features", data.shape[1] - 1)
            
            # Vorschau
            with st.expander("Vorschau Trainingsdaten"):
                df_preview = pd.DataFrame(data[:10])
                df_preview.columns = [f"F{i+1}" for i in range(data.shape[1]-1)] + ["Label"]
                st.dataframe(df_preview, use_container_width=True)


# ================================================================================================
# TAB 3: TRAINING
# ================================================================================================

with tab_training:
    st.header("Modell Training")
    st.markdown("---")
    
    # Training-Counter Anzeige
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Gesamtzahl Trainings-Durchgänge", st.session_state.total_training_count)
    with col2:
        if "model" in st.session_state:
            st.metric("✓ Modell Status", "Trainiert")
        else:
            st.metric("✓ Modell Status", "Neu")
    with col3:
        if "last_training_time" in st.session_state:
            st.metric("Letztes Training", st.session_state.last_training_time.strftime("%H:%M:%S"))
    with col4:
        if "current_loss" in st.session_state:
            st.metric("Aktueller Loss", f"{st.session_state.current_loss:.6f}")
    
    st.markdown("---")
    
    # Training Options
    col_train, col_load, col_clear = st.columns(3)
    
    with col_train:
        start_training = st.button("Training starten", use_container_width=True, key="train_btn")
    
    with col_load:
        load_checkpoint = st.button("Checkpoint laden", use_container_width=True, key="load_btn")
    
    with col_clear:
        reset_model = st.button("Modell zurücksetzen", use_container_width=True, key="reset_btn")
    
    st.markdown("")
    
    # Training durchführen
    if start_training:
        if "data" not in st.session_state or st.session_state.data is None:
            st.error("❌ Keine Trainingsdaten geladen!")
        else:
            config = st.session_state.config
            data = st.session_state.data
            
            # Für Variable-Size Daten: Konvertiere zu fixed-size
            if isinstance(data, list):
                # Nutze Dynamic Input Handler
                max_len = max(len(d) for d in data)
                data = np.array([
                    np.concatenate([d[:-1], [0] * (max_len - len(d) + 1), [d[-1]]])
                    for d in data
                ], dtype=np.float32)
            
            # Dynamisches Input-Handling
            input_handler = st.session_state.input_handler
            processed_data, data_info = input_handler.filter_and_prepare_network_input(
                data, 
                use_detected_active_features=True
            )
            
            # Aktualisiere Input-Größe basierend auf echten Features
            actual_input_size = data_info["active_feature_count"]
            
            st.info(f"ℹ{data_info['padding_feature_count']} Padding-Features erkannt und gefiltert")
            
            # Teile Daten auf
            n_samples = len(processed_data)
            n_test = int(n_samples * config["test_split"])
            n_train = n_samples - n_test
            
            indices = np.random.permutation(n_samples)
            train_indices = indices[:n_train]
            test_indices = indices[n_train:]
            
            train_data = processed_data[train_indices]
            test_data = processed_data[test_indices]
            
            st.info(f"Aufteilung: {n_train} Training | {n_test} Test")
            
            # Initialisiere Netzwerk
            np.random.seed(42)
            
            W1 = np.random.normal(0, 0.1, (actual_input_size, config["hidden_size"])).astype(np.float32)
            b1 = np.zeros((1, config["hidden_size"]), dtype=np.float32)
            W2 = np.random.normal(0, 0.1, (config["hidden_size"], 1)).astype(np.float32)
            b2 = np.zeros((1, 1), dtype=np.float32)
            
            train_errors = []
            test_errors = []
            
            # Progress Bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Training Loop
            for epoch in range(config["epochs"]):
                X_train = train_data[:, :-1].astype(np.float32)
                y_train = train_data[:, -1:].astype(np.float32)
                
                # Forward Pass
                z1 = X_train @ W1 + b1
                a1 = np.maximum(0, z1)  # ReLU
                z2 = a1 @ W2 + b2
                a2 = 1 / (1 + np.exp(-np.clip(z2, -500, 500)))  # Sigmoid
                
                train_loss = np.mean((a2 - y_train) ** 2)
                train_errors.append(train_loss)
                
                # Backpropagation
                dz2 = (a2 - y_train) * a2 * (1 - a2)
                dW2 = (a1.T @ dz2) / len(train_data) * config["learning_rate"]
                db2 = np.mean(dz2, axis=0, keepdims=True) * config["learning_rate"]
                
                da1 = dz2 @ W2.T
                dz1 = da1 * (z1 > 0)
                dW1 = (X_train.T @ dz1) / len(train_data) * config["learning_rate"]
                db1 = np.mean(dz1, axis=0, keepdims=True) * config["learning_rate"]
                
                W2 -= dW2
                b2 -= db2
                W1 -= dW1
                b1 -= db1
                
                # Test Error
                X_test = test_data[:, :-1].astype(np.float32)
                y_test = test_data[:, -1:].astype(np.float32)
                
                z1_test = X_test @ W1 + b1
                a1_test = np.maximum(0, z1_test)
                z2_test = a1_test @ W2 + b2
                a2_test = 1 / (1 + np.exp(-np.clip(z2_test, -500, 500)))
                
                test_loss = np.mean((a2_test - y_test) ** 2)
                test_errors.append(test_loss)
                
                # Update Progress
                if epoch % max(1, config["epochs"] // 20) == 0:
                    progress_bar.progress(min(epoch / config["epochs"], 1.0))
                    status_text.text(
                        f"Epoch {epoch}/{config['epochs']} | "
                        f"Train Loss: {train_loss:.4f} | "
                        f"Test Loss: {test_loss:.4f}"
                    )
            
            progress_bar.progress(1.0)
            status_text.text("✓ Training abgeschlossen!")
            
            # Speichere Model
            st.session_state.model = {
                "W1": W1, "b1": b1, "W2": W2, "b2": b2,
                "input_size": actual_input_size,
                "hidden_size": config["hidden_size"]
            }
            st.session_state.train_errors = train_errors
            st.session_state.test_errors = test_errors
            st.session_state.current_loss = test_errors[-1]
            st.session_state.last_training_time = datetime.now()
            st.session_state.total_training_count += 1
            st.session_state.data_info = data_info
            
            st.success(f"✓ Training abgeschlossen! (Gesamt-Durchgänge: {st.session_state.total_training_count})")
            st.rerun()
    
    if load_checkpoint:
        st.info("Checkpoint-Laden im Tab 'Checkpoints'")
    
    if reset_model:
        if "model" in st.session_state:
            del st.session_state.model
            del st.session_state.train_errors
            del st.session_state.test_errors
            st.session_state.total_training_count = 0
            st.success("✓ Modell zurückgesetzt")
            st.rerun()
    
    # Zeige Trainingsergebnisse
    if "model" in st.session_state and "train_errors" in st.session_state:
        st.markdown("---")
        st.subheader("Trainings-Ergebnisse")
        
        # Chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            y=st.session_state.train_errors,
            mode='lines',
            name='Training Loss',
            line=dict(color='#5DBE50', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            y=st.session_state.test_errors,
            mode='lines',
            name='Test Loss',
            line=dict(color='#BF616A', width=3)
        ))
        
        fig.update_layout(
            title="Fehler-Entwicklung (MSE)",
            xaxis_title="Epoche",
            yaxis_title="MSE Loss",
            hovermode="x unified",
            template="plotly_white",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Metriken
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Final Training Loss", f"{st.session_state.train_errors[-1]:.6f}")
        with col2:
            st.metric("Final Test Loss", f"{st.session_state.test_errors[-1]:.6f}")
        with col3:
            improvement = ((st.session_state.train_errors[0] - st.session_state.train_errors[-1]) / st.session_state.train_errors[0] * 100)
            st.metric("Verbesserung", f"{improvement:.1f}%")


# ================================================================================================
# TAB 4: CHECKPOINTS
# ================================================================================================

with tab_checkpoint:
    st.header("Checkpoint Management")
    st.markdown("---")
    
    checkpoint_manager = st.session_state.checkpoint_manager
    
    col_save, col_load, col_list = st.columns(3)
    
    with col_save:
        save_checkpoint = st.button("Checkpoint speichern", use_container_width=True)
    
    with col_load:
        load_checkpoint_btn = st.button("Checkpoint laden", use_container_width=True)
    
    with col_list:
        refresh_list = st.button("Liste aktualisieren", use_container_width=True)
    
    st.markdown("")
    
    # Checkpoint speichern
    if save_checkpoint:
        if "model" not in st.session_state:
            st.error("❌ Kein trainiertes Modell vorhanden!")
        else:
            checkpoint_name = st.text_input("Checkpoint-Name (optional):")
            
            if st.button("✓ Speichern bestätigen"):
                model_state = st.session_state.model
                
                training_stats = {
                    "total_training_count": st.session_state.total_training_count,
                    "train_errors": st.session_state.train_errors,
                    "test_errors": st.session_state.test_errors,
                    "last_epoch": len(st.session_state.train_errors),
                    "normalization_params": st.session_state.data_info.get("normalization_params", {})
                }
                
                config = {
                    "input_size": st.session_state.model["input_size"],
                    "hidden_size": st.session_state.model["hidden_size"],
                    "learning_rate": st.session_state.config["learning_rate"],
                    "description": checkpoint_name or "No description"
                }
                
                filename = f"checkpoint_{checkpoint_name or 'auto'}.npz" if checkpoint_name else None
                
                try:
                    filepath = checkpoint_manager.save_checkpoint(
                        model_state,
                        training_stats,
                        config,
                        filename
                    )
                    st.success(f"✓ Checkpoint gespeichert: {os.path.basename(filepath)}")
                except Exception as e:
                    st.error(f"❌ Fehler beim Speichern: {e}")
    
    # Checkpoint laden
    st.markdown("---")
    st.subheader("Verfügbare Checkpoints")
    
    checkpoints = checkpoint_manager.list_checkpoints()
    
    if not checkpoints:
        st.info("Noch keine Checkpoints gespeichert")
    else:
        for idx, ckpt in enumerate(checkpoints):
            with st.expander(f"{ckpt['filename']} | Training-Count: {ckpt['total_training_count']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Timestamp:** {ckpt['timestamp']}")
                    st.write(f"**Config:**")
                    st.write(f"  - Input: {ckpt['config'].get('input_size')}")
                    st.write(f"  - Hidden: {ckpt['config'].get('hidden_size')}")
                    st.write(f"  - LR: {ckpt['config'].get('learning_rate')}")
                
                with col2:
                    st.write(f"**Training Stats:**")
                    st.write(f"  - Total Durchgänge: {ckpt['total_training_count']}")
                    st.write(f"  - Final Train Loss: {ckpt['final_train_loss']:.6f}")
                    st.write(f"  - Final Test Loss: {ckpt['final_test_loss']:.6f}")
                
                col_load_ckpt, col_delete_ckpt = st.columns(2)
                
                with col_load_ckpt:
                    if st.button(f"Laden", key=f"load_{idx}"):
                        try:
                            model_state, training_stats, config = checkpoint_manager.load_checkpoint(
                                ckpt['filename']
                            )
                            
                            st.session_state.model = model_state
                            st.session_state.model["input_size"] = config.get("input_size", 19)
                            st.session_state.model["hidden_size"] = config.get("hidden_size", 32)
                            st.session_state.total_training_count = training_stats.get("total_training_count", 0)
                            st.session_state.last_training_time = datetime.fromisoformat(ckpt['timestamp'])
                            st.session_state.current_loss = training_stats.get("final_test_loss", 0.0)
                            
                            st.success("✓ Checkpoint geladen und Modell wiederhergestellt!")
                            st.info(f"Training-Counter: {st.session_state.total_training_count}")
                            
                        except Exception as e:
                            st.error(f"❌ Fehler beim Laden: {e}")
                
                with col_delete_ckpt:
                    if st.button(f"Löschen", key=f"delete_{idx}"):
                        checkpoint_manager.delete_checkpoint(ckpt['filename'])
                        st.success("✓ Checkpoint gelöscht")
                        st.rerun()


# ================================================================================================
# TAB 5: VORHERSAGEN
# ================================================================================================

with tab_predict:
    st.header("Vorhersagen")
    st.markdown("---")
    
    if "model" not in st.session_state:
        st.warning("Bitte trainieren Sie zunächst ein Modell!")
    else:
        st.subheader("Neue Eingabe testen")
        
        model = st.session_state.model
        input_size = model["input_size"]
        
        # Input-Felder
        col_inputs = st.columns(min(5, input_size))
        new_input = []
        
        for i in range(input_size):
            with col_inputs[i % 5]:
                val = st.number_input(
                    f"Feature {i+1}",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05,
                    key=f"predict_input_{i}"
                )
                new_input.append(val)
        
        st.markdown("")
        
        if st.button("Vorhersage machen", use_container_width=True):
            X_pred = np.array(new_input, dtype=np.float32).reshape(1, -1)
            
            # Forward Pass
            z1 = X_pred @ model["W1"] + model["b1"]
            a1 = np.maximum(0, z1)
            z2 = a1 @ model["W2"] + model["b2"]
            a2 = 1 / (1 + np.exp(-np.clip(z2, -500, 500)))
            
            prediction = a2[0, 0]
            is_pyramid = prediction > 0.5
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Progress-Bar für Konfidenz
                st.metric("Konfidenz", f"{prediction*100:.1f}%")
                st.progress(float(prediction))
            
            with col2:
                if is_pyramid:
                    st.success("✓ PYRAMIDE erkannt")
                else:
                    st.info("✗ Keine Pyramide")


# ================================================================================================
# FOOTER
# ================================================================================================

st.markdown("---")

col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.caption("**Neuronales Netz Konfiguration:**")
    st.caption(f"Input: {st.session_state.config.get('input_size', '?')} | Hidden: {st.session_state.config.get('hidden_size', '?')} | Output: 1")

with col_info2:
    st.caption("**Training Stats:**")
    st.caption(f"Gesamtzahl Durchgänge: {st.session_state.total_training_count}")


