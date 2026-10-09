import logging
import unicodedata
from datetime import date
from pathlib import Path

import pytest

from automail.dateiname import Dateiinfo, zerlege


@pytest.mark.parametrize(
    "name, erwartet",
    [
        ("Beispiel AG_4500123456_2026-10-09.pdf",
         Dateiinfo("Beispiel AG", "4500123456", date(2026, 10, 9))),
        ("Müller GmbH_4500000017_09.10.2026.pdf",
         Dateiinfo("Müller GmbH", "4500000017", date(2026, 10, 9))),
        ("Schäfer & Söhne_B-2026-017_2026-01-31.pdf",
         Dateiinfo("Schäfer & Söhne", "B-2026-017", date(2026, 1, 31))),
        # Unterstrich im Lieferantennamen ist erlaubt, getrennt wird von rechts
        ("Meier_Technik GmbH_123_2026-02-28.pdf",
         Dateiinfo("Meier_Technik GmbH", "123", date(2026, 2, 28))),
        # Großgeschriebene Endung, Leerzeichen um die Teile, doppelte Leerzeichen im Namen
        (" Beispiel  AG _ 4711 _ 2026-10-09 .PDF",
         Dateiinfo("Beispiel AG", "4711", date(2026, 10, 9))),
    ],
)
def test_gueltige_namen(name, erwartet):
    assert zerlege(name) == erwartet


def test_pfad_wird_auf_dateinamen_reduziert():
    pfad = Path("/eingang/unterordner_mit_strich/Beispiel AG_4711_2026-10-09.pdf")
    assert zerlege(pfad).lieferant == "Beispiel AG"


def test_umlaute_werden_vereinheitlicht():
    name_nfd = unicodedata.normalize("NFD", "Müller GmbH_4711_2026-10-09.pdf")
    assert zerlege(name_nfd).lieferant == "Müller GmbH"


@pytest.mark.parametrize(
    "name, grund",
    [
        ("Beispiel AG_4711_2026-10-09.docx", "keine PDF-Datei"),
        ("Beispiel AG_4711_2026-10-09", "keine PDF-Datei"),
        ("Beispiel AG_2026-10-09.pdf", "Lieferant_Bestellnr_Datum"),
        ("Beispiel AG.pdf", "Lieferant_Bestellnr_Datum"),
        ("_4711_2026-10-09.pdf", "Lieferant fehlt"),
        ("Beispiel AG__2026-10-09.pdf", "Bestellnummer"),
        ("Beispiel AG_47 11_2026-10-09.pdf", "Bestellnummer"),
        ("Beispiel AG_-4711_2026-10-09.pdf", "Bestellnummer"),
        ("Beispiel AG_4711_2026-02-30.pdf", "Datum"),
        ("Beispiel AG_4711_09-10-2026.pdf", "Datum"),
        ("Beispiel AG_4711_heute.pdf", "Datum"),
    ],
)
def test_ungueltige_namen(name, grund, caplog):
    with caplog.at_level(logging.WARNING):
        assert zerlege(name) is None
    assert grund in caplog.text
