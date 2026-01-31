from __future__ import annotations

import sys
from pathlib import Path


REP_BASE = Path(__file__).resolve().parents[1]
if str(REP_BASE) not in sys.path:
    sys.path.insert(0, str(REP_BASE))