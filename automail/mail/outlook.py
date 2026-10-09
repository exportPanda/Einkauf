"""Windows: Entwurf im Ordner "Entwürfe" des klassischen Outlook ablegen (über pywin32).

Das "neue Outlook" lässt sich nicht per Skript steuern. Outlook verwendet das
Standardkonto; [mail] absender gilt nur für den eml-Modus.

Selbsttest auf dem Arbeitslaptop:
    .venv\\Scripts\\python -m automail.mail.outlook empfaenger@example.com
"""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

from ..config import Konfiguration

log = logging.getLogger(__name__)

OL_MAIL_ITEM = 0  # OlItemType.olMailItem


class OutlookFehler(Exception):
    pass


def _outlook():
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        raise OutlookFehler(
            "pywin32 fehlt. Installieren mit: .venv\\Scripts\\pip install -r requirements.txt"
        ) from None
    pythoncom.CoInitialize()  # nötig, falls nicht im Hauptthread aufgerufen
    try:
        return win32com.client.Dispatch("Outlook.Application")
    except Exception as e:
        raise OutlookFehler(
            f"Outlook nicht erreichbar ({e}). Ist das klassische Outlook installiert "
            "(nicht das 'neue Outlook')?"
        ) from e


def entwurf_anlegen(empfaenger: str, betreff: str, text: str, anhang: Path) -> None:
    if not anhang.is_file():
        raise OutlookFehler(f"Anhang nicht gefunden: {anhang}")
    outlook = _outlook()
    try:
        item = outlook.CreateItem(OL_MAIL_ITEM)
        item.To = empfaenger
        item.Subject = betreff
        item.Body = text.replace("\r\n", "\n").replace("\n", "\r\n")
        item.Attachments.Add(str(anhang.resolve()))
        item.Save()  # nur speichern, niemals Send()
    except Exception as e:
        raise OutlookFehler(f"Outlook-Entwurf konnte nicht angelegt werden: {e}") from e
    log.info("Outlook-Entwurf gespeichert: %s → %s", betreff, empfaenger)


def entwurf_ablegen(
    empfaenger: str, betreff: str, text: str, anhang: Path, *, cfg: Konfiguration
) -> None:
    entwurf_anlegen(empfaenger, betreff, text, anhang)


def selbsttest(empfaenger: str) -> None:
    """Legt einen Testentwurf mit kleiner PDF an. Danach in Outlook unter 'Entwürfe' prüfen."""
    with tempfile.TemporaryDirectory() as ordner:
        pdf = Path(ordner) / "Automail Test_0000_Grüße.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")
        entwurf_anlegen(
            empfaenger,
            "Automail Selbsttest – Umlaute: äöüß",
            "Dies ist ein Testentwurf von Automail.\nUmlaute: Ä Ö Ü ä ö ü ß\n",
            pdf,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(sys.argv) != 2:
        sys.exit("Aufruf: python -m automail.mail.outlook empfaenger@example.com")
    try:
        selbsttest(sys.argv[1])
    except OutlookFehler as e:
        sys.exit(f"Fehler: {e}")
    print("OK – Testentwurf liegt in Outlook unter 'Entwürfe'.")
