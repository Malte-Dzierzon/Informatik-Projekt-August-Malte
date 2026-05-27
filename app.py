"""
PYRAMIDEN-KLASSIFIKATION - DASHBOARD
======================================
Zentralisiertes Dashboard zur Klassifikation von 3D-Pyramiden.
Fokus auf Clean-Code, Lesbarkeit und strukturierten Markdown-Export.
"""

import streamlit as st
import numpy as np
import json
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from scipy.special import expit

# Sichere Imports der Kern-Dateien
from pyramid_generator import PyramidGenerator
from dynamic_input import DynamicInputHandler

# App-Konfiguration für maximale Übersicht
st.set_page_config(
    page_title="Pyramiden-Klassifikation",
    layout="wide"
)

# Titel-Sektion (clean & vergrößert via HTML)
st.markdown("<h1 style='font-size: 2.5rem; margin-bottom: 0rem;'>Pyramiden-Klassifikation</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1rem; color: #666;'>Neuronales Netzwerk zur Erkennung von Pyramiden | Informatik-Projekt</p>", unsafe_allow_html=True)
st.markdown("---")


# ---------------------------------------------------------------------------
# SESSION STATE MANAGEMENT
# ---------------------------------------------------------------------------
if "pyramid_generator" not in st.session_state:
    st.session_state.pyramid_generator = PyramidGenerator(seed=42)

if "input_handler" not in st.session_state:
    st.session_state.input_handler = DynamicInputHandler()

if "model" not in st.session_state:
    st.session_state.model = None

if "total_training_count" not in st.session_state:
    st.session_state.total_training_count = 0

if "train_losses" not in st.session_state:
    st.session_state.train_losses = []

if "test_losses" not in st.session_state:
    st.session_state.test_losses = []

if "last_validation_result" not in st.session_state:
    st.session_state.last_validation_result = None

if "current_test_vector" not in st.session_state:
    st.session_state.current_test_vector = None

if "current_soll" not in st.session_state:
    st.session_state.current_soll = None


