"""One-shot script: pull all ElevenLabs conversations into MongoDB."""
import asyncio, os, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

import httpx
from backend.database import conversations_collection

async def main():
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    agent_id = os.environ.get("AGENT_ID", "")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set"); return

    col = conversations_collection()

    # Show current DB state
    existing = await col.find({}).to_list(100)
    print(f"MongoDB currently has {len(existing)} conversations")

    synced = updated = skipped = 0
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {"xi-api-key": api_key}
        params = {"page_size": 25}
        if agent_id:
            params["agent_id"] = agent_id
        r = await client.get("https://api.elevenlabs.io/v1/convai/conversations", headers=headers, params=params)
        summaries = r.json().get("conversations", [])
        print(f"ElevenLabs has {len(summaries)} conversations")

        for s in summaries:
            cid = s.get("conversation_id", "")
            if not cid:
                continue
            if s.get("status") == "in-progress":
                print(f"  SKIP {cid} (in-progress)")
                skipped += 1
                continue

            dr = await client.get("https://api.elevenlabs.io/v1/convai/conversations/" + cid, headers=headers)
            if dr.status_code != 200:
                print(f"  ERROR {cid}: {dr.status_code}")
                continue
            d = dr.json()

            lines = []
            for entry in d.get("transcript", []):
                role = entry.get("role", "unknown").capitalize()
                msg = entry.get("message", "").strip()
                if msg:
                    lines.append(f"{role}: {msg}")
            transcript_text = "\n".join(lines) if lines else "(no transcript)"

            has_audio = bool(d.get("has_audio") or d.get("has_response_audio"))
            record = {
                "caller_id": cid,
                "transcript": transcript_text,
                "booking_status": "incomplete",
                "has_audio": has_audio,
                "has_response_audio": bool(d.get("has_response_audio")),
                "conv_status": d.get("status", "done"),
                "agent_id": d.get("agent_id", agent_id),
                "call_duration_secs": d.get("metadata", {}).get("call_duration_secs", 0),
                "summary": d.get("analysis", {}).get("transcript_summary", ""),
            }

            existing_doc = await col.find_one({"caller_id": cid})
            if existing_doc:
                await col.update_one({"caller_id": cid}, {"$set": record})
                print(f"  UPDATED {cid}  has_audio={has_audio}  transcript_lines={len(lines)}")
                updated += 1
            else:
                record["created_at"] = datetime.now(timezone.utc)
                await col.insert_one(record)
                print(f"  INSERTED {cid}  has_audio={has_audio}  transcript_lines={len(lines)}")
                synced += 1

    print(f"\nDone: inserted={synced} updated={updated} skipped={skipped}")

    # Verify
    docs = await col.find({}).to_list(100)
    print(f"MongoDB now has {len(docs)} conversations")
    for doc in docs:
        print(f"  {doc.get('caller_id')}  has_audio={doc.get('has_audio')}  transcript={str(doc.get('transcript',''))[:60]}")

asyncio.run(main())
