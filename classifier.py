from keywords import (
    PHISHING, WRONG_TRANSFER, PAYMENT_FAILED,
    REFUND, DUPLICATE, MERCHANT_SETTLEMENT, AGENT_CASH_IN,
)

DEPARTMENT_MAP = {
    "wrong_transfer": "dispute_resolution",
    "payment_failed": "payments_ops",
    "refund_request": "customer_support",
    "duplicate_payment": "payments_ops",
    "merchant_settlement_delay": "merchant_operations",
    "agent_cash_in_issue": "agent_operations",
    "phishing_or_social_engineering": "fraud_risk",
    "other": "customer_support",
}

SEVERITY_BASE = {
    "phishing_or_social_engineering": "critical",
    "wrong_transfer": "high",
    "payment_failed": "high",
    "duplicate_payment": "high",
    "agent_cash_in_issue": "high",
    "merchant_settlement_delay": "medium",
    "refund_request": "low",
    "other": "low",
}

CONFIDENCE_BASE = {
    "phishing_or_social_engineering": 0.95,
    "wrong_transfer": 0.88,
    "payment_failed": 0.90,
    "duplicate_payment": 0.93,
    "agent_cash_in_issue": 0.88,
    "merchant_settlement_delay": 0.92,
    "refund_request": 0.85,
    "other": 0.60,
}


def classify(msg: str, inv: dict, user_type: str) -> dict:
    case_type = _get_case_type(msg, inv, user_type)
    verdict = inv["evidence_verdict"]

    severity = SEVERITY_BASE[case_type]
    if verdict == "inconsistent" and severity == "high":
        severity = "medium"

    txn = inv.get("matched_txn")

    return {
        "case_type": case_type,
        "severity": severity,
        "department": DEPARTMENT_MAP[case_type],
        "human_review_required": _needs_review(case_type, verdict),
        "confidence": _confidence(case_type, verdict),
        "reason_codes": _reason_codes(case_type, verdict, txn),
        "agent_summary": _agent_summary(case_type, txn, verdict),
        "recommended_next_action": _next_action(case_type, txn, verdict),
    }


def _get_case_type(msg: str, inv: dict, user_type: str) -> str:
    # priority order matters — phishing first, always
    if inv.get("is_phishing"):
        return "phishing_or_social_engineering"

    if any(kw in msg for kw in DUPLICATE):
        return "duplicate_payment"

    if user_type == "merchant" or any(kw in msg for kw in MERCHANT_SETTLEMENT):
        return "merchant_settlement_delay"

    if any(kw in msg for kw in AGENT_CASH_IN):
        return "agent_cash_in_issue"

    if any(kw in msg for kw in WRONG_TRANSFER):
        return "wrong_transfer"

    if any(kw in msg for kw in PAYMENT_FAILED):
        return "payment_failed"

    if any(kw in msg for kw in REFUND):
        return "refund_request"

    return "other"


def _needs_review(case_type: str, verdict: str) -> bool:
    if case_type in ("phishing_or_social_engineering", "wrong_transfer",
                     "agent_cash_in_issue", "duplicate_payment"):
        return True
    if verdict == "inconsistent":
        return True
    return False


def _confidence(case_type: str, verdict: str) -> float:
    base = CONFIDENCE_BASE.get(case_type, 0.70)
    if verdict == "inconsistent":
        return round(base - 0.13, 2)
    if verdict == "insufficient_data":
        return round(base - 0.25, 2)
    return base


def _reason_codes(case_type: str, verdict: str, txn: dict | None) -> list:
    codes = [case_type]
    if txn:
        codes.append("transaction_match")
    if verdict == "inconsistent":
        codes.append("evidence_inconsistent")
    if verdict == "insufficient_data":
        codes.append("needs_clarification")
    return codes


