from __future__ import annotations

import csv
import os
from typing import Any, Dict, List

from azimg_auditor.utils.log import debug


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if not rows:
        # still create an empty file with headers to show it ran
        headers = [
            "subscriptionId","resourceGroup","location","vmName",
            "imageType","imageId","publisher","offer","sku","version",
            "timeCreated",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
        return

    headers = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    debug(f"Wrote CSV: {path}")