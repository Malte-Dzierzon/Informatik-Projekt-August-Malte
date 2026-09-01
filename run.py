"""
Automatic Setup & Launch Script
================================
Checks dependencies, installs missing packages, and launches the app.

Fast and no-frills: everything prints instantly, and a spinner shows progress
only while pip/venv work is actually running. Uses Nerd Font icons on
Linux/macOS terminals that support them and plain ASCII elsewhere (Windows,
Termux, Linux console, or when RUN_NO_ICONS=1 is set).

Cross-platform: Windows, Linux, macOS and Android/Termux.
- Windows: pip + --user + venv fallback
- Linux: PEP 668 aware, --break-system-packages + venv + distro hints
- macOS: Homebrew-aware, Xcode tools hints, venv fallback (externally-managed)
- Termux: automatic `pkg install` for native libs, pip --no-build-isolation
"""

import argparse
import importlib.util
import os
import platform as platform_module
import shutil
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# CROSS-PLATFORM TERMINAL SETUP
# ---------------------------------------------------------------------------
# Force UTF-8 for Windows terminals (prevents UnicodeEncodeError with glyphs)
reconfigure_stdout = getattr(sys.stdout, 'reconfigure', None)
if reconfigure_stdout is not None:
    try:
        reconfigure_stdout(encoding='utf-8')
    except (AttributeError, OSError):
        pass

# Enable ANSI escape sequences on Windows CMD/PowerShell
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except (ImportError, AttributeError, OSError):
        pass


# ---------------------------------------------------------------------------
# PLATFORM DETECTION & GLYPHS
# ---------------------------------------------------------------------------
def is_android_termux() -> bool:
    """Detect Android/Termux environment."""
    android_data = os.environ.get("ANDROID_DATA")
    termux_flag = os.environ.get("TERMUX_VERSION") or os.environ.get("PREFIX", "").startswith("/data/data/")
    return bool(android_data and termux_flag)


def _detect_platform() -> str:
    """Return canonical platform id: windows | macos | termux | linux | unknown."""
    if is_android_termux():
        return "termux"
    if sys.platform == "darwin":
        return "macos"
    if os.name == "nt":
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    return "unknown"


PLATFORM = _detect_platform()
IS_WINDOWS = PLATFORM == "windows"
IS_MACOS = PLATFORM == "macos"
IS_TERMUX = PLATFORM == "termux"
IS_LINUX = PLATFORM == "linux"

# Linux/macOS terminals with a Nerd Font (Kitty, WezTerm, Alacritty, ...) get
# proper icon glyphs; Windows cmd, Termux and the Linux console fall back to
# plain ASCII. Set RUN_NO_ICONS=1 to force the ASCII fallback anywhere.
force_plain = os.environ.get("RUN_NO_ICONS") == "1" or os.environ.get("TERM") == "linux"
USE_ICONS = not IS_WINDOWS and not IS_TERMUX and not force_plain

if USE_ICONS:
    # Nerd Font (Font Awesome) private-use-area codepoints
    ICONS = {
        "info": "\uf05a",   # info-circle
        "ok": "\uf058",     # check-circle
        "err": "\uf057",    # times-circle
        "warn": "\uf071",   # exclamation-triangle
        "web": "\uf108",    # desktop
        "tui": "\uf120",    # terminal
        "dl": "\uf019",     # download
        "cube": "\uf1b2",   # cube
    }
    SPINNER_FRAMES = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c",
                      "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]
else:
    ICONS = {
        "info": "[INFO]", "ok": "[OK]", "err": "[ERROR]", "warn": "[WARN]",
        "web": "[WEB]", "tui": "[TUI]", "dl": "->", "cube": "###",
    }
    SPINNER_FRAMES = ["|", "/", "-", "\\"]


# ---------------------------------------------------------------------------
# LOGGING HELPERS
# ---------------------------------------------------------------------------
def _log(kind: str, color: str, msg: str) -> None:
    print(f"\033[{color}m{ICONS[kind]} {msg}\033[0m")


def log_info(msg: str) -> None:
    _log("info", "94", msg)


