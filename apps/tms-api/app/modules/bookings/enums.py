import enum

class BookingRequestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REQUESTED = "REQUESTED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class BookingStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class BookingType(str, enum.Enum):
    ETS = "ETS"
    SPOT = "SPOT"
    FIXED = "FIXED"
    RENTAL = "RENTAL"
    AIRPORT = "AIRPORT"
    LOCAL = "LOCAL"
    OUTSTATION = "OUTSTATION"
    CORPORATE = "CORPORATE"
    CONTRACT = "CONTRACT"
    RECURRING = "RECURRING"

class BookingServiceType(str, enum.Enum):
    PASSENGER = "PASSENGER"
    CARGO = "CARGO"
