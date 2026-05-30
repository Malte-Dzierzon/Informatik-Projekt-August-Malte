"""
AUTOMATISCHES SETUP & START-SKRIPT (OPTIMIERT)
====================================================================
Überprüft die Abhängigkeiten, bietet eine visuelle Progressbar bei 
der Pip-Injektion und sichert die Cross-Device-Kompatibilität.
"""

import subprocess
import sys
import os
import importlib.util
import time
import random
import argparse

# Fallback für debug_utils, falls das Skript isoliert ausgeführt wird
try:
    from debug_utils import debug_error, debug_info
except ImportError:
    def debug_error(msg, err=None):
        print(f"\033[91m[FEHLER] {msg} ({err if err else ''})\033[0m")
    def debug_info(msg):
        print(f"\033[94m[INFO] {msg}\033[0m")

# UTF-8 Erzwingung für Windows-Terminals gegen UnicodeEncodeError bei Braille-Grafiken
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ANSI-Escape-Zyklen für Windows CMD/PowerShell aktivieren
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# Pip-Paketnamen, die installiert werden müssen
REQUIRED_PACKAGES = [
    "streamlit",
    "numpy",
    "scipy",
    "pandas",
    "plotly"
]

IMPORT_MAPPING = {}

# Die originale Pyramide, exakt block-formatiert gegen Verzerrungen und Zeilenbugs
PYRAMID_LINES = [
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⡞⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣴⠖⠋⠀⠀⡸⠁⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠋⡟⠁⠀⠀⠀⡴⡁⢁⡇⠀⣀⣠⡤⠶⠖⠛⠋⠉⠉⠉⠉⠉⠉⠉⢉⣉⣽⠶⠶⠦⠤⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠞⠄⢸⠁⠀⠀⢠⢞⠌⣀⡾⠖⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⡶⠯⠭⠤⠤⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡎⠎⠀⠾⣀⠤⠞⠁⠅⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠝⠒⠢⠤⠤⢤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣎⠀⠀⠀⠀⠀⠀⠠⡐⠀⣀⡤⠤⢖⣲⠶⠖⠒⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⢓⠲⠤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡠⠴⠽⠤⠀⠀⠀⠠⠊⠐⡴⠋⠀⣠⠞⡩⠐⠈⠀⠀⠉⠉⠒⠒⠦⢤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠤⠶⠶⠶⣶⡤⠴⣄⣉⠓⢦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠋⠀⠀⠀⠀⠀⠀⠉⠢⡀⡼⠁⢀⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⢦⡀⠀⠀⠀⠀⠀⠐⠒⠤⣀⠀⠀⠀⠉⠀⠒⠠⢉⠳⣄⠈⠉⠒⠬⣳⢄⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡤⠞⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡈⠌⠢⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠳⡀⠀⠀⠀⠀⠀⠀⠂⠝⠢⣄⠀⠀⠀⠀⠀⠈⠐⠑⢄⠀⠀⠀⠉⠓⢄⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⢀⣀⡤⠖⠫⠑⠀⠀⠀⠀⠀⡠⠚⠁⠀⠀⠀⠀⠀⠀⠈⠁⠒⠚⠦⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢦⡀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠲⢤⣀⡀⠀⠀⠀⠨⡳⣄⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠒⠒⠒⢒⡾⠁⠀⠀⢀⢞⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢒⠲⠤⣑⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠱⡀⠀⠀⢠⡀⠀⠀⠀⠉⡒⠒⠲⠿⠍⠓⠒⠂⠐⠌⢷⣄⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠋⠀⠀⠀⢠⠏⠂⢠⠞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠐⠌⡑⡄⠀⠀⠀⠀⠀⠀⠀⡄⠀⠀⠀⠀⡀⠀⠀⠀⠙⡄⠀⠀⠙⢦⡀⢢⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠢⡙⢷⣄⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠟⠁⠀⠀⠀⠀⣼⠀⣰⢯⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠹⠀⠀⠀⢰⡄⠀⢀⣧⠀⠀⠀⠀⠙⣷⡄⠀⠀⢹⡄⠀⠀⢨⣷⡈⢷⠀⠀⠀⠀⢶⡆⣤⣀⠀⠀⠀⠙⢮⡻⢷⣄⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠏⣠⡾⠀⠀⠀⠀⢻⢠⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢷⠀⢸⢸⠀⠀⠀⠀⠀⠙⡽⣆⠀⠀⣷⠀⠀⠀⢣⢳⡘⡇⠀⠀⣄⠀⠹⡌⠙⠻⠷⣶⣤⣤⣁⣰⣝⣻⣦⡄⡀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠏⠀⡱⠁⠀⠀⠀⠀⠈⢞⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣄⠀⠀⠀⠀⠀⢸⠀⡎⡌⠀⠀⠀⠀⠀⠀⠰⠹⡄⠀⢸⢰⠀⠀⠀⢊⢧⡇⠀⠀⠘⢄⠀⠐⡀⠄⠀⠈⠳⣍⠉⠉⠉⠉⠁⠀⠁",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠘⡴⠁⠀⠀⠀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢳⢆⠀⠀⠀⠀⡜⡜⡰⠀⠀⠀⠀⠀⠀⠀⠀⢃⢻⡀⢸⢸⠀⠀⠀⠀⢺⠁⠀⠀⠀⠈⢣⠀⠘⡆⢀⠂⠀⠈⢣⡀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⣞⠂⠀⠀⠀⡜⠈⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣎⠄⠀⠀⡐⢋⠔⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡼⡇⡜⢦⡀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠡⢳⡀⢹⡄⠀⠐⠀⠈⢵⡀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡎⡆⠀⠀⠀⡜⠀⠀⠘⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⣸⢺⡌⢆⠘⠊⠁⠀⠀⢀⡀⠀⠀⠀⠀⡀⠀⠀⢱⡿⡙⠈⣷⡀⠀⠀⠀⠀⡀⠀⠀⠀⠀⢃⢧⠀⡇⠀⡁⠐⠀⠀⢷⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡧⡇⠀⠀⠜⠀⠠⠀⡄⠰⠀⠀⠀⠠⡀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⡀⠀⢀⣏⣧⢻⡄⠢⠀⠀⠀⠀⢼⡿⣇⠀⠀⠀⠹⢄⠀⣘⠜⠀⡄⡗⣷⡀⠀⠀⠀⣷⡀⠀⠀⠀⠈⡼⡆⡇⠐⡀⢂⠁⢀⠘⡇⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡄⡇⢀⠌⠠⠀⠡⠀⡇⠀⡆⠀⡰⡅⢁⠀⠀⠀⠀⡇⠀⠀⠀⠀⢼⠁⠀⣸⢵⠈⢖⢻⣆⠑⠄⠀⠀⢸⠈⢾⢷⡀⠀⠀⢛⡆⠁⠀⠀⢇⡟⡜⣧⠀⠀⢸⢇⣷⠀⠀⠀⠀⢁⣧⠃⠐⡀⢂⠐⠠⠀⢻⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣯⠁⠧⠂⠀⡀⠠⠁⠄⡇⠀⠁⡔⡼⠀⠸⡀⠀⠀⢠⢹⠀⠀⠀⢌⣾⡆⢬⢏⠇⠀⠀⣣⢞⢷⣌⠢⡀⢸⡀⠀⢺⢳⡄⠀⠈⢽⠀⠀⠀⢸⢯⠳⢿⠀⢠⡿⡘⡜⡆⠀⠀⠀⠈⢼⠐⠠⠐⢠⡀⠠⠀⢸⡄⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⠌⠀⣠⡄⠄⠀⡐⠈⢠⡇⠀⣠⠞⠁⠀⠀⢷⠀⠀⠸⠘⣇⠀⠘⣼⢺⣣⣯⣮⣤⣤⣄⣈⠛⢿⣿⣦⣌⠪⣇⠀⠀⢣⢿⡀⠀⢸⡆⢀⣠⣾⡟⠃⢿⡇⢰⡿⠁⢏⣳⠀⠀⠀⢠⠀⠀⠄⡁⠈⣿⢦⡀⢸⡇⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡸⠉⣠⠼⠃⣇⠀⠂⠐⢀⣸⢡⣶⡛⣇⢀⠀⠂⠈⣇⠀⠀⡄⣽⡄⢳⣷⣾⣿⣿⣿⣿⣿⣿⣿⣿⣶⣌⠙⠿⢷⣼⣄⠀⠀⠫⣷⠀⢸⣇⠉⣫⣷⣵⣶⣾⣷⣿⣅⡀⠸⡜⡧⠀⠀⡘⠀⠈⢴⢨⣄⠐⢷⡹⣼⠃⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⠃⠉⠁⠀⠀⣿⠀⢁⡶⣻⣷⡻⠖⢫⠽⣆⠠⠀⠂⠘⣧⠀⠇⣿⢹⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀⠈⠀⠀⠀⠹⣇⢸⣽⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣭⡇⠇⠠⡇⢐⡀⠆⡈⡇⠙⠲⠽⠿⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡏⢀⡿⡙⠉⢀⣀⠀⠀⠙⢽⣶⣌⠀⠀⢿⣧⡘⣯⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀⢹⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⢿⣿⣷⢘⠆⢣⣸⣇⠘⠭⣿⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⢸⠇⠁⠀⢀⡛⢿⣦⡀⠀⠑⠻⣶⣆⡜⡾⣳⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⢿⣿⣿⣤⡶⣾⣟⣿⡶⣦⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⣋⣶⣿⣿⣍⡁⠀⠀⣉⢻⡆⠀⣼⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⠔⠻⡆⡀⠀⠐⡼⡟⢭⢳⡄⠀⠀⠀⠁⠉⠛⠊⢫⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⣅⣾⣿⣿⣿⠋⠁⠀⠀⠀⠀⠙⢹⣿⣿⣿⣿⣿⣿⡿⢟⣑⣾⣿⠟⡡⣪⣿⣯⠆⣼⣿⠾⣷⠀⣼⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢳⡡⠀⠈⠐⠈⠄⢂⠹⡄⠀⠀⠀⠀⠀⠀⠈⢞⣿⣿⣿⣿⣿⣿⡿⠟⣡⣾⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⠿⣋⣼⣾⡿⣋⢦⣼⣾⣿⣿⠁⠁⠇⠄⣰⠎⡇⡇⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢳⣕⡀⠀⠀⠀⠀⠀⢁⡀⠀⠀⠀⠀⠀⡀⠈⠺⣻⣿⣿⣿⣿⣦⣿⣿⣿⣿⣿⠿⠁⠀⠀⣲⠶⢤⣄⣀⠀⠀⢻⣿⣿⣥⣷⣿⢟⠩⣔⣴⣿⣿⣿⡿⠃⢰⠀⣠⡾⠃⠀⡷⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠳⣤⣀⠀⠀⣀⡨⠵⡄⠀⠀⠀⠀⠀⡐⠀⠈⠚⠽⠛⣿⣿⣿⡿⠻⠛⠁⠀⠀⠀⠀⣿⠀⡀⠠⠉⢻⠂⠀⠙⢟⡿⣿⣿⣮⣾⣿⣿⣿⣿⠟⠁⡘⡿⠚⠋⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠛⠛⠛⠛⠻⣆⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⠀⠀⡁⢠⡾⠀⠀⠀⠀⠈⠑⠛⠙⠉⠛⠋⠈⠁⠀⡰⣱⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠳⣕⣠⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣇⢁⢠⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠔⣱⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠲⠥⣆⣰⣞⣿⣗⣒⣒⣶⡶⠤⣤⣄⣀⠀⠀⠀⠈⠛⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣪⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡟⣗⠉⢟⢦⡀⠀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⣿⣶⣦⡶⣤⣤⣤⣤⣤⣤⣤⣴⣶⣴⣤⣤⠶⠞⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠈⠀⠀⠀⢻⣼⣯⣷⣿⣿⣯⣽⣿⣖⣒⣶⡦⠤⢤⣄⣀⣀⣀⣀⣀⣠⣿⡻⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣶⣶⣶⣶⣿⣿⣯⣅⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡄⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣾⣿⣯⣭⣽⣟⣛⣒⠲⠦⠤⢤⣤⣄⣀⣀⡀⠀⠀⠀⣀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡟⠛⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣶⣦⣬⣍⣷⣠⠶⢫⠟⣳⡄",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠺⢵⣰⣒⢾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠁⠀⠀⠈⣸⠇",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⣰⠏⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⡀⠀⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⢄⠙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⢼⣃⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⠀⠉⠑⠪⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⠡⠀⠹⣄⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡉⠙⠛⠻⠿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⣔⣢⣆⣿⠟⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⡀⠀⠀⠈⠙⠻⢿⣿⠿⠛⠉⠏⠀⠀⠀⠀⠀⠁⠀⠈⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⡀⠀⠀⠀⠀⠀⠉⠉⠛⠻⠿⣿⣿⣿⣿⡿⠋⠀⠉⠉⠉⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠇⠀⠀⠀⢠⠾⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⡀⠀⠙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠛⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣿⣿⣷⡄⣆⠈⢛⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⠀⢹⠀⠀⠀⠀⠀⣠⣴⣶⣶⣤⡀⠀⠀⠀⠀⣾⣿⣿⣿⡿⣿⢿⣗⡈⡔⡘⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣍⣛⠒⠶⢤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⣠⠴⠛⠉⠀⣠⠇⢸⡄⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣆⠔⠞⠲⣿⣿⣿⣿⡾⣃⣾⡿⠘⠄⠛⢰⣿⠟⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣤⣍⢳⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⣠⠞⠁⠀⠀⢀⡼⠁⢠⠇⠀⠀⠀⢐⣿⣿⣿⣿⢟⣿⣿⡿⢦⡰⡤⠟⢻⣿⣿⣷⣿⠟⠁⠀⠀⠀⠋⠁⠀⠀⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⢹⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⡼⠁⠀⠀⠀⠀⡞⠀⠀⠈⢹⠀⠀⠀⠈⢽⣿⣿⣵⣿⣿⡿⠃⢸⠀⡇⠀⠀⠈⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡻⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⣼⠁⠀⠀⠀⠀⢸⠁⠀⠀⠀⡟⠀⠀⠀⠀⠀⠁⠉⠩⠉⠋⠀⠀⣼⣠⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣽⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⢀⣀⠀⡇⠀⠀⠀⠀⠀⣿⢰⢾⠙⠛⠒⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡄⠰⢾⣿⣿⣿⣿⣿⣿⣿⡿⠿⠿⠿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡦⢤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀",
"⡎⠈⠧⡇⠀⠀⠀⠀⠀⢹⠸⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡤⢀⡇⠀⣴⣿⣿⣿⣿⣿⠟⠋⠀⠀⠀⠀⠀⠀⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⣴⣿⣶⣭⣽⣲⡄⠀⠀⠀⠀⠀",
"⢱⡀⠀⠉⠀⠀⠀⢂⠀⠈⢧⡙⠲⠤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⠁⠛⠐⠀⢹⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⠀⠀⠀",
"⠀⢳⡄⠀⠀⠀⠀⠀⠁⠀⠀⠙⢦⡀⠀⢸⠂⠀⠠⠠⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀",
"⠀⠀⠱⣦⡀⠀⠀⠀⠀⠀⠑⠄⢀⠉⠒⠸⡆⠀⠀⠀⠙⠦⠜⠒⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠓⢤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠋⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠈⠓⢤⡄⠀⠀⠀⠀⠀⠀⠐⠒⠮⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣹⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣿⣿⣿⣿⣿⡿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⢩⠷⠀⠀⠀⠀⠀⠀⠀⢠⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢐⣻⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠋⠉⠁⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠈⠳⠤⣄⣀⣀⣠⠤⠞⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣤⡴⠴⠶⠒⠚⠛⠉⠉⠉⠛⠛⠒⠒⠛⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⡀⣷⢾⣆⢲⡅⢶⡆⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⣇⣆⠄⠀⠀⣀⣀⣤⠤⠶⠚⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
]


