"""Einstieg: python -m automail [--config config.toml] [--einmal]"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
from pathlib import Path

from . import __version__, config, kontakte, protokoll, vorlage, watcher

log = logging.getLogger("automail")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="automail", description="Erzeugt E-Mail-Entwürfe aus eingehenden PDFs."
    )
    parser.add_argument(
        "--config", type=Path, default=Path("config.toml"),
        help="Pfad zur Konfigurationsdatei (Standard: config.toml)",
    )
    parser.add_argument(
        "--einmal", action="store_true",
        help="Eingang einmal prüfen und verarbeiten, dann beenden",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    try:
        cfg = config.laden(args.config)
    except config.KonfigurationsFehler as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2

    protokoll.einrichten(cfg.pfade.protokoll)
    log.info("Konfiguration geladen: %s (mail.modus=%s)", args.config, cfg.mail.modus)
    log.info("Eingangsordner: %s", cfg.pfade.eingang)

    # Kontakttabelle und Vorlage schon beim Start prüfen, damit Fehler sofort auffallen.
    try:
        kontakte.laden(cfg.pfade.kontakte)
        vorlage.laden(cfg.pfade.vorlage)
    except (kontakte.KontaktFehler, vorlage.VorlagenFehler) as e:
        log.error("%s", e)
        return 2
    if not cfg.pfade.eingang.is_dir():
        log.warning("Eingangsordner nicht erreichbar: %s", cfg.pfade.eingang)

    # Strg+C bzw. "systemctl stop" beenden die Schleife erst nach der aktuellen Datei.
    stopp = threading.Event()

    def beenden(signum, _frame):
        log.info("Signal %s empfangen, beende nach der aktuellen Datei", signal.Signals(signum).name)
        stopp.set()

    vorher = {s: signal.signal(s, beenden) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        watcher.lauf(cfg, einmal=args.einmal, stopp=stopp)
    finally:
        for s, handler in vorher.items():
            signal.signal(s, handler)
    return 0


if __name__ == "__main__":
    sys.exit(main())
