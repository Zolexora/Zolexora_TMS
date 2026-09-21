import enum

class ExpenseCategory(str, enum.Enum):
    FUEL = "FUEL"
    TOLL = "TOLL"
    PARKING = "PARKING"
    MAINTENANCE = "MAINTENANCE"
    DRIVER_ALLOWANCE = "DRIVER_ALLOWANCE"
    FOOD = "FOOD"
    MISCELLANEOUS = "MISCELLANEOUS"
