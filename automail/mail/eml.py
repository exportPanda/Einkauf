"""Ubuntu: Entwurf als .eml-Datei ablegen (in Thunderbird zu öffnen). Umsetzung in Phase 3.1."""

from __future__ import annotations

from pathlib import Path

from ..config import Konfiguration


def entwurf_ablegen(
    empfaenger: str, betreff: str, text: str, anhang: Path, *, cfg: Konfiguration
) -> None:
    raise NotImplementedError("Phase 3.1")
