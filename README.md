# Dental Help — AI Voice Dental Booking System

A fully functional demo dental clinic voice booking system built with **ElevenLabs Conversational AI**, **FastAPI**, and **MongoDB Atlas**. Deployed on **Render**.

Speak to an AI dental receptionist, get available appointment slots, and book a confirmed appointment - all without touching a keyboard. Every conversation and booking is stored automatically in MongoDB.

---

## Demo Clinic

| | |
|---|---|
| **Name** | Dental Help |
| **Address** | 42 Oak Street, Suite 200, Springfield, IL 62701 |
| **Phone** | (217) 555-0148 |
| **Mon–Fri** | 9:00 AM – 6:00 PM |
| **Saturday** | 9:00 AM – 2:00 PM |
| **Sunday** | Closed |

**Services:** Routine Checkup ($80)  Teeth Cleaning ($120)  Teeth Whitening ($200)  Cavity Filling ($150)  Root Canal ($850)  X-Ray ($75)  Extraction ($200)  Braces Consultation (Free)  Emergency Care ($250)

---

## Architecture

```
Browser
   Frontend (HTML + CSS + JS)
         ElevenLabs voice widget    ElevenLabs Cloud
         REST /api/*                FastAPI Backend (Render)
                                               /api/slots             (agent tool)
                                               /api/book-appointment  (agent tool)
                                               /webhook/elevenlabs    (post-call)
                                               MongoDB Atlas
                                                     conversations
                                                     appointments
```

**Call flow:**
1. User opens site  clicks voice widget
2. ElevenLabs connects the user to **Aria** the AI receptionist
3. User asks to book  agent calls `check_availability`  backend returns open slots
4. User confirms a slot  agent calls `book_appointment`  written to MongoDB
5. Call ends  ElevenLabs fires post-call webhook  backend stores full transcript + booking_status
6. Frontend polls `/api/conversations` and `/api/appointments` every 10 s  tables update automatically

---

## Tech Stack

| Layer | Technology |
|---|---|
| Voice AI | ElevenLabs Conversational AI (GPT-4o-mini, server tools) |
| Backend | Python 3.11  FastAPI  Motor (async MongoDB) |
| Database | MongoDB Atlas (free M0 tier) |
| Frontend | HTML5  CSS3  Vanilla JS (no build step) |
| Deployment | Render (free web service) |

---

## Prerequisites

