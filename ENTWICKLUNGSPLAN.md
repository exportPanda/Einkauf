# Entwicklungsplan Automail

Ziel: Ein Python-Dienst, der einen Ordner auf neue PDFs prüft, den Dateinamen zerlegt,
den passenden Kontakt nachschlägt, eine Vorlage füllt und daraus einen E-Mail-Entwurf
ablegt. Entwickelt wird auf Ubuntu, eingesetzt auf einem Windows-Arbeitslaptop.

Nur zwei Stellen sind betriebssystemabhängig: **E-Mail-Ablage** und **Pfade**.
Beides wird über die Konfigurationsdatei umgeschaltet, nicht im Code.

## Ausgangslage (Ubuntu, Stand 2026-10-09)

| Werkzeug | Status |
|---|---|
| Ubuntu | 24.04.4 LTS |
| Python | 3.12.3 |
| Git | vorhanden |
| Ollama | vorhanden (`/usr/local/bin/ollama`) |
| Thunderbird | vorhanden (zum Öffnen der `.eml`-Testentwürfe) |
| Projektordner | `~/almig/Einkauf/Automail` (leer, noch kein Git-Repository) |

---

## Phase 0: Vorab bei der Arbeit klären (vor dem Programmieren)

Diese Punkte entscheiden, ob der Python-Weg überhaupt passt.

- [ ] **Python auf dem Arbeitslaptop erlaubt?** Wenn nein: Power Automate prüfen, Projekt ggf. stoppen.
- [ ] **Outlook-Version:** klassisches Outlook oder „neues Outlook"? Nur das klassische lässt sich per `pywin32` steuern.
- [ ] **Ollama erlaubt?** Und reicht die Leistung des Laptops? Wenn nein: KI-Teil per Konfiguration abschalten.
- [ ] **Netzlaufwerke:** volle UNC-Pfade notieren (`\\server\freigabe\...`) für Eingangsordner, Kontakttabelle, Vorlagen, Protokoll.
- [ ] **Dateinamen-Schema** der PDFs mit Beispielen festhalten (z. B. `Lieferant_Bestellnr_Datum.pdf`).
- [ ] **Kontakttabelle:** Spaltennamen und eine anonymisierte Beispielzeile besorgen.
- [ ] **Dauerbetrieb:** Darf eine geplante Aufgabe (Aufgabenplanung) angelegt werden?

**Ergebnis:** kurze Notiz `docs/klaerung.md` mit den Antworten.

---

## Phase 1: Projektgerüst auf Ubuntu (ca. ½ Tag)

```bash
cd ~/almig/Einkauf/Automail
git init
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### Ordnerstruktur

```
Automail/
├── automail/
│   ├── __init__.py
│   ├── __main__.py          # Einstieg: python -m automail
│   ├── config.py            # Konfiguration laden (pathlib, utf-8)
│   ├── watcher.py           # Ordner per Schleife abfragen, Größen-Stabilitätsprüfung
│   ├── dateiname.py         # Dateinamen zerlegen
│   ├── kontakte.py          # Kontakttabelle lesen (utf-8-sig, Semikolon), Suche
│   ├── vorlage.py           # Textvorlage füllen
│   ├── protokoll.py         # Logging in Datei, utf-8
│   ├── ki.py                # optionale Ollama-Anbindung, abschaltbar
│   └── mail/
│       ├── __init__.py      # entwurf_ablegen(...) wählt Umsetzung laut Konfiguration
│       ├── eml.py           # Ubuntu: .eml-Datei in Testordner
│       └── outlook.py       # Windows: Outlook-Entwurf über pywin32
├── tests/
│   ├── test_dateiname.py
│   ├── test_kontakte.py
│   ├── test_vorlage.py
│   ├── test_watcher.py
│   └── test_mail_eml.py
├── beispieldaten/           # nur erfundene Daten, im Git
│   ├── kontakte_beispiel.csv
│   ├── vorlage.txt
│   └── eingang/             # Test-PDFs
├── config.beispiel.toml     # im Git
├── config.toml              # echte Konfiguration, NICHT im Git
├── requirements.txt
├── requirements-dev.txt     # pytest
├── .gitignore
└── README.md
```

### `requirements.txt`

```
pywin32; sys_platform == "win32"
requests          # nur falls Ollama per HTTP angesprochen wird
```

Konfiguration im TOML-Format: `tomllib` ist ab Python 3.11 eingebaut, keine Zusatzabhängigkeit.

### `.gitignore`

```
.venv/
__pycache__/
config.toml
*.log
ausgang/
kontakte*.csv
!beispieldaten/kontakte_beispiel.csv
```

### `config.beispiel.toml`

```toml
[pfade]
eingang     = "beispieldaten/eingang"
kontakte    = "beispieldaten/kontakte_beispiel.csv"
vorlage     = "beispieldaten/vorlage.txt"
ausgang_eml = "ausgang"            # nur für mail.modus = "eml"
erledigt    = "beispieldaten/erledigt"
protokoll   = "automail.log"
# Windows-Beispiel: eingang = '\\server\freigabe\Einkauf\Eingang'

