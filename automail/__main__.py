"""Einstieg: python -m automail [--config config.toml]"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__, config, protokoll

log = logging.getLogger("automail")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="automail", description="Erzeugt E-Mail-Entwürfe aus eingehenden PDFs."
    )
    parser.add_argument(
        "--config", type=Path, default=Path("config.toml"),
        help="Pfad zur Konfigurationsdatei (Standard: config.toml)",
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
    # Die Abfrageschleife folgt in Phase 2 (watcher.py).
    return 0


if __name__ == "__main__":
    sys.exit(main())
