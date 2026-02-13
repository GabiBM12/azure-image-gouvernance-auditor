import os
import sys
from datetime import datetime

def _debug_enabled() -> bool:
    return os.getenv("AZIMG_DEBUG", "0").strip() == "1"

def info(msg: str) -> None:
    print(msg)

def debug(msg: str) -> None:
    if _debug_enabled():
        ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        print(f"[DEBUG {ts}] {msg}", file=sys.stderr)