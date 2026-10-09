import sys
from email import policy
from email.parser import BytesParser
from pathlib import Path

import pytest

from automail.mail import entwurf_ablegen
from automail.watcher import lauf

PDF = b"%PDF-1.4\n\xe2\xe3\xcf\xd3 binaer\n%%EOF\n"


def lese(pfad: Path):
    with pfad.open("rb") as f:
        return BytesParser(policy=policy.default).parse(f)


def ablegen_test(umgebung, text="Guten Tag Jürgen Müller,\nanbei die Bestellung.\n"):
    pdf = umgebung.ordner / "Müller GmbH_4711_2026-10-09.pdf"
    pdf.write_bytes(PDF)
    entwurf_ablegen("j.mueller@example.com", "Bestellung 4711 – Müller GmbH", text, pdf, cfg=umgebung.cfg)
    [eml] = (umgebung.ordner / "ausgang").glob("*.eml")
    return eml


def test_eml_inhalt(umgebung):
    eml = ablegen_test(umgebung)
    assert eml.name.endswith("_Müller GmbH_4711_2026-10-09.eml")
    msg = lese(eml)
    assert msg["From"] == "einkauf@example.com"
    assert msg["To"] == "j.mueller@example.com"
    assert msg["Subject"] == "Bestellung 4711 – Müller GmbH"
    assert msg["X-Unsent"] == "1"
    assert msg.get_body(("plain",)).get_content() == "Guten Tag Jürgen Müller,\nanbei die Bestellung.\n"
    [anhang] = msg.iter_attachments()
    assert anhang.get_content_type() == "application/pdf"
    assert anhang.get_filename() == "Müller GmbH_4711_2026-10-09.pdf"
    assert anhang.get_content() == PDF


def test_eml_ist_reines_ascii(umgebung):
    # Umlaute müssen kodiert sein, sonst zeigen manche Programme Zeichensalat.
    ablegen_test(umgebung).read_bytes().decode("ascii")


def test_keine_hilfsdatei_uebrig(umgebung):
    ablegen_test(umgebung)
    assert [p.suffix for p in (umgebung.ordner / "ausgang").iterdir()] == [".eml"]


def test_gleicher_name_ueberschreibt_nicht(umgebung, monkeypatch):
    import automail.mail.eml as eml_modul

    class FesteZeit:
        @staticmethod
        def now():
            from datetime import datetime
            return datetime(2026, 10, 9, 12, 0, 0)

    monkeypatch.setattr(eml_modul, "datetime", FesteZeit)
    pdf = umgebung.ordner / "a.pdf"
    pdf.write_bytes(PDF)
    for _ in range(2):
        entwurf_ablegen("x@example.com", "B", "T", pdf, cfg=umgebung.cfg)
    namen = sorted(p.name for p in (umgebung.ordner / "ausgang").iterdir())
    assert namen == ["2026-10-09_120000_a (2).eml", "2026-10-09_120000_a.eml"]


def test_ablauf_von_anfang_bis_ende(umgebung, uhr):
    umgebung.pdf("Müller GmbH_4711_2026-10-09.pdf", PDF)
    lauf(umgebung.cfg, einmal=True, schlafen=uhr.schlafen, uhr=uhr)
    assert umgebung.inhalt("erledigt") == ["Müller GmbH_4711_2026-10-09.pdf"]
    [eml] = (umgebung.ordner / "ausgang").glob("*.eml")
    msg = lese(eml)
    assert msg["Subject"] == "Bestellung 4711"
    assert next(msg.iter_attachments()).get_content() == PDF


@pytest.mark.skipif(sys.platform == "win32", reason="prüft das Verhalten ohne pywin32")
def test_eml_modus_importiert_kein_pywin32(umgebung):
    ablegen_test(umgebung)
    assert "win32com" not in sys.modules
