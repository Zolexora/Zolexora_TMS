import enum

class VehicleBodyType(str, enum.Enum):
    TRUCK = "TRUCK"
    TRAILER = "TRAILER"
    CONTAINER = "CONTAINER"
    TANKER = "TANKER"
    TIPPER = "TIPPER"
    TEMPO = "TEMPO"
    PICKUP = "PICKUP"
    OTHER = "OTHER"

class VehicleOwnershipType(str, enum.Enum):
    OWNED = "OWNED"
    LEASED = "LEASED"
    EMI = "EMI"
    ATTACHED = "ATTACHED"

class FuelType(str, enum.Enum):
    DIESEL = "DIESEL"
    CNG = "CNG"
    ELECTRIC = "ELECTRIC"
    PETROL = "PETROL"

class VehicleOperationalStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ON_DUTY = "ON_DUTY"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"
