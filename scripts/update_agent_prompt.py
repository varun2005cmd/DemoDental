#!/usr/bin/env python3
"""
Patches the existing ElevenLabs agent with the updated system prompt.
Run whenever the system prompt changes without needing to recreate the agent.

    python scripts/update_agent_prompt.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_KEY  = os.environ.get("ELEVENLABS_API_KEY", "").strip()
AGENT_ID = os.environ.get("AGENT_ID", "").strip()

if not API_KEY:
    print("ERROR: ELEVENLABS_API_KEY not set", file=sys.stderr); sys.exit(1)
if not AGENT_ID:
    print("ERROR: AGENT_ID not set — run setup_agent.py first", file=sys.stderr); sys.exit(1)

# Import the same SYSTEM_PROMPT from setup_agent.py
sys.path.insert(0, str(ROOT))
from scripts.setup_agent import SYSTEM_PROMPT

HEADERS = {"xi-api-key": API_KEY, "Content-Type": "application/json"}

def main():
    print(f"Patching agent {AGENT_ID[:20]}… with updated system prompt")

    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": SYSTEM_PROMPT,
                }
            }
        }
    }

    with httpx.Client(headers=HEADERS, timeout=30) as client:
        resp = client.patch(
            f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}",
            json=payload,
        )

    if resp.status_code not in (200, 201):
        print(f"ERROR [{resp.status_code}]: {resp.text}", file=sys.stderr)
        sys.exit(1)

    print("✓ Agent prompt updated successfully")
    print(f"  Agent ID: {AGENT_ID}")

if __name__ == "__main__":
    main()
