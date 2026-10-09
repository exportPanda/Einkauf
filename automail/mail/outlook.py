"""Windows: Entwurf in Outlook (klassisch) über pywin32 ablegen. Umsetzung in Phase 3.2."""

from __future__ import annotations

from pathlib import Path

from ..config import Konfiguration


def entwurf_ablegen(
    empfaenger: str, betreff: str, text: str, anhang: Path, *, cfg: Konfiguration
) -> None:
    raise NotImplementedError("Phase 3.2")
