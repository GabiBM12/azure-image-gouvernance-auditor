from __future__ import annotations

import io
import os
import csv
from datetime import datetime, timezone
from typing import Any, Dict, List

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


HEADERS = [
    "subscriptionId","resourceGroup","location","vmName",
    "imageType","imageId","publisher","offer","sku","version",
    "timeCreated",
]


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def upload_csv_report(rows: List[Dict[str, Any]], *, container: str, prefix: str) -> str:
    """
    Builds a CSV in-memory and uploads it to Azure Blob Storage using Managed Identity.

    Returns the blob name that was written.
    """
    account = os.environ["AZIMG_STORAGE_ACCOUNT"]
    prefix = (prefix or "").lstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    blob_name = f"{prefix}vm_inventory_{_now_stamp()}.csv"

    # Build CSV in-memory
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=HEADERS)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in HEADERS})

    data = buf.getvalue().encode("utf-8")

    # Upload
    cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    bsc = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=cred)
    bc = bsc.get_container_client(container)
    bc.upload_blob(name=blob_name, data=data, overwrite=True)

    return blob_name