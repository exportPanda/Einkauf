"""Ubuntu: Entwurf als .eml-Datei im Ordner [pfade] ausgang_eml ablegen.

Öffnen mit Thunderbird; zum Bearbeiten "Nachricht > Als neu bearbeiten".
Der Header X-Unsent: 1 lässt Outlook die Datei ebenfalls als Entwurf öffnen.
"""

from __future__ import annotations

import logging
from datetime import datetime
from email import policy
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

from ..config import Konfiguration

log = logging.getLogger(__name__)


def nachricht(absender: str, empfaenger: str, betreff: str, text: str, anhang: Path) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = absender
    msg["To"] = empfaenger
    msg["Subject"] = betreff
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=absender.rpartition("@")[2] or None)
    msg["X-Unsent"] = "1"
    msg.set_content(text, charset="utf-8", cte="quoted-printable")
    msg.add_attachment(anhang.read_bytes(), maintype="application", subtype="pdf", filename=anhang.name)
    return msg


def entwurf_ablegen(
    empfaenger: str, betreff: str, text: str, anhang: Path, *, cfg: Konfiguration
) -> Path:
    ordner = cfg.pfade.ausgang_eml
    ordner.mkdir(parents=True, exist_ok=True)
    msg = nachricht(cfg.mail.absender, empfaenger, betreff, text, anhang)

    stamm = f"{datetime.now():%Y-%m-%d_%H%M%S}_{anhang.stem}"
    ziel = ordner / f"{stamm}.eml"
    nr = 2
    while ziel.exists():
        ziel = ordner / f"{stamm} ({nr}).eml"
        nr += 1

    # Erst unter Hilfsnamen schreiben, dann umbenennen: keine halben .eml-Dateien.
    tmp = ziel.with_suffix(".eml.tmp")
    # CRLF-Zeilenenden wie im Mail-Standard; sonst erkennt Outlook X-Unsent evtl. nicht.
    tmp.write_bytes(msg.as_bytes(policy=policy.SMTP))
    tmp.replace(ziel)
    log.info("Entwurf gespeichert: %s", ziel)
    return ziel
