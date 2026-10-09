# Automail

Erzeugt aus PDFs in einem Eingangsordner E-Mail-Entwürfe mit passendem Empfänger und Text.
Entwicklung auf Ubuntu (Entwürfe als `.eml`), Betrieb auf Windows (Entwürfe in Outlook).
Plan und Stand: siehe [ENTWICKLUNGSPLAN.md](ENTWICKLUNGSPLAN.md).

## Einrichtung

Voraussetzung: Python 3.11 oder neuer.

Ubuntu:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp config.beispiel.toml config.toml
.venv/bin/pytest
.venv/bin/python -m automail
```

Windows (ausführlich, mit Dauerbetrieb und Checkliste: [docs/windows.md](docs/windows.md)):

```bat
py -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
copy config.beispiel.toml config.toml
.venv\Scripts\pytest
.venv\Scripts\python -m automail
```

In `config.toml` auf Windows `mail.modus = "outlook"` setzen und die Pfade als
Serveradresse (`\\server\freigabe\...`) eintragen.

Outlook-Anbindung prüfen (legt einen Testentwurf unter „Entwürfe" an, sendet nichts):

```bat
.venv\Scripts\python -m automail.mail.outlook ihre.adresse@example.com
```

## Dauerbetrieb

- Ubuntu: systemd-Benutzerdienst, siehe Kopf von `deploy/linux/automail.service`.
- Windows: geplante Aufgabe, siehe [docs/windows.md](docs/windows.md).
- Start immer über `automail_start.py`; es nimmt die `config.toml` neben sich, egal aus welchem Ordner.
- Beenden (Strg+C, `systemctl --user stop automail`) wartet, bis die aktuelle PDF fertig ist.

## Regeln

- Pfade stehen nur in `config.toml`, im Code immer `pathlib`.
- Dateien immer mit ausdrücklicher Kodierung öffnen (`utf-8`, Kontakttabelle `utf-8-sig` mit `;`).
- `config.toml`, echte Kontaktdaten und Zugangsdaten kommen nicht ins Git.
