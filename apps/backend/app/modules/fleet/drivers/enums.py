import enum

class DriverType(str, enum.Enum):
    PERMANENT = "PERMANENT"
    CONTRACT = "CONTRACT"
    MARKET = "MARKET"

class DriverStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ON_DUTY = "ON_DUTY"
    ON_LEAVE = "ON_LEAVE"
    INACTIVE = "INACTIVE"
