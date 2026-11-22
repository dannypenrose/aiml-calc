"""Run a generated (and possibly edited) Python program and capture its output.

Each run uses the current Python interpreter in isolated mode, in its own temporary folder, with a time limit.

Running code is only enabled when the app runs on your own machine. Set AIML_CALC_PUBLIC=1 (the Streamlit
Community Cloud entry point does this) to turn it off, because a public page that runs arbitrary code would
let anyone run commands on the server.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass


@dataclass
class RunResult:
    ok: bool
    output: str
    error: str
    seconds: float


def running_allowed() -> bool:
    return os.environ.get("AIML_CALC_PUBLIC", "").strip().lower() not in ("1", "true", "yes")


def run(code: str, timeout: float = 20.0) -> RunResult:
    if not running_allowed():
        return RunResult(False, "", "Running code is turned off on this public deployment. Copy or download the "
                                    "program and run it with `python program.py`.", 0.0)
    with tempfile.TemporaryDirectory(prefix="aiml-calc-") as tmp:
        path = os.path.join(tmp, "program.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(code)
        start = time.perf_counter()
        try:
            p = subprocess.run([sys.executable, "-I", path], cwd=tmp, capture_output=True, text=True,
                               timeout=timeout, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        except subprocess.TimeoutExpired as e:
            out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            return RunResult(False, out, f"Stopped after {timeout:.0f} seconds (is there an infinite loop?).",
                             time.perf_counter() - start)
        return RunResult(p.returncode == 0, p.stdout, p.stderr.strip(), time.perf_counter() - start)
