"""Eingangsordner per Schleife abfragen.

Bewusst ohne Dateisystem-Ereignisse, weil diese auf Netzlaufwerken unzuverlässig sind.
Eine PDF gilt erst als fertig, wenn Größe und Änderungszeit lange genug gleich bleiben.
"""

from __future__ import annotations

import logging
import time
from functools import partial
from pathlib import Path
from typing import Callable

from . import ablauf, kontakte, mail, vorlage
from .config import Konfiguration

log = logging.getLogger(__name__)


def pdfs_im_eingang(eingang: Path) -> list[Path]:
    """PDFs direkt im Eingang; Office-Sperrdateien (~$...) und versteckte Dateien zählen nicht."""
    return sorted(
        p for p in eingang.iterdir()
        if p.suffix.lower() == ".pdf" and not p.name.startswith(("~$", ".")) and p.is_file()
    )


class Stabilitaetspruefer:
    def __init__(self, stabil_sekunden: float, uhr: Callable[[], float] = time.monotonic):
        self.stabil_sekunden = stabil_sekunden
        self.uhr = uhr
        self._gesehen: dict[Path, tuple[int, int, float]] = {}

    def fertige(self, dateien: list[Path]) -> list[Path]:
        jetzt = self.uhr()
        stand: dict[Path, tuple[int, int, float]] = {}
        fertig = []
        for pfad in dateien:
            try:
                st = pfad.stat()
            except OSError:
                continue  # inzwischen verschwunden oder gesperrt
            vorher = self._gesehen.get(pfad)
            if vorher and vorher[:2] == (st.st_size, st.st_mtime_ns):
                stand[pfad] = vorher
                if st.st_size > 0 and jetzt - vorher[2] >= self.stabil_sekunden:
                    fertig.append(pfad)
            else:
                stand[pfad] = (st.st_size, st.st_mtime_ns, jetzt)
        self._gesehen = stand
        return fertig


def durchlauf(cfg: Konfiguration, pruefer: Stabilitaetspruefer, ablegen: ablauf.Ablage) -> int:
    """Ein Durchgang. Gibt die Zahl der fertigen PDFs zurück."""
    try:
        fertig = pruefer.fertige(pdfs_im_eingang(cfg.pfade.eingang))
    except OSError as e:
        log.warning("Eingang nicht erreichbar: %s", e)
        return 0
    if not fertig:
        return 0

    # Tabelle und Vorlage pro Durchgang neu laden, damit Änderungen ohne Neustart greifen.
    try:
        liste = kontakte.laden(cfg.pfade.kontakte)
        vorl = vorlage.laden(cfg.pfade.vorlage)
    except (kontakte.KontaktFehler, vorlage.VorlagenFehler) as e:
        log.error("%s – PDFs bleiben im Eingang", e)
        return len(fertig)

    for pdf in fertig:
        try:
            ablauf.verarbeite(pdf, cfg, liste, vorl, ablegen)
        except Exception:
            log.exception("Unerwarteter Fehler bei %s", pdf.name)
    return len(fertig)


def lauf(
    cfg: Konfiguration,
    *,
    einmal: bool = False,
    ablegen: ablauf.Ablage | None = None,
    schlafen: Callable[[float], None] = time.sleep,
    uhr: Callable[[], float] = time.monotonic,
) -> None:
    """Dauerschleife. Mit einmal=True: zweimal hinsehen (Stabilitätsprüfung), verarbeiten, Ende."""
    ablegen = ablegen or partial(mail.entwurf_ablegen, cfg=cfg)
    pruefer = Stabilitaetspruefer(cfg.abfrage.stabil_sekunden, uhr)

    if einmal:
        pruefer.fertige(pdfs_im_eingang(cfg.pfade.eingang))
        schlafen(cfg.abfrage.stabil_sekunden)
        durchlauf(cfg, pruefer, ablegen)
        return

    log.info("Abfrage alle %g s gestartet", cfg.abfrage.intervall_sekunden)
    while True:
        try:
            durchlauf(cfg, pruefer, ablegen)
        except Exception:
            log.exception("Unerwarteter Fehler im Durchgang")
        schlafen(cfg.abfrage.intervall_sekunden)
