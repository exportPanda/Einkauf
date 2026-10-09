from pathlib import Path

import pytest

from automail import config

PROJEKT = Path(__file__).resolve().parent.parent
BEISPIEL = PROJEKT / "config.beispiel.toml"

MINIMAL = """
[pfade]
eingang = "ein"
kontakte = "k.csv"
vorlage = "v.txt"
erledigt = "fertig"
fehler = "fehler"
protokoll = "log.txt"
ausgang_eml = "aus"

[mail]
modus = "eml"
absender = "a@example.com"
"""


def schreibe(tmp_path: Path, inhalt: str) -> Path:
    datei = tmp_path / "config.toml"
    datei.write_text(inhalt, encoding="utf-8")
    return datei


def test_beispielkonfiguration_ist_gueltig():
    cfg = config.laden(BEISPIEL)
    assert cfg.mail.modus == "eml"
    assert cfg.pfade.kontakte == PROJEKT / "beispieldaten" / "kontakte_beispiel.csv"
    assert cfg.ki.aktiv is False


def test_relative_pfade_gelten_relativ_zur_konfigurationsdatei(tmp_path):
    cfg = config.laden(schreibe(tmp_path, MINIMAL))
    assert cfg.pfade.eingang == tmp_path.resolve() / "ein"
    assert all(isinstance(p, Path) for p in vars(cfg.pfade).values())


def test_standardwerte(tmp_path):
    cfg = config.laden(schreibe(tmp_path, MINIMAL))
    assert cfg.abfrage.intervall_sekunden == 30
    assert cfg.abfrage.stabil_sekunden == 5
    assert cfg.ki.aktiv is False


def test_fehlender_pflichtwert(tmp_path):
    datei = schreibe(tmp_path, MINIMAL.replace('eingang = "ein"\n', ""))
    with pytest.raises(config.KonfigurationsFehler, match=r"\[pfade\] eingang"):
        config.laden(datei)


def test_unbekannter_mailmodus(tmp_path):
    datei = schreibe(tmp_path, MINIMAL.replace('modus = "eml"', 'modus = "smtp"'))
    with pytest.raises(config.KonfigurationsFehler, match="mail.modus"):
        config.laden(datei)


def test_outlook_braucht_kein_ausgang_eml(tmp_path):
    inhalt = MINIMAL.replace('modus = "eml"', 'modus = "outlook"').replace('ausgang_eml = "aus"\n', "")
    cfg = config.laden(schreibe(tmp_path, inhalt))
    assert cfg.pfade.ausgang_eml is None


def test_unc_pfad_bleibt_unveraendert_absolut(tmp_path):
    # Auf Windows ist '\\server\freigabe\x' absolut; auf Linux wird nur geprüft, dass das Laden klappt.
    inhalt = MINIMAL.replace('eingang = "ein"', r"eingang = '\\server\freigabe\Eingang'")
    cfg = config.laden(schreibe(tmp_path, inhalt))
    assert "freigabe" in str(cfg.pfade.eingang)


def test_fehlende_datei(tmp_path):
    with pytest.raises(config.KonfigurationsFehler, match="nicht gefunden"):
        config.laden(tmp_path / "gibtsnicht.toml")


def test_kaputte_datei(tmp_path):
    with pytest.raises(config.KonfigurationsFehler, match="fehlerhaft"):
        config.laden(schreibe(tmp_path, "[pfade\n"))
