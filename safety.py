PIN_REMINDER = "Please do not share PIN or OTP with anyone."
PIN_REMINDER_BN = "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
SAFE_REFUND = "any eligible amount will be returned through official channels"

# anything that would trigger the -15 or -10 penalty
_FORBIDDEN = [
    "PIN", "your otp", "your password", "share your otp",
    "share PIN", "enter PIN", "enter your otp",
    "provide your otp", "provide PIN", "send your otp",
    "we will refund you", "we will refund", "you will be refunded",
    "we will reverse", "we will credit", "we guarantee your refund",
    "account will be unblocked", "we will unblock",
    "your money will be returned", "we will return your money",
    "contact this number", "call this number", "visit this link",
    "go to this website",
]


def build_reply(case_type: str, txn: dict | None, lang: str, ticket_id: str) -> str:
    tid = txn["transaction_id"] if txn else None
    is_bn = lang == "bn"
    reply = _template(case_type, tid, is_bn)
    return _safety_filter(reply)


def _template(case_type: str, tid: str | None, is_bn: bool) -> str:
    t = tid or "your recent transaction"

    if case_type == "phishing_or_social_engineering":
        return (
            "Thank you for reaching out before sharing any information. "
            "We never ask for PIN, OTP, or password under any circumstances. "
            "Please do not share these with anyone, even if they claim to be from us. "
            "Our fraud team has been notified of this incident."
        )

    if case_type == "wrong_transfer":
        return (
            f"We have received your concern about transaction {t}. "
            "Our dispute team will review the details carefully and reach out to you through official support channels. "
            f"{PIN_REMINDER}"
        )

    if case_type == "payment_failed":
        return (
            f"We have noted that transaction {t} may have caused an unexpected balance deduction. "
            f"Our payments team will investigate and {SAFE_REFUND}. "
            f"{PIN_REMINDER}"
        )

    if case_type == "duplicate_payment":
        return (
            f"We have noted the possible duplicate charge related to transaction {t}. "
            f"Our payments team will verify this with the biller and {SAFE_REFUND}. "
            f"{PIN_REMINDER}"
        )

    if case_type == "refund_request":
        return (
            "Thank you for reaching out. Refunds for completed payments depend on the merchant's own refund policy. "
            "We recommend contacting the merchant directly. "
            "If you need help reaching them, please reply and we will assist you. "
            f"{PIN_REMINDER}"
        )

    if case_type == "merchant_settlement_delay":
        return (
            f"We have noted your concern about settlement {t}. "
            "Our merchant operations team will check the batch status and update you on the expected settlement time through official channels."
        )

    if case_type == "agent_cash_in_issue":
        if is_bn:
            return (
                f"আপনার লেনদেন {t} এর বিষয়ে আমরা অবগত হয়েছি। "
                "আমাদের এজেন্ট অপারেশন্স দল এটি দ্রুত যাচাই করবে এবং অফিসিয়াল চ্যানেলে আপনাকে জানাবে। "
                f"{PIN_REMINDER_BN}"
            )
        return (
            f"We have noted your concern about cash-in transaction {t}. "
            "Our agent operations team will verify the settlement status and update you through official channels. "
            f"{PIN_REMINDER}"
        )

    # other / fallback
    return (
        "Thank you for reaching out. To help you faster, please share the transaction ID, "
        "the amount involved, and a short description of what went wrong. "
        f"{PIN_REMINDER}"
    )


def _safety_filter(reply: str) -> str:
    lower = reply.lower()
    for phrase in _FORBIDDEN:
        if phrase in lower:
            # swap out the unsafe phrase with the approved safe language
            idx = lower.find(phrase)
            reply = reply[:idx] + SAFE_REFUND + reply[idx + len(phrase):]
            lower = reply.lower()
    return reply
