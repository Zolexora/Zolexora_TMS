import enum

class ComplianceCategory(str, enum.Enum):
    STATUTORY = "STATUTORY"
    CONTRACTUAL = "CONTRACTUAL"
    INTERNAL = "INTERNAL"
    SAFETY = "SAFETY"

class ComplianceEntityType(str, enum.Enum):
    ORGANISATION = "ORGANISATION"
    VEHICLE = "VEHICLE"
    DRIVER = "DRIVER"
    VENDOR = "VENDOR"
    CUSTOMER = "CUSTOMER"
    SERVICE = "SERVICE"
    ROUTE = "ROUTE"
    DUTY = "DUTY"

class ComplianceStatus(str, enum.Enum):
    MISSING = "MISSING"
    PENDING = "PENDING"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    VALID = "VALID"
    EXPIRING_SOON = "EXPIRING_SOON"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    WAIVED = "WAIVED"

class ComplianceVerificationAction(str, enum.Enum):
    VERIFY = "VERIFY"
    REJECT = "REJECT"
    WAIVE = "WAIVE"
