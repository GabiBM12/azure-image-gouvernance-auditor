from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient

from azimg_auditor.azure.resource_graph import query_vm_inventory
from azimg_auditor.utils.log import debug


@dataclass
class VmInventoryRow:
    subscriptionId: str
    resourceGroup: str
    location: str
    vmName: str

    imageType: str               # marketplace | compute_gallery | managed_image | unknown
    imageId: str                 # imageRef.id or empty
    publisher: str
    offer: str
    sku: str
    version: str

    timeCreated: str             # ISO string or empty


def _classify_image(image_ref: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """
    Azure VM imageReference can look like:
      - Marketplace: {publisher, offer, sku, version}
      - Gallery/Managed Image: {id: ".../galleries/.../versions/..."} or {id:".../images/..."}
    """
    if not isinstance(image_ref, dict) or not image_ref:
        return {"imageType": "unknown", "imageId": "", "publisher": "", "offer": "", "sku": "", "version": ""}

    img_id = str(image_ref.get("id") or "").strip()
    publisher = str(image_ref.get("publisher") or "").strip()
    offer = str(image_ref.get("offer") or "").strip()
    sku = str(image_ref.get("sku") or "").strip()
    version = str(image_ref.get("version") or "").strip()

    if img_id:
        lid = img_id.lower()
        if "/galleries/" in lid and "/versions/" in lid:
            image_type = "compute_gallery"
        elif "/images/" in lid:
            image_type = "managed_image"
        else:
            image_type = "unknown"
        return {"imageType": image_type, "imageId": img_id, "publisher": "", "offer": "", "sku": "", "version": ""}

    # Marketplace-style
    if publisher and offer and sku:
        return {"imageType": "marketplace", "imageId": "", "publisher": publisher, "offer": offer, "sku": sku, "version": version}

    return {"imageType": "unknown", "imageId": "", "publisher": publisher, "offer": offer, "sku": sku, "version": version}


def _discover_subscriptions() -> List[str]:
    """
    Gets all subscriptions visible to the signed-in identity.
    Works with `az login` via DefaultAzureCredential.
    """
    cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    sub_client = SubscriptionClient(cred)
    subs = [s.subscription_id for s in sub_client.subscriptions.list() if s.subscription_id]
    debug(f"Discovered {len(subs)} subscription(s) from ARM")
    return subs


def run_inventory(subscriptions: List[str]) -> List[VmInventoryRow]:
    subs = subscriptions or _discover_subscriptions()
    if not subs:
        raise RuntimeError("No subscriptions found. Set AZIMG_SUBSCRIPTIONS or check your Azure login.")

    raw = query_vm_inventory(subs)
    out: List[VmInventoryRow] = []

    for r in raw:
        image_ref = r.get("imageRef")
        c = _classify_image(image_ref)

        out.append(
            VmInventoryRow(
                subscriptionId=str(r.get("subscriptionId") or ""),
                resourceGroup=str(r.get("resourceGroup") or ""),
                location=str(r.get("location") or ""),
                vmName=str(r.get("vmName") or ""),
                imageType=c["imageType"],
                imageId=c["imageId"],
                publisher=c["publisher"],
                offer=c["offer"],
                sku=c["sku"],
                version=c["version"],
                timeCreated=str(r.get("timeCreated") or ""),
            )
        )

    debug(f"Built {len(out)} normalized inventory row(s)")
    return out


def to_dicts(rows: List[VmInventoryRow]) -> List[Dict[str, Any]]:
    return [asdict(r) for r in rows]