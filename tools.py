import json
import os
import re
from pypdf import PdfReader
import pypdf

PROFILE_FILE = "user_profile.json"
POLICY_PDF_PATH = "AIDTM Admission Policy.pdf"

# 1. Load the Mock Student Database
try:
    with open("student_data.json", "r", encoding="utf-8") as f:
        STUDENT_DB = json.load(f)
except FileNotFoundError:
    STUDENT_DB = {}

# 2. Deterministic Privacy Check Helper
def _is_authorized(authenticated_user: str, target_student_id: str) -> bool:
    """Helper to enforce strict identity matching in python code."""
    if not authenticated_user or not target_student_id:
        return False
    norm_auth = authenticated_user.replace("-", "").upper().strip()
    norm_target = target_student_id.replace("-", "").upper().strip()
    
    # Allow if exact user match or admin override
    return ("ADMIN" in norm_auth) or (norm_auth == norm_target)

# 3. Memory Sanitization Guardrail
SENSITIVE_PATTERNS = [
    r'\b\d{4,8}\b',                 # OTPs / PIN codes (4-8 digits)
    r'(?i)password',                 # Password references
    r'(?i)otp',                      # OTP references
    r'(?i)secret',                   # Secret keys
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b' # Sensitive email address strings if blocked
]

def sanitize_for_memory(key: str, value: str) -> bool:
    """Returns True if content is safe to store in persistent profile, False if sensitive."""
    combined_text = f"{key} {value}".lower()
    
    # 1. Block prohibited keys explicitly
    prohibited_keys = ["fee", "balance", "student_id", "password", "otp", "secret", "cvv", "card", "bank"]
    if any(pk in key.lower() for pk in prohibited_keys):
        return False
        
    # 2. Scan value content against sensitive regex patterns (OTPs, passwords)
    if re.search(r'(?i)(password|otp|pin|token|auth_key)', value):
        return False
        
    return True

# 4. Core Tool Implementation

def check_fee_status(student_id: str = None, current_user_id: str = "STU-101") -> dict:
    """Check fee status with deterministic in-code authorization checks."""
    if not student_id or not student_id.strip():
        student_id = current_user_id

    # Code-level authorization check
    if not _is_authorized(current_user_id, student_id):
        print(f"🚨 [PRIVACY VIOLATION BLOCKED] User '{current_user_id}' denied access to student '{student_id}'.")
        return {
            "status": "error",
            "success": False,
            "error": f"Access Denied: Authenticated user '{current_user_id}' is not authorized to view private records for student '{student_id}'. You may only view your own records.",
            "authenticated_user": current_user_id,
            "requested_student": student_id
        }

    norm_target = student_id.replace("-", "").upper().strip()
    target_key = None
    for key in STUDENT_DB.keys():
        if key.replace("-", "").upper().strip() == norm_target:
            target_key = key
            break

    if target_key and target_key in STUDENT_DB:
        return {
            "success": True, 
            "student_id": target_key, 
            "name": STUDENT_DB[target_key]["name"],
            "programme": STUDENT_DB[target_key]["programme"],
            "fee_status": STUDENT_DB[target_key]["fee_status"]
        }
    return {"success": False, "error": f"Student ID '{student_id}' not found in records."}

def request_fee_waiver(student_id: str, reason: str, current_user_id: str = "STU-101", approval_status: str = "pending") -> dict:
    """Request a fee waiver requiring explicit administrative/human approval."""
    if not _is_authorized(current_user_id, student_id):
        return {
            "success": False, 
            "error": f"Access Denied: You cannot request fee concessions for student '{student_id}'."
        }

    if approval_status != "approved":
        print(f"🔒 [APPROVAL PAUSE] Fee waiver request for '{student_id}' requires human approval.")
        return {
            "success": False,
            "requires_approval": True,
            "action_name": "request_fee_waiver",
            "arguments": {"student_id": student_id, "reason": reason},
            "message": f"🔒 [APPROVAL REQUIRED] Fee waiver request for student '{student_id}' (Reason: '{reason}') requires manual administrative approval."
        }

    print(f"✅ [ACTION EXECUTED] Fee waiver approved for student '{student_id}'.")
    return {
        "success": True,
        "message": f"Successfully approved and logged fee waiver request for student '{student_id}' based on reason: '{reason}'."
    }