def matrix_glitch_text(text, delay=0.03, glitch_count=3):
    """Erzeugt einen coolen Cyberpunk/Matrix-Einblendeffekt für Text."""
    chars = "X@#$&%*+=-_~"
    for i in range(len(text) + 1):
        visible = text[:i]
        if i < len(text):
            for _ in range(glitch_count):
                glitch_char = random.choice(chars)
                sys.stdout.write(f"\r{visible}{glitch_char}")
                sys.stdout.flush()
                time.sleep(delay / glitch_count)
        else:
            sys.stdout.write(f"\r{visible}")
    print()


def animate_pyramid(lines, delay=0.01):
    """Baut die Pyramide flüssig und sauber Zeile für Zeile auf."""
    print("\n")
    for line in lines:
        try:
            print(line)
        except UnicodeEncodeError:
            # Fallback für Terminals, die absolut kein UTF-8/Braille nativ interpretieren können
            print(line.encode('ascii', errors='replace').decode('ascii'))
        time.sleep(delay)
    print("\n")


def render_progress_bar(package_name, current, total, percentage):
    """Zeigt eine Cyberpunk-Style Progressbar im Terminal an."""
    bar_width = 30
    filled_len = int(round(bar_width * percentage / 100))
    bar = '█' * filled_len + '░' * (bar_width - filled_len)
    
    # Formatierter Ausgabestring mit fester Breite für stabiles UI-Rendering
    sys.stdout.write(f"\r  [\033[92m{bar}\033[0m] {percentage:3d}% | Injektiere: \033[96m{package_name:<12}\033[0m ({current}/{total})")
    sys.stdout.flush()


