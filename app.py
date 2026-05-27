"""
PYRAMIDEN-KLASSIFIKATION - TRAININGSANWENDUNG
==============================================

Neuronales Netz zur Klassifikation: Pyramiden (1) vs. Andere (0)

STRUKTUR:
1. Trainingsdaten: Datengenerierung oder Upload
2. Training: Modell trainieren mit konfigurierbaren Parametern
3. Checkpoints: Modelle speichern/laden
4. Stats: Modell-Info, Export/Import

Starten: einfach steup_and_run.py ausführen, dann öffnet sich die Streamlit-App im Browser.
"""

import streamlit as st
import numpy as np
import os
import json
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from checkpoint import CheckpointManager
from pyramid_generator import PyramidGenerator
from dynamic_input import DynamicInputHandler


st.set_page_config(
    page_title="Pyramiden-Klassifikation",
    layout="wide"
)

st.markdown("# Pyramiden-Klassifikation")
st.markdown("Neuronales Netz zur Erkennung von Pyramiden | Informatik-Projekt")
st.markdown("---")

# Session State Initialisierung
if "checkpoint_manager" not in st.session_state:
    st.session_state.checkpoint_manager = CheckpointManager()
    st.session_state.pyramid_generator = PyramidGenerator(seed=42)
    st.session_state.input_handler = DynamicInputHandler()
    st.session_state.total_training_count = 0


tab_data, tab_training, tab_checkpoint, tab_stats = st.tabs([
    "Daten",
    "Training",
    "Checkpoints",
    "Statistiken"
])


# ---------------------------------------------------------------------------
# TAB DATA: Trainingsdaten Management
# ---------------------------------------------------------------------------

with tab_data:
    st.subheader("Trainingsdaten Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Datengenerierung**")
        n_pyramids = st.number_input("Pyramiden", min_value=10, value=100, step=10)
        n_non_pyramids = st.number_input("Andere", min_value=10, value=100, step=10)
        
        if st.button("Generieren", use_container_width=True, key="gen_btn"):
            with st.spinner("Generiere Daten..."):
                gen = st.session_state.pyramid_generator
                data, _ = gen.generate_dataset(n_pyramids, n_non_pyramids)
                # Direkt als float32 speichern spart RAM bei großen Mengen
                st.session_state.data = data.astype(np.float32)
                st.success(f"Erfolgreich: {len(data)} Samples generiert")
    
    with col2:
        st.markdown("**CSV Upload**")
        uploaded = st.file_uploader("CSV hochladen", type="csv")
        if uploaded:
            try:
                # Schnellerer Import via Pandas (wichtig für große Datensätze ab 100k Zeilen)
                # 'header=None' geht von reinen Zahlen aus. Falls Text drin ist, fängt es das ab.
                df_upload = pd.read_csv(uploaded, header=None)
                
                # Falls die erste Zeile Text (Header) enthält, ignorieren wir sie
                if isinstance(df_upload.iloc[0, 0], str):
                    df_upload = pd.read_csv(uploaded)
                    
                st.session_state.data = df_upload.to_numpy(dtype=np.float32)
                st.success(f"Erfolgreich: {len(st.session_state.data)} Samples geladen")
            except Exception as e:
                st.error(f"Fehler beim Laden der CSV: {e}")
    
    if "data" in st.session_state:
        st.markdown("---")
        data = st.session_state.data
        
        # Vektorisierte, schnelle Zählung
        pyramids = int(np.sum(data[:, -1] == 1))
        non_pyramids = len(data) - pyramids
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Gesamt", f"{len(data):,}".replace(",", "."))
        col2.metric("Pyramiden (1)", f"{pyramids:,}".replace(",", "."))
        col3.metric("Andere (0)", f"{non_pyramids:,}".replace(",", "."))
        
        with st.expander("Daten-Vorschau"):
            # Speicheroptimierung: Zeige maximal die ersten 1000 Zeilen im UI an!
            # Streamlit friert sonst bei 1 Million Zeilen im Browser komplett ein.
            preview_size = min(1000, len(data))
            
            df_preview = pd.DataFrame(
                data[:preview_size],
                columns=[f"Feature_{i+1}" for i in range(data.shape[1]-1)] + ["Label"]
            )
            df_preview["Label"] = df_preview["Label"].astype(int)
            
            st.dataframe(df_preview, use_container_width=True, height=400)
            if len(data) > 1000:
                st.caption(f"Hinweis: Es werden nur die ersten 1.000 von {len(data):,} Zeilen als Vorschau angezeigt.")

