import sys
from pathlib import Path

import pytest

from automail import config
from automail.mail import entwurf_ablegen
from tests.test_config import MINIMAL, schreibe


@pytest.mark.skipif(sys.platform == "win32", reason="prüft das Verhalten ohne pywin32")
def test_eml_modus_importiert_kein_pywin32(tmp_path):
    cfg = config.laden(schreibe(tmp_path, MINIMAL))
    with pytest.raises(NotImplementedError):  # bis Phase 3.1
        entwurf_ablegen("x@example.com", "Betreff", "Text", Path("a.pdf"), cfg=cfg)
    assert "win32com" not in sys.modules
