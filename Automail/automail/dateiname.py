"""Dateinamen zerlegen.

Schema: Lieferant_Bestellnr_Datum.pdf
  - Lieferant: beliebiger Text, darf Leerzeichen, Umlaute und auch "_" enthalten
  - Bestellnr: Buchstaben, Ziffern und Bindestriche, z. B. 4500123456 oder B-2026-017
  - Datum:     JJJJ-MM-TT oder TT.MM.JJJJ
Getrennt wird von rechts, deshalb darf nur der Lieferant Unterstriche enthalten.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

log = logging.getLogger(__name__)

BESTELLNR = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
DATUMSFORMATE = ("%Y-%m-%d", "%d.%m.%Y")


@dataclass(frozen=True)
class Dateiinfo:
    lieferant: str
    bestellnr: str
    datum: date


def _datum(text: str) -> date | None:
    for fmt in DATUMSFORMATE:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def zerlege(dateiname: str | Path) -> Dateiinfo | None:
    """Zerlegt einen Dateinamen. Ungültige Namen ergeben None und einen Protokolleintrag."""
    pfad = Path(dateiname)
    # NFC, damit "ü" aus Windows/macOS-Dateisystemen gleich aussieht wie in der Kontakttabelle.
    name = unicodedata.normalize("NFC", pfad.name)

    def ungueltig(grund: str) -> None:
        log.warning("Dateiname ungültig (%s): %s", grund, name)

    stamm, punkt, endung = name.rpartition(".")
    if not punkt or endung.lower() != "pdf":
        return ungueltig("keine PDF-Datei")

    teile = stamm.rsplit("_", 2)
    if len(teile) != 3:
        return ungueltig("erwartet Lieferant_Bestellnr_Datum")
    lieferant, bestellnr, datumstext = (t.strip() for t in teile)

    if not lieferant:
        return ungueltig("Lieferant fehlt")
    if not BESTELLNR.fullmatch(bestellnr):
        return ungueltig(f"Bestellnummer {bestellnr!r}")
    datum = _datum(datumstext)
    if datum is None:
        return ungueltig(f"Datum {datumstext!r}")

    return Dateiinfo(lieferant=" ".join(lieferant.split()), bestellnr=bestellnr, datum=datum)
