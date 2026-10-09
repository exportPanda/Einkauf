"""Outlook-Anbindung mit nachgebautem pywin32 testen. Der echte Test folgt auf Windows."""

import sys
import types

import pytest

from automail.mail import entwurf_ablegen, outlook
from automail.mail.outlook import OutlookFehler


class FakeItem:
    def __init__(self):
        self.anhaenge = []
        self.gespeichert = False
        self.gesendet = False
        self.Attachments = types.SimpleNamespace(Add=self.anhaenge.append)

    def Save(self):
        self.gespeichert = True

    def Send(self):
        self.gesendet = True


class FakeOutlook:
    def __init__(self):
        self.items = []

    def CreateItem(self, typ):
        assert typ == 0
        self.items.append(FakeItem())
        return self.items[-1]


@pytest.fixture
def fake_pywin32(monkeypatch):
    app = FakeOutlook()
    status = {"dispatch_fehler": None}

    def dispatch(name):
        assert name == "Outlook.Application"
        if status["dispatch_fehler"]:
            raise status["dispatch_fehler"]
        return app

    win32com = types.ModuleType("win32com")
    client = types.ModuleType("win32com.client")
    client.Dispatch = dispatch
    win32com.client = client
    pythoncom = types.ModuleType("pythoncom")
    pythoncom.CoInitialize = lambda: None
    monkeypatch.setitem(sys.modules, "win32com", win32com)
    monkeypatch.setitem(sys.modules, "win32com.client", client)
    monkeypatch.setitem(sys.modules, "pythoncom", pythoncom)
    return app, status


@pytest.fixture
def outlook_umgebung(umgebung):
    umgebung.konfigdatei.write_text(
        umgebung.konfigdatei.read_text(encoding="utf-8").replace('modus = "eml"', 'modus = "outlook"'),
        encoding="utf-8",
    )
    return umgebung


def test_entwurf_wird_gespeichert_nicht_gesendet(fake_pywin32, outlook_umgebung):
    app, _ = fake_pywin32
    pdf = outlook_umgebung.ordner / "Müller GmbH_4711_2026-10-09.pdf"
    pdf.write_bytes(b"%PDF")
    entwurf_ablegen("j.mueller@example.com", "Bestellung 4711", "Zeile 1\nZeile 2\n", pdf,
                    cfg=outlook_umgebung.cfg)
    [item] = app.items
    assert item.To == "j.mueller@example.com"
    assert item.Subject == "Bestellung 4711"
    assert item.Body == "Zeile 1\r\nZeile 2\r\n"
    assert item.anhaenge == [str(pdf.resolve())]
    assert item.gespeichert and not item.gesendet


def test_ablauf_mit_outlook(fake_pywin32, outlook_umgebung, uhr):
    from automail.watcher import lauf

    app, _ = fake_pywin32
    outlook_umgebung.pdf("Müller GmbH_4711_2026-10-09.pdf")
    lauf(outlook_umgebung.cfg, einmal=True, schlafen=uhr.schlafen, uhr=uhr)
    assert outlook_umgebung.inhalt("erledigt") == ["Müller GmbH_4711_2026-10-09.pdf"]
    erwartet = outlook_umgebung.ordner / "erledigt" / "Müller GmbH_4711_2026-10-09.pdf"
    assert app.items[0].anhaenge == [str(erwartet.resolve())]


def test_outlook_nicht_erreichbar_pdf_bleibt_im_eingang(fake_pywin32, outlook_umgebung, uhr):
    from automail.watcher import lauf

    _, status = fake_pywin32
    status["dispatch_fehler"] = OSError("Klasse nicht registriert")
    outlook_umgebung.pdf("Müller GmbH_4711_2026-10-09.pdf")
    lauf(outlook_umgebung.cfg, einmal=True, schlafen=uhr.schlafen, uhr=uhr)
    assert outlook_umgebung.inhalt("eingang") == ["Müller GmbH_4711_2026-10-09.pdf"]


def test_fehlermeldung_nennt_klassisches_outlook(fake_pywin32, tmp_path):
    _, status = fake_pywin32
    status["dispatch_fehler"] = OSError("Klasse nicht registriert")
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    with pytest.raises(OutlookFehler, match="klassische Outlook"):
        outlook.entwurf_anlegen("x@example.com", "B", "T", pdf)


def test_fehlender_anhang(fake_pywin32, tmp_path):
    with pytest.raises(OutlookFehler, match="Anhang nicht gefunden"):
        outlook.entwurf_anlegen("x@example.com", "B", "T", tmp_path / "fehlt.pdf")


@pytest.mark.skipif(sys.platform == "win32", reason="auf Windows ist pywin32 installiert")
def test_ohne_pywin32_klare_meldung(tmp_path):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    with pytest.raises(OutlookFehler, match="pywin32 fehlt"):
        outlook.entwurf_anlegen("x@example.com", "B", "T", pdf)


def test_selbsttest(fake_pywin32):
    app, _ = fake_pywin32
    outlook.selbsttest("ich@example.com")
    [item] = app.items
    assert "äöüß" in item.Subject and item.gespeichert
