import enum

class PaymentStatus(str, enum.Enum):
    INITIATED = "INITIATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    REVERSED = "REVERSED"