def check_and_install_dependencies(packages):
    """Prüft Abhängigkeiten und installiert fehlende Module mit echter Echtzeit-Progressbar."""
    matrix_glitch_text("[SYSTEM] Initialisiere Core-Validierung...", delay=0.02)
    missing_packages = []
    
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    for package in packages:
        import_name = IMPORT_MAPPING.get(package, package)
        
        for r in range(4):
            sys.stdout.write(f"\r  {spinner[r % len(spinner)]} Analysiere Environment-Struktur... [{package}]")
            sys.stdout.flush()
            time.sleep(0.03)
            
        if importlib.util.find_spec(import_name) is None:
            missing_packages.append(package)
            
    sys.stdout.write("\r[ERFOLG] Environment-Struktur erfolgreich gescannt.\n\n")
    sys.stdout.flush()

    if missing_packages:
        matrix_glitch_text(f"[WARN] Fehlende Module entdeckt: {missing_packages}", delay=0.02)
        matrix_glitch_text("[EXEC] Starte pip-Injektion via Subprozess-Pipeline...", delay=0.02)
        
        total_pkgs = len(missing_packages)
        
        for idx, package in enumerate(missing_packages, 1):
            # Initiale Bar für das aktuelle Paket auf 0%
            render_progress_bar(package, idx, total_pkgs, 0)
            
            # Basis-Kommando erstellen
            cmd = [sys.executable, "-m", "pip", "install", package]
            
            # PEP 668 Schutz für modernere Linux-Distributionen & Termux einpflegen
            if os.name != 'nt':
                cmd.append("--break-system-packages")
            
            # Simulation einer dynamischen Progressbar während der Ausführung des Subprozesses
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                
                # Solange der Installationsprozess läuft, animieren wir die Progressbar hoch
                fake_progress = 0
                while proc.poll() is None:
                    time.sleep(0.1)
                    if fake_progress < 85:
                        fake_progress += random.randint(2, 7)
                        if fake_progress > 85: fake_progress = 85
                    render_progress_bar(package, idx, total_pkgs, fake_progress)
                
                # Checken, ob die Installation mit Code 0 beendet wurde
                if proc.returncode == 0:
                    render_progress_bar(package, idx, total_pkgs, 100)
                    time.sleep(0.1)
                else:
                    # Fehlerbehandlung bei ungültigen Pip-Parametern (z.B. alte Pip-Version ohne --break-system-packages)
                    stderr_output = proc.stderr.read().decode('utf-8', errors='ignore')
                    if "--break-system-packages" in stderr_output or "no such option" in stderr_output.lower():
                        # Retry ohne den Flag
                        cmd = [sys.executable, "-m", "pip", "install", package]
                        proc_retry = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                        while proc_retry.poll() is None:
                            time.sleep(0.1)
                        if proc_retry.returncode == 0:
                            render_progress_bar(package, idx, total_pkgs, 100)
                            continue
                    
                    raise subprocess.CalledProcessError(proc.returncode, cmd)
                    
            except (subprocess.CalledProcessError, Exception) as e:
                print() # Zeilenumbruch nach der Progressbar bei Fehler
                if is_android_termux():
                    debug_error(f"Pip-Kompilierung auf Android fehlgeschlagen bei: {package}", e)
                    print("\033[93m[HINWEIS]\033[0m Auf Android/Termux benötigen Pakete wie numpy/scipy native Compiler-Bibliotheken.")
                    print("Bitte installiere sie manuell über Termux via: \033[96mpkg install python-numpy python-scipy\033[0m")
                else:
                    debug_error(f"Kritischer Fehler bei Injektion von {package}.", e)
                sys.exit(1)
                
        print("\n\033[92m[OK] Alle Module erfolgreich kompiliert und injiziert.\033[0m")
    else:
        debug_info("Alle Core-Abhängigkeiten sind bereits aktiv.")


