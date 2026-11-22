"""`aiml-calc-ui`: launch the Streamlit app."""

import pathlib
import subprocess
import sys


def main() -> None:
    app = pathlib.Path(__file__).with_name("app.py")
    args = [sys.executable, "-m", "streamlit", "run", str(app),
            "--theme.base", "light", "--theme.primaryColor", "#2563EB", "--client.toolbarMode", "minimal", *sys.argv[1:]]
    raise SystemExit(subprocess.call(args))
