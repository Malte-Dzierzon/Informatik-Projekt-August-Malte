"""UI Components: Panel, Table, Menu, Form, Progress, StatusBar."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .render import Layout
from .theme import get_theme


class Key(Enum):
    """Normalized key names."""
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
    QUIT = "q"
    HELP = "?"


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _display_len(text: str) -> int:
    """Length of a string ignoring ANSI color codes."""
    return len(_ANSI_RE.sub("", text))


def _truncate_ansi(text: str, width: int) -> str:
    """Truncate a (possibly ANSI-colored) string to a display width."""
    if _display_len(text) <= width:
        return text

    out: list[str] = []
    count = 0
    i = 0
    while i < len(text) and count < max(0, width - 3):
        ch = text[i]
        if ch == "\x1b":
            m = _ANSI_RE.match(text, i)
            if m:
                out.append(m.group(0))
                i = m.end()
                continue
        out.append(ch)
        count += 1
        i += 1
    return "".join(out) + "..."


@dataclass
class MenuItem:
    """Menu item with label, key, and action."""
    label: str
    key: str | None = None
    action: str | Callable | None = None
    description: str = ""
    enabled: bool = True


class Component(ABC):
    """Base class for all UI components."""

    def __init__(self, layout: Layout | None = None):
        self.layout = layout
        self.focused = False

    @abstractmethod
    def render(self, layout: Layout | None = None) -> list[str]:
        """Return list of lines to render."""
        raise NotImplementedError

    def handle_key(self, key: str) -> Any:
        """Handle key press. Return action or None."""
        return None

    def focus(self) -> None:
        self.focused = True

    def blur(self) -> None:
        self.focused = False


class Panel(Component):
    """Bordered panel with title and content."""

    def __init__(
        self,
        title: str = "",
        content: list[str] | None = None,
        border_style: str = "single",
        layout: Layout | None = None,
    ):
        super().__init__(layout)
        self.title = title
        self.content = content or []
        self.border_style = border_style
        self.theme = get_theme()

    def set_content(self, content: list[str]) -> None:
        self.content = content

    def add_line(self, line: str) -> None:
        self.content.append(line)

    def render(self, layout: Layout | None = None) -> list[str]:
        l = layout or self.layout
        if l is None:
            return self.content

        w = l.inner_width
        theme = self.theme
        lines = []

        # Top border
        if self.border_style == "single":
            top = f"┌{'─' * (w - 2)}┐"
            bottom = f"└{'─' * (w - 2)}┘"
            side = "│"
        elif self.border_style == "double":
            top = f"╔{'═' * (w - 2)}╗"
            bottom = f"╚{'═' * (w - 2)}╝"
            side = "║"
        else:  # none
            top = bottom = ""
            side = ""

        if top:
            if self.title:
                title_str = f" {self.title} "
                if len(title_str) > w - 4:
                    title_str = title_str[:w - 7] + "..."
                padding = w - 2 - len(title_str)
                left_pad = padding // 2
                right_pad = padding - left_pad
                top = f"┌{'─' * left_pad}{theme.primary(title_str)}{'─' * right_pad}┐"
            lines.append(top)

        for line in self.content:
            visible_len = _display_len(line)
            if side:
                padding = max(0, w - 4 - visible_len)
                lines.append(f"{side} {line}{' ' * padding} {side}")
            else:
                padding = max(0, w - visible_len)
                lines.append(f"{line}{' ' * padding}")

        if bottom:
            lines.append(bottom)

        return lines


class Table(Component):
    """Data table with headers, rows, and selection."""

    def __init__(
        self,
        headers: list[str],
        rows: list[list[str]],
        selected_row: int = -1,
        col_widths: list[int] | None = None,
        layout: Layout | None = None,
    ):
        super().__init__(layout)
        self.headers = headers
        self.rows = rows
        self.selected_row = selected_row
        self.col_widths = col_widths or [15] * len(headers)
        self.theme = get_theme()
        self.scroll_offset = 0

    def render(self, layout: Layout | None = None) -> list[str]:
        l = layout or self.layout
        if l is None:
            return []

        w = l.inner_width
        theme = self.theme
        lines = []

        # Calculate column widths
        total_width = sum(self.col_widths) + len(self.headers) + 1
        if total_width > w:
            # Scale down proportionally
            scale = (w - len(self.headers) - 1) / sum(self.col_widths)
            col_widths = [max(5, int(cw * scale)) for cw in self.col_widths]
        else:
            col_widths = self.col_widths

        # Header
        header_parts = []
        for i, (h, cw) in enumerate(zip(self.headers, col_widths)):
            header_parts.append(h[:cw].ljust(cw))
        lines.append(f"│{'│'.join(header_parts)}│")
        lines.append(f"├{'┼'.join('─' * cw for cw in col_widths)}┤")

        # Rows
        visible_rows = max(1, l.body_height - 2)
        start = self.scroll_offset
        end = min(start + visible_rows, len(self.rows))

        for row_idx in range(start, end):
            row = self.rows[row_idx]
            is_selected = row_idx == self.selected_row
            row_parts = []
            for i, (cell, cw) in enumerate(zip(row, col_widths)):
                cell_str = str(cell)[:cw].ljust(cw)
                row_parts.append(cell_str)
            line = f"│{'│'.join(row_parts)}│"
            if is_selected:
                line = theme.selected(line)
            lines.append(line)

        # Fill remaining
        for _ in range(end - start, visible_rows):
            lines.append(f"│{'│'.join(' ' * cw for cw in col_widths)}│")

        return lines

    def handle_key(self, key: str) -> str | None:
        if key in (Key.UP.value, "k"):
            self.selected_row = max(0, self.selected_row - 1)
            self.scroll_offset = min(self.scroll_offset, self.selected_row)
            return "selection_changed"
        if key in (Key.DOWN.value, "j"):
            self.selected_row = min(len(self.rows) - 1, self.selected_row + 1)
            l = self.layout
            if l and self.selected_row >= self.scroll_offset + (l.body_height - 2):
                self.scroll_offset = self.selected_row - (l.body_height - 2) + 1
            return "selection_changed"
        if key == Key.ENTER.value:
            return "select"
        return None


class Menu(Component):
    """Vertical menu with keyboard navigation."""

    def __init__(
        self,
        items: list[MenuItem],
        selected: int = 0,
        show_shortcuts: bool = True,
        layout: Layout | None = None,
    ):
        super().__init__(layout)
        self.items = items
        self.selected = selected
        self.show_shortcuts = show_shortcuts
        self.theme = get_theme()

    def render(self, layout: Layout | None = None) -> list[str]:
        l = layout or self.layout
        if l is None:
            return []

        w = l.inner_width
        theme = self.theme
        lines = []

        for i, item in enumerate(self.items):
            if not item.enabled:
                prefix = theme.muted("  ")
                label = theme.muted(item.label)
            elif i == self.selected:
                prefix = theme.highlight("► ")
                label = theme.highlight(item.label)
            else:
                prefix = "  "
                label = item.label

            shortcut = ""
            if self.show_shortcuts and item.key:
                shortcut = theme.muted(f"  ({item.key})")

            desc = ""
            if item.description and i == self.selected:
                desc = theme.muted(f"  — {item.description}")

            line = f"{prefix}{label}{shortcut}{desc}"
            # Truncate if needed (ANSI-aware)
            if _display_len(line) > w:
                line = _truncate_ansi(line, w)
            lines.append(line)

        return lines

    def handle_key(self, key: str) -> str | None:
        # Number keys
        if key.isdigit():
            idx = int(key) - 1
            if 0 <= idx < len(self.items) and self.items[idx].enabled:
                self.selected = idx
                return "select"

        if key in (Key.UP.value, "k"):
            self.selected = max(0, self.selected - 1)
            return "navigate"
        if key in (Key.DOWN.value, "j"):
            self.selected = min(len(self.items) - 1, self.selected + 1)
            return "navigate"
        if key in (Key.ENTER.value, Key.RIGHT.value, "l") and self.items[self.selected].enabled:
            return "select"
        if key in (Key.LEFT.value, "h", Key.ESC.value):
            return "back"
        if key == Key.HELP.value:
            return "help"
        return None


class Form(Component):
    """Form with labeled input fields."""

    def __init__(
        self,
        fields: list[dict],
        layout: Layout | None = None,
    ):
        super().__init__(layout)
        self.fields = fields  # [{name, label, type, value, validator, required}]
        self.focused_field = 0
        self.values = {f["name"]: f.get("value", "") for f in fields}
        self.errors = {}
        self.theme = get_theme()

    def render(self, layout: Layout | None = None) -> list[str]:
        l = layout or self.layout
        if l is None:
            return []

        w = l.inner_width
        theme = self.theme
        lines = []

        for i, f in enumerate(self.fields):
            is_focused = i == self.focused_field
            name = f["name"]
            label = f.get("label", name)
            value = self.values.get(name, "")
            error = self.errors.get(name)

            prefix = theme.highlight("► ") if is_focused else "  "
            label_str = f"{prefix}{label}: "
            value_str = str(value)

            if is_focused:
                value_str = theme.highlight(value_str + "█")  # Cursor indicator

            line = f"{label_str}{value_str}"
            if error:
                line += theme.error(f"  ✗ {error}")

            lines.append(_truncate_ansi(line, w))

        return lines

    def handle_key(self, key: str) -> str | None:
        f = self.fields[self.focused_field]

        if key == Key.TAB.value or key == Key.DOWN.value:
            self.focused_field = (self.focused_field + 1) % len(self.fields)
            return "navigate"
        if key == "S-TAB" or key == Key.UP.value:  # Shift+Tab
            self.focused_field = (self.focused_field - 1) % len(self.fields)
            return "navigate"
        if key == Key.ENTER.value:
            if self.focused_field == len(self.fields) - 1:
                return "submit"
            self.focused_field = (self.focused_field + 1) % len(self.fields)
            return "navigate"
        if key == Key.ESC.value:
            return "cancel"
        if key == Key.BACKSPACE.value:
            self.values[f["name"]] = self.values[f["name"]][:-1]
            return "change"
        if len(key) == 1 and key.isprintable():
            self.values[f["name"]] += key
            return "change"
        return None

    def validate(self) -> bool:
        self.errors = {}
        for f in self.fields:
            name = f["name"]
            value = self.values.get(name, "")
            if f.get("required") and not value:
                self.errors[name] = "Required field"
                continue
            validator = f.get("validator")
            if validator and value:
                result = validator(value)
                if result is not True:
                    self.errors[name] = result
        return len(self.errors) == 0

    def get_values(self) -> dict:
        return self.values.copy()


class Progress(Component):
    """Progress indicator: spinner, bar, or percentage."""

    def __init__(
        self,
        message: str = "",
        total: int = 0,
        current: int = 0,
        style: str = "bar",  # bar, spinner, percent
        layout: Layout | None = None,
    ):
        super().__init__(layout)
        self.message = message
        self.total = total
        self.current = current
        self.style = style
        self.spinner_frame = 0
        self.theme = get_theme()

    def update(self, current: int, message: str = "") -> None:
        self.current = current
        if message:
            self.message = message

    def tick(self) -> None:
        self.spinner_frame = (self.spinner_frame + 1) % len(self.theme.icons.spinner)

    def render(self, layout: Layout | None = None) -> list[str]:
        theme = self.theme
        lines = []

        if self.style == "spinner":
            spinner = theme.icons.spinner[self.spinner_frame]
            lines.append(f"  {spinner} {self.message}")
        elif self.style == "bar" and self.total > 0:
            pct = self.current / self.total
            bar_width = 40
            filled = int(bar_width * pct)
            bar = theme.icons.fill * filled + theme.icons.empty * (bar_width - filled)
            lines.append(f"  {theme.primary(bar)} {pct * 100:.0f}%  {self.message}")
        elif self.style == "percent" and self.total > 0:
            pct = self.current / self.total
            lines.append(f"  {theme.accent(f'{pct * 100:.1f}%')}  {self.message}")
        else:
            lines.append(f"  {self.message}")

        return lines


class StatusBar(Component):
    """Persistent status bar at bottom with hints."""

    def __init__(
        self,
        left: str = "",
        center: str = "",
        right: str = "",
        hints: list[str] | None = None,
        layout: Layout | None = None,
    ):
        super().__init__(layout)
        self.left = left
        self.center = center
        self.right = right
        self.hints = hints or []
        self.theme = get_theme()

    def set_hints(self, hints: list[str]) -> None:
        self.hints = hints

    def render(self, layout: Layout | None = None) -> list[str]:
        l = layout or self.layout
        if l is None:
            return []

        w = l.width
        theme = self.theme

        left_part = f" {self.left} " if self.left else ""
        right_part = f" {self.right} " if self.right else ""
        center_part = f" {self.center} " if self.center else ""
        hints_str = center_part or "  ".join(self.hints)

        left_len = _display_len(left_part)
        right_len = _display_len(right_part)
        mid_space = max(0, w - left_len - right_len)

        if hints_str:
            if _display_len(hints_str) > mid_space:
                hints_str = _truncate_ansi(hints_str, mid_space)
            hints_len = _display_len(hints_str)
            pad_left = (mid_space - hints_len) // 2
            pad_right = mid_space - hints_len - pad_left
            middle = " " * pad_left + hints_str + " " * pad_right
        else:
            middle = " " * mid_space

        return [f"{theme.muted(left_part)}{middle}{theme.muted(right_part)}"]


class Notification(Component):
    """Toast-style notification."""

    def __init__(self, message: str, level: str = "info", duration: float = 3.0):
        super().__init__()
        self.message = message
        self.level = level  # info, success, warning, error
        self.duration = duration
        self.visible = True
        self.theme = get_theme()

    def render(self, layout: Layout | None = None) -> list[str]:
        if not self.visible:
            return []

        l = layout or self.layout
        if l is None:
            return []

        theme = self.theme
        colors = {
            "info": theme.primary,
            "success": theme.success,
            "warning": theme.warning,
            "error": theme.error,
        }
        color_fn = colors.get(self.level, theme.primary)
        icon = {
            "info": theme.icons.arrow_right,
            "success": theme.icons.check,
            "warning": "⚠",
            "error": theme.icons.cross,
        }.get(self.level, theme.icons.arrow_right)

        return [f"  {color_fn(f'{icon} {self.message}')}"]

    def hide(self) -> None:
        self.visible = False
