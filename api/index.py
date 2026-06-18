import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
capstone3_path = str(project_root / "Capstone3")

sys.path.insert(0, capstone3_path)

from app import app
