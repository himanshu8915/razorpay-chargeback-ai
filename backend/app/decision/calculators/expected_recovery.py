from decimal import Decimal

def calculate_recoverable_amount(dispute_amount: float) -> Decimal:
    """
    For the current Phase 5 MVO:
    Recoverable Amount = Total Dispute Amount.
    """
    return Decimal(str(dispute_amount))

def calculate_expected_recovery(success_likelihood: float, recoverable_amount: Decimal) -> Decimal:
    """
    Expected Recovery = P(Win) × Recoverable Amount
    """
    p_win = Decimal(str(success_likelihood))
    expected = p_win * recoverable_amount
    return expected.quantize(Decimal("0.01"))

def calculate_net_expected_value(expected_recovery: Decimal, operational_cost: Decimal) -> Decimal:
    """
    NEV = Expected Recovery - Operational Cost
    """
    nev = expected_recovery - operational_cost
    return nev.quantize(Decimal("0.01"))
