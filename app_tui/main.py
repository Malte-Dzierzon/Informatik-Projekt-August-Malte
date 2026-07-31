"""Application entry point: TUIApp controller and main loop."""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Any, ClassVar

import numpy as np

from nn import NeuralNet, TrainConfig

from .components import Form
from .config import TUIConfig, get_or_create_config, save_config
from .input import Action, ActionType, get_action
from .render import (
    CLEAR_SCREEN,
    CURSOR_HOME,
    Layout,
    alternate_screen,
    disable_mouse,
    enable_mouse,
    get_key,
    poll_key,
    raw_mode,
    show_cursor,
)
from .screens import (
    DataMenuScreen,
    ExportMenuScreen,
    FormScreen,
    HelpScreen,
    MainMenuScreen,
    PreviewScreen,
    ProgressScreen,
    ScreenBase,
    SettingsMenuScreen,
    TestMenuScreen,
    TrainMenuScreen,
)
from .state import (
    AppState,
    GoBack,
    Screen,
    SetData,
    SetError,
    SetScreen,
    SetStatus,
    SetTestVector,
    UpdateConfig,
    reducer,
)
from .theme import get_theme, init_theme

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _positive_int(value: str) -> bool | str:
    try:
        return int(value) > 0
    except ValueError:
        return "Must be a positive integer"


def _required(value: str) -> bool | str:
    return bool(value.strip()) or "Value required"


