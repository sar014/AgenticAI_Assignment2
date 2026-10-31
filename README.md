# AgenticAI_Assignment2
Agentic AI student chatbot with added security policies

## 🛡️ Assignment 2: Security, Privacy & Production Enhancements

This section outlines the advanced production-grade security, data privacy, and governance guardrails implemented in **Assignment 2** to transition the Student Support Agent into a secure, auditable, and human-supervised system.

### 1. Identity Management & Context Session
* **Dynamic Student Session State**: Implemented a sidebar session switcher in `app.py` allowing dynamic identification across student accounts (`STU101`, `STU102`) and administrative roles (`STU999_ADMIN`).
* **Contextual Injection**: Authenticated user identity is passed directly to both the system prompt layer and downstream tool dispatchers to ensure context awareness.

### 2. Deterministic Data Privacy & Code-Level Authorization
* **Code-Level Guardrails**: Enforced strict authorization checks inside `tools.py` rather than relying solely on soft LLM prompts.
* **Cross-Student Protection**: Functions like `check_fee_status` verify whether the authenticated user matches the target student ID. Any unauthorized attempt to view another student's records is hard-blocked with an explicit `Access Denied` error and tracked via a privacy trigger flag.

### 3. Human-in-the-Loop (HITL) Approval Workflow
* **Sensitive Action Gatekeeping**: High-risk or sensitive actions—such as `request_fee_waiver`—pause execution (`requires_approval: True`) when triggered.
* **Admin-Only Authorization**: Implemented a secure UI confirmation loop requiring administrative sign-in (`STU999_ADMIN`) to review arguments and grant explicit sign-off before the tool executes. Unauthenticated student attempts to approve sensitive actions are rejected.

### 4. Memory Sanitization & Credential Protection
* **Persistent Memory Safeguards**: Added automated regex-based filters (`sanitize_for_memory`) inspecting user inputs and storage keys.
* **Secret Blocking**: Automatically detects and blocks attempts to persist sensitive credentials, financial secrets, passwords, OTPs, or tokens into `user_profile.json`, raising a security violation error.

### 5. Enhanced Audit Trail & Tracing
* **Comprehensive Run Logging**: Every interaction records detailed metrics into `traces/run_logs.jsonl`, capturing per-turn token counts, response latency, authenticated user data, and binary security flags (`Privacy Block Triggered`, `Human Approval Requested`, `Human Approval Granted`).
* **Excel Compilation**: Updated `format_trace.py` to compile raw JSONL run logs into a structured **`agent_evaluation_log.xlsx`** evaluation spreadsheet.