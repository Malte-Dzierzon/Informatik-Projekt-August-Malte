"""
AUTOMATISCHES SETUP & START-SKRIPT
==================================
Überprüft die Abhängigkeiten und startet das Pyramiden-Dashboard
ordnungsgemäß im nativen Streamlit-Laufzeitmodus.
"""

import subprocess
import sys
import os
import importlib.util
import time
import random

from debug_utils import debug_error, debug_info

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
    "⠀⠠⢄⢠⢲⣒⠧⡐⢄⢢⠰⢠⠄⡀⠰⢢⠔⡢⠔⡢⢄⠀⠆⡴⡰⢠⠤⡀⠐⠹⢶⣒⢖⢢⢖⡰⢂⠦⡤⡀⠠⡀⠀⠲⢒⡔⣢⠔⡰⢠⠄⢢⡐⢠⢂⡔⢠⠄⡄⠂⡄⠠⢀⠀⡀",
    "⢈⠱⡌⢢⢯⡝⢢⡉⢦⡑⢎⡡⢎⡐⠈⣇⢮⢱⡹⣰⣉⠦⠘⢰⢻⣦⠳⣱⠀⢀⠈⢻⣿⣔⡧⣽⢩⣎⡵⣩⡤⠐⢆⠀⠈⠑⠃⠞⢱⠣⡝⡴⣈⠇⢦⡘⢆⠎⡔⡡⢂⠅⠢⢌⠠⢁⠈⠄⠂⠁⠠⠀⠄",
    "⢠⠣⡜⢣⡛⡌⠧⣜⡡⢚⠥⣚⠤⣊⠄⢺⣬⠳⡼⣱⢎⡼⡀⠀⠑⣾⣧⡳⣍⠀⠣⢄⠘⢿⣾⣵⣻⣜⣷⣣⢿⡵⡈⢧⡀⠃⠜⣠⢂⢄⡉⠐⠹⣌⠧⣘⡍⡜⢢⡱⠌⣌⠑⡠⠒⡈⠄⢂⠡⠈⠄⡐⠀⡈⠀⠁",
    "⢄⡳⡜⢧⡽⣖⡳⣬⢳⡝⣮⣜⡱⢆⠢⢹⣎⡿⡵⢯⣞⡵⡃⢈⣆⠐⢿⣽⡚⣥⠘⣦⡁⠈⢻⣯⣿⢾⣭⣟⣯⢿⣵⡈⢷⡄⢡⠂⡄⠈⠘⠕⣆⣀⠘⠐⠌⡐⠃⠤⠑⡠⠊⠄⡑⠠⠈⠄⠂⢁⠠⠀⠀⠀⠀⠁",
    "⣌⡳⣝⢧⣿⣻⣷⣭⢗⣻⢶⣭⢳⣍⢎⠰⣿⣻⡟⣿⢯⣷⡁⢠⢿⣧⡈⢳⣿⡳⠆⢹⣿⣅⡂⢹⣿⢿⣾⣟⣾⡿⣾⣷⠘⣿⡄⠳⣌⢆⠀⠀⠀⠈⠳⣦⡀⠀⠈⠀⠀⠀⠐⠀⠀⠀⠁⠀⠈",
    "⢢⣟⣼⢻⣷⣿⣷⡿⣿⣽⣳⣯⢷⣎⡎⡄⣿⣷⣿⢿⣻⢾⠁⣸⠘⣿⣷⡄⠻⣧⡟⠀⣿⣿⣦⡀⠙⣿⣿⡾⣿⣽⣿⣽⣆⢸⣿⡄⠹⣞⡕⡀⠀⠀⠀⠀⠙⢦⡀",
    "⣹⢾⡽⣻⣿⣾⡿⣿⣷⣻⣷⢯⣿⢶⡹⠄⣿⣿⢾⣿⢿⣻⠀⣷⡂⣿⣿⣿⠄⠹⣿⣃⠈⣉⣉⣉⣀⠙⣷⣿⢿⣽⣾⣟⣿⡀⢿⣷⡀⠛⣿⣮⣆⠀⠀⠀⠀⠀⠙⢦⡀",
    "⢫⣿⣽⣻⣷⡿⣿⣿⡿⣽⡿⣿⣾⢯⡟⡆⣹⣿⡿⣯⣿⡏⢘⡮⠓⠉⣁⣤⣴⣆⠹⣷⠈⣿⣿⣿⣿⡄⠙⣿⣿⢯⣿⣾⢿⣇⢸⣿⣷⠀⠱⢾⣻⣧⡀⠀⠀⠀⠀⠀⠳⣄",
    "⢸⣷⡿⣽⣾⢿⣿⣷⣿⢿⣻⣿⢾⡿⣝⠦⢹⣿⣟⣿⣷⠁⢁⣤⣶⣿⣿⣿⣿⣿⣧⠸⡆⢻⣿⣿⣿⣯⣃⠸⣿⡿⣯⣿⡿⣿⠀⣿⣿⡆⠀⠈⠳⣟⣷⡄⠀⠀⠀⠀⠀⠈⢣⡀⠀⠀⠀⢀⠀⠀⠀⠀⡈⠐⠀⠂",
    "⡇⢿⣟⣿⣽⡿⣷⣿⣯⣿⣿⣽⣿⣻⡽⢎⢸⣿⣿⣽⡞⢰⣟⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠘⣿⠻⣿⡟⢁⣆⠹⣿⣟⣷⣿⢿⡇⣿⢿⣿⠀⠀⠀⠙⢯⣿⣆⠀⠀⠂⠀⠀⠀⠱⡀⠀⠀⠀⠀⠀⠀⠀⠄⡀⢀",
    "⣿⡸⣿⣏⣿⣹⣿⣷⣿⢿⣾⡿⣾⣿⣹⠇⣸⣿⣷⣿⠁⣾⣿⣿⣿⣿⣿⡿⣁⣿⣿⡿⠇⠀⠀⠀⠀⠀⠉⠏⠀⢹⣿⣏⣿⣿⡇⢹⣿⣿⡇⠀⠀⠀⠀⢿⣹⣇⠀⠀⠀⠆⠀⠀⢱⠀⠀⠀⠀⢀⠀⠰⠆⡀⠀⠀⠀⠀⠰",
    "⢿⣧⢻⣿⣽⣿⣳⣿⣯⣿⣯⣿⣟⣷⣯⠃⣿⣿⣽⡏⣰⣿⣿⣿⣿⡿⢋⣴⡿⠛⠁⣠⣤⠤⠶⠾⠶⣶⣦⣄⠈⠈⣿⣯⣿⣾⡇⢸⣿⣟⣧⠘⣁⠀⠀⠀⠙⣿⣆⠀⠄⠀⠀⠄⠀⢡⠀⠀⠴⠀⠠⠘⡐⡆⠘⠄⡀⠀⠄⠐",
    "⡞⣿⡎⢿⣾⣻⣽⣷⡿⣽⣾⣯⣿⣻⡼⠃⣿⣟⡾⢠⣿⣿⣿⣿⠟⣱⡿⠋⠀⣠⡾⠋⠀⠀⢀⠀⠀⠀⠉⠻⣷⣄⠸⣿⡷⣿⣇⢸⣿⡿⣿⡄⢯⢄⣀⠀⠀⠈⢻⣦⠀⠀⠁⠀⠀⠀⢂⠀⠂⠀⠀⠄⡑⡀⠀⠁⠒⠀⠊⢐",
    "⣷⡘⣿⡜⣿⣻⣽⣾⢿⣟⣷⣿⣳⡿⣍⢣⣿⡿⢀⣿⣿⣿⣿⣿⣾⡟⠱⠀⣴⡽⠁⠀⠀⠆⣐⣬⣐⠀⠀⠀⠙⣿⡆⢻⣟⣿⡇⢸⣿⣿⢿⡇⠈⠀⣿⣿⡄⠀⠀⠙⣷⡀⠈⠀⠀⠀⠈⢀⣀⠀⠀⢠⠐⠃⠚⠀⠀⠀⠔⢈⠀⠀⠒",
    "⠿⠇⠘⣿⡘⢿⣯⡿⣟⣯⣿⢾⡿⣽⢣⢸⣿⢁⣾⣿⣿⣿⣿⣿⣿⣧⠆⠀⣿⣿⣾⣷⣆⢈⡿⣞⣟⣷⡄⠀⠀⠘⣷⠸⣿⣯⡇⢸⣿⣯⣿⡇⢸⠀⢹⣿⣿⡀⠀⠀⠈⢻⣄⠀⠂⠈⠀⠘⢽⠀⠀⠠⢉⢦⠰⠀⡀⠄⣀⠨⠀⠀⠀",
    "⠀⣴⣧⠘⣿⡌⢿⣟⣿⢯⣿⣟⡿⣝⠆⡿⠃⣼⣿⣿⣿⣿⣿⣿⣿⣿⣸⠈⣿⣿⣿⣿⡿⠀⠹⣯⣛⣯⡆⢸⣯⣄⠙⠀⣿⣟⡇⣾⣿⣽⡿⡇⠘⠁⠀⠻⣿⡇⠀⠀⠄⠀⠹⣆⠀⠀⠀⠀⠈⠜⠁⠀⠨⠠⢉⠔⡁⠊⠄⡘⠀⠀⠈",
    "⠀⢻⣿⣧⡘⣧⠆⢻⣯⣿⣻⣾⢿⡱⢲⢃⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⣿⣿⣷⡀⠀⠀⣶⣌⡙⠓⢂⣼⣿⠟⣀⡅⢻⣿⠀⣿⣽⣾⣿⠃⠀⣀⣀⣰⣿⡇⢰⠀⠀⠀⡀⠈⢧⡀⠀⠀⠀⠀⠀⠀⠀⠁⢂⠐⠠⢁⠂⠄⠐⠀⠀",
    "⡩⠀⢿⣿⣷⡈⢟⡄⢹⡿⣽⣛⣮⠃⢡⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠸⣿⣿⣿⣿⣿⡿⢋⣼⣿⡇⢸⡇⢰⣿⣯⣷⣿⠀⠀⢿⣿⣿⣿⠆⠈⢱⠀⠀⢀⠀⠈⠳⡀⠀⠀⠃⠀⠐⠱⠚⠲⠞⠳⠦⠈⠀⠀⠀⠤",
    "⡱⢁⠘⣿⣿⣿⡄⠙⠄⡉⢻⡿⣅⠀⢺⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⠻⢿⣷⣌⠻⠿⠟⣫⣴⣿⣿⣿⡇⢸⠃⠈⣿⣽⣷⡇⠀⠀⢸⣿⡾⠟⠀⠀⠈⢆⠀⠀⠀⠄⠀⠱⡄⠀⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⣱⠩⡀⠸⣿⡍⠀⣀⠀⠀⠈⢻⠖⠀⠀⠘⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⣶⣶⣾⣿⣿⣿⣿⣿⣿⠇⡛⡰⢈⣿⣻⣾⠁⠀⠀⠉⠁⠀⠀⠀⠀⠀⠈⠆⠀⠀⠀⠀⠀⠘⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⣇⠣⠜⡀⢠⡅⠀⣿⣷⡄⢀⢀⢇⣦⠀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠂⢁⡏⢸⣟⡞⡟⠀⠀⠀⠀⠀⠀⢀⣀⣤⣶⣾⣿⣿⣿⣶⣤⡀⠀⠈⢦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠸⣹⡐⠡⠀⢠⠀⣿⣿⠿⠆⠀⢞⡦⢯⠐⣦⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⣸⡇⣸⢯⡿⠁⠀⠀⠀⢀⣠⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⠀⠀⢣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠑⢌⣃⠂⠀⠣⣹⣿⣦⠀⠀⣦⡈⠃⠀⡁⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⣰⣿⠃⣼⢯⠓⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠡⠀⠀⠀⠠⡄⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⢍⡀⠀⠙⢟⣿⣷⣄⠻⣿⡿⠃⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⣯⡜⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠄⠀⠀⠡⣤⣬⣥⣤⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠠⢘⠶⠁⠀⠀⠀⠀⠀⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠋⡠⠁⠬⠁⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠁⢂⠐⡀⠄",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠁⡴⠋⠀⠁⠀⠀⠀⠀⡇⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠆",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡁⠉⢙⣿⣿⣿⣿⣿⣿⣿⣿⠟⠠⠮⠁⠀⠀⠀⠀⠀⠀⠀⣾⣷⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⢂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣯⣿⣿⣿⣿⣿⣿⠟⠀⠀⠂⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⡇⠀⠀⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⣠⣾⠀⢂⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⢂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠛⠿⠿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⣿⠀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠋⣰⣿⣿⠄⠡⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠲⠖⠢⠀⢌⡉⠙⠛⠛⠛⠛⠛⣁⠤⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀⢀⣼⣿⣿⣿⣿⣿⣇⠀⠀⠸⣿⣿⣿⣿⣿⣿⣿⡿⠁⢸⡿⣿⣿⠀⠈⠡⠀⠀⠰⢄⠢⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⢸⡏⢹⣷⠀⢀⠀⠀⢎⣱⢹⡸⢈⡹⡎⣀⠀⠀⢀⠀⠀⠀⠀⢀⣿⡿⣿⣏⣿⣹⣏⣿⠀⠀⠀⢿⣷⣿⣹⣿⣹⡿⠁⣶⠈⢸⢷⡏⢀⠀⠁⠀⠀⢾⣆⢉⡆",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠸⣤⡑⢨⢇⠲⡩⢆⡣⢄⡀⢂⡀⣠⣼⢿⡷⡿⣯⣟⣷⣻⢯⡿⡇⠀⠀⠸⣧⢿⣽⣾⠏⢁⣾⣻⠀⢈⠻⠀⣞⣧⢦⡄⢸⠢⠁⠀⠈",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⢀⠡⢈⠡⠒⠀⠀⠐⢻⠳⢮⡶⣜⢦⣣⡤⣤⣤⠟⣗⣏⡾⣵⣻⣞⣞⣳⢯⣟⢳⣇⠀⠄⠀⢷⣋⣷⣋⢤⡟⣾⢝⠂⠠⠀⢘⡳⣬⠞⣅⠘⠂",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠁⠂⠄⢃⠢⢑⢂⡀⠀⠈⣟⡱⣚⢬⠗⣣⠝⣦⢫⠞⡭⣞⡱⢧⡳⣍⢾⡱⣞⢎⣧⢳⠀⠀⠀⢈⠵⣣⢟⢮⢽⡸⠋⠀⢰⣙⠀⢹⣊⠽⣜⠲⡄",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⢁⠘⡨⠄⡊⠔⡂⡔⠀⠀⢎⠱⣘⠪⡹⢡⠛⠴⠋⡞⣱⢣⡝⢬⡓⡭⢎⡵⣌⢏⠶⣩⠇⢈⢠⠈⡞⡵⢎⡳⢎⡑⠁⠀⡸⣜⠀⢠⠓⠞⡬⡱⡈",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⢂⠡⢂⠥⡉⢔⡈⠆⢀⠀⠈⠄⠣⢡⢃⠹⡈⠣⠜⢂⢣⠚⡥⡱⡙⡜⢦⡙⢎⡱⢃⠆⠈⠀⠀⡜⡱⢎⡕⠊⢀⠌⠀⠰⡘⡄⠀⢐⠎⢥⠓⡡⠂",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠰⢁⠂⠀⠀⠀⠀⠠⢀⠀⠁⠂⠜⢠⢃⡌⠀⢂⠄⠀⠀⠀⠊⠐⠨⠁⡜⠈⠢⢁⠢⠡⢱⠘⠤⣉⠦⠱⣉⠆⠀⠀⠀⡸⢑⢎⠈⠠⠌⠀⠀⢒⠱⡘⠄⠈⡜⢢⠉⠔⠁",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠀⠀⠀⠀⠀⠐⠀⡀⢂⠐⠠⡀⠄⡀⠈⠂⠈⠘⡄⢣⢁⡀⠠⠐⠂⠀⠀⠁⠂⠀⠃⠂⠁⠂⠐⠄⠃⠐⠂⠀⠀⠀⠡⠋⠀⠌⠂⠀⠀⡈⠆⢂⠱⠀⡈⠔⢂⠉⡄",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠀⠈⠄⠐⠈⠄⡁⢂⠐⢀⠈⠐⠤⢈⠱⠀⡔⠠⡀⠄⡀⣀⠂⠡⠌⢂⠡⠒⠰⡀⠄⡀⢀⠠⢀⢂⠉⠀⠀⢀⠂⡘⠠⡁⠀⡐⠈⠔⡈⠰",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠂⠁⠠⠈⠐⠠⠀⠄⡀⠂⡀⠄⡀⢀⠀⠁⠐⠁⠐⠈⠐⡀⠌⠡⠘⠠⢁⠊⠡⠐⡡⠈⠄⢂⠁⠂⠀⠀⠀⠂⠐⠁⠂⠀⠐⢀⠁⠂⠐",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⡈⢀⠡⠀⠀⢁⠀⠂⠐⠀⠂⠁⢀⠂⠐⢤⠄⡀⠈⠠⠁⠂⠄⡈⠄⠁⡀⠁⠀⠂⠀⠀⠀⠀⠀⠄⠀⠀⡀⠐⠈⠀⠠⠈"
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


