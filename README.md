# AgenticAI_Assignment2
Agentic AI student chatbot with added security policies

### 1. System Architecture Overview

The application follows a secure, modular **ReAct (Reasoning and Acting)** agentic architecture built on Streamlit, Groq LLM API, and deterministic Python guardrails:

* **User Interface Layer (`app.py`)**: A Streamlit chat interface that captures user queries, maintains chat history, and manages active user sessions via a sidebar identity switcher (`STU101`, `STU102`, `STU999_ADMIN`).
* **LLM Reasoning Layer (Groq API)**: Analyzes user intent, determines necessary tool calls, and generates structured reasoning turns using the `llama-3.3-70b-versatile` model.
* **Tool & Security Execution Layer (`tools.py`)**: Executes requested tool functions while strictly enforcing three core security guardrails:
  * **Code-Level Authorization**: Inspects `student_data.json` to hard-block unauthorized cross-student data access.
  * **Human-in-the-Loop (HITL) Gatekeeper**: Pauses sensitive actions (e.g., `request_fee_waiver`) until an administrator (`STU999_ADMIN`) approves the action via the UI widget.
  * **Memory Sanitization Filter**: Scans preference update inputs via regex to prevent sensitive credentials (passwords, OTPs, financial tokens) from persisting to disk (`user_profile.json`).
* **Audit & Governance Layer (`format_trace.py`)**: Logs every execution turn into `traces/run_logs.jsonl` (capturing token counts, latency, identity, and security flags) and compiles them into a clean Excel evaluation report (`agent_evaluation_log.xlsx`).

### 2. Core Components

* **`app.py`**: The Streamlit user interface handling chat state, rendering assistant responses, injecting authenticated user identity from the sidebar switcher, and hosting the Human-in-the-Loop (HITL) administrative approval widget.
* **`tools.py`**: The execution engine containing tool schemas, code-level authorization checks reading directly from `student_data.json`, admin-enforced HITL approval workflows, and regex-based memory sanitization protecting `user_profile.json`.
* **`format_trace.py`**: The audit compilation script that aggregates raw JSONL run logs into a structured Excel evaluation workbook (`agent_evaluation_log.xlsx`).

---

### 3. How to Run the Application

Follow these steps to set up and run the agent locally:

* **Step 1: Install Dependencies**  
  Ensure you have Python 3.12 and the required libraries installed in your virtual environment:
  ```bash
  pip install streamlit groq pandas openpyxl requests

  ** Step 2: Configure Your API Key**
  Set your Groq API key as an environment variable in your terminal

  **Step 3: Run the Streamlit App**
  Launch the local web interface
  ```bash
  streamlit run app.py

  **Compile the Audit Logs**
  Run python format_trace.py to compile audit logs

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