def _agent_summary(case_type: str, txn: dict | None, verdict: str) -> str:
    tid = txn["transaction_id"] if txn else None
    amt = int(txn["amount"]) if txn else None
    cp = txn["counterparty"] if txn else None
    status = txn["status"] if txn else None

    if case_type == "phishing_or_social_engineering":
        return (
            "Customer reports a suspicious contact asking for credentials. "
            "Possible social engineering attempt. No credentials confirmed shared."
        )

    if case_type == "wrong_transfer":
        if tid:
            base = f"Customer claims {amt} BDT sent via {tid} to {cp} was a wrong transfer."
            if verdict == "inconsistent":
                base += " History shows repeated prior transfers to the same recipient — inconsistent with the claim."
            return base
        return "Customer claims a wrong transfer but no matching transaction identified in history."

    if case_type == "payment_failed":
        if tid:
            return f"Customer reports {amt} BDT payment ({tid}) failed with a possible balance deduction. Status: {status}."
        return "Customer reports a failed payment with possible balance deduction. No matching transaction identified."

    if case_type == "duplicate_payment":
        if tid:
            return f"Suspected duplicate payment detected. {tid} ({amt} BDT to {cp}) appears to be a second charge within a short window."
        return "Customer reports a duplicate charge. No transaction pair matched from history."

    if case_type == "merchant_settlement_delay":
        if tid:
            return f"Merchant reports settlement {tid} ({amt} BDT) is delayed beyond the expected window. Status: {status}."
        return "Merchant reports a settlement delay. No matching settlement transaction identified."

    if case_type == "agent_cash_in_issue":
        if tid:
            return f"Customer reports {amt} BDT cash-in via {cp} ({tid}) not reflected in account balance. Status: {status}."
        return "Customer reports a cash-in via agent not reflected in balance. No matching transaction identified."

    if case_type == "refund_request":
        if tid:
            return f"Customer requests refund for {tid} ({amt} BDT to {cp}). Not a service failure — change of mind or policy dispute."
        return "Customer requests a refund for a completed transaction. No specific transaction identified."

    # other
    return "Customer submitted a general or vague complaint without sufficient detail to classify."


def _next_action(case_type: str, txn: dict | None, verdict: str) -> str:
    tid = txn["transaction_id"] if txn else None

    if case_type == "phishing_or_social_engineering":
        return (
            "Escalate to fraud_risk team immediately. Log the reported contact details. "
            "Confirm to customer that the platform never requests credentials under any circumstances."
        )

    if case_type == "wrong_transfer":
        if tid:
            action = f"Verify {tid} details and initiate the wrong-transfer dispute workflow per policy."
            if verdict == "inconsistent":
                action += " Flag the repeated recipient pattern — verify with the customer before proceeding."
            return action
        return "Ask customer for transaction ID and recipient number to identify the transfer before initiating dispute."

    if case_type == "payment_failed":
        if tid:
            return f"Investigate {tid} ledger status. If balance was deducted on a failed payment, initiate the automatic reversal flow within standard SLA."
        return "Ask customer for approximate time and amount to locate the failed payment transaction."

    if case_type == "duplicate_payment":
        if tid:
            return f"Verify suspected duplicate {tid} with payments_ops. If biller confirms single receipt, initiate reversal of the duplicate charge."
        return "Locate the duplicate payment pair in the ledger and route to payments_ops for verification."

    if case_type == "merchant_settlement_delay":
        if tid:
            return f"Route {tid} to merchant_operations to check batch settlement status. Communicate a revised ETA to the merchant if the batch is delayed."
        return "Route to merchant_operations to investigate the settlement batch for this merchant."

    if case_type == "agent_cash_in_issue":
        if tid:
            return f"Investigate {tid} pending status with agent_operations. Confirm settlement state and resolve within the standard cash-in SLA."
        return "Ask customer for agent ID and time of deposit to locate the transaction and route to agent_operations."

    if case_type == "refund_request":
        return (
            "Inform customer that refund eligibility depends on the merchant's own refund policy. "
            "Guide customer to contact the merchant directly for resolution."
        )

    # other
    return "Reply to customer requesting specific details: transaction ID, amount involved, what went wrong, and approximate time."
