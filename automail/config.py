"""Konfiguration laden. Alle Pfade werden hier zu pathlib.Path."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

MAIL_MODI = ("eml", "outlook")


class KonfigurationsFehler(Exception):
    pass


@dataclass(frozen=True)
class Pfade:
    eingang: Path
    kontakte: Path
    vorlage: Path
    erledigt: Path
    fehler: Path
    protokoll: Path
    ausgang_eml: Path | None


@dataclass(frozen=True)
class Mail:
    modus: str
    absender: str


@dataclass(frozen=True)
class Abfrage:
    intervall_sekunden: float
    stabil_sekunden: float


@dataclass(frozen=True)
class Ki:
    aktiv: bool
    modell: str
    url: str


@dataclass(frozen=True)
class Konfiguration:
    pfade: Pfade
    mail: Mail
    abfrage: Abfrage
    ki: Ki


def _pflicht(abschnitt: dict, name: str, schluessel: str):
    try:
        return abschnitt[schluessel]
    except KeyError:
        raise KonfigurationsFehler(f"Pflichtwert fehlt: [{name}] {schluessel}") from None


def _pfad(basis: Path, wert: str) -> Path:
    pfad = Path(wert)
    return pfad if pfad.is_absolute() else (basis / pfad).resolve()


def laden(datei: Path | str) -> Konfiguration:
    datei = Path(datei)
    if not datei.is_file():
        raise KonfigurationsFehler(f"Konfigurationsdatei nicht gefunden: {datei}")
    with datei.open("rb") as f:
        try:
            daten = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise KonfigurationsFehler(f"Konfigurationsdatei fehlerhaft: {e}") from None

    basis = datei.resolve().parent
    p = daten.get("pfade", {})
    m = daten.get("mail", {})
    a = daten.get("abfrage", {})
    k = daten.get("ki", {})

    modus = _pflicht(m, "mail", "modus")
    if modus not in MAIL_MODI:
        raise KonfigurationsFehler(
            f"Unbekannter mail.modus {modus!r}, erlaubt: {', '.join(MAIL_MODI)}"
        )
    ausgang_eml = p.get("ausgang_eml")
    if modus == "eml" and ausgang_eml is None:
        raise KonfigurationsFehler("Pflichtwert fehlt: [pfade] ausgang_eml (für mail.modus = 'eml')")

    return Konfiguration(
        pfade=Pfade(
            eingang=_pfad(basis, _pflicht(p, "pfade", "eingang")),
            kontakte=_pfad(basis, _pflicht(p, "pfade", "kontakte")),
            vorlage=_pfad(basis, _pflicht(p, "pfade", "vorlage")),
            erledigt=_pfad(basis, _pflicht(p, "pfade", "erledigt")),
            fehler=_pfad(basis, _pflicht(p, "pfade", "fehler")),
            protokoll=_pfad(basis, _pflicht(p, "pfade", "protokoll")),
            ausgang_eml=_pfad(basis, ausgang_eml) if ausgang_eml else None,
        ),
        mail=Mail(modus=modus, absender=_pflicht(m, "mail", "absender")),
        abfrage=Abfrage(
            intervall_sekunden=float(a.get("intervall_sekunden", 30)),
            stabil_sekunden=float(a.get("stabil_sekunden", 5)),
        ),
        ki=Ki(
            aktiv=bool(k.get("aktiv", False)),
            modell=k.get("modell", "llama3.2"),
            url=k.get("url", "http://localhost:11434"),
        ),
    )
