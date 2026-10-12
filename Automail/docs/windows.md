# Automail auf dem Windows-Arbeitslaptop

Diese Anleitung deckt Phase 7 des Entwicklungsplans ab. Zeitbedarf: ½–1 Tag.

## Voraussetzungen

- **Python 3.11 oder neuer** (wegen `tomllib`). Ohne Administratorrechte: Installer von python.org,
  „Install for me only" (bzw. ohne „for all users"), Haken bei „Add python.exe to PATH" optional;
  der Python-Launcher `py` reicht.
- **Klassisches Outlook** (nicht das „neue Outlook"). Prüfen: In Outlook oben rechts darf kein
  Schalter „Neues Outlook" auf *Ein* stehen; unter *Datei > Office-Konto* steht „Microsoft 365 / Outlook".
- Lese- und Schreibrechte auf Eingangs-, Erledigt- und Fehlerordner im Netzlaufwerk.

## 1. Code übertragen

Entweder über ein privates Git-Remote (`git clone ...`) oder als ZIP. ZIP auf Ubuntu erzeugen:

```bash
git archive --format=zip -o automail.zip HEAD
```

Das ZIP enthält nur eingecheckte Dateien, also **keine** `config.toml`, keine venv und keine Protokolle.
Auf dem Laptop z. B. nach `C:\Users\<name>\Automail` entpacken (nicht auf das Netzlaufwerk).

## 2. Installieren

In der Eingabeaufforderung (`cmd`) im Projektordner:

```bat
py -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\pytest
```

`pytest` muss vollständig grün sein; die Outlook-Tests laufen dabei mit einem nachgebauten
Outlook, der echte Test folgt in Schritt 4.

## 3. Konfigurieren

```bat
copy config.beispiel.toml config.toml
notepad config.toml
```

- `[mail] modus = "outlook"`
- Pfade als volle Serveradresse in **einfachen** Anführungszeichen, keine Laufwerksbuchstaben:
  `eingang = '\\server\freigabe\Einkauf\Eingang'`
- Kontakttabelle in Excel als **„CSV UTF-8 (durch Trennzeichen getrennt)"** speichern.
- Vorlage (`vorlage.txt`) in Notepad mit Kodierung **UTF-8** speichern.

## 4. Outlook-Anbindung prüfen

Outlook öffnen, dann:

```bat
.venv\Scripts\python -m automail.mail.outlook ihre.adresse@example.com
```

Erwartet: „OK – Testentwurf liegt in Outlook unter 'Entwürfe'." Den Entwurf öffnen und prüfen:
Umlaute im Betreff und Text, PDF-Anhang vorhanden. Danach löschen.

## 5. Einmal-Durchlauf

Eine Test-PDF mit gültigem Namen (z. B. `Beispiel AG_4711_2026-10-09.pdf`) in den Eingang legen:

```bat
.venv\Scripts\python automail_start.py --einmal
```

Prüfen: Entwurf in Outlook, PDF im Erledigt-Ordner, Eintrag im Protokoll. Dabei auf
Geschwindigkeit des Netzlaufwerks achten; bei langsamen Kopiervorgängen `stabil_sekunden` erhöhen.

## 6. Dauerbetrieb

Outlook-Steuerung funktioniert nur in der angemeldeten Benutzersitzung. Deshalb startet Automail
**bei der Anmeldung** und **nur, wenn der Benutzer angemeldet ist**. Drei Wege, der erste passende genügt:

**a) Skript** (PowerShell, im Projektordner):

```bat
powershell -ExecutionPolicy Bypass -File deploy\windows\aufgabe_einrichten.ps1
```

**b) Aufgabenplanung von Hand** (falls Skripte gesperrt sind): *Einfache Aufgabe erstellen* ist zu
eingeschränkt, deshalb *Aufgabe erstellen…*:

| Reiter | Einstellung |
|---|---|
| Allgemein | Name `Automail`, „Nur ausführen, wenn der Benutzer angemeldet ist" |
| Trigger | „Bei Anmeldung", eigener Benutzer |
| Aktionen | Programm: `C:\Users\<name>\Automail\.venv\Scripts\pythonw.exe`<br>Argumente: `automail_start.py`<br>Starten in: `C:\Users\<name>\Automail` |
| Bedingungen | „Nur starten, falls Computer im Netzbetrieb" **aus** |
| Einstellungen | „Aufgabe beenden, falls sie länger läuft als" **aus**; „Neue Instanz nicht starten" |

**c) Autostart-Ordner** (falls auch die Aufgabenplanung gesperrt ist): `Win+R`, `shell:startup`,
dort eine Verknüpfung anlegen mit Ziel
`C:\Users\<name>\Automail\.venv\Scripts\pythonw.exe automail_start.py` und
„Ausführen in" `C:\Users\<name>\Automail`.

`pythonw.exe` startet ohne Konsolenfenster; alle Meldungen stehen im Protokoll.
Beenden: Aufgabenplanung > Automail > *Beenden* bzw. Task-Manager > `pythonw.exe`.

## 7. Probebetrieb

- Eine Woche lang alle Entwürfe vor dem Senden prüfen.
- Ordner `Fehler` täglich ansehen: ungültige Dateinamen oder fehlende Kontakte.
- Wenn der Virenscanner oder eine Ausführungssperre etwas blockiert: Protokoll und genaue
  Fehlermeldung an die IT geben.

## Aktualisieren

Neue Version wie in Schritt 1 übertragen (Git: `git pull`), dann
`.venv\Scripts\pip install -r requirements-dev.txt` und `.venv\Scripts\pytest`.
`config.toml` bleibt unverändert, solange keine neuen Pflichtwerte dazugekommen sind
(Vergleich mit `config.beispiel.toml`).