[mail]
modus = "eml"                      # "eml" (Ubuntu) oder "outlook" (Windows)
absender = "einkauf@example.com"

[abfrage]
intervall_sekunden = 30
stabil_sekunden    = 5             # Größe muss so lange gleich bleiben

[ki]
aktiv  = false
modell = "llama3.2"
url    = "http://localhost:11434"
```

**Ergebnis:** `python -m automail --help` läuft, `pytest` läuft (noch ohne Tests), erster Git-Commit.

---

## Phase 2: Kernlogik, betriebssystemunabhängig (ca. 2–3 Tage)

Reihenfolge so gewählt, dass jeder Schritt sofort testbar ist.

### 2.1 Konfiguration (`config.py`)
- TOML laden, alle Pfade sofort in `pathlib.Path` umwandeln.
- Relative Pfade relativ zur Konfigurationsdatei auflösen.
- Klare Fehlermeldung, wenn ein Pflichtwert fehlt.

### 2.2 Dateinamen zerlegen (`dateiname.py`) – erledigt
- Funktion `zerlege(dateiname) -> Dateiinfo | None` mit `lieferant`, `bestellnr`, `datum`.
- Schema `Lieferant_Bestellnr_Datum.pdf`, Datum als `JJJJ-MM-TT` oder `TT.MM.JJJJ`,
  Trennung von rechts (Lieferant darf `_` enthalten), Umlaute werden nach NFC vereinheitlicht.
- Ungültige Namen geben `None` zurück und werden protokolliert, nicht verarbeitet.
- **Tests:** gültige Namen, Umlaute, Leerzeichen, falsche Endung, fehlende Teile.

### 2.3 Kontaktsuche (`kontakte.py`) – erledigt
- `laden(pfad) -> Kontaktliste`, dann `finde(lieferant) -> Kontakt | None` (`lieferant`, `ansprechpartner`, `email`).
- Spalten `Lieferant;Ansprechpartner;E-Mail`. ANSI-Export, falsches Trennzeichen oder fehlende Spalten ergeben eine klare Fehlermeldung.
- Suche ignoriert Groß-/Kleinschreibung, Leerzeichen und Unicode-Form (auch ß = SS). Dubletten mit gleicher Adresse gelten als eindeutig.
- CSV mit `encoding="utf-8-sig"` und `delimiter=";"` lesen (Excel-Export).
- Suche nach Lieferant, unabhängig von Groß-/Kleinschreibung und Leerzeichen am Rand.
- Kein Treffer bzw. mehrere Treffer → protokollieren, Datei nicht verarbeiten.
- **Tests:** Umlaute (Müller, Größe), BOM am Dateianfang, fehlender Kontakt, Dubletten.

### 2.4 Vorlage füllen (`vorlage.py`) – erledigt
- `laden(pfad) -> Vorlage` prüft beim Start: erste Zeile `Betreff: ...`, nur bekannte Platzhalter, gültige `$`.
- `fuellen(vorlage, info, kontakt) -> Entwurf` (`empfaenger`, `betreff`, `text`).
- Platzhalter `$lieferant $bestellnr $datum $ansprechpartner $anrede $email`; `$anrede` fällt ohne Ansprechpartner auf „Sehr geehrte Damen und Herren" zurück.
- Vorlage mit `encoding="utf-8"` lesen, Platzhalter per `string.Template` (`$lieferant`, `$bestellnr`).
- Fehlender Platzhalter → klare Fehlermeldung.
- **Tests:** alle Platzhalter gefüllt, fehlender Wert.

### 2.5 Protokoll (`protokoll.py`) – erledigt
- `logging` mit `FileHandler(..., encoding="utf-8")` plus Konsolenausgabe.
- Jede verarbeitete Datei: Zeitpunkt, Dateiname, Empfänger, Ergebnis.

### 2.6 Ordner abfragen (`watcher.py`, `ablauf.py`) – erledigt
- Nur `*.pdf` direkt im Eingang; `~$...` und versteckte Dateien werden ignoriert.
- Fertig erst, wenn Größe **und** Änderungszeit `stabil_sekunden` lang gleich bleiben; leere Dateien nie.
- Ungültiger Dateiname oder kein Kontakt → Ordner `fehler` (neuer Pflichtpfad `[pfade] fehler`).
- Erst nach `erledigt` verschieben, dann Entwurf ablegen; scheitert die Ablage, geht die PDF zurück in den Eingang (kein doppelter Entwurf).
- Kontakttabelle und Vorlage werden pro Durchgang neu geladen, wenn PDFs anstehen; beim Start einmal geprüft.
- `python -m automail --einmal` für einen einzelnen Durchgang.
- **Abfrage per Schleife**, kein Dateisystem-Ereignis (auf Netzlaufwerken unzuverlässig).
- Datei gilt erst als fertig, wenn die Größe `stabil_sekunden` lang gleich bleibt.
- Verarbeitete PDFs in den Ordner `erledigt` verschieben, damit nichts doppelt läuft.
- Fehler bei einer Datei dürfen die Schleife nicht beenden.
- **Tests:** Datei, die noch wächst, wird übersprungen; stabile Datei wird erkannt.

**Ergebnis:** Ablauf Eingang → Zerlegung → Kontakt → Vorlage ist vollständig getestet.

---

## Phase 3: E-Mail-Ablage mit zwei Umsetzungen (ca. 1 Tag)

### Einheitliche Schnittstelle (`mail/__init__.py`)

```python
def entwurf_ablegen(empfaenger: str, betreff: str, text: str, anhang: Path) -> None:
    ...  # wählt eml.py oder outlook.py anhand von config["mail"]["modus"]
