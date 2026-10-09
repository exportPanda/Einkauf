"""Protokoll in Datei (utf-8) und auf der Konsole."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def einrichten(datei: Path, stufe: int = logging.INFO) -> None:
    datei.parent.mkdir(parents=True, exist_ok=True)
    wurzel = logging.getLogger()
    wurzel.setLevel(stufe)
    wurzel.handlers.clear()
    handler_liste: list[logging.Handler] = [logging.FileHandler(datei, encoding="utf-8")]
    if sys.stderr is not None:  # unter pythonw.exe (Windows, ohne Konsole) gibt es kein stderr
        handler_liste.append(logging.StreamHandler())
    for handler in handler_liste:
        handler.setFormatter(logging.Formatter(FORMAT))
        wurzel.addHandler(handler)
