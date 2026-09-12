# Just a placeholder to ensure pytest doesn't break
def test_dco_enum_exists():
    from app.modules.vendors.models import VendorType
    assert VendorType.DCO == "DCO"
    assert VendorType.EMI_DRIVER == "EMI_DRIVER"