def run_countdown(seconds=3):
    """Führt einen animierten, coolen Countdown vor dem App-Start aus (Überlauf-sicher)."""
    print()
    matrix_glitch_text("[SYSTEM] Alle Checks bestanden. Bereite System-Start vor...", delay=0.02)
    
    blocks = ["███", "██", "█"]
    
    for i in range(seconds, 0, -1):
        block_visual = blocks[(i - 1) % len(blocks)]
        sys.stdout.write(f"\r  >> Starte Server in {i} Sekunden... {block_visual:<3}")
        sys.stdout.flush()
        time.sleep(1)
        
    sys.stdout.write("\r  >> INITIALISIERE STREAMLIT FRAMEWORK... (100%)\n")
    sys.stdout.flush()
    time.sleep(0.4)


def choose_launch_mode() -> bool:
    """Fragt den Nutzer, ob Streamlit oder die Terminal-CLI gestartet werden soll."""
    print("Wähle den Startmodus:")
    print("  1) Streamlit(Web)")
    print("  2) Terminal-CLI")
    while True:
        choice = input("Auswahl [1-2]: ").strip()
        if choice == "1":
            return False
        if choice == "2":
            return True
        print("Ungültige Eingabe. Bitte 1 für Streamlit oder 2 für Terminal wählen.")


