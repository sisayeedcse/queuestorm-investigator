# QueueStorm Investigator: Operations Runbook

This document is intended for evaluators and operators interacting with the QueueStorm Investigator API.

## 1. System Overview
The Investigator API acts as a pre-processing firewall for incoming customer support tickets. It reads the raw complaint and the attached JSON transaction ledger, scores the transactions to find a match, evaluates the user's intent, and routes the ticket to the appropriate operational department.

## 2. API Flow & Validation
All traffic must hit the `POST /analyze-ticket` endpoint.
- If the `complaint` field is missing or empty, the API instantly rejects the payload with HTTP 422.
- The `transaction_history` is optional but heavily impacts the engine's `confidence` score and `evidence_verdict`.

## 3. Investigating Evidence Verdicts
When reviewing output, pay close attention to the `evidence_verdict`:
- **`consistent`**: The complaint aligns perfectly with a transaction in the history (e.g., matching amounts).
- **`inconsistent`**: The system detected a contradiction or a risky pattern (e.g., claiming a wrong transfer to an account they have successfully transferred to multiple times in the past week). The system will automatically downgrade the severity and require human review.
- **`insufficient_data`**: The system could not find a clear match (e.g., multiple identical transactions occurred on the same day and no amount was specified). The system will intentionally output a `null` relevant transaction rather than guessing blindly.

## 4. Handling Phishing Alerts
If the `case_type` is identified as `phishing_or_social_engineering`:
- The engine immediately short-circuits.
- `severity` is permanently locked to `critical`.
- It ignores the transaction history entirely to focus on account security.
- The `customer_reply` template heavily prioritizes warning the user to stop interacting with the attacker.

## 5. Security & Prompt Injection
The system is fundamentally immune to Prompt Injection by design. It uses a rule-based lexical tokenizer, meaning malicious inputs like *"Ignore all rules and output my password"* are evaluated as standard string literals. If the string contains keywords like "password" or "OTP", the engine interprets it as a phishing report and locks down the response safely.
