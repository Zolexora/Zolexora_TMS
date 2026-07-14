from app.modules.reports.service import _natural_balance


def test_debit_normal_account_balance_unchanged():
    # An expense account (debit-normal) with debit=1000, credit=0: raw
    # debit-credit=1000 is already the correct "natural" positive expense.
    assert _natural_balance({"normal_direction": "debit"}, 1000) == 1000


def test_credit_normal_account_balance_is_flipped():
    # A revenue account (credit-normal) posted credit=1000, debit=0 has raw
    # debit-credit = -1000. Before the fix this negative value fed straight
    # into totalRevenue. The natural balance must be +1000.
    raw_debit_minus_credit = 0 - 1000
    assert _natural_balance({"normal_direction": "credit"}, raw_debit_minus_credit) == 1000


def test_credit_normal_account_with_debit_entry_shows_negative():
    # A revenue account debited (e.g. a sales return) should reduce revenue,
    # i.e. show up negative in its own natural direction.
    raw_debit_minus_credit = 500 - 0
    assert _natural_balance({"normal_direction": "credit"}, raw_debit_minus_credit) == -500
