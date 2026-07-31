"""Theme system: colors, icons, styles for TUI."""

import os
import sys
from dataclasses import dataclass

# ANSI color codes (bare SGR codes, combined by Theme.color)
RESET = "\033[0m"
BOLD = "1"
DIM = "2"
REVERSE = "7"

# 16-color ANSI (works everywhere)
FG_BLACK = "30"
FG_RED = "31"
FG_GREEN = "32"
FG_YELLOW = "33"
FG_BLUE = "34"
FG_MAGENTA = "35"
FG_CYAN = "36"
FG_WHITE = "37"
FG_BRIGHT_BLACK = "90"
FG_BRIGHT_RED = "91"
FG_BRIGHT_GREEN = "92"
FG_BRIGHT_YELLOW = "93"
FG_BRIGHT_BLUE = "94"
FG_BRIGHT_MAGENTA = "95"
FG_BRIGHT_CYAN = "96"
FG_BRIGHT_WHITE = "97"

BG_BLACK = "40"
BG_RED = "41"
BG_GREEN = "42"
BG_YELLOW = "43"
BG_BLUE = "44"
BG_MAGENTA = "45"
BG_CYAN = "46"
BG_WHITE = "47"


@dataclass(frozen=True)
class IconSet:
    """Icon set for different font capabilities."""
    pyramid: str
    data: str
    model: str
    train: str
    test: str
    export: str
    settings: str
    arrow_right: str
    check: str
    cross: str
    spinner: list[str]
    # Border glyphs
    h: str
    v: str
    tl: str
    tr: str
    bl: str
    br: str
    ml: str
    mr: str
    # Progress bar
    fill: str
    empty: str


NERD_FONT_ICONS = IconSet(
    pyramid="",      # nf-md-triangle
    data="󰆧",        # nf-md-database
    model="󰍛",       # nf-md-brain
    train="󰑮",       # nf-md-play-circle
    test="󰙨",        # nf-md-flask
    export="󰏔",      # nf-md-download
    settings="󰍟",    # nf-md-cog
    arrow_right="",  # nf-fa-angle_right
    check="",       # nf-fa-check
    cross="",       # nf-fa-times
    spinner=["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"],  # Braille spinner
    h="─", v="│", tl="┌", tr="┐", bl="└", br="┘", ml="├", mr="┤",
    fill="█", empty="░",
)

UNICODE_ICONS = IconSet(
    pyramid="▲",
    data="▣",
    model="◆",
    train="▶",
    test="✦",
    export="⤓",
    settings="◉",
    arrow_right="►",
    check="√",
    cross="×",
    spinner=["|", "/", "-", "\\"],
    h="─", v="│", tl="┌", tr="┐", bl="└", br="┘", ml="├", mr="┤",
    fill="█", empty="░",
)

ASCII_ICONS = IconSet(
    pyramid="^",
    data="[D]",
    model="[M]",
    train=">",
    test="*",
    export=">>",
    settings="[S]",
    arrow_right=">",
    check="[x]",
    cross="[ ]",
    spinner=["|", "/", "-", "\\"],
    h="-", v="|", tl="+", tr="+", bl="+", br="+", ml="+", mr="+",
    fill="#", empty="-",
)


class Theme:
    """Application theme with color and icon configuration."""

    def __init__(self, use_nerd_font: bool | None = None, use_color: bool | None = None):
        self.use_color = self._detect_color_support() if use_color is None else use_color
        self.use_nerd_font = self._detect_nerd_font() if use_nerd_font is None else use_nerd_font
        self.icons = self._pick_icons()

    def _pick_icons(self) -> IconSet:
        if self.use_nerd_font:
            return NERD_FONT_ICONS
        if os.name == "nt":
            # Windows terminals (cmd / PowerShell default fonts) cannot render
            # the Unicode icon set reliably → pure ASCII symbols.
            return ASCII_ICONS
        return UNICODE_ICONS if self._supports_unicode() else ASCII_ICONS

    def apply(self, use_nerd_font: bool | None = None, use_color: bool | None = None) -> None:
        """Mutate the theme in place (components keep their reference)."""
        if use_nerd_font is not None:
            self.use_nerd_font = use_nerd_font
        if use_color is not None:
            self.use_color = use_color
        self.icons = self._pick_icons()

    def _detect_color_support(self) -> bool:
        """Check if terminal supports color."""
        if not sys.stdout.isatty():
            return False
        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("TERM") == "dumb":
            return False
        # Check for common color-supporting terminals
        term = os.environ.get("TERM", "").lower()
        colorterm = os.environ.get("COLORTERM", "").lower()
        return (
            "color" in term or "xterm" in term or "screen" in term
            or "256" in term or "truecolor" in colorterm or "24bit" in colorterm
        )

    def _detect_nerd_font(self) -> bool:
        """Platform-based detection: Linux/macOS → Nerd Font icons,
        Windows → ASCII symbols (legacy terminal fonts lack the glyphs)."""
        return os.name != "nt" and sys.platform != "win32"

    def _supports_unicode(self) -> bool:
        """Check if terminal supports basic Unicode."""
        encoding = sys.stdout.encoding or "ascii"
        return encoding.lower() in ("utf-8", "utf8", "utf-16", "utf-32")

    # Color helpers
    def color(self, fg: str = "", bg: str = "", bold: bool = False, dim: bool = False, reverse: bool = False) -> str:
        if not self.use_color:
            return ""
        codes = []
        if bold:
            codes.append("1")
        if dim:
            codes.append("2")
        if reverse:
            codes.append("7")
        if fg:
            codes.append(fg)
        if bg:
            codes.append(bg)
        return f"\033[{';'.join(codes)}m" if codes else ""

    def reset(self) -> str:
        return RESET if self.use_color else ""

    # Semantic colors
    def primary(self, text: str) -> str:
        return f"{self.color(FG_BLUE, bold=True)}{text}{self.reset()}"

    def success(self, text: str) -> str:
        return f"{self.color(FG_GREEN, bold=True)}{text}{self.reset()}"

    def warning(self, text: str) -> str:
        return f"{self.color(FG_YELLOW, bold=True)}{text}{self.reset()}"

    def error(self, text: str) -> str:
        return f"{self.color(FG_RED, bold=True)}{text}{self.reset()}"

    def muted(self, text: str) -> str:
        return f"{self.color(FG_BRIGHT_BLACK)}{text}{self.reset()}"

    def accent(self, text: str) -> str:
        return f"{self.color(FG_CYAN, bold=True)}{text}{self.reset()}"

    def highlight(self, text: str) -> str:
        return f"{self.color(FG_BLACK, BG_WHITE)}{text}{self.reset()}"

    def selected(self, text: str) -> str:
        return f"{self.color(REVERSE)}{text}{self.reset()}"

    def dim(self, text: str) -> str:
        return f"{self.color(DIM)}{text}{self.reset()}"


# Global theme instance (initialized in main)
theme: Theme | None = None


def get_theme() -> Theme:
    global theme
    if theme is None:
        theme = Theme()
    return theme


def init_theme(nerd_font: bool | None = None, color: bool | None = None) -> Theme:
    global theme
    theme = Theme(use_nerd_font=nerd_font, use_color=color)
    return theme
