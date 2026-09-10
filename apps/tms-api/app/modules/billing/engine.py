import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.modules.bookings.models import Booking
from app.modules.duties.models import Duty
from app.modules.trips.models import Trip
from app.modules.billing.models import (
    RateCardVersion, RateCardRule, RateRuleType,
    FinancialSnapshot, FinancialSnapshotLine
)

class FinancialEngine:
    @staticmethod
    def _round(value: Decimal) -> Decimal:
        """Central rounding policy: round to 2 decimal places using HALF_UP."""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def extract_operational_facts(duty: Duty, trip: Trip | None) -> Dict[str, Any]:
        """Extract deterministic operational facts from a completed duty/trip."""
        facts = {
            "duty_id": str(duty.id),
            "trip_id": str(trip.id) if trip else None,
            "distance_km": Decimal("0.0"),
            "duration_hours": Decimal("0.0"),
            "waiting_minutes": Decimal("0.0"),
            "toll_amount": Decimal("0.0"),
            "parking_amount": Decimal("0.0"),
            "fuel_amount": Decimal("0.0"),
        }
        
        if trip:
            if trip.total_distance_km is not None:
                facts["distance_km"] = Decimal(str(trip.total_distance_km))
            elif trip.start_odometer is not None and trip.end_odometer is not None:
                facts["distance_km"] = Decimal(str(trip.end_odometer - trip.start_odometer))
            
            if trip.start_timestamp and trip.end_timestamp:
                delta = trip.end_timestamp - trip.start_timestamp
                facts["duration_hours"] = Decimal(str(delta.total_seconds() / 3600))
                
            facts["waiting_minutes"] = Decimal(str(trip.waiting_minutes))
            facts["toll_amount"] = Decimal(str(trip.toll_amount))
            facts["parking_amount"] = Decimal(str(trip.parking_amount))
            facts["fuel_amount"] = Decimal(str(trip.fuel_amount))
            
        return facts

    @classmethod
    def evaluate_rule(cls, rule: RateCardRule, facts: Dict[str, Any], current_subtotal: Decimal, current_taxable: Decimal) -> Tuple[Decimal, Decimal, str]:
        """
        Evaluates a single rule and returns (amount, quantity, unit_str).
        """
        amount = Decimal("0.0")
        qty = Decimal("1.0")
        unit = "Fixed"
        
        rule_type = rule.rule_type
        
        if rule_type == RateRuleType.FIXED_TRIP:
            amount = rule.base_amount
            qty = Decimal("1.0")
            unit = "Trip"
            
        elif rule_type == RateRuleType.PER_KM:
            distance = facts["distance_km"]
            # Apply included quantity logic
            chargeable_dist = max(Decimal("0.0"), distance - rule.quantity_included)
            amount = rule.base_amount + (chargeable_dist * rule.rate_per_unit)
            qty = distance
            unit = "KM"
            
        elif rule_type == RateRuleType.EXTRA_KM:
            distance = facts["distance_km"]
            if distance > rule.quantity_included:
                chargeable = distance - rule.quantity_included
                amount = chargeable * rule.rate_per_unit
                qty = chargeable
                unit = "KM"
            else:
                qty = Decimal("0.0")
                
        elif rule_type == RateRuleType.PER_HOUR:
            hours = facts["duration_hours"]
            chargeable_hours = max(Decimal("0.0"), hours - rule.quantity_included)
            amount = rule.base_amount + (chargeable_hours * rule.rate_per_unit)
            qty = hours
            unit = "Hour"
            
        elif rule_type == RateRuleType.EXTRA_HOUR:
            hours = facts["duration_hours"]
            if hours > rule.quantity_included:
                chargeable = hours - rule.quantity_included
                amount = chargeable * rule.rate_per_unit
                qty = chargeable
                unit = "Hour"
            else:
                qty = Decimal("0.0")
                
        elif rule_type == RateRuleType.WAITING_CHARGE:
            # Assuming rate_per_unit is per hour. waiting is in minutes.
            wait_hours = facts["waiting_minutes"] / Decimal("60.0")
            chargeable_wait = max(Decimal("0.0"), wait_hours - rule.quantity_included)
            amount = chargeable_wait * rule.rate_per_unit
            qty = wait_hours
            unit = "Hour"
            
        elif rule_type == RateRuleType.TOLL:
            # Pass-through or fixed
            amount = facts["toll_amount"] if facts["toll_amount"] > 0 else rule.base_amount
            qty = Decimal("1.0")
            unit = "Fixed"
            
        elif rule_type == RateRuleType.PARKING:
            amount = facts["parking_amount"] if facts["parking_amount"] > 0 else rule.base_amount
            qty = Decimal("1.0")
            unit = "Fixed"
            
        elif rule_type in [RateRuleType.PERCENTAGE_SURCHARGE]:
            amount = current_subtotal * (rule.percentage_value / Decimal("100.0"))
            qty = rule.percentage_value
            unit = "%"
            
        elif rule_type in [RateRuleType.PERCENTAGE_DISCOUNT]:
            amount = current_subtotal * (rule.percentage_value / Decimal("100.0"))
            qty = rule.percentage_value
            unit = "%"
            
        elif rule_type in [RateRuleType.TAX_CGST, RateRuleType.TAX_SGST, RateRuleType.TAX_IGST]:
            amount = current_taxable * (rule.percentage_value / Decimal("100.0"))
            qty = rule.percentage_value
            unit = "%"
            
        else:
            # Default fallback for custom or unhandled types
            if rule.is_percentage:
                amount = current_subtotal * (rule.percentage_value / Decimal("100.0"))
                qty = rule.percentage_value
                unit = "%"
            else:
                amount = rule.base_amount
                qty = Decimal("1.0")
                unit = "Fixed"
                
        return cls._round(amount), cls._round(qty), unit

    @classmethod
    async def calculate_snapshot(
        cls, 
        db: AsyncSession, 
        duty: Duty, 
        trip: Trip | None, 
        rate_card_version: RateCardVersion,
        user_id: uuid.UUID | None = None
    ) -> FinancialSnapshot:
        """
        Evaluate a duty against a rate card version to produce a deterministic FinancialSnapshot.
        """
        facts = cls.extract_operational_facts(duty, trip)
        
        # Lock in rules ordered by sequence
        rules = sorted(rate_card_version.rules, key=lambda r: r.sequence)
        
        snapshot = FinancialSnapshot(
            organisation_id=duty.organisation_id,
            booking_id=duty.booking_id,
            duty_id=duty.id,
            trip_id=trip.id if trip else None,
            rate_card_version_id=rate_card_version.id,
            operational_inputs=facts,
            currency="INR", # Could be inherited from rate card
            is_finalized=False,
            created_by_user_id=user_id
        )
        
        current_subtotal = Decimal("0.0")
        current_taxable = Decimal("0.0")
        total_discount = Decimal("0.0")
        total_surcharge = Decimal("0.0")
        total_tax = Decimal("0.0")
        
        lines: List[FinancialSnapshotLine] = []
        
        for rule in rules:
            amount, qty, unit = cls.evaluate_rule(rule, facts, current_subtotal, current_taxable)
            
            if qty == Decimal("0.0") and amount == Decimal("0.0"):
                continue # Skip non-applicable rules
                
            line = FinancialSnapshotLine(
                rule_id=rule.id,
                description=rule.name,
                rule_type=rule.rule_type,
                quantity=qty,
                unit=unit,
                unit_rate=rule.rate_per_unit if rule.rule_type not in [
                    RateRuleType.PERCENTAGE_DISCOUNT, RateRuleType.PERCENTAGE_SURCHARGE, 
                    RateRuleType.TAX_CGST, RateRuleType.TAX_SGST, RateRuleType.TAX_IGST
                ] else rule.percentage_value,
                amount=amount,
                is_tax=False
            )
            
            if rule.rule_type == RateRuleType.PERCENTAGE_DISCOUNT:
                total_discount += amount
                # Discounts usually reduce taxable amount but maybe not subtotal depending on accounting
                # We'll subtract from taxable here for typical behavior
                current_taxable -= amount
            elif rule.rule_type in [RateRuleType.TAX_CGST, RateRuleType.TAX_SGST, RateRuleType.TAX_IGST]:
                total_tax += amount
                line.is_tax = True
            else:
                if rule.rule_type == RateRuleType.PERCENTAGE_SURCHARGE:
                    total_surcharge += amount
                else:
                    current_subtotal += amount
                current_taxable += amount
                
            lines.append(line)
            
        snapshot.subtotal = current_subtotal
        snapshot.discount_amount = total_discount
        snapshot.surcharge_amount = total_surcharge
        snapshot.taxable_amount = current_taxable
        snapshot.tax_amount = total_tax
        snapshot.grand_total = current_subtotal + total_surcharge - total_discount + total_tax
        
        # Assign lines
        snapshot.lines = lines
        
        db.add(snapshot)
        await db.flush()
        
        return snapshot