def animate_pyramid(lines, delay=0.02):
    """Baut die Pyramide flüssig und sauber Zeile für Zeile auf."""
    print("\n")
    for line in lines:
        print(line)
        time.sleep(delay)
    print("\n")


def check_and_install_dependencies():
    """Prüft Abhängigkeiten mit einer klassischen Retro-Spinner-Animation."""
    matrix_glitch_text("[SYSTEM] Initialisiere Core-Validierung...", delay=0.02)
    missing_packages = []
    
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    for package in REQUIRED_PACKAGES:
        import_name = IMPORT_MAPPING.get(package, package)
        
        # Coole Spinner-Animation pro Paket
        for r in range(6):
            sys.stdout.write(f"\r  {spinner[r % len(spinner)]} Analysiere Environment-Struktur... [{package}]")
            sys.stdout.flush()
            time.sleep(0.04)
            
        if importlib.util.find_spec(import_name) is None:
            missing_packages.append(package)
            
    # Zeile sauber löschen und Erfolg melden
    sys.stdout.write("\r[ERFOLG] Environment-Struktur erfolgreich gescannt.\n\n")
    sys.stdout.flush()

    if missing_packages:
        matrix_glitch_text(f"[WARN] Fehlende Module entdeckt: {missing_packages}", delay=0.02)
        matrix_glitch_text("[EXEC] Starte pip-Injektion...", delay=0.02)
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", *missing_packages],
                stdout=subprocess.DEVNULL
            )
            matrix_glitch_text("[OK] Alle Module erfolgreich kompiliert und injiziert.", delay=0.02)
        except subprocess.CalledProcessError as e:
            debug_error("Kritischer Fehler bei der Installation der Abhängigkeiten.", e)
            sys.exit(1)
    else:
        debug_info("Alle Core-Abhängigkeiten sind bereits aktiv.")


