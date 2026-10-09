from automail import kontakte, vorlage
from automail.ablauf import Ergebnis, verarbeite, verschiebe


def vorbereiten(umgebung):
    cfg = umgebung.cfg
    return cfg, kontakte.laden(cfg.pfade.kontakte), vorlage.laden(cfg.pfade.vorlage)


def test_verschiebe_ueberschreibt_nicht(tmp_path):
    ziel = tmp_path / "ziel"
    for _ in range(3):
        (tmp_path / "a.pdf").write_text("x")
        verschiebe(tmp_path / "a.pdf", ziel)
    assert sorted(p.name for p in ziel.iterdir()) == ["a (2).pdf", "a (3).pdf", "a.pdf"]


def test_erfolg(umgebung):
    cfg, liste, vorl = vorbereiten(umgebung)
    aufrufe = []
    pdf = umgebung.pdf("Müller GmbH_4711_2026-10-09.pdf")
    ergebnis = verarbeite(pdf, cfg, liste, vorl, lambda *a: aufrufe.append(a))
    assert ergebnis is Ergebnis.ERLEDIGT
    assert aufrufe[0][3].exists()            # Anhang zeigt auf die PDF in "erledigt"


def test_ungueltiger_name(umgebung):
    cfg, liste, vorl = vorbereiten(umgebung)
    pdf = umgebung.pdf("scan0001.pdf")
    assert verarbeite(pdf, cfg, liste, vorl, lambda *a: None) is Ergebnis.FEHLER
    assert umgebung.inhalt("fehler") == ["scan0001.pdf"]


def test_ablage_scheitert(umgebung, caplog):
    cfg, liste, vorl = vorbereiten(umgebung)
    pdf = umgebung.pdf("Müller GmbH_4711_2026-10-09.pdf")

    def kaputt(*args):
        raise OSError("Outlook nicht erreichbar")

    assert verarbeite(pdf, cfg, liste, vorl, kaputt) is Ergebnis.SPAETER
    assert umgebung.inhalt("eingang") == ["Müller GmbH_4711_2026-10-09.pdf"]
    assert umgebung.inhalt("erledigt") == []
    assert "Outlook nicht erreichbar" in caplog.text
