def partial_refund(total_cents, refunded_cents, requested_cents, days_since_payment):
    if days_since_payment > 30:
        raise ValueError("Refund period expired")
    if requested_cents <= 0 or requested_cents > total_cents - refunded_cents:
        raise ValueError("Invalid refund amount")
    return requested_cents