def log_error(msg: str, err: Exception | None = None) -> None:
    _log("err", "91", msg)
    if err:
        print(f"\033[91m       {err}\033[0m")


def log_success(msg: str) -> None:
    _log("ok", "92", msg)


def log_warn(msg: str) -> None:
    _log("warn", "93", msg)


# ---------------------------------------------------------------------------
# DEPENDENCY CHECKING & INSTALLATION
# ---------------------------------------------------------------------------
REQUIRED_PACKAGES = [
    "streamlit",
    "numpy",
    "scipy",
    "pandas",
    "plotly",
    "Pillow",
]

# Packages not needed for CLI mode
CLI_EXCLUDE = {"streamlit", "plotly", "pandas", "Pillow", "pillow"}

# Isolated virtual environment used when the system Python is externally managed
# (PEP 668) or lacks write permission — common on many Linux distributions and
# on Homebrew-managed macOS.
VENV_DIRNAME = ".venv"
VENV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), VENV_DIRNAME)

# Set to True once this run falls back to the project venv for installs.
USED_VENV = False

# Import-name overrides (pip name -> import name). Pillow is imported as PIL,
# but we don't require it explicitly — streamlit pulls it — still handle it.
PACKAGE_IMPORT_MAP = {
    "Pillow": "PIL",
    "pillow": "PIL",
}

# Termux: pip packages that have faster / more reliable native `pkg` equivalents
TERMUX_PKG_MAP = {
    "numpy": "python-numpy",
    "scipy": "python-scipy",
    "pandas": "python-pandas",
}


def run_with_spinner(cmd: list[str], label: str, timeout: int = 180) -> subprocess.CompletedProcess:
    """Run a command while showing a spinner. Output is captured until done."""
    # No spinner when stdout is redirected (CI, logs) - just run quietly.
    if not sys.stdout.isatty():
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)

    sys.stdout.write(f"  {label} {SPINNER_FRAMES[0]}")
    sys.stdout.flush()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    start = time.monotonic()
    frame = 0
    try:
        while proc.poll() is None:
            if time.monotonic() - start > timeout:
                proc.kill()
                proc.wait()
                raise subprocess.TimeoutExpired(cmd, timeout)
            frame += 1
            sys.stdout.write(f"\r  {label} {SPINNER_FRAMES[frame % len(SPINNER_FRAMES)]}")
            sys.stdout.flush()
            time.sleep(0.08)
    except KeyboardInterrupt:
        proc.kill()
        proc.wait()
        raise

    stdout, stderr = proc.communicate()
    # Clear the spinner line
    sys.stdout.write("\r" + " " * (len(label) + 8) + "\r")
    sys.stdout.flush()
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


def get_venv_python() -> str:
    """Absolute path to the interpreter inside the project venv."""
    if os.name == 'nt':
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def in_venv() -> bool:
    """True when already running inside a virtual environment."""
    return sys.prefix != sys.base_prefix


def venv_ready() -> bool:
    """True when the project venv exists with a working interpreter."""
    return os.path.exists(get_venv_python())


