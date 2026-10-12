from dataclasses import dataclass
from pathlib import Path

import pytest

from automail import config

KONFIG = """
[pfade]
eingang = "eingang"
kontakte = "kontakte.csv"
vorlage = "vorlage.txt"
erledigt = "erledigt"
fehler = "fehler"
protokoll = "automail.log"
ausgang_eml = "ausgang"

[mail]
modus = "eml"
absender = "einkauf@example.com"

[abfrage]
intervall_sekunden = 30
stabil_sekunden = 5
"""


@dataclass
class Umgebung:
    ordner: Path
    konfigdatei: Path

    @property
    def cfg(self) -> config.Konfiguration:
        return config.laden(self.konfigdatei)

    def pdf(self, name: str, inhalt: bytes = b"%PDF-1.4 test") -> Path:
        pfad = self.ordner / "eingang" / name
        pfad.write_bytes(inhalt)
        return pfad

    def inhalt(self, unterordner: str) -> list[str]:
        ordner = self.ordner / unterordner
        return sorted(p.name for p in ordner.iterdir()) if ordner.exists() else []


@pytest.fixture
def umgebung(tmp_path) -> Umgebung:
    """Vollständige Testumgebung mit erfundenen Daten in einem temporären Ordner."""
    (tmp_path / "eingang").mkdir()
    (tmp_path / "kontakte.csv").write_text(
        "Lieferant;Ansprechpartner;E-Mail\nMüller GmbH;Jürgen Müller;j.mueller@example.com\n",
        encoding="utf-8-sig",
    )
    (tmp_path / "vorlage.txt").write_text(
        "Betreff: Bestellung $bestellnr\n\n$anrede,\nanbei Bestellung $bestellnr.\n", encoding="utf-8"
    )
    konfigdatei = tmp_path / "config.toml"
    konfigdatei.write_text(KONFIG, encoding="utf-8")
    return Umgebung(tmp_path, konfigdatei)


class Uhr:
    """Gesteuerte Zeit für Tests: schlafen() stellt die Uhr vor statt zu warten."""

    def __init__(self):
        self.jetzt = 1000.0

    def __call__(self) -> float:
        return self.jetzt

    def schlafen(self, sekunden: float) -> None:
        self.jetzt += sekunden


@pytest.fixture
def uhr() -> Uhr:
    return Uhr()
