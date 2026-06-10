import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
capstone3_path = str(project_root / "Capstone3")
db_path = project_root / "Capstone2" / "capstone.db"

sys.path.insert(0, capstone3_path)

if not db_path.exists():
    raise RuntimeError(
        f"Database not found at {db_path}. "
        "Ensure Capstone2/capstone.db is included in the deployment."
    )

from app import app
