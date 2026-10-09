# Automail

Erzeugt aus PDFs in einem Eingangsordner E-Mail-Entwürfe mit passendem Empfänger und Text.
Entwicklung auf Ubuntu (Entwürfe als `.eml`), Betrieb auf Windows (Entwürfe in Outlook).
Plan und Stand: siehe [ENTWICKLUNGSPLAN.md](ENTWICKLUNGSPLAN.md).

## Einrichtung

Ubuntu:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp config.beispiel.toml config.toml
.venv/bin/pytest
.venv/bin/python -m automail
```

Windows:

```bat
py -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
copy config.beispiel.toml config.toml
.venv\Scripts\pytest
.venv\Scripts\python -m automail
```

In `config.toml` auf Windows `mail.modus = "outlook"` setzen und die Pfade als
Serveradresse (`\\server\freigabe\...`) eintragen.

## Regeln

- Pfade stehen nur in `config.toml`, im Code immer `pathlib`.
- Dateien immer mit ausdrücklicher Kodierung öffnen (`utf-8`, Kontakttabelle `utf-8-sig` mit `;`).
- `config.toml`, echte Kontaktdaten und Zugangsdaten kommen nicht ins Git.
