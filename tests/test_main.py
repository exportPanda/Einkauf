from automail.__main__ import main
from tests.test_config import MINIMAL, schreibe


def test_start_mit_gueltiger_konfiguration(tmp_path):
    assert main(["--config", str(schreibe(tmp_path, MINIMAL))]) == 0
    assert (tmp_path / "log.txt").read_text(encoding="utf-8").count("Konfiguration geladen") == 1


def test_start_ohne_konfiguration(tmp_path, capsys):
    assert main(["--config", str(tmp_path / "fehlt.toml")]) == 2
    assert "nicht gefunden" in capsys.readouterr().err
