import streamlit as st
import numpy as np
import json
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from scipy.special import expit

from pyramid_generator import PyramidGenerator
from dynamic_input import DynamicInputHandler

st.set_page_config(
    page_title="Pyramiden-Klassifikation",
    layout="wide"
)

st.markdown("<h1 style='font-size: 2.5rem; margin-bottom: 0rem;'>Pyramiden-Klassifikation</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1rem; color: #666;'>Neuronales Netzwerk zur Erkennung von Pyramiden | Informatik-Projekt</p>", unsafe_allow_html=True)
st.markdown("---")


# ---------------------------------------------------------------------------
# SPEICHER-VERWALTUNG (SESSION STATE)
# ---------------------------------------------------------------------------
if "pyramid_generator" not in st.session_state:
    st.session_state.pyramid_generator = PyramidGenerator(seed=42)

if "input_handler" not in st.session_state:
    st.session_state.input_handler = DynamicInputHandler(max_vertices=12, coordinates_per_vertex=3)

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
        label_visibility="collapsed"
    )
    
    if imported:
        try:
            if "last_loaded_file" not in st.session_state or st.session_state.last_loaded_file != imported.name:
                imported.seek(0)
                data = json.loads(imported.read().decode("utf-8"))
                
                required_keys = ["W1", "b1", "W2", "b2", "config"]
                if not all(k in data for k in required_keys):
                    st.error("[FEHLER] Da fehlen wichtige Daten im JSON!")
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
                    st.success("[ERFOLG] Modell wurde geladen!")
                    st.rerun()
        except Exception as e:
            st.error(f"[FEHLER] Beim Laden ging was schief: {str(e)[:50]}")

    st.markdown("---")
    
    if st.session_state.model is not None:
        model = st.session_state.model
        
        st.markdown("<h3 style='font-size: 1.2rem;'>Architektur</h3>", unsafe_allow_html=True)
        col_a1, col_a2 = st.columns(2)
        col_a1.metric("Input Nodes", f"{model['input_size']}")
        col_a2.metric("Hidden Nodes", f"{model['hidden_size']}")
        
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
        st.markdown("<h3 style='font-size: 1.2rem;'>Exporte & Berichte</h3>", unsafe_allow_html=True)
        
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
            label="Download JSON (Gewichte)",
            data=json.dumps(export_data, indent=2),
            file_name=f"model_weights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
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
            f"| **Eingangsschicht (Input)** | {model['input_size']:,} | Identische Abbildung |\n"
            f"| **Versteckte Schicht (Hidden)** | {model['hidden_size']} | ReLU |\n"
            f"| **Ausgangsschicht (Output)** | 1 | Sigmoid |\n\n".replace(",", ".") +
            f"## 3. Trainings-Metriken\n\n"
            f"* **Absolvierte Epochen gesamt:** {formatted_epochs}\n"
            f"* **Letzter Fehlerwert (MSE Loss):** `{current_loss:.6f}`\n\n"
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
            use_container_width=True
        )
    else:
        st.info("Noch kein Modell aktiv. Generiere erst Daten und starte das Training.")


