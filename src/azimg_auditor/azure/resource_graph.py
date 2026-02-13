from __future__ import annotations

from typing import Any, Dict, List

from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

from azimg_auditor.utils.log import debug


VM_IMAGE_QUERY = r"""
Resources
| where type =~ 'microsoft.compute/virtualmachines'
| project
    subscriptionId,
    resourceGroup,
    location,
    vmName = name,
    imageRef = properties.storageProfile.imageReference,
    timeCreated = properties.timeCreated
"""


def query_vm_inventory(subscriptions: List[str]) -> List[Dict[str, Any]]:
    """
    Returns raw rows from Azure Resource Graph.
    If subscriptions is empty, caller should pass an explicit list (we fetch it elsewhere).
    """
    cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    client = ResourceGraphClient(cred)

    debug(f"Querying Resource Graph across {len(subscriptions)} subscription(s)")
    req = QueryRequest(
        subscriptions=subscriptions,
        query=VM_IMAGE_QUERY,
        options={"resultFormat": "objectArray"},
    )
    resp = client.resources(req)
    # resp.data is a list[dict] when using objectArray
    rows = list(resp.data) if resp.data else []
    debug(f"Resource Graph returned {len(rows)} row(s)")
    return rows