# ───────────────────────────────────────────────────────────────────────────
# TAB TRAINING: Modell trainieren
# ───────────────────────────────────────────────────────────────────────────

from scipy.special import expit  # Extrem schnelle, C-optimierte Sigmoid-Funktion
import numpy as np
import streamlit as st  # Korrigiert auf 'st' passend zum restlichen Code

with tab_training:
    st.subheader("Training starten")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        input_size = st.number_input("Input-Größe", value=19, step=1)
    with col2:
        hidden_size = st.number_input("Hidden Layer", value=32, step=1)
    with col3:
        learning_rate = st.slider("Learning Rate", 0.001, 1.0, 0.1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        epochs = st.number_input("Epochen", value=500, step=50)
    with col2:
        test_split = st.slider("Test-Anteil", 0.1, 0.5, 0.2)
    with col3:
        normalize = st.checkbox("Normalisieren", value=True)
    
    if st.button("Training starten", use_container_width=True, key="train_btn"):
        if "data" not in st.session_state:
            st.error("Keine Daten geladen!")
        else:
            data = st.session_state.data
            
            # Normalisierung (Inplace & Vektorisiert für große Datenmengen)
            if normalize:
                features = data[:, :-1].astype(np.float32)
                f_min = features.min(axis=0)
                f_max = features.max(axis=0)
                f_range = f_max - f_min
                f_range[f_range == 0] = 1.0
                features = (features - f_min) / f_range
                data = np.concatenate([features, data[:, -1:].astype(np.float32)], axis=1)
            else:
                data = data.astype(np.float32)
            
            # Train/Test Split
            n = len(data)
            n_test = int(n * test_split)
            idx = np.random.permutation(n)
            train_data = data[idx[:n-n_test]]
            test_data = data[idx[n-n_test:]]
            
            # Datensätze VOR der Schleife final extrahieren (spart Gigabytes an RAM-Kopien!)
            X_train = train_data[:, :-1]
            y_train = train_data[:, -1:]
            X_test = test_data[:, :-1]
            y_test = test_data[:, -1:]
            
            n_train = len(X_train)
            X_train_T = X_train.T  # Einmalig cachen
            
            # --- FIX: Dynamische Ermittlung der tatsächlichen Input-Größe ---
            actual_input_size = X_train.shape[1]
            
            # Initialisierung (He/Xavier-Varianz-Skalierung für stabileres Lernen)
            np.random.seed(42)
            W1 = (np.random.randn(actual_input_size, hidden_size) * np.sqrt(2.0 / actual_input_size)).astype(np.float32)
            b1 = np.zeros((1, hidden_size), dtype=np.float32)
            W2 = (np.random.randn(hidden_size, 1) * np.sqrt(2.0 / hidden_size)).astype(np.float32)
            b2 = np.zeros((1, 1), dtype=np.float32)
            
            train_losses = []
            test_losses = []
            
            progress_bar = st.progress(0)
            status = st.empty()
            
            # UI-Update-Intervall dynamisch anpassen (bei vielen Daten seltener updaten)
            ui_step = max(1, epochs // 20)
            
            # --- Optimierte Trainings-Schleife ---
            for epoch in range(epochs):
                
                # Forward - Training
                z1 = X_train @ W1 + b1
                a1 = np.maximum(0.0, z1)  # ReLU
                z2 = a1 @ W2 + b2
                a2 = expit(np.clip(z2, -500.0, 500.0))  # C-optimierte, stabile Sigmoid
                
                # Loss - Training
                train_loss = np.mean((a2 - y_train) ** 2)
                train_losses.append(train_loss)
                
                # Backpropagation
                dz2 = (a2 - y_train) * a2 * (1.0 - a2)
                dW2 = (a1.T @ dz2) / n_train * learning_rate
                db2 = np.mean(dz2, axis=0, keepdims=True) * learning_rate
                
                da1 = dz2 @ W2.T
                dz1 = da1 * (z1 > 0.0)
                dW1 = (X_train_T @ dz1) / n_train * learning_rate
                db1 = np.mean(dz1, axis=0, keepdims=True) * learning_rate
                
                # Gewichts-Update
                W2 -= dW2
                b2 -= db2
                W1 -= dW1
                b1 -= db1
                
                # Forward - Test (Nur berechnen, wenn UI geupdated wird -> Spart enorm Zeit!)
                if epoch % ui_step == 0 or epoch == epochs - 1:
                    z1_test = X_test @ W1 + b1
                    a1_test = np.maximum(0.0, z1_test)
                    z2_test = a1_test @ W2 + b2
                    a2_test = expit(np.clip(z2_test, -500.0, 500.0))
                    test_loss = np.mean((a2_test - y_test) ** 2)
                    test_losses.append(test_loss)
                    
                    progress_bar.progress(min(epoch / epochs, 1.0))
                    status.text(f"Epoch {epoch}/{epochs} | Train: {train_loss:.4f} | Test: {test_loss:.4f}")
                else:
                    # Damit die Listenlänge synchron bleibt
                    test_losses.append(test_losses[-1] if test_losses else train_loss)
            
            progress_bar.progress(1.0)
            status.text("Training abgeschlossen!")
            
            # Speichere Modell mit der echten Input-Größe im Zustand ab
            st.session_state.model = {
                "W1": W1, "b1": b1, "W2": W2, "b2": b2,
                "input_size": actual_input_size, "hidden_size": hidden_size
            }
            st.session_state.train_losses = train_losses
            st.session_state.test_losses = test_losses
            st.session_state.total_training_count += 1
            
            st.success("Modell trainiert!")
            st.rerun()
            
    
    # Zeige Ergebnisse
    if "model" in st.session_state and "train_losses" in st.session_state:
        st.markdown("---")
        st.subheader("Trainingsergebnisse")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=st.session_state.train_losses, name="Train", line=dict(color="green")))
        fig.add_trace(go.Scatter(y=st.session_state.test_losses, name="Test", line=dict(color="red")))
        fig.update_layout(xaxis_title="Epoch", yaxis_title="Loss", template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Final Train Loss", f"{st.session_state.train_losses[-1]:.6f}")
        col2.metric("Final Test Loss", f"{st.session_state.test_losses[-1]:.6f}")
        improvement = ((st.session_state.train_losses[0] - st.session_state.train_losses[-1]) / st.session_state.train_losses[0] * 100)
        col3.metric("Verbesserung", f"{improvement:.1f}%")


# ───────────────────────────────────────────────────────────────────────────
# TAB CHECKPOINTS: Modelle verwalten
# ───────────────────────────────────────────────────────────────────────────

with tab_checkpoint:
    st.subheader("Checkpoint Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Speichern", use_container_width=True):
            if "model" not in st.session_state:
                st.error("Kein Modell trainiert!")
            else:
                name = st.text_input("Name (optional):")
                if st.button("Bestätigen"):
                    cm = st.session_state.checkpoint_manager
                    model = st.session_state.model
                    weights = {k: v for k, v in model.items() if k not in ["input_size", "hidden_size"]}
                    config = {"input_size": model["input_size"], "hidden_size": model["hidden_size"]}
                    stats = {"final_loss": st.session_state.test_losses[-1], "epochs": len(st.session_state.train_losses)}
                    
                    cm.save(weights, config, stats, name or None)
                    st.success("Checkpoint gespeichert")
    
    with col2, col3:
        st.write("")
    
    st.markdown("---")
    st.subheader("Verfügbare Checkpoints")
    
    checkpoints = st.session_state.checkpoint_manager.list()
    
    if not checkpoints:
        st.info("Keine Checkpoints vorhanden")
    else:
        for ckpt in checkpoints:
            with st.expander(f"{ckpt['name']} | Loss: {ckpt['stats'].get('final_loss', '?'):.4f}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Timestamp:** {ckpt['timestamp'][:10]}")
                    st.write(f"**Config:**")
                    st.write(f"  Input: {ckpt['config'].get('input_size')}")
                    st.write(f"  Hidden: {ckpt['config'].get('hidden_size')}")
                
                with col2:
                    if st.button("Laden", key=f"load_{ckpt['name']}"):
                        try:
                            w, cfg, sts = st.session_state.checkpoint_manager.load(ckpt['name'])
                            model = {"W1": w["W1"], "b1": w["b1"], "W2": w["W2"], "b2": w["b2"]}
                            model["input_size"] = cfg["input_size"]
                            model["hidden_size"] = cfg["hidden_size"]
                            st.session_state.model = model
                            st.success("Geladen")
                        except Exception as e:
                            st.error(f"Fehler: {e}")
                    
                    if st.button("Löschen", key=f"del_{ckpt['name']}"):
                        st.session_state.checkpoint_manager.delete(ckpt['name'])
                        st.rerun()


# ───────────────────────────────────────────────────────────────────────────
# TAB STATS: Modell-Informationen & Export/Import
# ───────────────────────────────────────────────────────────────────────────

with tab_stats:
    st.subheader("Modell-Statistiken")
    
    col1, col2 = st.columns(2)
    
    # Modell-Info (nur wenn vorhanden)
    with col1:
        st.markdown("### Netzwerk-Architektur")
        
        if "model" in st.session_state:
            model = st.session_state.model
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Input Layer", model["input_size"])
            col_b.metric("Hidden Layer", model["hidden_size"])
            col_c.metric("Output Layer", 1)
            
            st.markdown("### Gewichte")
            st.write(f"W1 (Input-Hidden): {model['W1'].shape}")
            st.write(f"b1 (Bias): {model['b1'].shape}")
            st.write(f"W2 (Hidden-Output): {model['W2'].shape}")
            st.write(f"b2 (Bias): {model['b2'].shape}")
            
            st.markdown("### Trainings-Info")
            col_x, col_y = st.columns(2)
            col_x.metric("Trainings-Durchgänge", st.session_state.total_training_count)
            if "test_losses" in st.session_state:
                col_y.metric("Aktueller Loss", f"{st.session_state.test_losses[-1]:.6f}")
        else:
            st.info("Kein Modell geladen. Trainiere ein Modell oder importiere eines.")
    
    # Export / Import
    with col2:
        st.markdown("### Export / Import")
        
        if "model" in st.session_state:
            if st.button("Modell als JSON exportieren"):
                export_data = {
                    "W1": st.session_state.model["W1"].tolist(),
                    "b1": st.session_state.model["b1"].tolist(),
                    "W2": st.session_state.model["W2"].tolist(),
                    "b2": st.session_state.model["b2"].tolist(),
                    "config": {
                        "input_size": st.session_state.model["input_size"],
                        "hidden_size": st.session_state.model["hidden_size"]
                    }
                }
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
        
        st.markdown("**JSON importieren**")
        imported = st.file_uploader("Wähle eine JSON-Datei", type="json", key="import_json")
        if imported:
            try:
                data = json.load(imported)
                model = {
                    "W1": np.array(data["W1"], dtype=np.float32),
                    "b1": np.array(data["b1"], dtype=np.float32),
                    "W2": np.array(data["W2"], dtype=np.float32),
                    "b2": np.array(data["b2"], dtype=np.float32),
                    "input_size": data["config"]["input_size"],
                    "hidden_size": data["config"]["hidden_size"]
                }
                st.session_state.model = model
                st.success("Modell erfolgreich importiert!")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Importieren: {e}")


# ───────────────────────────────────────────────────────────────────────────
# FOOTER
# ───────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption("Informatik-Projekt | Pyramiden-Klassifikation mit neuronalen Netzen")
