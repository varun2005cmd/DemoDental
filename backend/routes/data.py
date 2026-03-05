"""
Read/write endpoints consumed by the frontend to display and manage stored data.
"""
from __future__ import annotations

import os

import httpx
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from backend.clinic_data import DOCTORS
from backend.database import conversations_collection, appointments_collection

router = APIRouter(tags=["data"])


def _stringify_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serialisable dict."""
    doc["id"] = str(doc.pop("_id"))
    for key, value in doc.items():
        if hasattr(value, "isoformat"):
            doc[key] = value.isoformat()
    if "doctor" not in doc:
        doc["doctor"] = "Unassigned"
    return doc


@router.get("/api/conversations")
async def get_conversations(limit: int = 50):
    """Return the most recent conversations, newest first."""
    col = conversations_collection()
    cursor = col.find({}).sort("created_at", -1).limit(limit)
    results = []
    async for doc in cursor:
        results.append(_stringify_doc(doc))
    return JSONResponse({"conversations": results, "count": len(results)})


@router.get("/api/conversations/{conv_id}/audio")
async def get_conversation_audio(conv_id: str):
    """Proxy the ElevenLabs conversation audio so the browser can play it."""
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://api.elevenlabs.io/v1/convai/conversations/{conv_id}/audio",
            headers={"xi-api-key": api_key},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Audio not available yet")
    return Response(
        content=resp.content,
        media_type=resp.headers.get("content-type", "audio/mpeg"),
        headers={"Accept-Ranges": "bytes"},
    )


@router.get("/api/appointments")
async def get_appointments(limit: int = 50):
    """Return the most recent appointments, newest first."""
    col = appointments_collection()
    cursor = col.find({}).sort("created_at", -1).limit(limit)
    results = []
    async for doc in cursor:
        results.append(_stringify_doc(doc))
    return JSONResponse({"appointments": results, "count": len(results)})


@router.delete("/api/appointments/{appt_id}")
async def delete_appointment(appt_id: str):
    """Manually delete an appointment by its MongoDB ObjectId."""
    try:
        oid = ObjectId(appt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid appointment ID")
    col = appointments_collection()
    result = await col.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return JSONResponse({"status": "deleted", "id": appt_id})


class DoctorUpdate(BaseModel):
    doctor: str


@router.patch("/api/appointments/{appt_id}/doctor")
async def update_appointment_doctor(appt_id: str, body: DoctorUpdate):
    """Reassign a doctor to an appointment."""
    try:
        oid = ObjectId(appt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid appointment ID")
    if body.doctor not in [d["name"] for d in DOCTORS]:
        raise HTTPException(status_code=400, detail="Unknown doctor name")
    col = appointments_collection()
    result = await col.update_one({"_id": oid}, {"$set": {"doctor": body.doctor}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return JSONResponse({"status": "updated", "doctor": body.doctor})


@router.get("/api/doctors")
async def get_doctors():
    return JSONResponse({"doctors": DOCTORS})


@router.get("/api/config")
async def get_config():
    return JSONResponse({
        "agent_id": os.environ.get("AGENT_ID", ""),
        "clinic_name": "Dental Help",
    })


@router.get("/api/health")
async def health():
    return JSONResponse({"status": "ok", "service": "demodental-backend"})