def _format_epochs(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def _derive_extra_features(coords: np.ndarray) -> np.ndarray:
    """Recompute the 4 extra features from a coordinate block, mirroring
    PyramidGenerator._extra_features. Falls back to zeros when fewer than
    5 valid points are available."""
    valid = coords[~np.isnan(coords).any(axis=1)]
    if len(valid) < 5:
        return np.zeros(4, dtype=np.float32)
    base, apex = valid[:4], valid[4]
    center = base.mean(axis=0)
    height = float(np.linalg.norm(apex - center))
    balance = float(np.linalg.norm(apex[:2] - center[:2]))
    edge1 = base[1] - base[0]
    edge2 = base[3] - base[0]
    base_area = float(np.linalg.norm(np.cross(edge1, edge2)))
    return np.array([height, balance, base_area, float(center[0])], dtype=np.float32)


def prepare_test_vector(state: AppState, raw_vector: Any) -> dict[str, Any] | None:
    """Pad, transform, and normalize a raw test vector for prediction."""
    raw = np.array(raw_vector, dtype=np.float32).flatten()
    max_len = state.input_handler.max_vertices * state.input_handler.coordinates_per_vertex
    full_len = max_len + 4  # coordinate block + extra features

    if raw.size < full_len:
        padded = np.full(full_len, np.nan, dtype=np.float32)
        padded[: raw.size] = raw
        coords = padded[:max_len].reshape(-1, state.input_handler.coordinates_per_vertex)
        padded[max_len:] = _derive_extra_features(coords)
        raw = padded
    elif raw.size > full_len:
        raw = raw[:full_len]

    prep = np.zeros((1, raw.size + 1), dtype=np.float32)
    prep[0, : raw.size] = raw
    try:
        norm_matrix, _ = state.input_handler.filter_and_prepare(prep, fit=False)
    except (ValueError, IndexError, TypeError):
        return None
    return {
        "raw": raw,
        "normalized": norm_matrix[0, :-1],
        "input_vector": norm_matrix[0, :-1].reshape(1, -1),
    }


def _downloads_folder() -> Path:
    """Best-effort downloads directory (Android/Termux aware)."""
    home = Path.home()
    downloads = home / "Downloads"

    if sys.platform.startswith("linux") or sys.platform.startswith("android"):
        for candidate in [Path("/sdcard/Download"), Path("/sdcard/Downloads"), downloads]:
            if candidate.exists() and candidate.is_dir():
                return candidate

    try:
        downloads.mkdir(parents=True, exist_ok=True)
        return downloads
    except (OSError, PermissionError):
        return home


class TUIApp:
    """Main application controller: state, screens, and business logic."""

    SCREEN_CLASSES: ClassVar[dict[Screen, type[ScreenBase]]] = {
        Screen.MAIN_MENU: MainMenuScreen,
        Screen.DATA_MENU: DataMenuScreen,
        Screen.TRAIN_MENU: TrainMenuScreen,
        Screen.TEST_MENU: TestMenuScreen,
        Screen.EXPORT_MENU: ExportMenuScreen,
        Screen.SETTINGS_MENU: SettingsMenuScreen,
        Screen.HELP: HelpScreen,
        Screen.PROGRESS: ProgressScreen,
        Screen.FORM: FormScreen,
        Screen.PREVIEW: PreviewScreen,
    }

    def __init__(self, config: TUIConfig):
        self.config = config
        self.theme = get_theme()
        self.state = AppState()
        self.running = True
        self.screens: dict[str, ScreenBase] = {
            screen.value: cls(self) for screen, cls in self.SCREEN_CLASSES.items()
        }
        # Modal form state (hosted by FormScreen)
        self.form: Form | None = None
        self.form_id: str = ""
        self.form_title: str = ""
        self.form_description: str = ""
        self.current_screen = self.screens[Screen.MAIN_MENU.value]

    # ------------------------------------------------------------------
    # Theme / settings helpers
    # ------------------------------------------------------------------
    @property
    def theme_use_nerd_font(self) -> bool:
        return bool(self.theme.use_nerd_font)

    @property
    def theme_use_color(self) -> bool:
        return bool(self.theme.use_color)

    def dispatch(self, action: Any) -> None:
        """Apply a navigation action and switch to the resulting screen."""
        old_screen = self.state.current_screen
        self.state = reducer(self.state, action)
        if self.state.current_screen != old_screen:
            self.current_screen = self.screens[self.state.current_screen.value]
            self.current_screen.on_enter()

    def go_back(self) -> None:
        """Go back one navigation level; quit when already on the main menu."""
        if self.state.nav_stack:
            self.dispatch(GoBack())
        elif self.state.current_screen == Screen.MAIN_MENU:
            self.quit()

    def quit(self) -> None:
        self.running = False

    def set_status(self, message: str, error: bool = False) -> None:
        action = SetError(message) if error else SetStatus(message)
        self.state = reducer(self.state, action)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def _make_layout(self) -> Layout:
        try:
            size = os.get_terminal_size()
            width = self.config.terminal_width or size.columns
            height = max(20, size.lines)
        except OSError:
            width, height = 80, 24
        return Layout(width, height)

    def _status_line(self) -> str:
        """Last status/error message, rendered as a footer line."""
        theme = self.theme
        if self.state.error_message:
            return theme.error(f"  {theme.icons.cross} {self.state.error_message}")
        if self.state.status_message:
            return theme.success(f"  {theme.icons.check} {self.state.status_message}")
        return ""

    def _draw(self) -> None:
        layout = self._make_layout()
        lines = self.current_screen.render(layout)
        status = self._status_line()
        if status:
            lines.append("")
            lines.append(status)
        out = CLEAR_SCREEN + CURSOR_HOME + "\n".join(lines)
        sys.stdout.write(out)
        sys.stdout.flush()

    def _handle_mouse(self, key: str) -> None:
        """Handle SGR mouse events: wheel scrolls, clicks select menu items."""
        parts = key.split(":")
        if len(parts) < 5:
            return
        try:
            button = int(parts[1])
            col = int(parts[2])
            row = int(parts[3])
        except ValueError:
            return
        press = parts[4] == "P"

        if button in (64, 65):  # wheel up / wheel down
            action = Action(ActionType.SCROLL_DOWN if button == 65 else ActionType.SCROLL_UP)
            self.current_screen.handle_action(action)
            return
        if not press or button not in (0, 1, 2):  # releases, drags, other buttons
            return
        self.current_screen.handle_click(row, col)

    def run(self) -> None:
        try:
            with alternate_screen(), raw_mode():
                enable_mouse()
                self._draw()
                while self.running:
                    key = get_key()
                    if key == "":
                        break  # EOF (e.g. piped input)
                    screen = self.current_screen
                    if key.startswith("MOUSE"):
                        self._handle_mouse(key)
                        self._draw()
                        continue
                    if screen.captures_all_keys:
                        # Modal form: route every key to the form so single
                        # letters/numbers can be typed without being intercepted
                        # by global shortcuts (j/k/h/l, 1-9, ...).
                        screen.handle_raw_key(key)
                        self._draw()
                        continue
                    if len(key) == 1 and key.isprintable() and screen.handle_shortcut(key):
                        self._draw()
                        continue
                    action = get_action(key)
                    if action is not None:
                        if action.type == ActionType.HELP:
                            self.dispatch(SetScreen(Screen.HELP))
                        elif action.type == ActionType.QUIT:
                            self.quit()
                        else:
                            screen.handle_action(action)
                    else:
                        screen.handle_raw_key(key)
                    self._draw()
        except KeyboardInterrupt:
            pass
        finally:
            disable_mouse()
            show_cursor()

    # ------------------------------------------------------------------
    # Data management
    # ------------------------------------------------------------------
    def show_generate_form(self) -> None:
        state = self.state
        self._open_form(
            "generate",
            "Generate Synthetic Dataset",
            "Create random pyramid / non-pyramid samples",
            Form(fields=[
                {"name": "max_vertices", "label": "Max Vertices", "type": "int",
                 "value": str(state.input_handler.max_vertices), "required": True, "validator": _positive_int},
                {"name": "n_pyramids", "label": "Number of Pyramids", "type": "int",
                 "value": "100", "required": True, "validator": _positive_int},
                {"name": "n_others", "label": "Number of Other Shapes", "type": "int",
                 "value": "100", "required": True, "validator": _positive_int},
            ]),
        )

    def show_import_csv_form(self) -> None:
        self._open_form(
            "import_csv",
            "Import CSV File",
            "Load a dataset from a CSV file (last column = label)",
            Form(fields=[
                {"name": "path", "label": "CSV Path", "type": "str",
                 "value": "", "required": True, "validator": _required},
            ]),
        )

    def show_dataset_preview(self) -> None:
        if self.state.data is None:
            self.set_status("No dataset loaded.", error=True)
            return
        self.dispatch(SetScreen(Screen.PREVIEW))

    def _generate_dataset(self, values: dict[str, str]) -> None:
        try:
            max_vertices = int(values["max_vertices"])
            n_pyramids = int(values["n_pyramids"])
            n_others = int(values["n_others"])
        except (ValueError, KeyError):
            self.set_status("Invalid dataset parameters.", error=True)
            return

        try:
            data, meta = self.state.pyramid_generator.generate_dataset(
                max_vertices=max_vertices,
                coords_per_vertex=self.state.input_handler.coordinates_per_vertex,
                n_pyramids=n_pyramids,
                n_non_pyramids=n_others,
                shuffle=True,
            )
        except Exception as e:  # noqa: BLE001
            self.set_status(f"Dataset generation failed: {e}", error=True)
            return

        self.state = reducer(self.state, SetData(data.astype(np.float32), meta))
        self.set_status(
            f"Dataset generated: {len(data)} samples "
            f"({n_pyramids} pyramids / {n_others} other shapes)"
        )

    def _import_csv(self, path: str) -> None:
        path = path.strip().strip('"').strip("'")
        if not path:
            self.set_status("No file path given.", error=True)
            return
        if not os.path.exists(path):
            self.set_status(f"File not found: {path}", error=True)
            return

        try:
            with open(path, newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                rows = [row for row in reader if row]
            if not rows:
                raise ValueError("The CSV file is empty.")

            first_row = rows[0]
            has_header = any(
                not cell.replace(".", "", 1).replace("-", "", 1).isdigit()
                for cell in first_row
            )
            if has_header:
                rows = rows[1:]

            data = np.array(rows, dtype=np.float32)
            if data.ndim != 2 or data.shape[1] < 2:
                raise ValueError("The CSV must contain at least two columns.")
        except (OSError, ValueError, csv.Error) as exc:
            self.set_status(f"CSV import failed: {exc}", error=True)
            return

        self.state = reducer(self.state, SetData(data, []))
        self.set_status(f"Loaded {len(data)} samples from {path}")

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def update_training_config(self, values: dict[str, str]) -> None:
        try:
            hidden = int(values["hidden_size"])
            epochs = int(values["epochs"])
            lr = float(values["learning_rate"])
            val_split = float(values["val_split"])
        except (ValueError, KeyError):
            self.set_status("Invalid training configuration.", error=True)
            return

        self.state.hidden_size = hidden
        config = TrainConfig(
            epochs=epochs,
            learning_rate=lr,
            val_split=val_split,
            seed=self.state.train_config.seed,
        )
        self.state = reducer(self.state, UpdateConfig(config))
        self.set_status("Training configuration updated.")

    def start_training(self) -> None:
        state = self.state
        if state.data is None:
            self.set_status("No dataset loaded. Generate or import data first.", error=True)
            return

        try:
            prepared, _ = state.input_handler.filter_and_prepare(state.data, fit=True)
        except Exception as e:  # noqa: BLE001
            self.set_status(f"Data preparation failed: {e}", error=True)
            return

        X_all = prepared[:, :-1]
        y_all = prepared[:, -1:]
        input_size = X_all.shape[1]

        rng = np.random.default_rng(state.train_config.seed)
        indices = rng.permutation(len(prepared))
        split = int(len(indices) * 0.8)
        train_idx, val_idx = indices[:split], indices[split:]
        X_train, y_train = X_all[train_idx], y_all[train_idx]
        X_val = X_all[val_idx] if len(val_idx) else X_train
        y_val = y_all[val_idx] if len(val_idx) else y_train

        can_continue = state.can_continue_training(input_size, state.hidden_size)
        if can_continue and state.model is not None:
            net = state.model
            train_losses = list(state.train_losses)
            val_losses = list(state.val_losses)
        else:
            net = NeuralNet(
                input_size=input_size,
                hidden_size=state.hidden_size,
                seed=state.train_config.seed,
            )
            train_losses = []
            val_losses = []

        epochs = state.train_config.epochs
        lr = state.train_config.learning_rate

        progress = self.screens[Screen.PROGRESS.value]
        assert isinstance(progress, ProgressScreen)
        progress.set_task("Training neural network...", epochs)
        progress.cancelled = False
        self.dispatch(SetScreen(Screen.PROGRESS))
        self._draw()

        step = max(1, epochs // 40)
        loss = 0.0
        val_loss = 0.0
        cancelled = False
        for epoch in range(1, epochs + 1):
            loss = net.train_step(X_train, y_train, lr)
            train_losses.append(loss)
            val_loss = net.loss(X_val, y_val)
            val_losses.append(val_loss)
            if epoch % step == 0 or epoch == epochs:
                progress.update(epoch, f"loss {loss:.5f} | val {val_loss:.5f}")
                self._draw()
            # Non-blocking ESC check so the user can cancel long runs.
            if poll_key() == "ESC":
                cancelled = True
                break

        if cancelled:
            progress.cancelled = True
            self.dispatch(GoBack())
            self.set_status(f"Training cancelled after {epoch} epochs (loss {loss:.5f}).")
            return

        self.state.model = net
        self.state.train_losses = train_losses
        self.state.val_losses = val_losses
        self.state.total_epochs += epochs
        self.state.last_validation = f"Trained on {input_size} features (val loss {val_loss:.5f})"

        self.dispatch(GoBack())
        self.set_status(f"Training complete — loss {loss:.5f}, val loss {val_loss:.5f}")

    # ------------------------------------------------------------------
    # Testing
    # ------------------------------------------------------------------
    def show_manual_input(self) -> None:
        max_len = (
            self.state.input_handler.max_vertices
            * self.state.input_handler.coordinates_per_vertex
        )
        self._open_form(
            "manual_input",
            "Manual Input",
            f"Enter up to {max_len} coordinates, comma-separated ('NaN' for empty points)",
            Form(fields=[
                {"name": "coordinates", "label": "Coordinates", "type": "str",
                 "value": "", "required": True, "validator": _required},
            ]),
        )

    def _submit_manual_input(self, text: str) -> None:
        state = self.state
        if state.model is None:
            self.set_status("No model trained. Train a model first.", error=True)
            return

        try:
            parts = [item.strip() for item in text.split(",") if item.strip()]
            values: list[float] = []
            for part in parts:
                if part.lower() in ("nan", "x", "_"):
                    values.append(np.nan)
                else:
                    values.append(float(part.replace(",", ".")))
        except ValueError:
            self.set_status("Invalid manual input. Use numbers separated by commas.", error=True)
            return

        if not values:
            self.set_status("No coordinates entered.", error=True)
            return

        prep = prepare_test_vector(state, np.array(values, dtype=np.float32))
        if prep is None:
            self.set_status("Test vector could not be prepared.", error=True)
            return

        pred = float(state.model.forward(prep["input_vector"])[0, 0])
        self.state = reducer(self.state, SetTestVector(prep["raw"], None))
        self.state.test_prediction = pred
        self.set_status("Prediction computed for manual input.")

    def generate_test_vector(self, pyramid: bool) -> None:
        state = self.state
        if state.model is None:
            self.set_status("No model trained. Train a model first.", error=True)
            return

        gen = state.pyramid_generator
        if pyramid:
            raw = gen.generate_single_pyramid(
                state.input_handler.max_vertices,
                state.input_handler.coordinates_per_vertex,
            )
            expected = 1
        else:
            raw = gen.generate_single_non_pyramid(
                state.input_handler.max_vertices,
                state.input_handler.coordinates_per_vertex,
            )
            expected = 0

        prep = prepare_test_vector(state, raw)
        if prep is None:
            self.set_status("Test vector could not be prepared.", error=True)
            return

        pred = float(state.model.forward(prep["input_vector"])[0, 0])
        self.state = reducer(self.state, SetTestVector(prep["raw"], expected))
        self.state.test_prediction = pred
        self.set_status("Test vector generated — see 'Last Test Result' on the Test screen.")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def show_export_json_form(self) -> None:
        self._open_form(
            "export_json",
            "Export JSON",
            "Save model weights and config as JSON",
            Form(fields=[
                {"name": "filename", "label": "Filename", "type": "str",
                 "value": "model_export.json", "required": True, "validator": _required},
            ]),
        )

    def show_export_markdown_form(self) -> None:
        self._open_form(
            "export_markdown",
            "Export Markdown Report",
            "Generate a documentation report",
            Form(fields=[
                {"name": "filename", "label": "Filename", "type": "str",
                 "value": "model_report.md", "required": True, "validator": _required},
            ]),
        )

    def _resolve_export_path(self, filename: str) -> Path:
        name = (filename or "").strip() or "model_export.json"
        export_path = Path(os.path.expanduser(name))
        if not export_path.is_absolute():
            export_path = _downloads_folder() / export_path
        if not export_path.parent.exists():
            export_path.parent.mkdir(parents=True, exist_ok=True)
        return export_path

    def export_json(self, filename: str | None = None) -> None:
        state = self.state
        if state.model is None:
            self.set_status("No model to export. Train a model first.", error=True)
            return

        export_path = self._resolve_export_path(filename or "model_export.json")
        if export_path.is_dir():
            self.set_status(f"'{export_path}' is a directory.", error=True)
            return

        try:
            state.model.save_json(
                export_path,
                total_epochs=state.total_epochs,
                last_loss=float(state.val_losses[-1]) if state.val_losses else 0.0,
                validation=state.last_validation,
                normalization_params=state.input_handler.normalization_params,
            )
            self.set_status(f"Model saved to {export_path}")
        except (OSError, PermissionError) as exc:
            fallback = Path.home() / export_path.name
            try:
                state.model.save_json(
                    fallback,
                    total_epochs=state.total_epochs,
                    last_loss=float(state.val_losses[-1]) if state.val_losses else 0.0,
                    validation=state.last_validation,
                    normalization_params=state.input_handler.normalization_params,
                )
                self.set_status(f"Saved to fallback location: {fallback}")
            except (OSError, PermissionError):
                self.set_status(f"Model export failed: {exc}", error=True)

    def export_markdown(self, filename: str | None = None) -> None:
        state = self.state
        if state.model is None:
            self.set_status("No model to export. Train a model first.", error=True)
            return

        net = state.model
        last_loss = float(state.val_losses[-1]) if state.val_losses else 0.0
        md = (
            "# Model Export Report\n\n"
            "## 1. Model Architecture\n\n"
            "| Layer | Nodes | Activation |\n"
            "| :--- | :--- | :--- |\n"
            f"| **Input layer** | {net.input_size} | — |\n"
            f"| **Hidden layer** | {net.hidden_size} | ReLU |\n"
            "| **Output layer** | 1 | Sigmoid |\n\n"
            "## 2. Training Metrics\n\n"
            "| Metric | Value |\n"
            "| :--- | :--- |\n"
            f"| Total epochs completed | {_format_epochs(state.total_epochs)} |\n"
            f"| Final error value (MSE loss) | {last_loss:.6f} |\n"
            f"| Validation | {state.last_validation or '—'} |\n\n"
            "## 3. Weight Snapshot\n\n"
            f"- W1 shape: {net.W1.shape}\n"
            f"- W2 shape: {net.W2.shape}\n"
            f"- W1[0,0] = {net.W1.flat[0]:.5f}\n"
            f"- W2[0,0] = {net.W2.flat[0]:.5f}\n"
            f"- b1[0] = {net.b1.flat[0]:.5f}\n"
            f"- b2[0] = {net.b2.flat[0]:.5f}\n"
        )

        export_path = self._resolve_export_path(filename or "model_report.md")
        if export_path.is_dir():
            self.set_status(f"'{export_path}' is a directory.", error=True)
            return

        try:
            export_path.write_text(md, encoding="utf-8")
            self.set_status(f"Report saved to {export_path}")
        except (OSError, PermissionError) as exc:
            fallback = Path.home() / export_path.name
            try:
                fallback.write_text(md, encoding="utf-8")
                self.set_status(f"Saved to fallback location: {fallback}")
            except (OSError, PermissionError):
                self.set_status(f"Report export failed: {exc}", error=True)

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def toggle_nerd_font(self) -> None:
        new_value = not bool(self.theme.use_nerd_font)
        self.config.use_nerd_font = new_value
        self.theme.apply(use_nerd_font=new_value)
        save_config(self.config)
        self.set_status(f"Nerd Font icons: {'On' if new_value else 'Off'}")

    def toggle_color(self) -> None:
        new_value = not bool(self.theme.use_color)
        self.config.use_color = new_value
        self.theme.apply(use_color=new_value)
        save_config(self.config)
        self.set_status(f"Colors: {'On' if new_value else 'Off'}")

    def set_language(self, language: str) -> None:
        lang = language if language in ("en", "de") else "en"
        self.config.language = lang
        self.state.language = lang
        save_config(self.config)
        self.set_status(f"Language set to {lang.upper()}")

    # ------------------------------------------------------------------
    # Modal forms
    # ------------------------------------------------------------------
    def _open_form(self, form_id: str, title: str, description: str, form: Form) -> None:
        self.form_id = form_id
        self.form_title = title
        self.form_description = description
        self.form = form
        self.dispatch(SetScreen(Screen.FORM))

    def cancel_form(self) -> None:
        self.form = None
        self.dispatch(GoBack())

    def on_form_submit(self, values: dict[str, str]) -> None:
        form_id = self.form_id
        self.form = None
        if form_id == "generate":
            self._generate_dataset(values)
        elif form_id == "import_csv":
            self._import_csv(values.get("path", ""))
        elif form_id == "manual_input":
            self._submit_manual_input(values.get("coordinates", ""))
        elif form_id == "export_json":
            self.export_json(values.get("filename"))
        elif form_id == "export_markdown":
            self.export_markdown(values.get("filename"))
        self.dispatch(GoBack())


def main() -> None:
    """Entry point: load config, init theme, and run the app."""
    config = get_or_create_config()
    init_theme(nerd_font=config.use_nerd_font, color=config.use_color)
    app = TUIApp(config)
    app.run()


if __name__ == "__main__":
    main()