# ---------------------------------------------------------------------------
# SIDEBAR: MODELL-ZENTRALE (CLEAN)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='font-size: 1.6rem;'>Modell-Zentrale</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("**JSON-Modell importieren**")
    imported = st.file_uploader(
        "Datei auswählen", 
        type="json", 
        key="json_uploader_unique",
        label_visibility="collapsed"
    )
    
    if imported:
        try:
            if "last_loaded_file" not in st.session_state or st.session_state.last_loaded_file != imported.name:
                imported.seek(0)
                data = json.loads(imported.read().decode("utf-8"))
                
                required_keys = ["W1", "b1", "W2", "b2", "config"]
                if not all(k in data for k in required_keys):
                    st.error("❌ Ungültiges JSON-Format!")
                else:
                    st.session_state.model = {
                        "W1": np.array(data["W1"], dtype=np.float32),
                        "b1": np.array(data["b1"], dtype=np.float32),
                        "W2": np.array(data["W2"], dtype=np.float32),
                        "b2": np.array(data["b2"], dtype=np.float32),
                        "input_size": int(data["config"]["input_size"]),
                        "hidden_size": int(data["config"]["hidden_size"])
                    }
                    
                    stats = data.get("stats", {})
                    st.session_state.total_training_count = int(stats.get("total_epochs", 0))
                    last_loss_val = stats.get("last_loss", 0.0)
                    
                    st.session_state.train_losses = [float(last_loss_val)] if last_loss_val else []
                    st.session_state.test_losses = [float(last_loss_val)] if last_loss_val else []
                    st.session_state.last_validation_result = stats.get("validation", "Unbekannt")
                    
                    if "normalization_params" in data:
                        st.session_state.input_handler.set_params(data["normalization_params"])
                        
                    st.session_state.last_loaded_file = imported.name
                    st.success("✔️ Modell geladen!")
                    st.rerun()
        except Exception as e:
            st.error(f"❌ Fehler beim Import: {str(e)[:50]}")

    st.markdown("---")
    
    if st.session_state.model is not None:
        model = st.session_state.model
        
        st.markdown("<h3 style='font-size: 1.2rem;'>Architektur</h3>", unsafe_allow_html=True)
        st.markdown(f"Input Nodes: `{model['input_size']}`")
        st.markdown(f"Hidden Nodes: `{model['hidden_size']}`")
        
        st.markdown("---")
        st.markdown("<h3 style='font-size: 1.2rem;'>Status & Validierung</h3>", unsafe_allow_html=True)
        
        col_x, col_y = st.columns(2)
        formatted_epochs = f"{st.session_state.total_training_count:,}".replace(",", ".")
        col_x.metric("Epochen", formatted_epochs)
        
        if st.session_state.test_losses:
            col_y.metric("Loss", f"{st.session_state.test_losses[-1]:.5f}")
        else:
            col_y.metric("Loss", "—")
            
        val_status = st.session_state.last_validation_result
        if val_status:
            if "ERFOLGREICH" in val_status or "Perfekt" in val_status:
                st.success(val_status)
            else:
                st.warning(val_status)
        
        st.markdown("---")
        st.markdown("<h3 style='font-size: 1.2rem;'>Daten-Verwaltung</h3>", unsafe_allow_html=True)
        
        current_loss = float(st.session_state.test_losses[-1]) if st.session_state.test_losses else 0.0
        export_data = {
            "W1": model["W1"].tolist(), "b1": model["b1"].tolist(),
            "W2": model["W2"].tolist(), "b2": model["b2"].tolist(),
            "config": {"input_size": model["input_size"], "hidden_size": model["hidden_size"]},
            "stats": {
                "total_epochs": int(st.session_state.total_training_count),
                "last_loss": current_loss,
                "validation": st.session_state.last_validation_result
            },
            "normalization_params": st.session_state.input_handler.normalization_params
        }
        
        st.download_button(
            label="Download JSON (Sicherung)",
            data=json.dumps(export_data, indent=2),
            file_name=f"model_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
        
        w1_rounded = np.round(model["W1"], 3)
        w2_rounded = np.round(model["W2"].T, 3)
        
        markdown_report = (
            f"# Modellreport: KI-Pyramiden-Klassifikation\n\n"
            f"Automatisch generiertes Protokoll des fertig trainierten Netzwerks.\n\n"
            f"## Metriken & Zusammenfassung\n\n"
            f"| Parameter | Wert |\n"
            f"| :--- | :--- |\n"
            f"| Erstellungsdatum | {datetime.now().strftime('%d.%m.%Y, %H:%M:%S')} Uhr |\n"
            f"| Trainierte Epochen gesamt | {formatted_epochs} |\n"
            f"| Letzter Fehlerwert (MSE Loss) | `{current_loss:.6f}` |\n"
            f"| Validierungs-Status | {st.session_state.last_validation_result} |\n"
            f"| Eingangsschicht (Input Nodes) | {model['input_size']} Neuronen |\n"
            f"| Versteckte Schicht (Hidden Nodes) | {model['hidden_size']} Neuronen |\n\n"
            f"---\n\n"
            f"## Gewichtungsmatrizen\n\n"
            f"### 1. Gewichte: Input Schicht → Hidden Schicht (`W1`)\n"
            f"```text\n{np.array2string(w1_rounded, max_line_width=120)}\n```\n\n"
            f"**Schwellenwerte (Bias `b1`) der Hidden Schicht:**\n"
            f"```text\n{np.array2string(np.round(model['b1'], 3))}\n```\n\n"
            f"### 2. Gewichte: Hidden Schicht → Ausgabe-Knoten (`W2`)\n"
            f"```text\n{np.array2string(w2_rounded, max_line_width=120)}\n```\n\n"
            f"**Schwellenwert (Bias `b2`) des Ausgangs:**\n"
            f"```text\n{np.array2string(np.round(model['b2'], 3))}\n```\n\n"
            f"---\n"
            f"*Ende des Protokolls. Informatik-Projekt 2026.*"
        )
        
        st.download_button(
            label="Download Markdown Report (.md)",
            data=markdown_report,
            file_name=f"Modell_Dokumentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    else:
        st.info("Kein Modell aktiv. Bitte generiere Daten und starte das Training.")


# ---------------------------------------------------------------------------
# HAUPT-TABS
# ---------------------------------------------------------------------------
tab_data, tab_training, tab_test = st.tabs([
    "Daten-Zentrale",
    "Training & Validierung",
    "Interaktiver Test (3D)"
])


# ---------------------------------------------------------------------------
# TAB DATA: Datensatz-Verwaltung
# ---------------------------------------------------------------------------
with tab_data:
    st.markdown("<h2 style='font-size: 1.5rem;'>Trainingsdaten-Management</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Synthetische Datengenerierung**")
        n_pyramids = st.number_input("Anzahl Pyramiden", min_value=10, value=100, step=10)
        n_non_pyramids = st.number_input("Anzahl andere Objekte", min_value=10, value=100, step=10)
        
        if st.button("Daten generieren", use_container_width=True, key="gen_btn"):
            with st.spinner("Generiere Daten..."):
                data, _ = st.session_state.pyramid_generator.generate_dataset(n_pyramids, n_non_pyramids)
                st.session_state.data = data.astype(np.float32)
                st.rerun()
    
    with col2:
        st.markdown("**CSV Daten-Upload**")
        uploaded = st.file_uploader("Datei hochladen", type="csv")
        if uploaded:
            try:
                df_upload = pd.read_csv(uploaded, engine="pyarrow", dtype_backend="pyarrow")
                is_pure_data = all(str(col).replace('.', '', 1).isdigit() or "Unnamed" in str(col) for col in df_upload.columns)
                if is_pure_data:
                    uploaded.seek(0)
                    df_upload = pd.read_csv(uploaded, header=None, engine="pyarrow", dtype_backend="pyarrow")
                st.session_state.data = df_upload.to_numpy(dtype=np.float32)
                st.success("✔️ Datei erfolgreich geladen!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Fehler bei CSV-Verarbeitung: {e}")
    
    if "data" in st.session_state:
        st.markdown("---")
        data = st.session_state.data
        pyramids = int((data[:, -1] == 1.0).sum())
        non_pyramids = len(data) - pyramids
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Gesamte Datenzeilen", f"{len(data)}")
        c2.metric("Pyramiden (Klasse 1)", f"{pyramids}")
        c3.metric("Andere (Klasse 0)", f"{non_pyramids}")


# ---------------------------------------------------------------------------
# TAB TRAINING: Netzwerk-Optimierung
# ---------------------------------------------------------------------------
with tab_training:
    st.markdown("<h2 style='font-size: 1.5rem;'>Modell trainieren</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        input_size = st.number_input("Input-Größe (Standard: 19)", value=19, step=1)
    with col2:
        hidden_size = st.number_input("Hidden Layer Neuronen", value=32, step=1)
    with col3:
        learning_rate = st.slider("Lernrate", 0.001, 1.0, 0.1)
        
    epochs = st.number_input("Maximale Epochenanzahl", value=1000, step=100)
    
    if st.button("Training starten & verifizieren", use_container_width=True):
        if "data" not in st.session_state:
            st.error("❌ Keine Trainingsdaten vorhanden! Bitte zuerst im Tab 'Daten-Zentrale' Datensätze erstellen.")
        else:
            raw_data = st.session_state.data
            data, _ = st.session_state.input_handler.filter_and_prepare(raw_data, fit=True)
            
            X_train = data[:, :-1]
            y_train = data[:, -1:]
            n_train = len(X_train)
            X_train_T = X_train.T
            
            actual_input_size = X_train.shape[1] if X_train.ndim > 1 else input_size
            
            np.random.seed(42)
            W1 = (np.random.randn(actual_input_size, hidden_size) * np.sqrt(2.0 / actual_input_size)).astype(np.float32)
            b1 = np.zeros((1, hidden_size), dtype=np.float32)
            W2 = (np.random.randn(hidden_size, 1) * np.sqrt(2.0 / hidden_size)).astype(np.float32)
            b2 = np.zeros((1, 1), dtype=np.float32)
            
            train_losses = []
            progress_bar = st.progress(0)
            status = st.empty()
            
            for epoch in range(epochs):
                z1 = X_train @ W1 + b1
                a1 = np.maximum(0.0, z1)
                z2 = a1 @ W2 + b2
                a2 = expit(np.clip(z2, -500.0, 500.0))
                
                loss = np.mean((a2 - y_train) ** 2)
                train_losses.append(loss)
                
                dz2 = (a2 - y_train) * a2 * (1.0 - a2)
                dW2 = (a1.T @ dz2) / n_train * learning_rate
                db2 = np.mean(dz2, axis=0, keepdims=True) * learning_rate
                
                da1 = dz2 @ W2.T
                dz1 = da1 * (z1 > 0.0)
                dW1 = (X_train_T @ dz1) / n_train * learning_rate
                db1 = np.mean(dz1, axis=0, keepdims=True) * learning_rate
                
                W2 -= dW2; b2 -= db2; W1 -= dW1; b1 -= db1
                
                if epoch % 50 == 0:
                    progress_bar.progress(epoch / epochs)
                    status.text(f"Epoche {epoch}/{epochs} | Aktueller Loss: {loss:.5f}")
            
            progress_bar.progress(1.0)
            status.text("Grundlagentraining abgeschlossen. Starte Verifikationslauf...")
            
            # Automatische Verifikation
            test_pyramid_raw, _ = st.session_state.pyramid_generator.generate_dataset(1, 0)
            raw_vector = test_pyramid_raw[0:1, :-1]
            handler_ready_input = np.concatenate([raw_vector, np.array([[1.0]], dtype=np.float32)], axis=1)
            normED_vector, _ = st.session_state.input_handler.filter_and_prepare(handler_ready_input, fit=False)
            final_test_input = normED_vector[:, :-1]
            
            tz1 = final_test_input @ W1 + b1
            ta1 = np.maximum(0.0, tz1)
            tz2 = ta1 @ W2 + b2
            pyramid_prediction = expit(np.clip(tz2, -500.0, 500.0))[0, 0]
            
            if pyramid_prediction >= 0.95:
                st.session_state.last_validation_result = f"✔️ ERFOLGREICH! Test-Pyramide zu {pyramid_prediction*100:.1f}% korrekt erkannt."
                st.success(st.session_state.last_validation_result)
            else:
                st.session_state.last_validation_result = f"❌ FEHLGESCHLAGEN! Test-Pyramide nur zu {pyramid_prediction*100:.1f}% erkannt!"
                st.warning(st.session_state.last_validation_result)
            
            st.session_state.model = {
                "W1": W1, "b1": b1, "W2": W2, "b2": b2,
                "input_size": actual_input_size, "hidden_size": hidden_size
            }
            st.session_state.train_losses = train_losses
            st.session_state.test_losses = train_losses
            st.session_state.total_training_count += epochs
            st.rerun()

    if st.session_state.model and st.session_state.train_losses:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=st.session_state.train_losses, name="Trainings-Verlauf", line=dict(color="#1f77b4")))
        fig.update_layout(xaxis_title="Epoche", yaxis_title="Loss (MSE)", template="plotly_white", height=350)
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# TAB TEST: Geometrie-Prüfung
# ---------------------------------------------------------------------------
with tab_test:
    st.markdown("<h2 style='font-size: 1.5rem;'>Interaktiver 3D-Geometrie-Test</h2>", unsafe_allow_html=True)
    
    if st.session_state.model is None:
        st.warning("❌ Bitte lade zuerst ein Modell oder trainiere eines im Tab 'Training', um Objekte zu prüfen.")
    else:
        model = st.session_state.model
        
        st.markdown("<h3 style='font-size: 1.2rem;'>Schritt 1: Test-Objekt bereitstellen</h3>", unsafe_allow_html=True)
        modus = st.radio(
            "Eingabemethode wählen:",
            ["Zufälliges Objekt automatisch generieren (Empfohlen)", "Eigene Koordinaten manuell eingeben"]
        )
        
        test_vector = None
        soll_ergebnis = None
        
        if "Zufälliges" in modus:
            objekt_typ = st.selectbox("Objekttyp festlegen:", ["Echte Pyramide (Soll = 1)", "Anderes Objekt / Rauschen (Soll = 0)"])
            
            if st.button("Objekt generieren / neu würfeln", use_container_width=True):
                if "Echte Pyramide" in objekt_typ:
                    raw_generated, _ = st.session_state.pyramid_generator.generate_dataset(1, 0)
                else:
                    raw_generated, _ = st.session_state.pyramid_generator.generate_dataset(0, 1)
                
                st.session_state.current_test_vector = raw_generated[0, :-1].tolist()
                st.session_state.current_soll = float(raw_generated[0, -1])
                st.rerun()
            
            if st.session_state.current_test_vector is not None:
                test_vector = np.array(st.session_state.current_test_vector, dtype=np.float32)
                soll_ergebnis = st.session_state.current_soll
                
                st.info(f"**Generierter 3D-Array ({len(test_vector)} Eigenschaften):**\n`{list(np.round(test_vector, 3))}`")
                if soll_ergebnis == 1.0:
                    st.markdown("Erwartete Zielklasse: **Pyramide (Klasse 1)**")
                else:
                    st.markdown("Erwartete Zielklasse: **Keine Pyramide (Klasse 0)**")
        
        else:
            st.markdown(f"Gib exakt `{model['input_size']}` Gleitkommazahlen kommagetrennt ein:")
            default_str = ", ".join([str(round(float(x), 2)) for x in np.random.uniform(0.1, 1.0, model["input_size"])])
            u_input = st.text_area("Vektor:", value=default_str, height=70)
            
            try:
                parsed = [float(x.strip()) for x in u_input.split(",") if x.strip() != ""]
                if len(parsed) == model["input_size"]:
                    test_vector = np.array(parsed, dtype=np.float32)
                    soll_ergebnis = None
                else:
                    st.error(f"❌ Ungültige Dimension! Erwartet: {model['input_size']} Werte, eingegeben: {len(parsed)}")
            except Exception as e:
                st.error(f"❌ Syntaxfehler beim Parsen der Eingabe: {e}")

        if test_vector is not None:
            st.markdown("---")
            st.markdown("<h3 style='font-size: 1.2rem;'>Schritt 2: Modellklassifikation</h3>", unsafe_allow_html=True)
            
            if st.button("Vorhersage berechnen", use_container_width=True):
                raw_vec_2d = np.array([list(test_vector) + [0.0]], dtype=np.float32)
                norm_vec, _ = st.session_state.input_handler.filter_and_prepare(raw_vec_2d, fit=False)
                
                z1 = norm_vec[:, :-1] @ model["W1"] + model["b1"]
                a1 = np.maximum(0.0, z1)
                z2 = a1 @ model["W2"] + model["b2"]
                prediction_raw = expit(np.clip(z2, -500.0, 500.0))[0, 0]
                
                final_class = 1 if prediction_raw >= 0.5 else 0
                
                st.markdown("**Auswertung der Netzwerkausgabe:**")
                
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.markdown("Modell-Rohwert (Wahrscheinlichkeit zwischen 0 und 1):")
                    st.code(f"{prediction_raw:.6f}", language="text")
                
                with col_res2:
                    st.markdown("Klassifikations-Entscheidung:")
                    if final_class == 1:
                        st.markdown("<h2 style='color:#2ca02c; margin:0; font-size:1.8rem;'>Klasse 1 (Pyramide erkannt)</h2>", unsafe_allow_html=True)
                    else:
                        st.markdown("<h2 style='color:#d62728; margin:0; font-size:1.8rem;'>Klasse 0 (Keine Pyramide)</h2>", unsafe_allow_html=True)
                
                st.progress(float(prediction_raw))
                st.caption("Ein Ausgabewert nahe 1.0 impliziert hohe Sicherheit für eine Pyramide, ein Wert nahe 0.0 schließt diese aus.")
                
                if soll_ergebnis is not None:
                    st.markdown("---")
                    if final_class == int(soll_ergebnis):
                        st.success(f"✔️ Validierung erfolgreich: Soll-Wert ({int(soll_ergebnis)}) stimmt mit der Vorhersage ({final_class}) überein.")
                    else:
                        st.error(f"❌ Fehlklassifikation: Der Soll-Wert war {int(soll_ergebnis)}, das Netzwerk hat sich für Klasse {final_class} entschieden.")

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption("Informatik-Projekt 2026 | Neuronale Netzwerkarchitekturen zur geometrischen Mustererkennung")