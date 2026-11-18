import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")
def test_voice_detector():
    """Runs the page's voice detector tests (tests/listener.test.mjs) under Node."""
    done = subprocess.run(["node", "--test", str(Path(__file__).with_name("listener.test.mjs"))], capture_output=True,
                          text=True)  # fmt: skip
    assert done.returncode == 0, done.stdout[-2000:]
