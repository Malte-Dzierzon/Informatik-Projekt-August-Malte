"""Input handling: key normalization, bindings, commands."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .render import get_key


class ActionType(Enum):
    QUIT = "quit"
    MENU_UP = "menu_up"
    MENU_DOWN = "menu_down"
    MENU_SELECT = "menu_select"
    MENU_BACK = "menu_back"
    MENU_HOME = "menu_home"
    MENU_END = "menu_end"
    TAB_NEXT = "tab_next"
    TAB_PREV = "tab_prev"
    FORM_SUBMIT = "form_submit"
    FORM_CANCEL = "form_cancel"
    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"
    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"
    HELP = "help"
    REFRESH = "refresh"
    NUMBER = "number"


@dataclass
class Action:
    type: ActionType
    payload: Any = None


# Key mappings (Vim-style + arrows + numbers)
KEY_MAP = {
    # Navigation
    "UP": ActionType.MENU_UP,
    "DOWN": ActionType.MENU_DOWN,
    "LEFT": ActionType.MENU_BACK,
    "RIGHT": ActionType.MENU_SELECT,
    "k": ActionType.MENU_UP,
    "j": ActionType.MENU_DOWN,
    "h": ActionType.MENU_BACK,
    "l": ActionType.MENU_SELECT,
    "g": ActionType.MENU_HOME,
    "G": ActionType.MENU_END,

    # Selection
    "ENTER": ActionType.MENU_SELECT,
    " ": ActionType.MENU_SELECT,
    "\t": ActionType.TAB_NEXT,
    "S-TAB": ActionType.TAB_PREV,  # Shift+Tab

    # Form
    "ESC": ActionType.FORM_CANCEL,

    # Scrolling
    "PAGE_UP": ActionType.PAGE_UP,
    "PAGE_DOWN": ActionType.PAGE_DOWN,
    "u": ActionType.SCROLL_UP,
    "d": ActionType.SCROLL_DOWN,

    # Actions
    "q": ActionType.QUIT,
    "Q": ActionType.QUIT,
    "?": ActionType.HELP,
    "r": ActionType.REFRESH,
    "R": ActionType.REFRESH,
}

# Number keys 1-9
for i in range(1, 10):
    KEY_MAP[str(i)] = ActionType.NUMBER


def normalize_key(raw: str) -> str:
    """Normalize raw key to standard name."""
    return raw


def get_action(key: str) -> Action | None:
    """Convert key to action."""
    if key in KEY_MAP:
        action_type = KEY_MAP[key]
        if action_type == ActionType.NUMBER:
            return Action(ActionType.NUMBER, int(key))
        return Action(action_type)

    # Check for Ctrl+key
    if len(key) == 1 and ord(key) < 32:
        return Action(ActionType.QUIT if key == "\x03" else ActionType.HELP)

    return None


class InputHandler:
    """Handles input loop and dispatches actions."""

    def __init__(self):
        self.bindings: dict[ActionType, list[Callable]] = {}
        self.running = True

    def bind(self, action: ActionType, callback: Callable) -> None:
        if action not in self.bindings:
            self.bindings[action] = []
        self.bindings[action].append(callback)

    def unbind(self, action: ActionType, callback: Callable) -> None:
        if action in self.bindings:
            self.bindings[action] = [c for c in self.bindings[action] if c != callback]

    def dispatch(self, action: Action) -> bool:
        """Dispatch action to bound callbacks. Return False to quit."""
        if action.type == ActionType.QUIT:
            self.running = False
            return False

        callbacks = self.bindings.get(action.type, [])
        for cb in callbacks:
            try:
                result = cb(action.payload)
                if result is False:
                    return False
            except Exception as e:  # noqa: BLE001
                print(f"Input handler error: {e}")
        return True

    def run(self) -> None:
        """Main input loop."""
        while self.running:
            key = get_key()
            action = get_action(key)
            if action:
                self.dispatch(action)

    def stop(self) -> None:
        self.running = False


class CommandPalette:
    """Fuzzy-searchable command palette."""

    def __init__(self, commands: list[dict]):
        """
        commands: [{id, label, description, keys, action}]
        """
        self.commands = commands
        self.filtered = commands
        self.query = ""
        self.selected = 0

    def update_query(self, query: str) -> None:
        self.query = query.lower()
        if not query:
            self.filtered = self.commands
        else:
            q = query.lower()
            self.filtered = [
                c for c in self.commands
                if q in c["label"].lower()
                or q in c.get("description", "").lower()
                or any(q in k.lower() for k in c.get("keys", []))
            ]
        self.selected = 0

    def handle_key(self, key: str) -> Action | None:
        if key == "ESC":
            return Action(ActionType.FORM_CANCEL)
        if key == "ENTER" and self.filtered:
            return Action(ActionType.MENU_SELECT, self.filtered[self.selected]["id"])
        if key in ("UP", "k"):
            self.selected = max(0, self.selected - 1)
            return None
        if key in ("DOWN", "j"):
            self.selected = min(len(self.filtered) - 1, self.selected + 1)
            return None
        if key == "BACKSPACE":
            self.update_query(self.query[:-1])
            return None
        if len(key) == 1 and key.isprintable():
            self.update_query(self.query + key)
            return None
        return None

    def render(self, width: int) -> list[str]:
        from .theme import get_theme
        theme = get_theme()

        lines = []
        # Search box
        search_display = f"  {theme.icons.arrow_right} {self.query}█"
        lines.append(theme.highlight(search_display[:width]))

        # Results
        for i, cmd in enumerate(self.filtered[:10]):
            prefix = "► " if i == self.selected else "  "
            keys = ", ".join(cmd.get("keys", []))
            line = f"{prefix}{cmd['label']}"
            if keys:
                line += theme.muted(f"  ({keys})")
            if cmd.get("description"):
                line += theme.muted(f"  — {cmd['description']}")
            if i == self.selected:
                line = theme.selected(line)
            lines.append(line[:width])

        return lines


# Key names for type hints (plain string constants)
class Key:
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    ENTER = "ENTER"
    ESC = "ESC"
    TAB = "TAB"
    BACKSPACE = "BACKSPACE"
    HOME = "HOME"
    END = "END"
    PAGE_UP = "PAGE_UP"
    PAGE_DOWN = "PAGE_DOWN"
