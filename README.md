# QueueStorm Investigator 🕵️‍♂️

QueueStorm Investigator is an ultra-fast, 100% rule-based classification and evidence-matching engine designed to automate initial ticket triage for financial operations.

Built for the **Codex Community Hackathon - bKash presents SUST CSE Carnival 2026**.

## 🚀 Key Features

- **Blazing Fast (< 1s Response):** Written in pure Python without external LLM dependencies, ensuring sub-second response times and eliminating API rate limits.
- **Transaction Matching Engine:** Automatically parses complex complaint text (including Bangla), extracts monetary values, and scans historical transaction ledgers to accurately identify the specific transaction involved.
- **Evidence Cross-Checking:** Detects fraudulent patterns, such as repeated transfers to the same incorrect recipient, automatically downgrading severity and flagging the ticket as `inconsistent`.
- **Absolute Safety:** Guaranteed 0% chance of prompt injection. Employs pre-cleared, template-driven customer replies and a rigorous post-generation safety filter to ensure credentials (PIN/OTP) are never requested and refunds are never promised.

## 🛠 Tech Stack

- **Framework:** FastAPI (Python 3.11)
- **Validation:** Pydantic
- **Server:** Uvicorn
- **Deployment:** Docker & Render

## 🧠 AI / Models Used

**None.** This solution deliberately avoids heavy LLMs. 
It utilizes a deterministic, heuristic-based pipeline consisting of regex extraction, transaction scoring logic, priority-based classification routing, and keyword matching. This approach guarantees consistent, predictable behavior and absolute safety against prompt injection attacks.

## 🚀 Live Deployment

- **Base URL:** `https://queuestorm-investigator-n61y.onrender.com`
- **Health Check:** `GET /health`
- **API Endpoint:** `POST /analyze-ticket`

## 💻 Local Development

### Running Locally (Python)
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Start the server: `uvicorn main:app --host 0.0.0.0 --port 8000`

### Running with Docker
```bash
docker build -t queuestorm-investigator .
docker run -p 8000:8000 queuestorm-investigator
```

## 📖 API Reference

### 1. Health Check
`GET /health`
Returns system status.
```json
{"status": "ok"}
```

### 2. Analyze Ticket
`POST /analyze-ticket`
Evaluates a customer complaint and its associated transaction history.

**Request Body (JSON)**
See `sample_request.json` for a complete example. The schema requires `ticket_id` and `complaint`. All other fields are optional.

**Response Body (JSON)**
```json
{
  "ticket_id": "TKT-001",
  "relevant_transaction_id": "TXN-9101",
  "evidence_verdict": "consistent",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer claims 5000 BDT sent via TXN-9101 to 017XXXXXXXX was a wrong transfer.",
  "recommended_next_action": "Verify TXN-9101 details and initiate the wrong-transfer dispute workflow per policy.",
  "customer_reply": "We have received your concern about transaction TXN-9101. Our dispute team will review the details carefully and reach out to you through official support channels. Please do not share PIN or OTP with anyone.",
  "human_review_required": true,
  "confidence": 0.88,
  "reason_codes": ["wrong_transfer", "transaction_match"]
}
```

## 🛡 System Architecture

1. **`main.py`**: API routing and Pydantic schema enforcement.
2. **`investigator.py`**: Extracts monetary values and evaluates the ledger. Applies heuristic scoring (amount match +3, type match +2). Checks for `duplicate` payments or `inconsistent` prior behavior.
3. **`classifier.py`**: Priority-based router (phishing checked first). Calculates confidence scores based on evidence. Generates dynamic agent summaries.
4. **`safety.py`**: Populates pre-cleared reply templates. Runs a final safety filter scan to eradicate any phrasing resembling "we will refund" or "enter your PIN".
5. **`keywords.py`**: Centralized lexicons containing English, Bangla, and Banglish transliterations.

## ⚠️ Known Limitations
- **Template Constraints:** Customer replies are constructed from safe templates rather than dynamic generative text.
- **Language Support:** Bangla amount extraction relies on common digit representations; highly informal or mixed Banglish abbreviations may drop the confidence score.
