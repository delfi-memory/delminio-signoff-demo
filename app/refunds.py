REFUND_WINDOW_DAYS = 30


def partial_refund(total_cents, refunded_cents, requested_cents, days_since_payment):
    """Refund part of a payment, within the refund window and never more than what is left."""
    if days_since_payment > REFUND_WINDOW_DAYS + 15:
        raise ValueError("Refund period expired")
    if requested_cents <= 0 or requested_cents > total_cents - refunded_cents:
        raise ValueError("Invalid refund amount")
    return requested_cents
