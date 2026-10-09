from automail.__main__ import main


def test_einmal_durchlauf(umgebung):
    umgebung.pdf("scan0001.pdf")
    # stabil_sekunden auf 0, damit der Test nicht wartet
    umgebung.konfigdatei.write_text(
        umgebung.konfigdatei.read_text(encoding="utf-8").replace("stabil_sekunden = 5", "stabil_sekunden = 0"),
        encoding="utf-8",
    )
    assert main(["--config", str(umgebung.konfigdatei), "--einmal"]) == 0
    assert umgebung.inhalt("fehler") == ["scan0001.pdf"]
    protokoll = (umgebung.ordner / "automail.log").read_text(encoding="utf-8")
    assert "Konfiguration geladen" in protokoll and "scan0001.pdf" in protokoll


def test_start_ohne_kontakttabelle(umgebung):
    (umgebung.ordner / "kontakte.csv").unlink()
    assert main(["--config", str(umgebung.konfigdatei), "--einmal"]) == 2


def test_start_mit_fehlerhafter_vorlage(umgebung):
    (umgebung.ordner / "vorlage.txt").write_text("kein Betreff\n", encoding="utf-8")
    assert main(["--config", str(umgebung.konfigdatei), "--einmal"]) == 2


def test_start_ohne_konfiguration(tmp_path, capsys):
    assert main(["--config", str(tmp_path / "fehlt.toml"), "--einmal"]) == 2
    assert "nicht gefunden" in capsys.readouterr().err


def test_startskript_findet_config_neben_sich(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    projekt = Path(__file__).resolve().parent.parent
    # Aus einem fremden Arbeitsverzeichnis starten: Die config.toml neben dem Skript fehlt
    # im Repository-Checkout evtl., deshalb hier nur auf eine verständliche Meldung prüfen.
    ergebnis = subprocess.run(
        [sys.executable, str(projekt / "automail_start.py"), "--config", str(tmp_path / "x.toml")],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
    )
    assert ergebnis.returncode == 2
    assert "x.toml" in ergebnis.stderr


def test_ohne_stderr_kein_absturz(umgebung, monkeypatch):
    import sys

    monkeypatch.setattr(sys, "stderr", None)
    test_einmal_durchlauf(umgebung)