def start_streamlit_app():
    """Ermittelt den Pfad zur app.py und startet das Dashboard."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_app = os.path.join(script_dir, "app.py")
    
    if not os.path.exists(target_app):
        debug_error(f"Kern-Instanz '{target_app}' fehlt!")
        sys.exit(1)
        
    run_countdown(seconds=3)
    print("-" * 110)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", target_app], check=True)
    except KeyboardInterrupt:
        print()
        debug_info("System vom Benutzer kontrolliert heruntergefahren.")
    except subprocess.CalledProcessError as e:
        debug_error("Streamlit-Instanz wurde unerwartet beendet.", e)


def is_android_termux() -> bool:
    """Erkennt Android/Termux anhand typischer Umgebungsvariablen."""
    android_data = os.environ.get("ANDROID_DATA")
    termux_flag = os.environ.get("TERMUX_VERSION") or os.environ.get("PREFIX", "").startswith("/data/data/")
    return bool(android_data and termux_flag)


def start_cli_app():
    """Startet die Terminal-Alternative `app_android.py` für Android/Termux."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cli_app = os.path.join(script_dir, "app_android.py")

    if not os.path.exists(cli_app):
        debug_error(f"Kern-Instanz '{cli_app}' fehlt!")
        sys.exit(1)

    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    try:
        import app_android
        app_android.main()
    except KeyboardInterrupt:
        print()
        debug_info("CLI-Anwendung vom Benutzer beendet.")
    except Exception as e:
        debug_error("Fehler beim Start der CLI-Anwendung.", e)
        sys.exit(1)


