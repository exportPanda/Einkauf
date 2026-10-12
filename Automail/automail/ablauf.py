"""Verarbeitung einer fertigen PDF: zerlegen, Kontakt suchen, Vorlage füllen, Entwurf ablegen."""

from __future__ import annotations

import enum
import logging
import shutil
from pathlib import Path
from typing import Callable

from . import dateiname
from .config import Konfiguration
from .kontakte import Kontaktliste
from .vorlage import Vorlage, fuellen

log = logging.getLogger(__name__)

# Signatur wie automail.mail.entwurf_ablegen, aber mit bereits gebundener Konfiguration
Ablage = Callable[[str, str, str, Path], None]


class Ergebnis(enum.Enum):
    ERLEDIGT = "erledigt"   # Entwurf erstellt, PDF liegt in "erledigt"
    FEHLER = "fehler"       # Problem mit der Datei selbst, PDF liegt in "fehler"
    SPAETER = "später"      # vorübergehendes Problem, PDF bleibt im Eingang


def verschiebe(quelle: Path, zielordner: Path) -> Path:
    """Verschiebt eine Datei, ohne vorhandene zu überschreiben ("name (2).pdf")."""
    zielordner.mkdir(parents=True, exist_ok=True)
    ziel = zielordner / quelle.name
    nr = 2
    while ziel.exists():
        ziel = zielordner / f"{quelle.stem} ({nr}){quelle.suffix}"
        nr += 1
    return Path(shutil.move(str(quelle), str(ziel)))


def verarbeite(
    pdf: Path, cfg: Konfiguration, kontaktliste: Kontaktliste, vorlage: Vorlage, ablegen: Ablage
) -> Ergebnis:
    info = dateiname.zerlege(pdf)
    kontakt = kontaktliste.finde(info.lieferant) if info else None
    if kontakt is None:
        ziel = verschiebe(pdf, cfg.pfade.fehler)
        log.warning("Nicht verarbeitet, verschoben nach %s", ziel)
        return Ergebnis.FEHLER

    entwurf = fuellen(vorlage, info, kontakt)

    # Erst verschieben, dann ablegen: So entsteht kein doppelter Entwurf, falls das
    # Verschieben scheitert. Scheitert das Ablegen, geht die PDF zurück in den Eingang.
    erledigt = verschiebe(pdf, cfg.pfade.erledigt)
    try:
        ablegen(entwurf.empfaenger, entwurf.betreff, entwurf.text, erledigt)
    except Exception:
        log.exception("Entwurf für %s konnte nicht abgelegt werden, neuer Versuch folgt", pdf.name)
        try:
            verschiebe(erledigt, pdf.parent)
        except OSError:
            log.exception("PDF konnte nicht zurück in den Eingang verschoben werden: %s", erledigt)
        return Ergebnis.SPAETER

    log.info("Entwurf erstellt: %s → %s (%s)", pdf.name, entwurf.empfaenger, entwurf.betreff)
    return Ergebnis.ERLEDIGT