def run_countdown(seconds=3):
    """Führt einen animierten, coolen Countdown vor dem App-Start aus."""
    print()
    matrix_glitch_text("[SYSTEM] Alle Checks bestanden. Bereite System-Start vor...", delay=0.02)
    
    # Optische Lade-Blöcke passend zum Countdown
    blocks = ["███", "██", "█"]
    
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\r  >> Starte Server in {i} Sekunden... {blocks[i-1]:<3}")
        sys.stdout.flush()
        time.sleep(1)
        
    sys.stdout.write("\r  >> INITIALISIERE STREAMLIT FRAMEWORK... (100%)\n")
    sys.stdout.flush()
    time.sleep(0.4)


def start_streamlit_app():
    """Ermittelt den Pfad zur app.py und startet das Dashboard."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_app = os.path.join(script_dir, "app.py")
    
    if not os.path.exists(target_app):
        debug_error(f"Kern-Instanz '{target_app}' fehlt!")
        sys.exit(1)
        
    python_version = sys.version.split()[0]
    
    # 3-Sekunden Cooldown/Countdown abfeuern
    run_countdown(seconds=3)
    print("-" * 110)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", target_app], check=True)
    except KeyboardInterrupt:
        debug_info("System vom Benutzer kontrolliert heruntergefahren.")
    except subprocess.CalledProcessError as e:
        debug_error("Streamlit-Instanz wurde unerwartet beendet.", e)


if __name__ == "__main__":
    # OS-Terminal säubern für maximalen Effekt
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # 1. Animierter Aufbau der originalen Pyramide
    animate_pyramid(PYRAMID_LINES, delay=0.02)
    
    # 2. Tech-Rahmen einblenden (Länge angepasst an Grafik)
    print("┌" + "─" * 108 + "┐")
    matrix_glitch_text("│                               >>>  K I - P Y R A M I D E N - P R O J E K T  2 0 2 6  <<<                             │", delay=0.01)
    print("└" + "─" * 108 + "┘")
    print()
    
    # 3. Validierung, Cooldown & Start
    check_and_install_dependencies()
    print("\n" + "=" * 110)
    
    start_streamlit_app()