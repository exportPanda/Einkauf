import logging
import os

from automail import watcher
from automail.watcher import Stabilitaetspruefer, durchlauf, lauf, pdfs_im_eingang


class Ablage:
    def __init__(self):
        self.aufrufe = []

    def __call__(self, empfaenger, betreff, text, anhang):
        self.aufrufe.append((empfaenger, betreff, text, anhang))


def test_pdfs_im_eingang(umgebung):
    for name in ("b.pdf", "a.PDF", "~$sperre.pdf", ".versteckt.pdf", "notiz.txt", "Thumbs.db"):
        umgebung.pdf(name)
    (umgebung.ordner / "eingang" / "ordner.pdf").mkdir()
    assert [p.name for p in pdfs_im_eingang(umgebung.ordner / "eingang")] == ["a.PDF", "b.pdf"]


def test_datei_erst_nach_stabilzeit_fertig(umgebung, uhr):
    pdf = umgebung.pdf("x.pdf")
    pruefer = Stabilitaetspruefer(5, uhr)
    assert pruefer.fertige([pdf]) == []      # zum ersten Mal gesehen
    uhr.schlafen(4)
    assert pruefer.fertige([pdf]) == []      # noch nicht lange genug gleich
    uhr.schlafen(1)
    assert pruefer.fertige([pdf]) == [pdf]


def test_wachsende_datei_ist_nicht_fertig(umgebung, uhr):
    pdf = umgebung.pdf("x.pdf", b"%PDF")
    pruefer = Stabilitaetspruefer(5, uhr)
    pruefer.fertige([pdf])
    uhr.schlafen(10)
    with pdf.open("ab") as f:
        f.write(b" noch mehr")
    assert pruefer.fertige([pdf]) == []      # Größe geändert: Zeit beginnt neu
    uhr.schlafen(5)
    assert pruefer.fertige([pdf]) == [pdf]


def test_geaenderte_zeit_bei_gleicher_groesse(umgebung, uhr):
    pdf = umgebung.pdf("x.pdf")
    pruefer = Stabilitaetspruefer(5, uhr)
    pruefer.fertige([pdf])
    uhr.schlafen(10)
    st = pdf.stat()
    os.utime(pdf, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))
    assert pruefer.fertige([pdf]) == []


def test_leere_datei_ist_nie_fertig(umgebung, uhr):
    pdf = umgebung.pdf("x.pdf", b"")
    pruefer = Stabilitaetspruefer(5, uhr)
    pruefer.fertige([pdf])
    uhr.schlafen(60)
    assert pruefer.fertige([pdf]) == []


def test_verschwundene_datei_wird_vergessen(umgebung, uhr):
    pdf = umgebung.pdf("x.pdf")
    pruefer = Stabilitaetspruefer(5, uhr)
    pruefer.fertige([pdf])
    pdf.unlink()
    assert pruefer.fertige([pdf]) == []
    umgebung.pdf("x.pdf")                    # neu angelegt: Zeit beginnt neu
    assert pruefer.fertige([pdf]) == []


def test_durchlauf_komplett(umgebung, uhr):
    umgebung.pdf("Müller GmbH_4711_2026-10-09.pdf")
    umgebung.pdf("Unbekannt KG_4712_2026-10-09.pdf")
    umgebung.pdf("falscher name.pdf")
    ablage = Ablage()
    lauf(umgebung.cfg, einmal=True, ablegen=ablage, schlafen=uhr.schlafen, uhr=uhr)

    assert umgebung.inhalt("eingang") == []
    assert umgebung.inhalt("erledigt") == ["Müller GmbH_4711_2026-10-09.pdf"]
    assert umgebung.inhalt("fehler") == ["Unbekannt KG_4712_2026-10-09.pdf", "falscher name.pdf"]
    [(empfaenger, betreff, text, anhang)] = ablage.aufrufe
    assert empfaenger == "j.mueller@example.com"
    assert betreff == "Bestellung 4711"
    assert text == "Guten Tag Jürgen Müller,\nanbei Bestellung 4711.\n"
    assert anhang == umgebung.ordner / "erledigt" / "Müller GmbH_4711_2026-10-09.pdf"


def test_ohne_kontakttabelle_bleiben_pdfs_im_eingang(umgebung, uhr, caplog):
    umgebung.pdf("Müller GmbH_4711_2026-10-09.pdf")
    (umgebung.ordner / "kontakte.csv").unlink()
    pruefer = Stabilitaetspruefer(5, uhr)
    durchlauf(umgebung.cfg, pruefer, Ablage())
    uhr.schlafen(5)
    with caplog.at_level(logging.ERROR):
        assert durchlauf(umgebung.cfg, pruefer, Ablage()) == 1
    assert "nicht gefunden" in caplog.text
    assert umgebung.inhalt("eingang") == ["Müller GmbH_4711_2026-10-09.pdf"]


def test_eingang_nicht_erreichbar(umgebung, uhr, caplog):
    (umgebung.ordner / "eingang").rmdir()
    with caplog.at_level(logging.WARNING):
        assert durchlauf(umgebung.cfg, Stabilitaetspruefer(5, uhr), Ablage()) == 0
    assert "Eingang nicht erreichbar" in caplog.text


def test_dauerschleife_ueberlebt_fehler(umgebung, uhr, monkeypatch):
    aufrufe = []

    def durchlauf_mit_fehler(*args):
        aufrufe.append(1)
        if len(aufrufe) == 1:
            raise RuntimeError("kaputt")
        if len(aufrufe) == 3:
            raise KeyboardInterrupt  # Schleife für den Test beenden

    monkeypatch.setattr(watcher, "durchlauf", durchlauf_mit_fehler)
    try:
        lauf(umgebung.cfg, ablegen=Ablage(), schlafen=uhr.schlafen, uhr=uhr)
    except KeyboardInterrupt:
        pass
    assert len(aufrufe) == 3
    assert uhr.jetzt == 1000 + 2 * 30
