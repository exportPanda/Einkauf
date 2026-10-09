"""Textvorlage laden und füllen.

Aufbau der Vorlagendatei (utf-8):
    Betreff: Bestellung $bestellnr vom $datum
    <Leerzeile>
    $anrede,
    ...

Platzhalter: siehe PLATZHALTER. Ein echtes Dollarzeichen schreibt man als $$.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from string import Template

from .dateiname import Dateiinfo
from .kontakte import Kontakt

PLATZHALTER = {
    "lieferant": "Lieferant aus dem Dateinamen",
    "bestellnr": "Bestellnummer aus dem Dateinamen",
    "datum": "Datum aus dem Dateinamen als TT.MM.JJJJ",
    "ansprechpartner": "Ansprechpartner aus der Kontakttabelle (kann leer sein)",
    "anrede": "'Guten Tag <Ansprechpartner>' oder 'Sehr geehrte Damen und Herren'",
    "email": "E-Mail-Adresse aus der Kontakttabelle",
}
BETREFF_PRAEFIX = "Betreff:"


class VorlagenFehler(Exception):
    pass


@dataclass(frozen=True)
class Vorlage:
    betreff: Template
    text: Template


@dataclass(frozen=True)
class Entwurf:
    empfaenger: str
    betreff: str
    text: str


def laden(pfad: Path) -> Vorlage:
    """Lädt die Vorlage und prüft sie sofort, damit Fehler beim Start auffallen."""
    try:
        inhalt = pfad.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise VorlagenFehler(f"Vorlage nicht gefunden: {pfad}") from None
    except UnicodeDecodeError:
        raise VorlagenFehler(f"Vorlage ist nicht UTF-8: {pfad}") from None

    erste, _, rest = inhalt.replace("\r\n", "\n").partition("\n")
    if not erste.startswith(BETREFF_PRAEFIX):
        raise VorlagenFehler(f"Erste Zeile der Vorlage muss mit '{BETREFF_PRAEFIX}' beginnen: {pfad}")
    betreff = erste.removeprefix(BETREFF_PRAEFIX).strip()
    text = rest.strip("\n") + "\n"
    if not betreff:
        raise VorlagenFehler(f"Betreff der Vorlage ist leer: {pfad}")

    vorlage = Vorlage(Template(betreff), Template(text))
    for teil, template in (("Betreff", vorlage.betreff), ("Text", vorlage.text)):
        if not template.is_valid():
            raise VorlagenFehler(f"Ungültiges '$' im {teil} der Vorlage (echtes Dollarzeichen als $$ schreiben)")
        unbekannt = sorted(set(template.get_identifiers()) - PLATZHALTER.keys())
        if unbekannt:
            raise VorlagenFehler(
                f"Unbekannte Platzhalter im {teil} der Vorlage: {', '.join('$' + u for u in unbekannt)} "
                f"(erlaubt: {', '.join('$' + p for p in PLATZHALTER)})"
            )
    return vorlage


def fuellen(vorlage: Vorlage, info: Dateiinfo, kontakt: Kontakt) -> Entwurf:
    werte = {
        "lieferant": info.lieferant,
        "bestellnr": info.bestellnr,
        "datum": info.datum.strftime("%d.%m.%Y"),
        "ansprechpartner": kontakt.ansprechpartner,
        "anrede": (f"Guten Tag {kontakt.ansprechpartner}" if kontakt.ansprechpartner
                   else "Sehr geehrte Damen und Herren"),
        "email": kontakt.email,
    }
    return Entwurf(
        empfaenger=kontakt.email,
        betreff=vorlage.betreff.substitute(werte),
        text=vorlage.text.substitute(werte),
    )
