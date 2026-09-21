import enum

class VendorType(str, enum.Enum):
    FLEET_SUPPLIER = "FLEET_SUPPLIER"
    DCO = "DCO"  # Driver Cum Owner
    EMI_DRIVER = "EMI_DRIVER"
    WORKSHOP = "WORKSHOP"
    FUEL_PARTNER = "FUEL_PARTNER"
    BROKER = "BROKER"
    OTHER = "OTHER"

class VendorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
