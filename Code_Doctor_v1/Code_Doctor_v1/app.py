"""Compatibility entrypoint for the existing Streamlit Cloud deployment.

The deployed app is currently configured to use:
    Code_Doctor_v1/Code_Doctor_v1/app.py

The actively maintained application is:
    Code_Doctor_v1/app.py

Keep this tiny forwarding script until Streamlit Cloud is redeployed with the
canonical path. This prevents future updates from being lost in the old copy.
"""
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
APP_ROOT = HERE.parent
APP_ENTRYPOINT = APP_ROOT / "app.py"

if not APP_ENTRYPOINT.is_file():
    raise RuntimeError("Code Doctor의 최신 앱 파일을 찾지 못했습니다.")

# Streamlit executes this script, but imports must resolve to the maintained
# modules in the parent directory, never the outdated nested copies.
if str(APP_ROOT) in sys.path:
    sys.path.remove(str(APP_ROOT))
sys.path.insert(0, str(APP_ROOT))

# Preserve existing records for an already-running nested deployment if its
# legacy SQLite DB still exists. New installs use the canonical DB location.
import database as db

legacy_db = HERE / "code_doctor.db"
if legacy_db.is_file():
    db.DB_PATH = legacy_db

# Keep the Streamlit script runner/session context unchanged.
runpy.run_path(str(APP_ENTRYPOINT), run_name="__main__")