- Python 3.11+
- [ElevenLabs](https://elevenlabs.io) account (free tier works)
- [MongoDB Atlas](https://cloud.mongodb.com) account (free M0 cluster)
- [Render](https://render.com) account (free tier works)
- [GitHub](https://github.com) account

---

## Setup Guide

### 1 — Get an ElevenLabs API key

1. Sign up at [elevenlabs.io](https://elevenlabs.io)
2. **Profile (top-right)  API Keys  Create API Key**
3. Copy the key (starts with `sk_`)

### 2 — Set up MongoDB Atlas

1. Sign up at [cloud.mongodb.com](https://cloud.mongodb.com)
2. Create a free **M0** cluster
3. **Database Access**  Add user  username + password  Read/Write
4. **Network Access**  Add IP  `0.0.0.0/0` (allow all)
5. **Databases  Connect  Drivers**  copy the connection string
   ```
   mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### 3 — Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/dental-help.git
git push -u origin master
```

### 4 — Deploy to Render

1. Go to [render.com](https://render.com)  **New  Web Service**
2. Connect your GitHub account  select the `dental-help` repo
3. Render auto-detects `render.yaml`. Confirm these settings:
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add:

   | Key | Value |
   |---|---|
   | `ELEVENLABS_API_KEY` | your key from Step 1 |
   | `MONGODB_URI` | your connection string from Step 2 |
   | `MONGODB_DBNAME` | `demodental` |
   | `BACKEND_URL` | *(leave blank for now — fill after first deploy)* |
   | `WEBHOOK_SECRET` | *(leave blank — auto-filled by setup script)* |
   | `AGENT_ID` | *(leave blank — auto-filled by setup script)* |

5. Click **Create Web Service**
6. Wait ~2 min  Render gives you a public URL:
   ```
   https://dental-help.onrender.com
   ```

### 5 — Run the agent setup script

Back on your local machine:

```bash
# Copy .env.example and fill in your values
cp .env.example .env

# Set ELEVENLABS_API_KEY, MONGODB_URI, and BACKEND_URL in .env
# BACKEND_URL = the Render URL from Step 4 (e.g. https://dental-help.onrender.com)

# Run the one-time setup
python scripts/setup_agent.py
```

This script will:
- Register the post-call webhook with ElevenLabs pointing to your Render URL
- Create the **Dental Help** AI agent with both server tools configured
- Write `WEBHOOK_SECRET` and `AGENT_ID` back to your `.env`
- Write `frontend/config.js` with the `agentId` so the widget loads

### 6 — Push final config and redeploy

```bash
git add frontend/config.js
git commit -m "chore: add agent config"
git push
```

Then in Render  your service  **Environment**  add the two new variables:
- `WEBHOOK_SECRET` = value from `.env`
- `AGENT_ID` = value from `.env`

Render redeploys automatically on push.

### 7 — Test

Open your Render URL  click the voice widget  talk to Aria.

**Sample conversation:**
> "Hi, I'd like to book a teeth cleaning for next Tuesday afternoon."

After the call ends (~30 s)  refresh the page  rows appear in both tables.

---

## Local Development

```bash
# Install deps
pip install -r requirements.txt

# Copy and fill .env
cp .env.example .env

# Run (serves frontend too)
uvicorn backend.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000).

> **Note:** ElevenLabs cannot reach `localhost` for webhooks and tools. Use [ngrok](https://ngrok.com) to expose a tunnel and set `BACKEND_URL` accordingly before running `setup_agent.py`.

```bash
ngrok http 8000
# Copy the https://xxxxx.ngrok-free.app URL  set as BACKEND_URL in .env
```

---

## MongoDB Verification

Log into [MongoDB Atlas](https://cloud.mongodb.com)  Browse Collections  database `demodental`:

**`conversations`** (created automatically after each call ends):
```json
{
  "caller_id": "conv_abc123",
  "transcript": "Aria: Thank you for calling...\nYou: I'd like to book...",
  "booking_status": "success",
  "call_duration_secs": 87,
  "created_at": "2026-03-05T14:32:00Z"
}
```

**`appointments`** (created the moment the agent confirms a booking):
```json
{
  "conversation_id": "conv_abc123",
  "patient_name": "John Smith",
  "service_type": "Teeth Cleaning",
  "appointment_time": "2026-03-09T14:00:00Z",
  "status": "confirmed",
  "created_at": "2026-03-05T14:31:45Z"
}
```

---

## Project Structure

```
dental-help/
 backend/
    main.py              FastAPI app, serves frontend static files
    database.py          Motor async MongoDB connection
    models.py            Pydantic models
    clinic_data.py       Demo clinic data + slot generator
    requirements.txt
    routes/
        tools.py         /api/slots, /api/book-appointment  (called by AI agent)
        webhook.py       /webhook/elevenlabs  (post-call event, HMAC-verified)
        data.py          /api/conversations, /api/appointments, /api/config
 frontend/
    index.html           Single-page UI
    styles.css           Dark minimal design
    app.js               Frontend logic
    config.js            Auto-generated: contains agentId
 scripts/
    setup_agent.py       One-time: creates ElevenLabs webhook + agent
 render.yaml              Render deployment config
 runtime.txt              Python 3.11 for Render
 requirements.txt         Root-level (Render build)
 Procfile
 .env.example
```

---

## Environment Variables

| Variable | Where set | Description |
|---|---|---|
| `ELEVENLABS_API_KEY` | Render + `.env` | ElevenLabs API key |
| `MONGODB_URI` | Render + `.env` | MongoDB Atlas connection string |
| `MONGODB_DBNAME` | Render (optional) | Database name, default `demodental` |
| `BACKEND_URL` | Render + `.env` | Public HTTPS URL of this Render service |
| `WEBHOOK_SECRET` | Render + `.env` | Auto-written by `setup_agent.py` |
| `AGENT_ID` | Render + `.env` | Auto-written by `setup_agent.py` |

---

## API Endpoints

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/config` | Returns `agent_id` for the frontend widget |
| `GET` | `/api/slots` | Available slots (called by AI agent tool) |
| `POST` | `/api/book-appointment` | Book a slot (called by AI agent tool) |
| `GET` | `/api/conversations` | All stored conversations |
| `GET` | `/api/appointments` | All stored appointments |
| `POST` | `/webhook/elevenlabs` | ElevenLabs post-call webhook (HMAC-verified) |

---

## Evaluation Notes

- No hardcoded transcripts — all MongoDB data comes from real ElevenLabs webhook payloads
- No manual inserts — conversations saved only on webhook; appointments saved only when agent calls the tool
- HMAC-SHA256 webhook signature verified on every request
- Agent responses driven entirely by system prompt and live tool responses
