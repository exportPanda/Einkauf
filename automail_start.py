"""Startskript für Dauerbetrieb (systemd, Windows-Aufgabenplanung).

Funktioniert unabhängig vom Arbeitsverzeichnis: Ohne --config wird die config.toml
neben dieser Datei verwendet. Unter Windows ohne Konsolenfenster mit pythonw.exe starten.
"""

import sys
from pathlib import Path

from automail.__main__ import main

if __name__ == "__main__":
    argumente = sys.argv[1:]
    if not any(a == "--config" or a.startswith("--config=") for a in argumente):
        argumente = ["--config", str(Path(__file__).resolve().parent / "config.toml"), *argumente]
    sys.exit(main(argumente))
