import json
import os
import pandas as pd

LOG_PATH = "traces/run_logs.jsonl"
EXCEL_PATH = "agent_evaluation_log.xlsx"

def format_traces():
    if not os.path.exists(LOG_PATH):
        print(f"⚠️ No trace logs found at '{LOG_PATH}'. Chat with your Streamlit app first!")
        return

    records = []
    with open(LOG_PATH, "r") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line.strip()))
                except Exception as e:
                    print(f"⚠️ Skipping malformed log line: {e}")

    if not records:
        print("⚠️ No valid trace records found in the log file.")
        return

    table_data = []
    for idx, r in enumerate(records, 1):
        trace_steps = r.get("trace", [])
        
        tools = [str(t["tool_called"]) for t in trace_steps if t.get("tool_called")]
        tools_str = ", ".join(tools) if tools else "None (Direct/Guardrail)"
        
        privacy_blocked = "NO"
        approval_requested = "NO"
        approval_granted = "NO"
        
        for step in trace_steps:
            obs = step.get("observation", {})
            if isinstance(obs, dict):
                if obs.get("privacy_block_triggered"):
                    privacy_blocked = "YES"
                if obs.get("human_approval_requested"):
                    approval_requested = "YES"
                if obs.get("human_approval_granted"):
                    approval_granted = "YES"
            if step.get("human_approval_requested"):
                approval_requested = "YES"
            if step.get("human_approval_granted"):
                approval_granted = "YES"
        
        row = {
            "Run #": idx,
            "Authenticated User": r.get("authenticated_user", "STU101"),
            "User Query": r.get("user_query", ""),
            "Tools Used": tools_str,
            "Privacy Block Triggered": privacy_blocked,
            "Human Approval Requested": approval_requested,
            "Human Approval Granted": approval_granted,
            "Latency (s)": r.get("latency_seconds", 0.0),
        }
        
        total_prompt = 0
        total_completion = 0
        for step in trace_steps:
            turn_num = step.get("turn", 1)
            p_tok = step.get("prompt_tokens", 0)
            c_tok = step.get("completion_tokens", 0)
            
            row[f"Turn {turn_num} Prompt Tokens"] = p_tok
            row[f"Turn {turn_num} Completion Tokens"] = c_tok
            
            total_prompt += p_tok
            total_completion += c_tok
            
        row["Total Prompt Tokens"] = total_prompt
        row["Total Completion Tokens"] = total_completion
        row["Final Answer"] = r.get("final_answer", "")
        
        table_data.append(row)

    df = pd.DataFrame(table_data)
    df.to_excel(EXCEL_PATH, index=False)

    print("\n================================================================================")
    print(f"✅ Successfully compiled {len(df)} audit traces into '{EXCEL_PATH}'!")
    print("================================================================ failure =\n")

if __name__ == "__main__":
    format_traces()
