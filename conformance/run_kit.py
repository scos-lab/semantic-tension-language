#!/usr/bin/env python3
"""stlconf CLI — run the conformance kit against an implementation.

    python3 run_kit.py                 # human report
    python3 run_kit.py --stl           # Eval-Verdict records
    python3 run_kit.py --only C13      # one clause
"""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import stlconf, checks                                   # noqa: F401  (import registers checks)
from adapter_sharedboard import SharedBoardSolo

ap = argparse.ArgumentParser()
ap.add_argument("--stl", action="store_true", help="emit Eval-Verdict STL records")
ap.add_argument("--only", default=None, help="substring filter on clause id")
a = ap.parse_args()

adapter = SharedBoardSolo()
results = stlconf.run_all(adapter, only=a.only)
print(stlconf.report(results, adapter.name, as_stl=a.stl))
sys.exit(1 if any(r.status == stlconf.FAIL for r in results) else 0)