# ---------------------------------------------------------------------------
# HAUPTTABS
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
    
    st.markdown("### Dynamische Geometrie-Struktur festlegen")
    st.markdown(
        "> **Info zur Padding-Logik:** Wenn du Objekte mit sehr vielen Eckpunkten lädst oder generierst, "
        "stellt die maximale Anzahl der Eckpunkte das globale Limit dar. Formen mit weniger Punkten werden "
        "automatisch mit `0.0` aufgefüllt, damit die Matrix-Form für das Netzwerk absolut stabil bleibt."
    )
    
    c_geo1, c_geo2 = st.columns(2)
    with c_geo1:
        max_vertices = st.number_input(
            "Maximale Anzahl an Eckpunkten (Vertices)", 
            min_value=3, 
            value=12, 
            step=1,
            key="ui_max_vertices"  # <-- Das hier löst das ID-Problem!
        )
    
    # Fest auf 3 setzen (X, Y, Z), da Geometrie im 3D-Raum stattfindet
    coords_per_vertex = 3 
    
    # Der Handler aktualisiert sich jetzt nur noch, wenn sich 'max_vertices' ändert
    if st.session_state.input_handler.max_vertices != max_vertices:
        st.session_state.input_handler = DynamicInputHandler(
            max_vertices=max_vertices, 
            coordinates_per_vertex=coords_per_vertex
        )
        
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Variante A: Künstliche Daten erzeugen**")
        n_pyramids = st.number_input("Wie viele Pyramiden?", min_value=10, value=100, step=10)
        n_non_pyramids = st.number_input("Wie viele andere Formen?", min_value=10, value=100, step=10)
        
        if st.button("Daten generieren", use_container_width=True, key="gen_btn"):
            with st.spinner("Objekte werden berechnet..."):
                data_matrix, _ = st.session_state.pyramid_generator.generate_dataset(
                    max_vertices=max_vertices,
                    coords_per_vertex=coords_per_vertex,
                    n_pyramids=n_pyramids,
                    n_non_pyramids=n_non_pyramids,
                    shuffle=True
                )
                
                st.session_state.data = data_matrix.astype(np.float32)
                st.success(f"✔️ Datensatz mit {data_matrix.shape[1] - 1} Inputs erfolgreich generiert!")
                st.rerun()
    
    with col2:
        st.markdown("**Variante B: Eigene CSV-Datei hochladen**")
        uploaded = st.file_uploader("CSV-Datei auswählen", type="csv")
        if uploaded:
            try:
                df_upload = pd.read_csv(uploaded, engine="pyarrow", dtype_backend="pyarrow")
                is_pure_data = all(str(col).replace('.', '', 1).isdigit() or "Unnamed" in str(col) for col in df_upload.columns)
                if is_pure_data:
                    uploaded.seek(0)
                    df_upload = pd.read_csv(uploaded, header=None, engine="pyarrow", dtype_backend="pyarrow")
                st.session_state.data = df_upload.to_numpy(dtype=np.float32)
                st.success("✔️ Daten erfolgreich importiert!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Da hat was beim Einlesen nicht geklappt: {e}")
    
    if "data" in st.session_state:
        st.markdown("---")
        data = st.session_state.data
        
        pyr_rows = data[data[:, -1] == 1.0]
        other_rows = data[data[:, -1] == 0.0]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Gesamte Datenzeilen", f"{len(data)}")
        c2.metric("Erkanntes Input-Format (Spalten)", f"{data.shape[1] - 1}")
        c3.metric("Klassenaufteilung (Pyr / Andere)", f"{len(pyr_rows)} / {len(other_rows)}")
        
        st.markdown("### Daten-Vorschau (Rohdaten vor Normalisierung)")
        
        num_features = data.shape[1] - 1
        col_names = []
        
        feat_counter = 0
        for v in range(max_vertices):
            for c in range(coords_per_vertex):
                if feat_counter < num_features:
                    coord_axis = ["X", "Y", "Z", "W"][c % 4]
                    col_names.append(f"P{v+1}_{coord_axis}")
                    feat_counter += 1
                    
        while len(col_names) < num_features:
            col_names.append(f"Zusatz_Feature_{len(col_names)+1}")
        
        col_names.append("Zielklasse (Label)")
        
        view_col1, view_col2 = st.columns(2)
        with view_col1:
            st.markdown("**🟢 Klasse 1: Echte Pyramiden (Auszug)**")
            if len(pyr_rows) > 0:
                df_pyr = pd.DataFrame(pyr_rows[:5], columns=col_names)
                st.dataframe(df_pyr.style.format(precision=3), use_container_width=True)
            else:
                st.info("Keine Pyramidendaten im aktuellen Set vorhanden.")
                
        with view_col2:
            st.markdown("**🔴 Klasse 0: Andere Formen / Komplexe Geometrien (Auszug)**")
            if len(other_rows) > 0:
                df_other = pd.DataFrame(other_rows[:5], columns=col_names)
                st.dataframe(df_other.style.format(precision=3), use_container_width=True)
            else:
                st.info("Keine Alternativformen im aktuellen Set vorhanden.")


