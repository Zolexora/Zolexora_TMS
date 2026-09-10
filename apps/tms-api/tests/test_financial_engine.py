import uuid
import pytest
from decimal import Decimal
from app.modules.billing.engine import FinancialEngine
from app.modules.billing.models import RateCardRule, RateRuleType
from app.modules.duties.models import Duty
from app.modules.trips.models import Trip


def test_financial_engine_rounding():
    # Verify half-up rounding to 2 decimals
    assert FinancialEngine._round(Decimal("10.123")) == Decimal("10.12")
    assert FinancialEngine._round(Decimal("10.125")) == Decimal("10.13")
    assert FinancialEngine._round(Decimal("10.126")) == Decimal("10.13")
    
def test_extract_operational_facts():
    duty = Duty(id=uuid.uuid4())
    trip = Trip(
        id=uuid.uuid4(),
        duty_id=duty.id,
        start_odometer=Decimal("100.5"),
        end_odometer=Decimal("150.5"), # 50 km
        waiting_minutes=30,
        toll_amount=Decimal("100.00"),
        parking_amount=Decimal("50.00"),
        fuel_amount=Decimal("0.00"),
    )
    
    facts = FinancialEngine.extract_operational_facts(duty, trip)
    assert facts["distance_km"] == Decimal("50.0")
    assert facts["waiting_minutes"] == Decimal("30.0")
    assert facts["toll_amount"] == Decimal("100.0")
    assert facts["parking_amount"] == Decimal("50.0")


def test_evaluate_fixed_trip():
    rule = RateCardRule(
        rule_type=RateRuleType.FIXED_TRIP,
        base_amount=Decimal("1500.00")
    )
    facts = {"distance_km": Decimal("100.0"), "duration_hours": Decimal("5.0")}
    
    amount, qty, unit = FinancialEngine.evaluate_rule(rule, facts, Decimal("0"), Decimal("0"))
    
    assert amount == Decimal("1500.00")
    assert qty == Decimal("1.00")
    assert unit == "Trip"


def test_evaluate_per_km():
    # Base 500 includes 20km, rate 15 per extra km
    rule = RateCardRule(
        rule_type=RateRuleType.PER_KM,
        base_amount=Decimal("500.00"),
        quantity_included=Decimal("20.0"),
        rate_per_unit=Decimal("15.00")
    )
    
    # Under included limit (15km)
    facts1 = {"distance_km": Decimal("15.0")}
    amount1, qty1, unit1 = FinancialEngine.evaluate_rule(rule, facts1, Decimal("0"), Decimal("0"))
    assert amount1 == Decimal("500.00")
    
    # Over included limit (30km -> 10 extra km = 150)
    facts2 = {"distance_km": Decimal("30.0")}
    amount2, qty2, unit2 = FinancialEngine.evaluate_rule(rule, facts2, Decimal("0"), Decimal("0"))
    assert amount2 == Decimal("650.00")
    assert qty2 == Decimal("30.00")


def test_evaluate_extra_km():
    rule = RateCardRule(
        rule_type=RateRuleType.EXTRA_KM,
        quantity_included=Decimal("80.0"),
        rate_per_unit=Decimal("12.00")
    )
    
    # Under limit
    facts1 = {"distance_km": Decimal("50.0")}
    amount1, qty1, unit1 = FinancialEngine.evaluate_rule(rule, facts1, Decimal("0"), Decimal("0"))
    assert amount1 == Decimal("0.00")
    assert qty1 == Decimal("0.00")
    
    # Over limit (100km -> 20 extra km = 240)
    facts2 = {"distance_km": Decimal("100.0")}
    amount2, qty2, unit2 = FinancialEngine.evaluate_rule(rule, facts2, Decimal("0"), Decimal("0"))
    assert amount2 == Decimal("240.00")
    assert qty2 == Decimal("20.00")


def test_evaluate_taxes_and_surcharges():
    rule_surcharge = RateCardRule(
        rule_type=RateRuleType.PERCENTAGE_SURCHARGE,
        percentage_value=Decimal("10.0")
    )
    rule_tax = RateCardRule(
        rule_type=RateRuleType.TAX_CGST,
        percentage_value=Decimal("9.0")
    )
    
    current_subtotal = Decimal("1000.00")
    current_taxable = Decimal("1100.00") # Assuming surcharge is taxable
    
    amount_s, qty_s, unit_s = FinancialEngine.evaluate_rule(rule_surcharge, {}, current_subtotal, current_taxable)
    assert amount_s == Decimal("100.00")
    
    amount_t, qty_t, unit_t = FinancialEngine.evaluate_rule(rule_tax, {}, current_subtotal, current_taxable)
    assert amount_t == Decimal("99.00") # 9% of 1100
