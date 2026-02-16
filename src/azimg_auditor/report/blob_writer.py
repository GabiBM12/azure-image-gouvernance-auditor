from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


def _blob_service_client() -> BlobServiceClient:
    account = os.getenv("AZIMG_STORAGE_ACCOUNT", "").strip()
    if not account:
        raise RuntimeError("AZIMG_STORAGE_ACCOUNT is not set")

    url = f"https://{account}.blob.core.windows.net"
    cred = DefaultAzureCredential()
    return BlobServiceClient(account_url=url, credential=cred)


def upload_bytes_report(
    data: bytes,
    *,
    container: str,
    prefix: str,
    filename_prefix: str,
    content_type: str = "application/octet-stream",
) -> str:
    bsc = _blob_service_client()
    cc = bsc.get_container_client(container)
    try:
        cc.create_container()
    except Exception:
        pass

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    blob_name = f"{prefix.rstrip('/')}/{filename_prefix}_{ts}.csv"

    bc = cc.get_blob_client(blob_name)
    bc.upload_blob(data, overwrite=True, content_settings={"content_type": content_type})
    return blob_name


def upload_csv_report(
    rows: List[Dict[str, Any]],
    *,
    container: str,
    prefix: str,
    filename_prefix: str = "vm_inventory",
) -> str:
    import csv
    import io

    if not rows:
        # still upload header-only file
        columns = []
    else:
        columns = list(rows[0].keys())

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

    return upload_bytes_report(
        buf.getvalue().encode("utf-8"),
        container=container,
        prefix=prefix,
        filename_prefix=filename_prefix,
        content_type="text/csv",
    )