def search_student_policy(query: str, max_results: int = 3) -> dict:
    """Searches official AIDTM Admission Policy document."""
    if not os.path.exists(POLICY_PDF_PATH):
        return {"status": "error", "message": f"Policy document '{POLICY_PDF_PATH}' not found."}

    try:
        reader = pypdf.PdfReader(POLICY_PDF_PATH)
        full_text = ""
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += f"\n--- Page {page_num + 1} ---\n" + text

        raw_chunks = [c.strip() for c in re.split(r'\n\s*\n', full_text) if len(c.strip()) > 40]
        query_words = set(re.findall(r'\w+', query.lower())) - {"what", "is", "the", "for", "a", "an", "in", "of", "and", "or", "to", "are"}
        
        scored_chunks = []
        for chunk in raw_chunks:
            chunk_words = set(re.findall(r'\w+', chunk.lower()))
            score = len(query_words.intersection(chunk_words))
            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        selected_chunks = [chunk for score, chunk in scored_chunks[:max_results]]

        if not selected_chunks:
            selected_chunks = raw_chunks[:2]

        return {
            "status": "success",
            "query": query,
            "retrieved_chunks_count": len(selected_chunks),
            "relevant_context": selected_chunks
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to parse policy document: {str(e)}"}

def _load_profile():
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_profile(profile_data):
    safe_data = {
        k: v for k, v in profile_data.items() 
        if k in ["user_name", "preferred_program", "preferred_specialization"]
    }
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(safe_data, f, indent=4)

def update_user_preference(key: str, value: str):
    """
    Saves non-sensitive preferences persistently while performing
    MEMORY SANITIZATION checks against passwords, OTPs, and sensitive credentials.
    """
    # Enforce Memory Sanitization Check
    if not sanitize_for_memory(key, value):
        print(f"🛡️ [MEMORY SANITIZATION BLOCKED] Prevented sensitive input ({key}:{value}) from entering persistent memory.")
        return {
            "status": "error",
            "privacy_blocked_triggered": True,
            "message": "Security Policy Violation: Sensitive details like OTPs, passwords, or financial credentials cannot be stored in persistent memory."
        }

    profile = _load_profile()
    profile[key] = value
    _save_profile(profile)
    return {"status": "success", "message": f"Successfully remembered preference: {key} = {value}"}

def get_user_preferences():
    return _load_profile()

# 5. Dispatcher & Schemas

TOOL_REGISTRY = {
    "check_fee_status": check_fee_status,
    "request_fee_waiver": request_fee_waiver,
    "search_student_policy": search_student_policy,
    "update_user_preference": update_user_preference,
    "get_user_preferences": get_user_preferences
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "check_fee_status",
            "description": "Check current fee payment status for a student (e.g. STU-101).",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "The student ID"}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_fee_waiver",
            "description": "Request a fee waiver/concession for a student. Requires human approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "The target student ID"},
                    "reason": {"type": "string", "description": "Justification for waiver"}
                },
                "required": ["student_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_student_policy",
            "description": "Search AIDTM Admission Policy PDF.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search topic"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_preference",
            "description": "Store non-sensitive persistent user preference (e.g., preferred_program). NEVER store credentials/OTPs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Preference key"},
                    "value": {"type": "string", "description": "Value to store"}
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_preferences",
            "description": "Retrieve non-sensitive user preferences.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def dispatch_tool(name: str, args: dict, current_user_id: str = "STU-101", approval_status: str = "pending") -> dict:
    """Validates and executes tool calls securely."""
    if name == "search_student_policy":
        return search_student_policy(**args)
    elif name == "check_fee_status":
        return check_fee_status(current_user_id=current_user_id, **args)
    elif name == "request_fee_waiver":
        return request_fee_waiver(current_user_id=current_user_id, approval_status=approval_status, **args)
    elif name == "update_user_preference":
        return update_user_preference(**args)
    elif name == "get_user_preferences":
        return get_user_preferences()
    else:
        return {"error": f"Unknown tool: {name}"}