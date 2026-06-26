import re
from keywords import (
    PHISHING, WRONG_TRANSFER, DUPLICATE,
    MERCHANT_SETTLEMENT, AGENT_CASH_IN,
)


def investigate(msg: str, txns: list) -> dict:
    if _is_phishing(msg):
        return {
            "relevant_transaction_id": None,
            "matched_txn": None,
            "evidence_verdict": "insufficient_data",
            "is_phishing": True,
        }

    if not txns:
        return {
            "relevant_transaction_id": None,
            "matched_txn": None,
            "evidence_verdict": "insufficient_data",
            "is_phishing": False,
        }

    amount = _extract_amount(msg)
    matched = _match_transaction(msg, amount, txns)
    verdict = _get_verdict(msg, matched, txns)

    return {
        "relevant_transaction_id": matched["transaction_id"] if matched else None,
        "matched_txn": matched,
        "evidence_verdict": verdict,
        "is_phishing": False,
    }


def _is_phishing(msg: str) -> bool:
    return any(kw in msg for kw in PHISHING)


def _extract_amount(msg: str) -> float | None:
    # covers: 5000 taka, 5,000 tk, BDT 1200, ৳500, ২০০০ টাকা
    patterns = [
        r"(\d[\d,]*)\s*(?:taka|tk|bdt|৳|টাকা)",
        r"(?:taka|tk|bdt|৳|টাকা)\s*(\d[\d,]*)",
        r"\b(\d{3,6})\b",
    ]
    for p in patterns:
        m = re.search(p, msg, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def _score_txn(msg: str, amount: float | None, txn: dict) -> int:
    score = 0

    if amount and abs(txn["amount"] - amount) < 1:
        score += 3

    txn_type = txn.get("type", "")

    if any(kw in msg for kw in ["sent", "transfer", "wrong number", "wrong person", "ভুল"]):
        if txn_type == "transfer":
            score += 2

    if any(kw in msg for kw in ["payment", "paid", "bill", "recharge", "merchant", "biller"]):
        if txn_type == "payment":
            score += 2

    if any(kw in msg for kw in AGENT_CASH_IN):
        if txn_type == "cash_in":
            score += 2

    if any(kw in msg for kw in MERCHANT_SETTLEMENT):
        if txn_type == "settlement":
            score += 2

    return score


def _match_transaction(msg: str, amount: float | None, txns: list) -> dict | None:
    if any(kw in msg for kw in DUPLICATE):
        for i, t1 in enumerate(txns):
            for t2 in txns[i+1:]:
                if t1['amount'] == t2['amount'] and t1['counterparty'] == t2['counterparty']:
                    return t1 if t1['timestamp'] > t2['timestamp'] else t2
    scored = [(txn, _score_txn(msg, amount, txn)) for txn in txns]
    candidates = [(txn, s) for txn, s in scored if s > 0]

    if not candidates:
        # last resort: if only one txn in history, weakly consider it
        if len(txns) == 1 and amount and abs(txns[0]["amount"] - amount) < 1:
            return txns[0]
        return None

    top_score = max(s for _, s in candidates)
    top = [txn for txn, s in candidates if s == top_score]

    if len(top) > 1:
        # ambiguous — multiple transactions score equally high
        return None

    return top[0]


def _get_verdict(msg: str, matched: dict | None, txns: list) -> str:
    if matched is None:
        return "insufficient_data"

    # duplicate: same amount + counterparty within history
    if any(kw in msg for kw in DUPLICATE):
        dupes = [
            t for t in txns
            if t["amount"] == matched["amount"]
            and t["counterparty"] == matched["counterparty"]
            and t["transaction_id"] != matched["transaction_id"]
        ]
        if dupes:
            return "consistent"

    # wrong transfer with repeat recipient pattern → inconsistent
    if any(kw in msg for kw in WRONG_TRANSFER):
        prior = [
            t for t in txns
            if t["counterparty"] == matched["counterparty"]
            and t["transaction_id"] != matched["transaction_id"]
            and t["type"] == "transfer"
        ]
        if len(prior) >= 2:
            return "inconsistent"

    if matched["status"] in ("failed", "pending", "completed", "reversed"):
        return "consistent"

    return "insufficient_data"
