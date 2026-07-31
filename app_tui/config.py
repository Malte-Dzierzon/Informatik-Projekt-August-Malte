"""Configuration management for TUI app."""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class TUIConfig:
    """User configuration for the TUI application."""
    use_nerd_font: bool | None = None  # None = auto-detect
    use_color: bool | None = None      # None = auto-detect
    language: str = "en"               # "en" | "de"
    terminal_width: int = 0            # 0 = auto
    show_tooltips: bool = True
    compact_mode: bool = False
    last_version: str = ""


CONFIG_DIR = Path.home() / ".config" / "pyramid-tui"
CONFIG_FILE = CONFIG_DIR / "config.json"
VERSION = "1.0.0"


def load_config() -> TUIConfig:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return TUIConfig()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Only keep known fields
        valid_fields = set(TUIConfig.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        config = TUIConfig(**filtered)
        config.last_version = VERSION
        return config
    except (json.JSONDecodeError, OSError, TypeError):
        return TUIConfig()


def save_config(config: TUIConfig) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config.last_version = VERSION
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(config), f, indent=2)
    except OSError:
        pass  # Non-critical


def nerd_font_detected() -> bool:
    """Heuristic: can the current terminal render Nerd Font glyphs?"""
    term = os.environ.get("TERM", "").lower()
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    font = os.environ.get("TERM_FONT", "").lower()

    nerd_indicators = [
        "kitty", "alacritty", "wezterm", "foot", "konsole",
        "ghostty", "rio", "tabby", "terminology",
    ]
    return (
        any(ind in term for ind in nerd_indicators)
        or any(ind in term_program for ind in ["vscode", "ghostty", "wezterm"])
        or "nerd" in font
    )


def prompt_nerd_font() -> bool:
    """Prompt user for Nerd Font preference on first run."""
    detected = nerd_font_detected()
    default_label = "[Y/n]" if detected else "[y/N]"

    print()
    print("┌─ First Run Setup ────────────────────────────────────────┐")
    print("│  Nerd Fonts add icons to the interface (▲ ◆ ▶ ✦ ⚙)        │")
    print("│  Without them, ASCII fallbacks are used (^ [M] > * >>)   │")
    if detected:
        print("│  Nerd Font support was detected on this terminal.        │")
    print("├──────────────────────────────────────────────────────────┤")
    prompt_line = f"  Use Nerd Font icons? {default_label}"
    print(f"│{prompt_line}{' ' * (57 - len(prompt_line))}│")
    print("└──────────────────────────────────────────────────────────┘")
    print()
    while True:
        choice = input("  > ").strip().lower()
        if choice == "":
            return detected
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no"):
            return False
        print("  Please enter 'y' or 'n'")


def get_or_create_config() -> TUIConfig:
    """Get existing config or create new one with first-run prompts."""
    config = load_config()

    # First run detection
    if config.last_version == "":
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║  Welcome to Pyramid Classification TUI!                  ║")
        print("║  Let's configure your preferences.                       ║")
        print("╚══════════════════════════════════════════════════════════╝")

        config.language = "en"  # Interface language is English
        config.use_nerd_font = prompt_nerd_font()
        save_config(config)
        print("\nConfiguration saved. Starting application...\n")

    return config
