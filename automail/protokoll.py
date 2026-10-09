"""Protokoll in Datei (utf-8) und auf der Konsole."""

from __future__ import annotations

import logging
from pathlib import Path

FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def einrichten(datei: Path, stufe: int = logging.INFO) -> None:
    datei.parent.mkdir(parents=True, exist_ok=True)
    wurzel = logging.getLogger()
    wurzel.setLevel(stufe)
    wurzel.handlers.clear()
    for handler in (logging.FileHandler(datei, encoding="utf-8"), logging.StreamHandler()):
        handler.setFormatter(logging.Formatter(FORMAT))
        wurzel.addHandler(handler)