if __name__ == "__main__":
    # OS-Terminal säubern (Cross-device sicher über system-call fallback)
    if os.name == 'nt':
        os.system('cls')
    else:
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

    parser = argparse.ArgumentParser(description="Startskript: Streamlit oder Terminal-CLI starten")
    parser.add_argument('--cli', action='store_true', help='Starte die terminalbasierte Android/Termux-Version (app_android)')
    parser.add_argument('--streamlit', action='store_true', help='Starte explizit das Streamlit-Dashboard')
    parser.add_argument('--no-prompt', action='store_true', help='Vermeide interaktive Auswahl (nützlich für CI)')
    args = parser.parse_args()

    if args.cli:
        selected_cli_mode = True
    elif args.streamlit:
        selected_cli_mode = False
    elif is_android_termux():
        selected_cli_mode = True
    elif not args.no_prompt and sys.stdin.isatty():
        selected_cli_mode = choose_launch_mode()
    else:
        selected_cli_mode = False

    if selected_cli_mode:
        debug_info('[SYSTEM] Starte terminalbasiertes Interface (CLI)')
        package_list = [pkg for pkg in REQUIRED_PACKAGES if pkg not in ('streamlit', 'plotly', 'pandas')]
        check_and_install_dependencies(package_list)
        print("\n" + "=" * 110)
        start_cli_app()
    else:
        # 1. Animierter Aufbau der originalen Pyramide
        animate_pyramid(PYRAMID_LINES, delay=0.01)

        # 2. Tech-Rahmen einblenden (Länge angepasst an Grafik)
        print("┌" + "─" * 108 + "┐")
        matrix_glitch_text("│                 >>>  K I - P Y R A M I D E N - P R O J E K T  2 0 2 6  <<<                   │", delay=0.01)
        print("└" + "─" * 108 + "┘")
        print()

        # 3. Validierung, Cooldown & Start
        check_and_install_dependencies(REQUIRED_PACKAGES)
        print("\n" + "=" * 110)

        start_streamlit_app()