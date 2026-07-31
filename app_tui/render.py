"""Screen rendering utilities: buffer, ANSI codes, cursor control."""

import os
import sys
from contextlib import contextmanager


class ScreenBuffer:
    """Double-buffered screen renderer to reduce flicker."""

    def __init__(self):
        self.width = 80
        self.height = 24
        self._buffer: list[str] = []
        self._prev_buffer: list[str] = []
        self._update_size()

    def _update_size(self) -> None:
        try:
            size = os.get_terminal_size()
            self.width = max(60, size.columns)
            self.height = max(20, size.lines)
        except OSError:
            pass

    def clear(self) -> None:
        self._buffer = []

    def write(self, text: str) -> None:
        self._buffer.append(text)

    def writeln(self, text: str = "") -> None:
        self._buffer.append(text + "\n")

    def render(self) -> str:
        return "".join(self._buffer)

    def flush(self) -> None:
        sys.stdout.write(self.render())
        sys.stdout.flush()
        self._prev_buffer = self._buffer.copy()
        self.clear()


# ANSI escape sequences
CSI = "\033["
ESC = "\033"

# Cursor control
CURSOR_HOME = f"{CSI}H"
CURSOR_UP = f"{CSI}A"
CURSOR_DOWN = f"{CSI}B"
CURSOR_RIGHT = f"{CSI}C"
CURSOR_LEFT = f"{CSI}D"
CURSOR_SAVE = f"{CSI}s"
CURSOR_RESTORE = f"{CSI}u"
CURSOR_HIDE = f"{CSI}?25l"
CURSOR_SHOW = f"{CSI}?25h"

# Screen control
CLEAR_SCREEN = f"{CSI}2J"
CLEAR_LINE = f"{CSI}2K"
CLEAR_LINE_END = f"{CSI}K"
CLEAR_LINE_START = f"{CSI}1K"
CLEAR_BELOW = f"{CSI}J"
CLEAR_ABOVE = f"{CSI}1J"

# Alternate screen buffer (for full-screen apps)
ALT_SCREEN_ON = f"{CSI}?1049h"
ALT_SCREEN_OFF = f"{CSI}?1049l"

# Mouse
MOUSE_ON = f"{CSI}?1000h{CSI}?1002h{CSI}?1006h"
MOUSE_OFF = f"{CSI}?1000l{CSI}?1002l{CSI}?1006l"


def move_cursor(row: int, col: int) -> str:
    """Move cursor to 1-indexed position."""
    return f"{CSI}{row};{col}H"


def set_title(title: str) -> str:
    """Set terminal window title."""
    return f"\033]0;{title}\007"


@contextmanager
def alternate_screen():
    """Context manager for alternate screen buffer."""
    sys.stdout.write(ALT_SCREEN_ON)
    sys.stdout.write(CURSOR_HIDE)
    sys.stdout.flush()
    try:
        yield
    finally:
        sys.stdout.write(ALT_SCREEN_OFF)
        sys.stdout.write(CURSOR_SHOW)
        sys.stdout.flush()


@contextmanager
def raw_mode():
    """Context manager for raw terminal input (Unix)."""
    if os.name == "nt" or not sys.stdin.isatty():
        # Nothing to configure on Windows or when input is not a TTY
        yield
        return

    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _read_utf8_char(fd: int) -> str:
    """Read one UTF-8 character straight from a file descriptor.

    Uses ``os.read`` instead of ``sys.stdin.read`` so the bytes are not
    pre-buffered by Python's TextIOWrapper. Otherwise select() on the
    underlying descriptor reports "no data" while the bytes already sit in
    the wrapper's buffer, which breaks ESC/mouse-sequence detection (and
    pipe-based testing).
    """
    try:
        first = os.read(fd, 1)
    except (EOFError, OSError):
        return ""
    if not first:
        return ""
    b0 = first[0]
    if b0 < 0x80:
        return chr(b0)
    if 0xC2 <= b0 <= 0xDF:
        extra = 1
    elif 0xE0 <= b0 <= 0xEF:
        extra = 2
    elif 0xF0 <= b0 <= 0xF4:
        extra = 3
    else:
        return chr(b0)  # lone continuation byte; keep it raw
    try:
        rest = os.read(fd, extra)
    except (EOFError, OSError):
        rest = b""
    return (first + rest).decode("utf-8", "replace")