```

`outlook.py` wird **erst innerhalb der Funktion** importiert, damit Ubuntu ohne `pywin32` läuft.

### 3.1 Ubuntu: `mail/eml.py` – erledigt
- Dateiname `JJJJ-MM-TT_HHMMSS_<PDF-Name>.eml`, wird nie überschrieben, erst als `.tmp` geschrieben.
- Text als Quoted-Printable, Betreff und Anhangname RFC-konform kodiert (Datei ist reines ASCII).
- In Thunderbird: Datei öffnen, dann „Nachricht > Als neu bearbeiten".
- `email.message.EmailMessage` aufbauen, PDF anhängen, Header `X-Unsent: 1` setzen.
- Als `.eml` in `ausgang_eml` speichern (Dateiname mit Zeitstempel).
- Kontrolle: `thunderbird ausgang/<datei>.eml` öffnen, Umlaute und Anhang prüfen.
- **Test:** `.eml` wieder einlesen, Empfänger/Betreff/Anhang vergleichen.

### 3.2 Windows: `mail/outlook.py` – geschrieben, auf Ubuntu mit nachgebautem pywin32 getestet
- Nur `Save()`, nie `Send()`. Outlook nutzt das Standardkonto, Signatur wird nicht eingefügt.
- Outlook nicht erreichbar → klare Meldung, PDF bleibt im Eingang und wird erneut versucht.
- Selbsttest auf Windows: `.venv\\Scripts\\python -m automail.mail.outlook ich@firma.de`
- `win32com.client.Dispatch("Outlook.Application")`, `CreateItem(0)`.
- `To`, `Subject`, `Body`, `Attachments.Add(str(anhang))`, dann `.Save()` (nicht `.Send()`).
- Auf Ubuntu nur Syntax prüfen; Testfall mit `pytest.mark.skipif(sys.platform != "win32")`.

**Ergebnis:** Auf Ubuntu entsteht für jede Test-PDF eine korrekte `.eml`-Datei.

---

## Phase 4: Lokale KI mit Ollama (optional, ca. 1 Tag)

- Nur nutzen, wo sie echten Mehrwert bringt (z. B. Betreff oder kurzen Begleitsatz formulieren).
- Ansprache per HTTP an `http://localhost:11434/api/generate`, mit Zeitlimit.
- `ki.aktiv = false` → Programm läuft komplett ohne KI, mit festem Vorlagentext.
- Fällt Ollama aus → Rückfall auf Vorlagentext, Eintrag im Protokoll.
- Modell lokal laden: `ollama pull llama3.2` (oder kleineres Modell, je nach Laptop-Leistung).

