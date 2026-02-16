from __future__ import annotations

import csv
import io
from typing import Dict, Any, List

from azimg_auditor.report.blob_writer import upload_bytes_report


FINDINGS_COLUMNS = [
    "ruleId", "severity", "title", "description",
    "subscriptionId", "resourceGroup", "location", "vmName",
    "imageType", "imageId", "publisher", "offer", "sku", "version", "timeCreated",
    "field", "actual", "expected", "message",
]


def findings_to_csv_bytes(findings: List[Dict[str, Any]]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FINDINGS_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for f in findings:
        writer.writerow(f)
    return buf.getvalue().encode("utf-8")


def upload_findings_csv(
    findings: List[Dict[str, Any]],
    *,
    container: str,
    prefix: str,
    filename_prefix: str = "findings",
) -> str:
    data = findings_to_csv_bytes(findings)
    blob_name = upload_bytes_report(
        data,
        container=container,
        prefix=prefix,
        filename_prefix=filename_prefix,
        content_type="text/csv",
    )
    return blob_name