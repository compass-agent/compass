import os
import sys
from pathlib import Path

# Get the absolute path to the project root
PROJECT_ROOT = Path(__file__).parent
SRC_PATH = PROJECT_ROOT / "src"

# Add the src directory to Python path
sys.path.insert(0, str(SRC_PATH)) 