def get_key() -> str:
    """Read a single key press (handles escape sequences). Returns "" on EOF."""
    if os.name == "nt":
        import msvcrt
        try:
            ch = msvcrt.getwch()
        except (EOFError, OSError):
            return ""
        if ch == "\xe0":  # Arrow key prefix
            ch = msvcrt.getwch()
            return {"H": "UP", "P": "DOWN", "M": "RIGHT", "K": "LEFT"}.get(ch, ch)
        if ch == "\x00":  # Function key prefix
            ch = msvcrt.getwch()
            return f"F{ch}"
        if ch == "\r":
            return "ENTER"
        if ch == "\x1b":
            return "ESC"
        return ch

    # Unix: read raw bytes from the descriptor (see _read_utf8_char).
    try:
        fd = sys.stdin.fileno()
    except (AttributeError, OSError, ValueError):
        return ""
    ch = _read_utf8_char(fd)
    if not ch:
        return ""  # EOF
    if ch == "\x1b":
        # Escape sequence - wait briefly for more bytes so a lone ESC
        # (e.g. "cancel") is not swallowed by a blocking read.
        try:
            import select
            ready, _, _ = select.select([fd], [], [], 0.05)
        except (ImportError, OSError, ValueError):
            ready = True
        if not ready:
            return "ESC"
        next_ch = _read_utf8_char(fd)
        if next_ch == "[":
            third = _read_utf8_char(fd)
            if third == "A":
                return "UP"
            if third == "B":
                return "DOWN"
            if third == "C":
                return "RIGHT"
            if third == "D":
                return "LEFT"
            if third == "Z":  # Shift+Tab
                return "S-TAB"
            if third == "<":  # SGR mouse sequence: ESC [ < b ; x ; y M|m
                buf = ""
                final = ""
                while True:
                    c = _read_utf8_char(fd)
                    if not c:
                        break
                    if c in "Mm":
                        final = c
                        break
                    buf += c
                parts = buf.split(";")
                if len(parts) == 3:
                    try:
                        button, mx, my = int(parts[0]), int(parts[1]), int(parts[2])
                    except ValueError:
                        return "MOUSE"
                    return f"MOUSE:{button}:{mx}:{my}:{'P' if final == 'M' else 'R'}"
                return "MOUSE"
            if third in "123456789":
                fourth = _read_utf8_char(fd)
                if fourth == "~":
                    return {  # Function keys
                        "1": "HOME", "2": "INSERT", "3": "DELETE",
                        "4": "END", "5": "PAGE_UP", "6": "PAGE_DOWN",
                        "7": "HOME", "8": "END", "9": "F9",
                    }.get(third, f"ESC[{third}~")
            return f"ESC[{third}"
        if next_ch == "O":  # Alt+key or function keys
            third = _read_utf8_char(fd)
            return {  # Common Alt+key combos
                "P": "F1", "Q": "F2", "R": "F3", "S": "F4",
            }.get(third, f"ALT+{third}")
        return f"ESC{next_ch}"
    if ch == "\r" or ch == "\n":
        return "ENTER"
    if ch == "\t":
        return "TAB"
    if ch == "\x7f" or ch == "\x08":
        return "BACKSPACE"
    return ch


def poll_key(timeout: float = 0.0) -> str:
    """Wait up to ``timeout`` seconds for a key; return "" if none is pressed.

    Used for non-blocking checks such as ESC-to-cancel during long
    synchronous operations (e.g. training).
    """
    if os.name == "nt" or not sys.stdin.isatty():
        return ""
    import select

    try:
        fd = sys.stdin.fileno()
        ready, _, _ = select.select([fd], [], [], timeout)
    except (OSError, ValueError):
        return ""
    if not ready:
        return ""
    return get_key()


def clear_screen() -> None:
    """Clear screen and move cursor to home."""
    sys.stdout.write(CLEAR_SCREEN + CURSOR_HOME)
    sys.stdout.flush()


def hide_cursor() -> None:
    sys.stdout.write(CURSOR_HIDE)
    sys.stdout.flush()


def show_cursor() -> None:
    sys.stdout.write(CURSOR_SHOW)
    sys.stdout.flush()


def enable_mouse() -> None:
    sys.stdout.write(MOUSE_ON)
    sys.stdout.flush()


def disable_mouse() -> None:
    sys.stdout.write(MOUSE_OFF)
    sys.stdout.flush()


class Layout:
    """Simple layout calculator for responsive UI."""

    def __init__(self, width: int, height: int, padding: int = 1):
        self.width = width
        self.height = height
        self.padding = padding
        self.inner_width = width - 2 * padding
        self.inner_height = height - 2 * padding

    @property
    def sidebar_width(self) -> int:
        return min(40, self.inner_width // 3)

    @property
    def content_width(self) -> int:
        return self.inner_width - self.sidebar_width - 1

    @property
    def header_height(self) -> int:
        return 4

    @property
    def footer_height(self) -> int:
        return 2

    @property
    def body_height(self) -> int:
        return self.inner_height - self.header_height - self.footer_height

    def split_vertical(self, left_ratio: float = 0.3) -> tuple["Layout", "Layout"]:
        left_w = int(self.inner_width * left_ratio)
        right_w = self.inner_width - left_w - 1
        left = Layout(left_w + 2 * self.padding, self.height, self.padding)
        right = Layout(right_w + 2 * self.padding, self.height, self.padding)
        return left, right

    def split_horizontal(self, top_ratio: float = 0.5) -> tuple["Layout", "Layout"]:
        top_h = int(self.inner_height * top_ratio)
        bottom_h = self.inner_height - top_h - 1
        top = Layout(self.width, top_h + 2 * self.padding, self.padding)
        bottom = Layout(self.width, bottom_h + 2 * self.padding, self.padding)
        return top, bottom
