import enum

class TripStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
