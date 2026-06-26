from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from investigator import investigate
from classifier import classify
from safety import build_reply

app = FastAPI(title="QueueStorm Investigator", version="1.0.0")


class TxnEntry(BaseModel):
    transaction_id: str
    timestamp: str
    type: str
    amount: float
    counterparty: str
    status: str


class TicketRequest(BaseModel):
    ticket_id: str
    complaint: str
    language: Optional[str] = "en"
    channel: Optional[str] = None
    user_type: Optional[str] = "customer"
    campaign_context: Optional[str] = None
    transaction_history: Optional[list[TxnEntry]] = []
    metadata: Optional[dict] = None


class TicketResponse(BaseModel):
    ticket_id: str
    relevant_transaction_id: Optional[str]
    evidence_verdict: str
    case_type: str
    severity: str
    department: str
    agent_summary: str
    recommended_next_action: str
    customer_reply: str
    human_review_required: bool
    confidence: float
    reason_codes: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze-ticket", response_model=TicketResponse)
def analyze_ticket(ticket: TicketRequest):
    if not ticket.complaint or not ticket.complaint.strip():
        return JSONResponse(status_code=422, content={"error": "complaint cannot be empty"})

    msg = ticket.complaint.lower()
    txns = [t.model_dump() for t in (ticket.transaction_history or [])]
    lang = ticket.language or "en"
    user_type = ticket.user_type or "customer"

    inv = investigate(msg, txns)
    cls = classify(msg, inv, user_type)
    reply = build_reply(cls["case_type"], inv.get("matched_txn"), lang, ticket.ticket_id)

    return TicketResponse(
        ticket_id=ticket.ticket_id,
        relevant_transaction_id=inv["relevant_transaction_id"],
        evidence_verdict=inv["evidence_verdict"],
        case_type=cls["case_type"],
        severity=cls["severity"],
        department=cls["department"],
        agent_summary=cls["agent_summary"],
        recommended_next_action=cls["recommended_next_action"],
        customer_reply=reply,
        human_review_required=cls["human_review_required"],
        confidence=cls["confidence"],
        reason_codes=cls["reason_codes"],
    )


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "internal server error"})