# ---------------------------------------------------------------------------
# OS HELPERS (slim, stable, no sudo auto-magic on desktop)
# ---------------------------------------------------------------------------
def _has_command(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _detect_linux_pm() -> str | None:
    for pm in ("apt", "apt-get", "dnf", "yum", "pacman", "zypper", "apk", "emerge"):
        if _has_command(pm):
            return pm
    return None


def _print_venv_hints() -> None:
    """Print actionable, OS-specific hints when venv creation fails."""
    if IS_TERMUX:
        log_warn("  Termux: pkg install python python-pip clang")
        log_warn("          pkg install python-numpy python-scipy python-pandas")
    elif IS_MACOS:
        if _has_command("brew"):
            log_warn("  macOS (brew): brew install python")
        else:
            log_warn("  macOS: install Homebrew from https://brew.sh then: brew install python")
        log_warn("  macOS (Xcode tools): xcode-select --install")
        log_warn("  Fallback venv: python3 -m venv .venv && source .venv/bin/activate")
    elif IS_LINUX:
        pm = _detect_linux_pm()
        if pm in ("apt", "apt-get"):
            log_warn("  Debian/Ubuntu: sudo apt update && sudo apt install python3-venv python3-pip")
        elif pm == "dnf":
            log_warn("  Fedora:        sudo dnf install python3-virtualenv python3-pip")
        elif pm == "yum":
            log_warn("  RHEL/CentOS:  sudo yum install python3-virtualenv python3-pip")
        elif pm == "pacman":
            log_warn("  Arch:          sudo pacman -S python python-virtualenv python-pip")
        elif pm == "zypper":
            log_warn("  openSUSE:      sudo zypper install python3-virtualenv python3-pip")
        elif pm == "apk":
            log_warn("  Alpine:        apk add python3 py3-virtualenv py3-pip")
        else:
            log_warn("  Debian/Ubuntu: sudo apt install python3-venv")
            log_warn("  Fedora:        sudo dnf install python3-virtualenv")
            log_warn("  Arch:          sudo pacman -S python-virtualenv")
            log_warn("  Generic:       python3 -m venv .venv && source .venv/bin/activate")
    elif IS_WINDOWS:
        log_warn("  Windows: reinstall Python with 'Add to PATH' and 'pip' enabled")
        log_warn("           or: py -m pip install --upgrade pip")
        log_warn("           or: python -m venv .venv && .venv\\Scripts\\activate")
    else:
        log_warn("  Generic: python3 -m venv .venv && source .venv/bin/activate")


def _ensure_termux_system_packages(packages: list[str]) -> None:
    """On Termux, auto-install native `pkg` packages before falling back to pip.

    This is safe (no sudo) and avoids compiling numpy/scipy which often fails on
    device. Silently no-ops on non-Termux or when `pkg` is unavailable.
    """
    if not IS_TERMUX:
        return
    pkg_cmd = "pkg" if _has_command("pkg") else ("apt" if _has_command("apt") else None)
    if pkg_cmd is None:
        return

    needed: list[str] = []
    for p in packages:
        pkg_name = TERMUX_PKG_MAP.get(p)
        if pkg_name and not is_package_installed(p):
            needed.append(pkg_name)

    if not needed:
        return

    # Ensure essential build chain is present (harmless if already installed)
    # clang/pkg-config help wheels that still need compilation.
    log_info(f"Termux detected — installing native packages: {' '.join(needed)} …")
    result = run_with_spinner([pkg_cmd, "install", "-y"] + needed, "Installing Termux packages", timeout=300)
    if result.returncode == 0:
        log_success("Termux system packages installed.")
        return

    # Fresh Termux installs often need `pkg update` first — retry once.
    err = ((result.stderr or "") + (result.stdout or "")).lower()
    if any(k in err for k in ("unable to locate", "package not found", "no such package", "404")):
        log_warn("Retrying after pkg update …")
        upd = run_with_spinner([pkg_cmd, "update", "-y"], "Updating Termux packages", timeout=300)
        if upd.returncode == 0:
            retry = run_with_spinner([pkg_cmd, "install", "-y"] + needed, "Installing Termux packages", timeout=300)
            if retry.returncode == 0:
                log_success("Termux system packages installed (after update).")
                return
    log_warn("Termux pkg install didn't complete — pip fallback will try anyway.")
    if result.stderr:
        last_line = result.stderr.strip().splitlines()[-1][:180] if result.stderr.strip() else ""
        if last_line:
            log_warn(last_line)


def _warn_macos_build_error(stderr: str) -> None:
    if not IS_MACOS:
        return
    low = stderr.lower()
    if any(k in low for k in ("xcode", "clang: error", "unable to execute clang", "failed building wheel", "compilation failed", "xcrun: error")):
        log_warn("macOS build tools missing — try: xcode-select --install")
        if _has_command("brew"):
            log_warn("With Homebrew you can also run: brew install python")
    if "externally-managed-environment" in low:
        log_warn("Homebrew Python is externally managed — using isolated venv instead (automatic).")


def ensure_venv() -> bool:
    """Create the project venv if missing. Returns True on success."""
    if venv_ready():
        return True

    log_info(f"Creating isolated virtual environment '{VENV_DIRNAME}'...")

    create_cmds = [
        [sys.executable, "-m", "venv", VENV_DIR],
        ["python3", "-m", "venv", VENV_DIR],
    ]
    if _has_command("virtualenv"):
        create_cmds.append(["virtualenv", VENV_DIR])

    created = False
    last_result: subprocess.CompletedProcess | None = None
    for cmd in create_cmds:
        result = run_with_spinner(cmd, "Creating virtual environment", timeout=180)
        last_result = result
        if result.returncode == 0 and venv_ready():
            created = True
            break

    if not created:
        # macOS auto-recovery via Homebrew: lightweight, only if brew exists
        # and venv creation failed because ensurepip/venv is broken.
        if IS_MACOS and _has_command("brew"):
            # Heuristic: if sys.executable is brew python, reinstall ensures venv support
            low = (last_result.stderr.lower() if last_result and last_result.stderr else "")
            if "ensurepip" in low or "venv" in low or "command not found" in low or not created:
                log_info("Attempting automatic recovery via Homebrew: brew install python …")
                brew_res = run_with_spinner(["brew", "install", "python"], "Installing Python via Homebrew", timeout=300)
                if brew_res.returncode == 0:
                    # Retry once after brew
                    for cmd in ([sys.executable, "-m", "venv", VENV_DIR], ["python3", "-m", "venv", VENV_DIR]):
                        r2 = run_with_spinner(cmd, "Creating virtual environment", timeout=180)
                        if r2.returncode == 0 and venv_ready():
                            created = True
                            break
                    if created:
                        log_success("Virtual environment created after Homebrew recovery.")
        if not created:
            log_error("Could not create a virtual environment.")
            log_warn("Install venv support first, then re-run this script:")
            _print_venv_hints()
            return False

    # Ensure pip works inside the venv (some distros ship bare venvs)
    venv_python = get_venv_python()
    probe = subprocess.run([venv_python, "-m", "pip", "--version"], capture_output=True, text=True, check=False)
    if probe.returncode != 0:
        log_info("Bootstrapping pip in the virtual environment...")
        run_with_spinner([venv_python, "-m", "ensurepip", "--upgrade"], "Bootstrapping pip")
        run_with_spinner([venv_python, "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip")
    return True


def install_into_venv(package: str) -> bool:
    """Install a package into the project venv. Returns True on success."""
    if not ensure_venv():
        return False
    venv_python = get_venv_python()
    for extra_args in ([], ["--no-build-isolation"]):
        result = _run_pip_install(package, extra_args, python_bin=venv_python)
        if result.returncode == 0:
            return True
    return False


def relaunch_in_venv() -> None:
    """Relaunch the script with the venv interpreter (packages are visible there)."""
    log_success(f"All modules installed into the virtual environment '{VENV_DIRNAME}'.")
    log_info("Relaunching with the venv interpreter...")
    os.execv(get_venv_python(), [get_venv_python(), os.path.abspath(__file__)] + sys.argv[1:])


def is_package_installed(package: str) -> bool:
    """Check if a package is importable (handles Pillow -> PIL etc.)."""
    import_name = PACKAGE_IMPORT_MAP.get(package, package).replace("-", "_")
    # try as-is and lowercase (Pillow vs pillow)
    for name in (import_name, import_name.lower()):
        if importlib.util.find_spec(name) is not None:
            return True
    return False


def _run_pip_install(package: str, extra_args: list[str] | None = None, python_bin: str | None = None) -> subprocess.CompletedProcess:
    """Run pip install with given extra arguments."""
    cmd = [python_bin or sys.executable, "-m", "pip", "install", "--quiet"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(package)
    return run_with_spinner(cmd, f"{ICONS['dl']} Installing {package}", timeout=180)


def install_package(package: str, android_mode: bool = False) -> bool:
    """
    Install a package with multiple fallback strategies.
    Returns True on success, False on failure.
    """
    global USED_VENV

    # Once this run committed to the venv, use it for every remaining package.
    if not android_mode and not IS_WINDOWS and not in_venv() and USED_VENV:
        return install_into_venv(package)

    strategies: list[list[str]] = []

    if android_mode:
        # Termux: try system packages first, then pip with --no-build-isolation
        strategies = [
            ["--no-build-isolation"],
            ["--no-build-isolation", "--no-deps"],
            [],
        ]
    elif IS_WINDOWS:
        # Windows: standard install, then --user, then --break-system-packages
        strategies = [
            [],
            ["--user"],
            ["--break-system-packages"],
        ]
    elif in_venv():
        # Already inside a venv: plain installs are safe
        strategies = [[]]
    else:
        # Linux/macOS: standard, then --user, then --break-system-packages
        # (bypasses PEP 668 "externally-managed-environment" blocks)
        strategies = [
            [],
            ["--user"],
            ["--break-system-packages"],
        ]

    last_result: subprocess.CompletedProcess | None = None
    for extra_args in strategies:
        result = _run_pip_install(package, extra_args)
        last_result = result
        if result.returncode == 0:
            return True
        stderr = result.stderr.lower() if result.stderr else ""
        if "externally-managed-environment" in stderr or "permission denied" in stderr:
            continue
        # For other errors, don't retry with different strategies
        break

    if last_result is not None and last_result.stderr and IS_MACOS:
        _warn_macos_build_error(last_result.stderr)

    # Last resort on Linux/macOS: install into an isolated project venv so we
    # sidestep externally-managed environments and permission issues entirely.
    if not android_mode and not IS_WINDOWS and not in_venv() and install_into_venv(package):
        USED_VENV = True
        return True

    return False


def check_and_install_dependencies(packages: list[str], android_mode: bool = False) -> None:
    """Install missing packages via pip with fallback strategies."""
    # Auto-handle Termux native packages before pip (no-op elsewhere)
    if android_mode or IS_TERMUX:
        _ensure_termux_system_packages(packages)

    missing = [p for p in packages if not is_package_installed(p)]

    if not missing:
        log_info("All core dependencies are already installed.")
        return

    # Short platform tag for transparency
    plat_label = {
        "windows": f"Windows {platform_module.version().split('.')[0] if IS_WINDOWS else ''}".strip(),
        "macos": f"macOS {platform_module.mac_ver()[0] or platform_module.release()}",
        "termux": "Android/Termux",
        "linux": f"Linux ({platform_module.release()})",
    }.get(PLATFORM, PLATFORM)
    log_info(f"Missing packages: {', '.join(missing)} - installing via pip… [{plat_label}]")

    total = len(missing)
    for idx, package in enumerate(missing, 1):
        success = install_package(package, android_mode=android_mode)

        if success:
            log_success(f"({idx}/{total}) {package} installed.")
        else:
            log_error(f"Failed to install '{package}' via pip.")
            if android_mode or IS_TERMUX:
                log_warn("On Android/Termux, try installing system packages first:")
                log_warn("  pkg install python-numpy python-scipy python-pandas")
                log_warn("  pkg install clang python-pip  # if compilation fails")
            elif IS_MACOS:
                log_warn("macOS Homebrew Python may be externally managed.")
                log_warn("  Try: python3 -m venv .venv && source .venv/bin/activate")
                log_warn("  Then: pip install <package>")
                if not _has_command("brew"):
                    log_warn("  Install Homebrew: https://brew.sh")
                else:
                    log_warn("  Or: brew install python")
                log_warn("  If you see clang/xcode errors: xcode-select --install")
            elif not IS_WINDOWS:
                log_warn("Your system may use an externally managed Python environment.")
                log_warn("Try: pip install --break-system-packages <package>")
                log_warn("Or create a virtual environment: python -m venv venv && source venv/bin/activate")
                _print_venv_hints()
            else:
                log_warn("Try: python -m pip install --user <package>")
                log_warn("Or: python -m venv .venv && .venv\\Scripts\\activate")
            sys.exit(1)

    if USED_VENV and not in_venv():
        # Packages were installed into the venv; relaunch so the app finds them.
        relaunch_in_venv()
        return

    log_success("All modules installed successfully.")


# ---------------------------------------------------------------------------
# LAUNCH HELPERS
# ---------------------------------------------------------------------------
def print_banner() -> None:
    """Compact project banner - printed instantly, no animation."""
    print()
    if USE_ICONS:
        title = f"{ICONS['cube']}  INFORMATICS PROJECT - AI & PYRAMIDS"
        print(f"  \033[1;96m{title}\033[0m")
        print("  " + "\u2500" * (len(title) + 4))
    else:
        print("  >>>  INFORMATICS PROJECT - AI & PYRAMIDS  <<<")
    print()


def choose_launch_mode() -> bool:
    """Interactive menu to choose the launch mode (True = CLI/TUI)."""
    print()
    print("  Select launch mode:")
    if USE_ICONS:
        print(f"    {ICONS['web']}  [1]  Streamlit Web Dashboard")
        print(f"    {ICONS['tui']}  [2]  Terminal UI (TUI)")
    else:
        print("    [1]  Streamlit Web Dashboard")
        print("    [2]  Terminal UI (TUI)")
    print()

    while True:
        try:
            choice = input("  Choice [1/2]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("  Aborted.")
            sys.exit(0)

        if choice == "1":
            print()
            log_success("Web dashboard selected. Starting Streamlit...")
            return False
        if choice == "2":
            print()
            log_success("Terminal UI selected. Starting interface...")
            return True

        print("  \033[91mInvalid input - please enter 1 or 2.\033[0m")


def start_streamlit_app() -> None:
    """Launch the Streamlit web dashboard."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_app = os.path.join(script_dir, "app.py")

    if not os.path.exists(target_app):
        log_error(f"Core instance '{target_app}' not found!")
        sys.exit(1)

    log_info("Launching Streamlit dashboard...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", target_app], check=False)
    except KeyboardInterrupt:
        print()
        log_info("System shut down by user.")
    except subprocess.CalledProcessError as e:
        log_error("Streamlit instance terminated unexpectedly.", e)


def start_cli_app() -> None:
    """Launch the terminal UI (app_tui package)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    try:
        from app_tui.main import main as tui_main
        tui_main()
    except KeyboardInterrupt:
        print()
        log_info("Terminal UI terminated by user.")
    except Exception as e:  # noqa: BLE001
        log_error("Failed to start terminal UI.", e)
        sys.exit(1)


def clear_screen() -> None:
    """Cross-platform screen clear."""
    if os.name == 'nt':
        os.system('cls')
    else:
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    clear_screen()

    parser = argparse.ArgumentParser(description="Launcher: Start Streamlit or Terminal CLI")
    parser.add_argument('--cli', action='store_true', help='Start the terminal UI (TUI)')
    parser.add_argument('--streamlit', action='store_true', help='Explicitly start Streamlit dashboard')
    parser.add_argument('--no-prompt', action='store_true', help='Skip interactive selection (useful for CI)')
    args = parser.parse_args()

    # Determine launch mode
    auto_mode = os.environ.get("AUTO_SETUP_MODE")
    if auto_mode == "cli":
        selected_cli_mode = True
    elif auto_mode == "web":
        selected_cli_mode = False
    elif args.cli:
        selected_cli_mode = True
    elif args.streamlit:
        selected_cli_mode = False
    elif is_android_termux():
        selected_cli_mode = True
    elif not args.no_prompt and sys.stdin.isatty():
        selected_cli_mode = choose_launch_mode()
    else:
        selected_cli_mode = False

    # Remember the choice so a venv relaunch doesn't prompt again.
    os.environ["AUTO_SETUP_MODE"] = "cli" if selected_cli_mode else "web"

    if selected_cli_mode:
        log_info("Starting terminal-based interface (TUI)")
        cli_packages = [p for p in REQUIRED_PACKAGES if p not in CLI_EXCLUDE]
        check_and_install_dependencies(cli_packages, android_mode=is_android_termux())
        print()
        start_cli_app()
    else:
        print_banner()
        check_and_install_dependencies(REQUIRED_PACKAGES)
        print()
        start_streamlit_app()
