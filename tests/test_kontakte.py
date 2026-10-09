import logging
import unicodedata
from pathlib import Path

import pytest

from automail import kontakte
from automail.kontakte import Kontakt, KontaktFehler

BEISPIEL = Path(__file__).resolve().parent.parent / "beispieldaten" / "kontakte_beispiel.csv"
KOPF = "Lieferant;Ansprechpartner;E-Mail\r\n"


def tabelle(tmp_path: Path, zeilen: str, *, kopf: str = KOPF, kodierung: str = "utf-8-sig") -> Path:
    datei = tmp_path / "kontakte.csv"
    datei.write_bytes((kopf + zeilen).encode(kodierung))
    return datei


def test_beispieltabelle():
    liste = kontakte.laden(BEISPIEL)
    assert len(liste) == 3
    assert liste.finde("Müller GmbH") == Kontakt("Müller GmbH", "Jürgen Müller", "j.mueller@example.com")
    assert liste.finde("Schäfer & Söhne").email == "a.schaefer@example.com"


def test_bom_wird_entfernt(tmp_path):
    datei = tabelle(tmp_path, "Beispiel AG;Max Mustermann;max@example.com\r\n")
    assert datei.read_bytes().startswith(b"\xef\xbb\xbf")
    assert kontakte.laden(datei).finde("Beispiel AG") is not None


def test_ohne_bom(tmp_path):
    datei = tabelle(tmp_path, "Beispiel AG;Max;max@example.com\n", kodierung="utf-8")
    assert kontakte.laden(datei).finde("Beispiel AG") is not None


@pytest.mark.parametrize(
    "suche", ["Müller GmbH", "müller gmbh", "MÜLLER GMBH", "  Müller   GmbH ",
              unicodedata.normalize("NFD", "Müller GmbH")],
)
def test_suche_tolerant(tmp_path, suche):
    datei = tabelle(tmp_path, " Müller  GmbH ;Jürgen Müller; j.mueller@example.com \r\n")
    gefunden = kontakte.laden(datei).finde(suche)
    assert gefunden == Kontakt("Müller GmbH", "Jürgen Müller", "j.mueller@example.com")


def test_scharfes_s(tmp_path):
    datei = tabelle(tmp_path, "Großhandel Nord;Eva;eva@example.com\r\n")
    assert kontakte.laden(datei).finde("GROSSHANDEL NORD") is not None


def test_kein_treffer(tmp_path, caplog):
    datei = tabelle(tmp_path, "Beispiel AG;Max;max@example.com\r\n")
    with caplog.at_level(logging.WARNING):
        assert kontakte.laden(datei).finde("Unbekannt KG") is None
    assert "Kein Kontakt" in caplog.text


def test_dublette_mit_gleicher_adresse_ist_eindeutig(tmp_path):
    datei = tabelle(tmp_path, "Beispiel AG;Max;max@example.com\r\nBeispiel AG;Max M.;MAX@example.com\r\n")
    assert kontakte.laden(datei).finde("Beispiel AG").ansprechpartner == "Max"


def test_dublette_mit_verschiedenen_adressen_ist_mehrdeutig(tmp_path, caplog):
    datei = tabelle(tmp_path, "Beispiel AG;Max;max@example.com\r\nBeispiel AG;Erika;erika@example.com\r\n")
    with caplog.at_level(logging.WARNING):
        assert kontakte.laden(datei).finde("Beispiel AG") is None
    assert "Mehrere Kontakte" in caplog.text


def test_leere_und_fehlerhafte_zeilen_werden_uebersprungen(tmp_path, caplog):
    datei = tabelle(
        tmp_path,
        "Beispiel AG;Max;max@example.com\r\n"
        ";;\r\n"
        ";Ohne Lieferant;x@example.com\r\n"
        "Ohne Mail GmbH;Jemand;\r\n"
        "Kaputt KG;Jemand;keine-adresse\r\n",
    )
    with caplog.at_level(logging.WARNING):
        liste = kontakte.laden(datei)
    assert len(liste) == 1
    assert "Zeile 4" in caplog.text and "Lieferant fehlt" in caplog.text
    assert "Zeile 5" in caplog.text and "Zeile 6" in caplog.text


def test_spaltenkopf_mit_leerzeichen(tmp_path):
    datei = tabelle(tmp_path, "Beispiel AG;Max;max@example.com\r\n",
                    kopf=" Lieferant ; Ansprechpartner ; E-Mail \r\n")
    assert kontakte.laden(datei).finde("Beispiel AG") is not None


def test_falsches_trennzeichen(tmp_path):
    datei = tabelle(tmp_path, "Beispiel AG,Max,max@example.com\r\n", kopf="Lieferant,Ansprechpartner,E-Mail\r\n")
    with pytest.raises(KontaktFehler, match="Trennzeichen"):
        kontakte.laden(datei)


def test_fehlende_spalte(tmp_path):
    datei = tabelle(tmp_path, "Beispiel AG;max@example.com\r\n", kopf="Lieferant;E-Mail\r\n")
    with pytest.raises(KontaktFehler, match="Ansprechpartner"):
        kontakte.laden(datei)


def test_ansi_export_wird_erkannt(tmp_path):
    datei = tabelle(tmp_path, "Müller GmbH;Jürgen;j@example.com\r\n", kodierung="cp1252")
    with pytest.raises(KontaktFehler, match="CSV UTF-8"):
        kontakte.laden(datei)


def test_fehlende_datei(tmp_path):
    with pytest.raises(KontaktFehler, match="nicht gefunden"):
        kontakte.laden(tmp_path / "fehlt.csv")