---

## Phase 5: Dauerbetrieb auf Ubuntu (ca. ½ Tag)

systemd-Benutzerdienst `~/.config/systemd/user/automail.service`:

```ini
[Unit]
Description=Automail

[Service]
WorkingDirectory=%h/almig/Einkauf/Automail
ExecStart=%h/almig/Einkauf/Automail/.venv/bin/python -m automail
Restart=on-failure

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now automail
journalctl --user -u automail -f
```

**Ergebnis:** Dienst läuft im Hintergrund, startet nach Fehlern neu, PDFs im Testordner werden automatisch verarbeitet.

---

## Phase 6: Übergabe an Windows vorbereiten (ca. ½ Tag)

- [ ] `README.md`: Installation auf Windows Schritt für Schritt
  (`py -m venv .venv`, `.venv\Scripts\pip install -r requirements.txt`, `config.toml` anlegen).
- [ ] `config.beispiel.toml` um einen auskommentierten Windows-Block mit UNC-Pfaden ergänzen.
- [ ] Anleitung Windows-Aufgabenplanung: Start „Bei Anmeldung", Programm `.venv\Scripts\pythonw.exe`,
  Argument `-m automail`, „Starten in" = Projektordner. Keine Laufwerksbuchstaben verwenden.
- [ ] Prüfen, dass keine echten Kontaktdaten oder Zugangsdaten im Git-Verlauf sind (`git log -p | grep -i @`).
- [ ] Repository übertragen (privates Git-Remote oder als ZIP, je nach Firmenrichtlinie).

---

## Phase 7: Einführung auf dem Arbeitslaptop (½–1 Tag einplanen)

Was nur dort getestet werden kann:

1. `pytest` ausführen → Dateinamen-Zerlegung und Kontaktsuche müssen sofort grün sein.
2. `mail.modus = "outlook"` setzen, eine Test-PDF verarbeiten, Entwurf in Outlook prüfen.
3. Zugriffsrechte und Geschwindigkeit der Netzlaufwerke prüfen, ggf. `intervall_sekunden` und `stabil_sekunden` anpassen.
4. Virenscanner / Ausführungssperren beobachten; bei Blockade IT einbeziehen.
5. Geplante Aufgabe einrichten, Neustart des Laptops testen.
6. Eine Woche Probebetrieb: Entwürfe nur prüfen, nicht automatisch senden.

---

## Zeitübersicht

| Phase | Inhalt | Aufwand |
|---|---|---|
| 0 | Klärung bei der Arbeit | parallel |
| 1 | Projektgerüst | ½ Tag |
| 2 | Kernlogik + Tests | 2–3 Tage |
| 3 | E-Mail-Ablage (eml + Outlook) | 1 Tag |
| 4 | Ollama (optional) | 1 Tag |
| 5 | systemd-Dauerbetrieb | ½ Tag |
| 6 | Übergabe vorbereiten | ½ Tag |
| 7 | Einführung Windows | ½–1 Tag |
| | **Gesamt** | **ca. 6–8 Arbeitstage** |

## Regeln, die durchgehend gelten

- Pfade **nur** in der Konfiguration, im Code **immer** `pathlib`.
- Netzlaufwerke als UNC-Pfad (`\\server\freigabe\...`), nie als Laufwerksbuchstabe.
- Jede Dateioperation mit ausdrücklicher Kodierung (`utf-8`, Kontakte `utf-8-sig` + `;`).
- `pywin32` nur mit Plattform-Marker in `requirements.txt`.
- Zugangsdaten und echte Kontaktdaten nie ins Git.
- Nach jeder Phase: `pytest` grün, dann Git-Commit.