# ---------------------------------------------------------------------------
# TAB TRAINING: Netzwerk-Optimierung
# ---------------------------------------------------------------------------
with tab_training:
    st.markdown("<h2 style='font-size: 1.5rem;'>Modell trainieren</h2>", unsafe_allow_html=True)
    
    if "data" in st.session_state:
        detected_inputs = st.session_state.data.shape[1] - 1
    else:
        detected_inputs = st.session_state.input_handler.max_vertices * st.session_state.input_handler.coordinates_per_vertex + 4

    col1, col2, col3 = st.columns(3)
    with col1:
        input_size = st.number_input("Input-Größe (wird automatisch angepasst)", value=int(detected_inputs), step=1)
    with col2:
        hidden_size = st.number_input("Neuronen im Hidden Layer", value=32, step=1)
    with col3:
        learning_rate = st.slider("Schrittweite (Lernrate)", 0.001, 1.0, 0.1)
        
    epochs = st.number_input("Wie viele Runden (Epochen)?", value=1000, step=100)
    
    if st.button("Training starten & verifizieren", use_container_width=True):
        if "data" not in st.session_state:
            st.error("❌ Geht noch nicht! Bitte erzeuge oder lade erst Datensätze im ersten Tab.")
        else:
            raw_data = st.session_state.data
            
            if raw_data.shape[1] - 1 != input_size:
                st.warning(f"Passe Daten-Spalten an manuelle UI-Vorgabe ({input_size}) an...")
                features_resized = raw_data[:, :input_size]
                labels_clean = raw_data[:, -1:]
                raw_data = np.concatenate([features_resized, labels_clean], axis=1)

            data, _ = st.session_state.input_handler.filter_and_prepare(raw_data, fit=True)
            
            X_train = data[:, :-1]
            y_train = data[:, -1:]
            n_train = len(X_train)
            X_train_T = X_train.T
            
            actual_input_size = X_train.shape[1]
            
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
            status.text("Grundlagentraining fertig!")
            
            st.session_state.last_validation_result = f"✔️ Modell erfolgreich auf {actual_input_size} Inputs trainiert!"
            st.success(st.session_state.last_validation_result)
            
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
# TAB TEST: Geometrie-Prüfung (EIN-KLICK-WORKFLOW & REPARIERTE KOORDINATEN)
# ---------------------------------------------------------------------------
with tab_test:
    st.markdown("<h2 style='font-size: 1.5rem;'>Interaktiver 3D-Geometrie-Test</h2>", unsafe_allow_html=True)
    
    if st.session_state.model is None:
        st.warning("❌ Ohne Modell geht das nicht. Bitte trainiere erst eins oder lade eine JSON-Datei hoch.")
    else:
        model = st.session_state.model
        current_input_dim = model["input_size"]
        
        st.markdown("<h3 style='font-size: 1.2rem;'>Schritt 1: Test-Objekt bereitstellen</h3>", unsafe_allow_html=True)
        modus = st.radio(
            "Wie willst du das Objekt eingeben?:",
            ["Zufälliges Objekt automatisch generieren (Empfohlen)", "Eigene Koordinaten manuell eingeben"]
        )
        
        test_vector = None
        soll_ergebnis = None
        
        if "Zufälliges" in modus:
            objekt_typ = st.selectbox("Was für ein Objekt soll es sein?:", ["Echte Pyramide (Soll = 1)", "Anderes Objekt / Rauschen (Soll = 0)"])
            
            if st.button("Objekt generieren & sofort klassifizieren", use_container_width=True):
                is_pyramid = 1.0 if "Echte Pyramide" in objekt_typ else 0.0
                
                # REPARATUR: Nutzt jetzt die korrekten, dedizierten Single-Methoden OHNE Label-Spalte!
                if is_pyramid == 1.0:
                    raw_vector = st.session_state.pyramid_generator.generate_single_pyramid(
                        max_vertices=st.session_state.input_handler.max_vertices,
                        coords_per_vertex=st.session_state.input_handler.coordinates_per_vertex
                    )
                else:
                    raw_vector = st.session_state.pyramid_generator.generate_single_non_pyramid(
                        max_vertices=st.session_state.input_handler.max_vertices,
                        coords_per_vertex=st.session_state.input_handler.coordinates_per_vertex
                    )
                
                # Sicherheitsprüfung für die Dimension
                if len(raw_vector) != current_input_dim:
                    st.error(f"Abweichung entdeckt: Der Generator liefert {len(raw_vector)} Features, das Modell braucht {current_input_dim}. Passe UI-Eckpunkte im Tab 'Daten-Zentrale' an.")
                else:
                    st.session_state.current_test_vector = raw_vector.tolist()
                    st.session_state.current_soll = is_pyramid
                    st.rerun()
                
            if st.session_state.current_test_vector is not None:
                test_vector = np.array(st.session_state.current_test_vector, dtype=np.float32)
                soll_ergebnis = st.session_state.current_soll
        
        else:
            st.markdown(f"Tippe hier exakt `{current_input_dim}` Zahlen ein (mit Komma getrennt):")
            default_str = ", ".join([str(round(float(x), 2)) for x in np.random.uniform(0.1, 1.0, current_input_dim)])
            u_input = st.text_area("Vektor:", value=default_str, height=70)
            
            try:
                parsed = [float(x.strip()) for x in u_input.split(",") if x.strip() != ""]
                if len(parsed) == current_input_dim:
                    test_vector = np.array(parsed, dtype=np.float32)
                else:
                    st.error(f"❌ Dimension fehlerhaft! Das Modell verlangt exakt {current_input_dim} Inputs. Du hast {len(parsed)} eingegeben.")
            except Exception as e:
                st.error(f"❌ Eingabe-Fehler: {e}")

        # Live-Auswertung und strukturierte Vektor-Anzeige
        if test_vector is not None and len(test_vector) == current_input_dim:
            st.markdown("---")
            st.markdown("<h3 style='font-size: 1.2rem;'>Schritt 2: Generierter Vektor & Modellklassifikation</h3>", unsafe_allow_html=True)
            
            # REPARATUR: Vorbereitung der Normalisierungsmatrix ohne künstlich verschobene Label-Spalten
            prep_matrix = np.zeros((1, current_input_dim + 1), dtype=np.float32)
            prep_matrix[0, :current_input_dim] = test_vector
            
            norm_matrix, _ = st.session_state.input_handler.filter_and_prepare(prep_matrix, fit=False)
            norm_vector = norm_matrix[0, :current_input_dim]
            
            # Strukturierte String-Generierung
            readable_features = []
            feat_counter = 0
                
            # 1. Geometrie-Punkte benennen
            for v in range(st.session_state.input_handler.max_vertices):
                for c in range(st.session_state.input_handler.coordinates_per_vertex):
                    if feat_counter < current_input_dim:
                        coord_axis = ["X", "Y", "Z", "W"][c % 4]
                        readable_features.append(f"P{v+1}_{coord_axis}: {norm_vector[feat_counter]:.4f}")
                        feat_counter += 1
            
            # 2. Zusatzfeatures durchnummerieren
            z_idx = 1
            while feat_counter < current_input_dim:
                readable_features.append(f"Zusatz_Feature_{z_idx}: {norm_vector[feat_counter]:.4f}")
                feat_counter += 1
                z_idx += 1
                
            vector_string = ", ".join(readable_features)
            
            st.markdown("**Generierter Feature-Vektor (Strukturierte String-Darstellung):**")
            st.text_area("Vektor-String (kopierbar für Dokumentationen):", value=vector_string, height=120, disabled=True)
            
            if "Zufälliges" in modus and soll_ergebnis is not None:
                st.info(f"Erwartete Soll-Klasse des Objekts: **{int(soll_ergebnis)}** ({objekt_typ})")
            
            berechnen_ausloesen = True
            if "Eigene Koordinaten" in modus:
                berechnen_ausloesen = st.button("Vorhersage manuell berechnen", use_container_width=True)
                
            if berechnen_ausloesen:
                X_input = norm_vector.reshape(1, -1)
                z1 = X_input @ model["W1"] + model["b1"]
                a1 = np.maximum(0.0, z1)
                z2 = a1 @ model["W2"] + model["b2"]
                prediction_raw = expit(np.clip(z2, -500.0, 500.0))[0, 0]
                
                final_class = 1 if prediction_raw >= 0.5 else 0
                
                st.markdown("**Das sagt unser Netzwerk:**")
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.markdown("Rohwert vom Ausgangsneuron:")
                    st.code(f"{prediction_raw:.6f}", language="text")
                with col_res2:
                    st.markdown("Klassifizierung:")
                    if final_class == 1:
                        st.markdown("<h2 style='color:#2ca02c; margin:0; font-size:1.8rem;'>Klasse 1 (Pyramide)</h2>", unsafe_allow_html=True)
                    else:
                        st.markdown("<h2 style='color:#d62728; margin:0; font-size:1.8rem;'>Klasse 0 (Keine Pyramide)</h2>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# FUSSZEILE (FOOTER)
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption("Informatik-Projekt 2026 | Neuronale Netzwerkarchitekturen zur geometrischen Mustererkennung")