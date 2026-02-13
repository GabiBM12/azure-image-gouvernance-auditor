from azimg_auditor.pipeline.step1_inventory import _classify_image

def test_marketplace_classification():
    ref = {"publisher": "Canonical", "offer": "0001-com-ubuntu-server-jammy", "sku": "22_04-lts", "version": "latest"}
    c = _classify_image(ref)
    assert c["imageType"] == "marketplace"

def test_gallery_classification():
    ref = {"id": "/subscriptions/x/resourceGroups/rg/providers/Microsoft.Compute/galleries/g/imgDefs/d/versions/1.0.0"}
    c = _classify_image(ref)
    assert c["imageType"] == "compute_gallery"

def test_managed_image_classification():
    ref = {"id": "/subscriptions/x/resourceGroups/rg/providers/Microsoft.Compute/images/myImage"}
    c = _classify_image(ref)
    assert c["imageType"] == "managed_image"