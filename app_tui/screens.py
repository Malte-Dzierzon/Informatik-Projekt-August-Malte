"""Screen implementations for the TUI application."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .components import Form, Menu, MenuItem, Panel, Progress, StatusBar, Table
from .input import Action, ActionType
from .render import Layout
from .state import Screen, SetScreen
from .theme import get_theme

if TYPE_CHECKING:
    from .main import TUIApp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ACTION_TO_KEY = {
    ActionType.MENU_UP: "UP",
    ActionType.MENU_DOWN: "DOWN",
    ActionType.MENU_SELECT: "ENTER",
    ActionType.FORM_CANCEL: "ESC",
    ActionType.TAB_NEXT: "TAB",
    ActionType.TAB_PREV: "S-TAB",
}


def _action_to_key(action: Action) -> str | None:
    """Convert an input Action back to a raw key for form components."""
    if action.type == ActionType.NUMBER:
        return str(action.payload)
    return _ACTION_TO_KEY.get(action.type)


def _positive_int_validator(value: str) -> bool | str:
    try:
        return int(value) > 0
    except ValueError:
        return "Must be a positive integer"


def _rate_validator(value: str) -> bool | str:
    try:
        return 0 < float(value) < 1
    except ValueError:
        return "Must be a number between 0 and 1"


def _nonempty_validator(value: str) -> bool | str:
    return bool(value.strip()) or "Value required"


def _full_layout(layout: Layout) -> Layout:
    """Layout that spans the full available width (no padding)."""
    return Layout(layout.inner_width, layout.height, padding=0)


class ScreenBase:
    """Base class for all screens."""

    # Screens that capture every key (e.g. modal forms) route all input to
    # handle_raw_key so that single letters can be typed without being
    # intercepted by global shortcuts (j/k/h/l, numbers, ...).
    captures_all_keys: bool = False

    def __init__(self, app: TUIApp):
        self.app = app
        self.theme = get_theme()
        # Dummy menu so the attribute is typed; subclasses replace it.
        self.menu: Menu = Menu(items=[])
        # Persisted cursor position of this screen instance (survives
        # leaving/returning to the screen).
        self.selection = 0
        # Rendered line indices of the menu items (for mouse clicks).
        self.menu_hit_rows: list[int] = []

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def render(self, layout: Layout) -> list[str]:
        return []

    def handle_action(self, action: Action) -> bool:
        return False

    def handle_raw_key(self, key: str) -> bool:
        """Handle keys that did not map to an Action (e.g. form input)."""
        return False

    def handle_shortcut(self, key: str) -> bool:
        """Handle single-letter menu shortcuts (item.key)."""
        menu = self.menu
        if not key:
            return False
        k = key.lower()
        for i, item in enumerate(menu.items):
            if item.enabled and item.key and item.key.lower() == k:
                menu.selected = i
                self.selection = i
                self._activate(i)
                return True
        return False

    def handle_click(self, row: int, col: int) -> bool:
        """Handle a mouse click at 1-based terminal coordinates (row, col).

        Default behavior for menu screens: move the cursor to the clicked item
        (activate it with Enter). Returns True if the click hit a menu item.
        """
        idx = self._hit_index(row)
        if idx is None:
            return False
        item = self.menu.items[idx]
        if item.enabled:
            self.menu.selected = idx
            self.selection = idx
            return True
        return False

    def _hit_index(self, row: int) -> int | None:
        """Map a 1-based terminal row to the menu item index rendered there."""
        line = row - 1
        for idx, rendered_row in enumerate(self.menu_hit_rows):
            if rendered_row == line:
                return idx
        return None

    def _render_menu_lines(self, lines: list[str], layout: Layout, height: int) -> None:
        """Render self.menu into ``lines`` and record the hit rows for clicks."""
        menu_layout = _full_layout(layout)
        menu_layout.height = height
        start = len(lines)
        menu_lines = self.menu.render(menu_layout)
        self.menu_hit_rows = [start + i for i in range(len(menu_lines))]
        lines.extend(menu_lines)

    def _activate(self, index: int) -> None:
        """Activate the menu item at index. Overridden by subclasses."""

    def _menu_action(self, action: Action) -> bool:
        """Common vim/arrow navigation for screens with a self.menu."""
        menu = self.menu
        if action.type == ActionType.MENU_UP:
            menu.handle_key("UP")
            self.selection = menu.selected
            return True
        if action.type == ActionType.MENU_DOWN:
            menu.handle_key("DOWN")
            self.selection = menu.selected
            return True
        if action.type == ActionType.MENU_SELECT:
            self.selection = menu.selected
            self._activate(menu.selected)
            return True
        if action.type == ActionType.NUMBER:
            idx = action.payload - 1
            if 0 <= idx < len(menu.items) and menu.items[idx].enabled:
                self.selection = idx
                self._activate(idx)
            return True
        if action.type in (ActionType.MENU_BACK, ActionType.FORM_CANCEL):
            self.app.go_back()
            return True
        return False


class MainMenuScreen(ScreenBase):
    """Main menu screen."""

    def __init__(self, app: TUIApp):
        super().__init__(app)
        self.menu = Menu(
            items=[
                MenuItem("Data Management", "d", "data_menu", "Load, generate, or inspect datasets"),
                MenuItem("Train Model", "t", "train_menu", "Configure and start training"),
                MenuItem("Interactive Test", "i", "test_menu", "Test model with generated or manual input"),
                MenuItem("Export Model", "e", "export_menu", "Save model weights and reports"),
                MenuItem("Settings", "s", "settings_menu", "Configure application preferences"),
                MenuItem("Help", "h", "help", "Show keyboard shortcuts and info"),
                MenuItem("Quit", "q", "quit", "Exit application"),
            ],
            selected=0,
        )

    def on_enter(self) -> None:
        self.menu.selected = self.selection

    def _activate(self, index: int) -> None:
        item = self.menu.items[index]
        if item.action == "quit":
            self.app.quit()
        elif item.action:
            self.app.dispatch(SetScreen(Screen(item.action)))

    def _build_status_content(self) -> list[str]:
        state = self.app.state
        theme = self.theme
        content = []

        if state.data is not None:
            rows = len(state.data)
            pyr = int(np.sum(state.data[:, -1] == 1.0))
            other = rows - pyr
            content.append(f"{theme.icons.data} Dataset: {theme.accent(str(rows))} samples  |  {theme.success(f'{pyr} pyramids')}  |  {theme.muted(f'{other} others')}")
            content.append(f"  Features: {state.data.shape[1] - 1}  |  Vertices: ~{state.max_vertices}")
        else:
            content.append(f"{theme.icons.data} No dataset loaded")
            content.append("  Press 'd' or '1' to load/generate data")

        if state.model is not None:
            model = state.model
            content.append("")
            content.append(f"{theme.icons.model} Model: {theme.accent(f'{model.input_size} → {model.hidden_size} → 1')}")
            content.append(f"  Epochs: {theme.accent(str(state.total_epochs))}  |  Val Loss: {theme.accent(f'{state.val_losses[-1]:.5f}' if state.val_losses else '—')}")
            if state.last_validation:
                content.append(f"  {theme.success(state.last_validation)}")
        else:
            content.append("")
            content.append(f"{theme.icons.model} No model trained")
            content.append("  Press 't' or '2' to train a model")

        return content

    def render(self, layout: Layout) -> list[str]:
        theme = self.theme
        lines = []

        # Header
        header = Panel(
            title=f"{theme.icons.pyramid} Pyramid Classification",
            content=[
                theme.primary("Neural Network Classifier for 3D Pyramid Detection"),
                theme.muted("Terminal User Interface  |  Informatik-Projekt"),
            ],
            border_style="double",
        )
        lines.extend(header.render(layout))

        lines.append("")

        # Status panel
        status_panel = Panel(
            title="Status Overview",
            content=self._build_status_content(),
            border_style="single",
        )
        lines.extend(status_panel.render(layout))

        lines.append("")

        # Menu
        self._render_menu_lines(lines, layout, 12)

        lines.append("")

        # Footer hints
        hints = StatusBar(
            left="v1.0.0",
            right="",
            hints=["d:Data  t:Train  i:Test  e:Export  s:Settings  h:Help  q:Quit"],
        )
        lines.extend(hints.render(layout))

        return lines

    def handle_action(self, action: Action) -> bool:
        return self._menu_action(action)


class DataMenuScreen(ScreenBase):
    """Data management screen."""

    def __init__(self, app: TUIApp):
        super().__init__(app)
        self.menu = Menu(
            items=[
                MenuItem("Generate Synthetic Dataset", "g", "generate", "Create random pyramid/non-pyramid data"),
                MenuItem("Import CSV File", "i", "import_csv", "Load dataset from CSV file"),
                MenuItem("View Dataset Preview", "v", "preview", "Inspect current dataset"),
                MenuItem("Back to Main Menu", "b", "back", "Return to main menu"),
            ],
            selected=0,
        )

    def on_enter(self) -> None:
        self.menu.selected = self.selection

    def _activate(self, index: int) -> None:
        item = self.menu.items[index]
        if item.action == "generate":
            self.app.show_generate_form()
        elif item.action == "import_csv":
            self.app.show_import_csv_form()
        elif item.action == "preview":
            self.app.show_dataset_preview()
        elif item.action == "back":
            self.app.go_back()

    def render(self, layout: Layout) -> list[str]:
        theme = self.theme
        lines = []

        header = Panel(
            title=f"{theme.icons.data} Data Management",
            content=[theme.primary("Manage training datasets")],
            border_style="double",
        )
        lines.extend(header.render(layout))

        lines.append("")

        # Current dataset info
        state = self.app.state
        if state.data is not None:
            rows = len(state.data)
            pyr = int(np.sum(state.data[:, -1] == 1.0))
            other = rows - pyr
            info = Panel(
                title="Current Dataset",
                content=[
                    f"Samples: {theme.accent(str(rows))}",
                    f"Pyramids: {theme.success(str(pyr))}  |  Others: {theme.muted(str(other))}",
                    f"Features: {state.data.shape[1] - 1}  |  Vertices: ~{state.max_vertices}",
                ],
                border_style="single",
            )
            lines.extend(info.render(layout))
        else:
            info = Panel(
                title="Current Dataset",
                content=[theme.muted("No dataset loaded")],
                border_style="single",
            )
            lines.extend(info.render(layout))

        lines.append("")

        self._render_menu_lines(lines, layout, 8)

        lines.append("")

        hints = StatusBar(hints=["g:Generate  i:Import  v:Preview  b/Esc:Back"])
        lines.extend(hints.render(layout))

        return lines

    def handle_action(self, action: Action) -> bool:
        return self._menu_action(action)


class TrainMenuScreen(ScreenBase):
    """Training configuration screen."""

    def __init__(self, app: TUIApp):
        super().__init__(app)
        self.menu = Menu(
            items=[
                MenuItem("Start Training", "s", "start", "Begin training with current settings"),
                MenuItem("Configure Parameters", "c", "config", "Set epochs, learning rate, hidden nodes"),
                MenuItem("Back to Main Menu", "b", "back", "Return to main menu"),
            ],
            selected=0,
        )
        self.config_form: Form | None = None

    def on_enter(self) -> None:
        self.menu.selected = self.selection

    def _activate(self, index: int) -> None:
        item = self.menu.items[index]
        if item.action == "start":
            self.app.start_training()
        elif item.action == "config":
            self.show_config_form()
        elif item.action == "back":
            self.app.go_back()

    def render(self, layout: Layout) -> list[str]:
        theme = self.theme
        lines = []

        header = Panel(
            title=f"{theme.icons.train} Train Model",
            content=[theme.primary("Configure and start training")],
            border_style="double",
        )
        lines.extend(header.render(layout))

        lines.append("")

        # Current config
        state = self.app.state
        config = state.train_config
        hidden = state.hidden_size

        input_size_text = "auto-detect"
        can_continue = False
        if state.data is not None:
            try:
                prepared = state.input_handler._transform_to_distances(state.data[:, :-1])
                input_size_text = str(prepared.shape[1])
                can_continue = state.can_continue_training(prepared.shape[1], hidden)
            except Exception:  # noqa: BLE001
                input_size_text = "auto-detect"

        config_content = [
            f"Input Nodes: {theme.accent(input_size_text)}",
            f"Hidden Nodes: {theme.accent(str(hidden))}",
            f"Learning Rate: {theme.accent(str(config.learning_rate))}",
            f"Epochs: {theme.accent(str(config.epochs))}",
            f"Val Split: {theme.accent(str(config.val_split))}",
        ]
        if can_continue:
            config_content.append(f"{theme.success('✓')} Existing model matches — can continue training")

        config_panel = Panel(
            title="Training Configuration",
            content=config_content,
            border_style="single",
        )
        lines.extend(config_panel.render(layout))

        lines.append("")

        if self.config_form is not None:
            form_layout = _full_layout(layout)
            form_layout.height = 8
            lines.extend(self.config_form.render(form_layout))
            lines.append("")

        self._render_menu_lines(lines, layout, 8)

        lines.append("")

        hints = StatusBar(hints=["s:Start  c:Config  b/Esc:Back"])
        lines.extend(hints.render(layout))

        return lines

    def show_config_form(self) -> None:
        state = self.app.state
        self.config_form = Form(
            fields=[
                {"name": "hidden_size", "label": "Hidden Nodes", "type": "int", "value": str(state.hidden_size), "required": True, "validator": _positive_int_validator},
                {"name": "learning_rate", "label": "Learning Rate", "type": "float", "value": str(state.train_config.learning_rate), "required": True, "validator": _rate_validator},
                {"name": "epochs", "label": "Epochs", "type": "int", "value": str(state.train_config.epochs), "required": True, "validator": _positive_int_validator},
                {"name": "val_split", "label": "Val Split", "type": "float", "value": str(state.train_config.val_split), "required": True, "validator": _rate_validator},
            ],
        )

    def _handle_form_result(self, result: str | None) -> bool:
        if self.config_form is None:
            return False
        if result == "submit":
            if self.config_form.validate():
                self.app.update_training_config(self.config_form.get_values())
                self.config_form = None
            return True
        if result == "cancel":
            self.config_form = None
            return True
        return result is not None

    def handle_action(self, action: Action) -> bool:
        if self.config_form is not None:
            key = _action_to_key(action)
            if key is not None:
                self._handle_form_result(self.config_form.handle_key(key))
            return True
        return self._menu_action(action)

    def handle_raw_key(self, key: str) -> bool:
        if self.config_form is not None:
            return self._handle_form_result(self.config_form.handle_key(key))
        return False

    def handle_shortcut(self, key: str) -> bool:
        if self.config_form is not None:
            return False
        return super().handle_shortcut(key)


class TestMenuScreen(ScreenBase):
    """Interactive testing screen."""

    def __init__(self, app: TUIApp):
        super().__init__(app)
        self.menu = Menu(
            items=[
                MenuItem("Generate Pyramid (Label=1)", "p", "gen_pyr", "Create random pyramid and test"),
                MenuItem("Generate Non-Pyramid (Label=0)", "n", "gen_non", "Create random non-pyramid and test"),
                MenuItem("Manual Input", "m", "manual", "Enter coordinates manually"),
                MenuItem("Back to Main Menu", "b", "back", "Return to main menu"),
            ],
            selected=0,
        )

    def _activate(self, index: int) -> None:
        item = self.menu.items[index]
        if item.action == "gen_pyr":
            self.app.generate_test_vector(pyramid=True)
        elif item.action == "gen_non":
            self.app.generate_test_vector(pyramid=False)
        elif item.action == "manual":
            self.app.show_manual_input()
        elif item.action == "back":
            self.app.go_back()

    def render(self, layout: Layout) -> list[str]:
        theme = self.theme
        lines = []

        if self.app.state.model is None:
            header = Panel(
                title=f"{theme.icons.test} Interactive Test",
                content=[theme.warning("No model trained. Please train a model first.")],
                border_style="double",
            )
            lines.extend(header.render(layout))
            lines.append("")
            hints = StatusBar(hints=["b/Esc:Back"])
            lines.extend(hints.render(layout))
            return lines

        header = Panel(
            title=f"{theme.icons.test} Interactive Test",
            content=[theme.primary("Test model with generated or manual input")],
            border_style="double",
        )
        lines.extend(header.render(layout))

        lines.append("")

        # Show last result if available
        if self.app.state.test_vector is not None:
            state = self.app.state
            pred = state.test_prediction
            expected = state.test_expected

            if pred is not None:
                pred_class = 1 if pred >= 0.5 else 0
                conf = pred if pred_class == 1 else 1 - pred
                result_color = theme.success if pred_class == expected else theme.error
                result_text = "Pyramid" if pred_class == 1 else "Non-Pyramid"
                expected_text = "Pyramid" if expected == 1 else "Non-Pyramid" if expected is not None else "Unknown"

                result_content = [
                    f"Prediction: {result_color(result_text)}  (confidence: {conf * 100:.1f}%)",
                    f"Expected: {theme.accent(expected_text)}",
                    f"Raw Output: {theme.accent(f'{pred:.5f}')}",
                ]
            else:
                result_content = ["Test vector ready. Press Enter to run prediction."]

            result_panel = Panel(
                title="Last Test Result",
                content=result_content,
                border_style="single",
            )
            lines.extend(result_panel.render(layout))
            lines.append("")

        self._render_menu_lines(lines, layout, 8)

        lines.append("")

        hints = StatusBar(hints=["p:Pyramid  n:Non-Pyramid  m:Manual  b/Esc:Back"])
        lines.extend(hints.render(layout))

        return lines

    def handle_action(self, action: Action) -> bool:
        return self._menu_action(action)


class ExportMenuScreen(ScreenBase):
    """Model export screen."""

    def __init__(self, app: TUIApp):
        super().__init__(app)
        self.menu = Menu(
            items=[
                MenuItem("Export JSON (Weights + Config)", "j", "json", "Save model as JSON file"),
                MenuItem("Export Markdown Report", "m", "markdown", "Generate documentation report"),
                MenuItem("Back to Main Menu", "b", "back", "Return to main menu"),
            ],
            selected=0,
        )

    def _activate(self, index: int) -> None:
        item = self.menu.items[index]
        if item.action == "json":
            self.app.show_export_json_form()
        elif item.action == "markdown":
            self.app.show_export_markdown_form()
        elif item.action == "back":
            self.app.go_back()

    def render(self, layout: Layout) -> list[str]:
        theme = self.theme
        lines = []

        if self.app.state.model is None:
            header = Panel(
                title=f"{theme.icons.export} Export Model",
                content=[theme.warning("No model to export. Please train a model first.")],
                border_style="double",
            )
            lines.extend(header.render(layout))
            lines.append("")
            hints = StatusBar(hints=["b/Esc:Back"])
            lines.extend(hints.render(layout))
            return lines

        header = Panel(
            title=f"{theme.icons.export} Export Model",
            content=[theme.primary("Save trained model and reports")],
            border_style="double",
        )
        lines.extend(header.render(layout))

        lines.append("")

        model = self.app.state.model
        info = Panel(
            title="Model Info",
            content=[
                f"Architecture: {theme.accent(f'{model.input_size} → {model.hidden_size} → 1')}",
                f"Total Epochs: {theme.accent(str(self.app.state.total_epochs))}",
                f"Val Loss: {theme.accent(f'{self.app.state.val_losses[-1]:.5f}' if self.app.state.val_losses else '—')}",
            ],
            border_style="single",
        )
        lines.extend(info.render(layout))

        lines.append("")

        self._render_menu_lines(lines, layout, 8)

        lines.append("")

        hints = StatusBar(hints=["j:JSON  m:Markdown  b/Esc:Back"])
        lines.extend(hints.render(layout))

        return lines

    def handle_action(self, action: Action) -> bool:
        return self._menu_action(action)


class SettingsMenuScreen(ScreenBase):
    """Settings screen."""

    def __init__(self, app: TUIApp):
        super().__init__(app)
        self.menu = Menu(
            items=[
                MenuItem("Toggle Nerd Font Icons", "n", "toggle_nerd", "Use Nerd Font icons if available"),
                MenuItem("Toggle Colors", "c", "toggle_color", "Enable/disable colored output"),
                MenuItem("Back to Main Menu", "b", "back", "Return to main menu"),
            ],
            selected=0,
        )

    def on_enter(self) -> None:
        self.menu.selected = self.selection
        self._update_menu_labels()

    def _update_menu_labels(self) -> None:
        config = self.app.config
        theme = self.theme

        # Nerd font status
        nerd_status = "On" if self.app.theme_use_nerd_font else "Off"
        if config.use_nerd_font is None:
            nerd_status += " (auto)"
        self.menu.items[0].label = f"Nerd Font Icons: {theme.accent(nerd_status)}"

        # Color status
        color_status = "On" if self.app.theme_use_color else "Off"
        if config.use_color is None:
            color_status += " (auto)"
        self.menu.items[1].label = f"Colors: {theme.accent(color_status)}"

    def _activate(self, index: int) -> None:
        item = self.menu.items[index]
        if item.action == "toggle_nerd":
            self.app.toggle_nerd_font()
        elif item.action == "toggle_color":
            self.app.toggle_color()
        elif item.action == "back":
            self.app.go_back()

    def render(self, layout: Layout) -> list[str]:
        theme = self.theme
        lines = []

        header = Panel(
            title=f"{theme.icons.settings} Settings",
            content=[
                theme.primary("Configure application preferences"),
                theme.muted("Language: English  |  Version: v1.0.0"),
            ],
            border_style="double",
        )
        lines.extend(header.render(layout))

        lines.append("")

        self._update_menu_labels()
        self._render_menu_lines(lines, layout, 8)

        lines.append("")

        hints = StatusBar(hints=["n:Nerd Font  c:Colors  b/Esc:Back"])
        lines.extend(hints.render(layout))

        return lines

    def handle_action(self, action: Action) -> bool:
        return self._menu_action(action)


class HelpScreen(ScreenBase):
    """Help screen with keyboard shortcuts."""

    def __init__(self, app: TUIApp):
        super().__init__(app)
        self.scroll = 0

    def render(self, layout: Layout) -> list[str]:
        theme = self.theme
        lines = []

        header = Panel(
            title=f"{theme.icons.arrow_right} Help & Shortcuts",
            content=[theme.primary("Keyboard Controls")],
            border_style="double",
        )
        lines.extend(header.render(layout))

        lines.append("")

        help_items = [
            ("Navigation", [
                ("↑/k / ↓/j", "Move up/down in menus and lists"),
                ("←/h / →/l", "Go back / select item"),
                ("g / G", "Jump to first / last item"),
                ("PgUp / PgDn", "Scroll pages"),
                ("Mouse", "Click: select item  |  Wheel: scroll"),
            ]),
            ("Actions", [
                ("Enter / Space", "Select / activate"),
                ("1-9", "Quick select menu item"),
                ("q / Q", "Quit application"),
                ("Esc", "Go back one level / cancel"),
                ("?", "Show this help"),
            ]),
            ("Screens", [
                ("d", "Data Management"),
                ("t", "Train Model"),
                ("i", "Interactive Test"),
                ("e", "Export Model"),
                ("s", "Settings"),
                ("h", "Help"),
            ]),
        ]

        body: list[str] = []
        for section, items in help_items:
            section_panel = Panel(
                title=section,
                content=[f"  {theme.accent(key):<15} {desc}" for key, desc in items],
                border_style="single",
            )
            body.extend(section_panel.render(layout))
            body.append("")

        max_scroll = max(0, len(body) - max(4, layout.height - 4))
        self.scroll = min(max_scroll, max(0, self.scroll))
        lines.extend(body[self.scroll:])

        hints = StatusBar(hints=["↑/↓:Scroll  Esc:Back  q:Quit"])
        lines.extend(hints.render(layout))

        return lines

    def handle_action(self, action: Action) -> bool:
        if action.type in (ActionType.MENU_DOWN, ActionType.SCROLL_DOWN, ActionType.PAGE_DOWN):
            self.scroll += 3
            return True
        if action.type in (ActionType.MENU_UP, ActionType.SCROLL_UP, ActionType.PAGE_UP):
            self.scroll = max(0, self.scroll - 3)
            return True
        if action.type in (ActionType.MENU_BACK, ActionType.FORM_CANCEL):
            self.app.go_back()
            return True
        return False


class ProgressScreen(ScreenBase):
    """Progress overlay for long operations."""

    def __init__(self, app: TUIApp):
        super().__init__(app)
        self.progress = Progress(message="", total=0, current=0, style="bar")
        self.cancelled = False

    def set_task(self, message: str, total: int) -> None:
        self.progress.message = message
        self.progress.total = total
        self.progress.current = 0

    def update(self, current: int, message: str = "") -> None:
        self.progress.current = current
        if message:
            self.progress.message = message

    def render(self, layout: Layout) -> list[str]:
        theme = self.theme
        lines = []

        overlay = Panel(
            title=f"{theme.icons.train} Processing",
            content=self.progress.render(layout),
            border_style="double",
        )
        lines.extend(overlay.render(layout))

        lines.append("")

        hints = StatusBar(hints=["Esc:Cancel"])
        lines.extend(hints.render(layout))

        return lines

    def handle_action(self, action: Action) -> bool:
        if action.type == ActionType.FORM_CANCEL:
            self.cancelled = True
            self.app.go_back()
            return True
        return False


class FormScreen(ScreenBase):
    """Hosts the currently active modal form (app.form).

    Captures every key so that single letters and numbers can be typed into
    fields without being intercepted by global shortcuts (j/k/h/l, numbers).
    """

    captures_all_keys = True

    def _form_result(self, result: str | None) -> bool:
        form = self.app.form
        if result == "submit":
            if form is not None and form.validate():
                self.app.on_form_submit(form.get_values())
            return True
        if result == "cancel":
            self.app.cancel_form()
            return True
        return result is not None

    def render(self, layout: Layout) -> list[str]:
        theme = self.theme
        form = self.app.form
        if form is None:
            return []

        lines = []
        header = Panel(
            title=f"{theme.icons.settings} {self.app.form_title or 'Form'}",
            content=[theme.primary(self.app.form_description or "")],
            border_style="double",
        )
        lines.extend(header.render(layout))

        lines.append("")

        form_layout = _full_layout(layout)
        form_layout.height = len(form.fields) + 2
        lines.extend(form.render(form_layout))

        lines.append("")

        hints = StatusBar(hints=["Tab:Next field  Enter:Submit  Esc:Cancel"])
        lines.extend(hints.render(layout))

        return lines

    def handle_action(self, action: Action) -> bool:
        if self.app.form is None:
            return False
        key = _action_to_key(action)
        if key is None:
            return False
        return self._form_result(self.app.form.handle_key(key))

    def handle_raw_key(self, key: str) -> bool:
        if self.app.form is None:
            return False
        return self._form_result(self.app.form.handle_key(key))


class PreviewScreen(ScreenBase):
    """Dataset preview table."""

    def __init__(self, app: TUIApp):
        super().__init__(app)
        self.scroll = 0
        self.table: Table | None = None
        self._visible_rows = 8

    def _adjust_scroll(self, delta: int) -> None:
        if self.table is None:
            return
        max_offset = max(0, len(self.table.rows) - self._visible_rows)
        self.scroll = min(max_offset, max(0, self.scroll + delta))

    def render(self, layout: Layout) -> list[str]:
        state = self.app.state
        theme = self.theme
        lines = []

        if state.data is None:
            header = Panel(
                title=f"{theme.icons.data} Dataset Preview",
                content=[theme.warning("No dataset loaded.")],
                border_style="double",
            )
            lines.extend(header.render(layout))
            return lines

        data = state.data
        n_show = min(20, len(data))
        rows: list[list[str]] = []
        for idx in range(n_show):
            row = data[idx]
            feats = ", ".join(
                f"{v:.2f}" if not np.isnan(v) else "NaN"
                for v in row[:-1][:8]
            )
            if row[:-1].size > 8:
                feats += " ..."
            label = "Pyramid" if row[-1] == 1.0 else "Other"
            rows.append([str(idx + 1), feats, label])

        header = Panel(
            title=f"{theme.icons.data} Dataset Preview",
            content=[theme.primary(f"{len(data)} samples loaded")],
            border_style="double",
        )
        lines.extend(header.render(layout))

        lines.append("")

        table_layout = _full_layout(layout)
        table_layout.height = max(8, n_show + 4)
        self._visible_rows = max(1, table_layout.body_height - 2)
        self.table = Table(
            headers=["#", "Features (first 8)", "Label"],
            rows=rows,
            col_widths=[5, 55, 10],
        )
        self.table.scroll_offset = self.scroll
        lines.extend(self.table.render(table_layout))

        lines.append("")

        hints = StatusBar(hints=["↑/↓ or wheel: Scroll  Esc:Back"])
        lines.extend(hints.render(layout))

        return lines

    def handle_action(self, action: Action) -> bool:
        if action.type in (ActionType.MENU_DOWN, ActionType.SCROLL_DOWN, ActionType.PAGE_DOWN):
            self._adjust_scroll(1)
            return True
        if action.type in (ActionType.MENU_UP, ActionType.SCROLL_UP, ActionType.PAGE_UP):
            self._adjust_scroll(-1)
            return True
        if action.type in (ActionType.MENU_BACK, ActionType.FORM_CANCEL):
            self.app.go_back()
            return True
        return False
