"""Einheitliche Schnittstelle für die E-Mail-Ablage.

Welche Umsetzung aktiv ist, steht in der Konfiguration unter [mail] modus.
"""

from __future__ import annotations

from pathlib import Path

from ..config import Konfiguration


def entwurf_ablegen(
    empfaenger: str, betreff: str, text: str, anhang: Path, *, cfg: Konfiguration
) -> None:
    if cfg.mail.modus == "eml":
        from . import eml
        eml.entwurf_ablegen(empfaenger, betreff, text, anhang, cfg=cfg)
    elif cfg.mail.modus == "outlook":
        # Erst hier importieren, damit Ubuntu ohne pywin32 läuft.
        from . import outlook
        outlook.entwurf_ablegen(empfaenger, betreff, text, anhang, cfg=cfg)
    else:
        raise ValueError(f"Unbekannter mail.modus: {cfg.mail.modus!r}")
