"""Pytest config to ensure project root is on sys.path for imports.

Pytest 8 uses importlib mode by default, which can break top-level imports
when the package isn't installed. This ensures `import app` works.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
