import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel


class PnLSummaryResponse(BaseModel):
    organisation_id: str
    start_date: Optional[datetime.date]
    end_date: Optional[datetime.date]
    currency: str = "INR"
    
    total_revenue_gross: Decimal
    total_revenue_net: Decimal  # Excludes taxes collected
    total_taxes_collected: Decimal
    
    total_vendor_driver_payables: Decimal
    total_operational_expenses: Decimal
    total_direct_costs: Decimal
    
    gross_profit: Decimal
    gross_margin_percentage: Decimal
