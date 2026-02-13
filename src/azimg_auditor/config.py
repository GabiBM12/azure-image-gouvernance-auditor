from dataclasses import dataclass
import os
from typing import List

@dataclass(frozen=True)
class Config:
    subscriptions: List[str]
    out_dir: str

def load_config() -> Config:
    subs_raw = os.getenv("AZIMG_SUBSCRIPTIONS", "").strip()
    subscriptions = [s.strip() for s in subs_raw.split(",") if s.strip()] if subs_raw else []
    out_dir = os.getenv("AZIMG_OUT_DIR", "out").strip() or "out"
    return Config(subscriptions=subscriptions, out_dir=out_dir)