"""Kontakttabelle lesen und durchsuchen.

Die Tabelle ist ein Excel-Export im Format "CSV UTF-8 (durch Trennzeichen getrennt)":
Kodierung utf-8-sig, Trennzeichen Semikolon, Spalten Lieferant;Ansprechpartner;E-Mail.
"""

from __future__ import annotations

import csv
import logging
import unicodedata
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

SPALTE_LIEFERANT = "Lieferant"
SPALTE_ANSPRECHPARTNER = "Ansprechpartner"
SPALTE_EMAIL = "E-Mail"
PFLICHTSPALTEN = (SPALTE_LIEFERANT, SPALTE_ANSPRECHPARTNER, SPALTE_EMAIL)


class KontaktFehler(Exception):
    pass


@dataclass(frozen=True)
class Kontakt:
    lieferant: str
    ansprechpartner: str
    email: str


def schluessel(text: str) -> str:
    """Vergleichsform: NFC, ohne Rand- und Mehrfachleerzeichen, ohne Groß-/Kleinschreibung."""
    return " ".join(unicodedata.normalize("NFC", text).split()).casefold()


class Kontaktliste:
    def __init__(self, kontakte: list[Kontakt]):
        self._nach_lieferant: dict[str, list[Kontakt]] = {}
        for k in kontakte:
            self._nach_lieferant.setdefault(schluessel(k.lieferant), []).append(k)

    def __len__(self) -> int:
        return sum(len(v) for v in self._nach_lieferant.values())

    def finde(self, lieferant: str) -> Kontakt | None:
        """Genau ein Treffer ergibt den Kontakt; kein oder mehrdeutiger Treffer ergibt None."""
        treffer = self._nach_lieferant.get(schluessel(lieferant), [])
        if not treffer:
            log.warning("Kein Kontakt für Lieferant %r", lieferant)
            return None
        if len({schluessel(k.email) for k in treffer}) > 1:
            log.warning(
                "Mehrere Kontakte für Lieferant %r: %s",
                lieferant, ", ".join(k.email for k in treffer),
            )
            return None
        return treffer[0]


def laden(pfad: Path) -> Kontaktliste:
    try:
        with pfad.open(encoding="utf-8-sig", newline="") as f:
            leser = csv.DictReader(f, delimiter=";")
            spalten = [s.strip() for s in (leser.fieldnames or [])]
            fehlend = [s for s in PFLICHTSPALTEN if s not in spalten]
            if fehlend:
                raise KontaktFehler(
                    f"Spalten fehlen in {pfad}: {', '.join(fehlend)} "
                    f"(gefunden: {', '.join(spalten) or 'keine'}; Trennzeichen muss ';' sein)"
                )
            leser.fieldnames = spalten
            kontakte = []
            for zeile in leser:
                kontakt = _kontakt(zeile, leser.line_num)
                if kontakt:
                    kontakte.append(kontakt)
    except FileNotFoundError:
        raise KontaktFehler(f"Kontakttabelle nicht gefunden: {pfad}") from None
    except UnicodeDecodeError:
        raise KontaktFehler(
            f"Kontakttabelle ist nicht UTF-8: {pfad}. "
            "In Excel als 'CSV UTF-8 (durch Trennzeichen getrennt)' speichern."
        ) from None

    log.info("%d Kontakte geladen aus %s", len(kontakte), pfad)
    return Kontaktliste(kontakte)


def _kontakt(zeile: dict, zeilennr: int) -> Kontakt | None:
    def wert(spalte: str) -> str:
        return " ".join(unicodedata.normalize("NFC", zeile.get(spalte) or "").split())

    lieferant, ansprechpartner, email = (wert(s) for s in PFLICHTSPALTEN)
    if not any((lieferant, ansprechpartner, email)):
        return None  # Leerzeile, z. B. am Ende eines Excel-Exports
    if not lieferant:
        log.warning("Kontakttabelle Zeile %d übersprungen: Lieferant fehlt", zeilennr)
        return None
    if "@" not in email or " " in email:
        log.warning("Kontakttabelle Zeile %d übersprungen: E-Mail %r ungültig", zeilennr, email)
        return None
    return Kontakt(lieferant, ansprechpartner, email)
