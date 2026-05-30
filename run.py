"""
AUTOMATISCHES SETUP & START-SKRIPT (Cross-Platform: Windows & Linux)
====================================================================
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
    """Prüft Abhängigkeiten mit einer klassischen Retro-Spinner-Animation (Robust & OS-Safe)."""
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
            # Linux Fix: Fallback-Optionen falls system-wide Paketmanager blockieren (--break-system-packages)
            cmd = [sys.executable, "-m", "pip", "install", *missing_packages]
            
            # Prüfen ob wir auf Linux sind, um ggf. restriktive Pip-Environments zu umgehen
            if os.name != 'nt':
                # Versucht die Standard-Installation, ignoriert PEP 668 Blockaden falls nötig
                cmd.append("--break-system-packages")
                
            subprocess.check_call(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            matrix_glitch_text("[OK] Alle Module erfolgreich kompiliert und injiziert.", delay=0.02)
        except subprocess.CalledProcessError:
            # Falls --break-system-packages auf alten Pip-Versionen fehlschlägt, normaler Retry
            try:
                cmd = [sys.executable, "-m", "pip", "install", *missing_packages]
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                matrix_glitch_text("[OK] Alle Module erfolgreich kompiliert.", delay=0.02)
            except subprocess.CalledProcessError as e:
                debug_error("Kritischer Fehler bei der Installation der Abhängigkeiten.", e)
                sys.exit(1)
    else:
        debug_info("Alle Core-Abhängigkeiten sind bereits aktiv.")


def run_countdown(seconds=3):
    """Führt einen animierten, coolen Countdown vor dem App-Start aus (Überlauf-sicher)."""
    print()
    matrix_glitch_text("[SYSTEM] Alle Checks bestanden. Bereite System-Start vor...", delay=0.02)
    
    # Optische Lade-Blöcke
    blocks = ["███", "██", "█"]
    
    for i in range(seconds, 0, -1):
        # Absicherung falls seconds > 3 übergeben wird (IndexError-Schutz)
        block_visual = blocks[(i - 1) % len(blocks)]
        sys.stdout.write(f"\r  >> Starte Server in {i} Sekunden... {block_visual:<3}")
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
        
    # 3-Sekunden Cooldown/Countdown abfeuern
    run_countdown(seconds=3)
    print("-" * 110)
    
    try:
        # Führt Streamlit nativ aus und reicht KeyboardInterrupts sauber durch
        subprocess.run([sys.executable, "-m", "streamlit", "run", target_app], check=True)
    except KeyboardInterrupt:
        print()
        debug_info("System vom Benutzer kontrolliert heruntergefahren.")
    except subprocess.CalledProcessError as e:
        debug_error("Streamlit-Instanz wurde unerwartet beendet.", e)


if __name__ == "__main__":
    # OS-Terminal säubern (Native Variante ohne Subprozess-Flackern auf Linux)
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.flush()

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

        # Sicherstellen, dass das Verzeichnis im Importpfad ist.
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
        # OS-Terminal säubern (Native Variante ohne Subprozess-Flackern auf Linux)
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

        if is_android_termux():
            print("[ANDROID] Termux-Umgebung erkannt. Starte terminalbasiertes Interface...")
            time.sleep(0.25)
            start_cli_app()
        else:
            # 1. Animierter Aufbau der originalen Pyramide
            animate_pyramid(PYRAMID_LINES, delay=0.02)

            # 2. Tech-Rahmen einblenden (Länge angepasst an Grafik)
            print("┌" + "─" * 108 + "┐")
            matrix_glitch_text("│                   >>>  K I - P Y R A M I D E N - P R O J E K T  2 0 2 6  <<<                    │", delay=0.01)
            print("└" + "─" * 108 + "┘")
            print()

            # 3. Validierung, Cooldown & Start
            check_and_install_dependencies()
            print("\n" + "=" * 110)

            start_streamlit_app()   