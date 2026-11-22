"""Entry point for Streamlit Community Cloud (and `streamlit run streamlit_app.py`).

Public deployments turn off the "Run" button in the code panels, because running arbitrary code on a shared server
isn't safe. To run code locally, start the app with `aiml-calc-ui`, or set AIML_CALC_PUBLIC=0.
"""

import os
import pathlib
import sys

os.environ.setdefault("AIML_CALC_PUBLIC", "1")
sys.path.insert(0, str(pathlib.Path(__file__).parent / "src"))

from aiml_calc.app import main  # noqa: E402

main()
