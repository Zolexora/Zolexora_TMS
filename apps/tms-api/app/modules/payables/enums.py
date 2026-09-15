import enum

class PayableStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"
