from datetime import date
from pathlib import Path

import pytest

from automail import vorlage
from automail.dateiname import Dateiinfo
from automail.kontakte import Kontakt
from automail.vorlage import Entwurf, VorlagenFehler

BEISPIEL = Path(__file__).resolve().parent.parent / "beispieldaten" / "vorlage.txt"
INFO = Dateiinfo("Müller GmbH", "4500000017", date(2026, 10, 9))
KONTAKT = Kontakt("Müller GmbH", "Jürgen Müller", "j.mueller@example.com")


def datei(tmp_path: Path, inhalt: str, kodierung: str = "utf-8") -> Path:
    pfad = tmp_path / "vorlage.txt"
    pfad.write_bytes(inhalt.encode(kodierung))
    return pfad


def test_beispielvorlage():
    entwurf = vorlage.fuellen(vorlage.laden(BEISPIEL), INFO, KONTAKT)
    assert entwurf.empfaenger == "j.mueller@example.com"
    assert entwurf.betreff == "Bestellung 4500000017 vom 09.10.2026 – Müller GmbH"
    assert entwurf.text.startswith("Guten Tag Jürgen Müller,\n\nanbei erhalten Sie unsere Bestellung 4500000017 vom 09.10.2026.")
    assert entwurf.text.endswith("Mit freundlichen Grüßen\nEinkauf\n")


def test_alle_platzhalter(tmp_path):
    inhalt = "Betreff: $bestellnr\n\n" + " ".join(f"[{p}=${{{p}}}]" for p in vorlage.PLATZHALTER) + "\n"
    entwurf = vorlage.fuellen(vorlage.laden(datei(tmp_path, inhalt)), INFO, KONTAKT)
    assert entwurf == Entwurf(
        "j.mueller@example.com",
        "4500000017",
        "[lieferant=Müller GmbH] [bestellnr=4500000017] [datum=09.10.2026] "
        "[ansprechpartner=Jürgen Müller] [anrede=Guten Tag Jürgen Müller] "
        "[email=j.mueller@example.com]\n",
    )


def test_anrede_ohne_ansprechpartner(tmp_path):
    ohne = Kontakt("Müller GmbH", "", "info@example.com")
    entwurf = vorlage.fuellen(vorlage.laden(datei(tmp_path, "Betreff: x\n\n$anrede,\n")), INFO, ohne)
    assert entwurf.text == "Sehr geehrte Damen und Herren,\n"


def test_windows_zeilenenden_und_bom(tmp_path):
    pfad = datei(tmp_path, "Betreff: Bestellung $bestellnr\r\n\r\nZeile 1\r\nZeile 2\r\n\r\n", "utf-8-sig")
    entwurf = vorlage.fuellen(vorlage.laden(pfad), INFO, KONTAKT)
    assert entwurf.betreff == "Bestellung 4500000017"
    assert entwurf.text == "Zeile 1\nZeile 2\n"


def test_dollarzeichen(tmp_path):
    entwurf = vorlage.fuellen(vorlage.laden(datei(tmp_path, "Betreff: x\n\nPreis in $$\n")), INFO, KONTAKT)
    assert entwurf.text == "Preis in $\n"


@pytest.mark.parametrize(
    "inhalt, meldung",
    [
        ("Hallo $anrede\n", "Betreff:"),
        ("Betreff:   \n\nText\n", "leer"),
        ("Betreff: $bestelnummer\n\nText\n", r"Unbekannte Platzhalter im Betreff.*\$bestelnummer"),
        ("Betreff: x\n\n$anrede, $kunde $preis\n", r"\$kunde, \$preis"),
        ("Betreff: x\n\nKosten 5 $ netto\n", r"\$\$"),
    ],
)
def test_fehlerhafte_vorlage(tmp_path, inhalt, meldung):
    with pytest.raises(VorlagenFehler, match=meldung):
        vorlage.laden(datei(tmp_path, inhalt))


def test_kein_utf8(tmp_path):
    with pytest.raises(VorlagenFehler, match="UTF-8"):
        vorlage.laden(datei(tmp_path, "Betreff: Grüße\n\nText\n", "cp1252"))


def test_fehlende_datei(tmp_path):
    with pytest.raises(VorlagenFehler, match="nicht gefunden"):
        vorlage.laden(tmp_path / "fehlt.txt")
