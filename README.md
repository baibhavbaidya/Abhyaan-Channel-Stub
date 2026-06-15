# Abhyaan — Channel Stub

Simulated messaging channel service for Abhyaan, an AI-native mini CRM for retail and D2C brands.

**Live:** [abhyaan-channel-stub.onrender.com](https://abhyaan-channel-stub.onrender.com)

**Frontend:** [github.com/baibhavbaidya/Abhyaan-Frontend](https://github.com/baibhavbaidya/Abhyaan-Frontend)

**Backend:** [github.com/baibhavbaidya/Abhyaan-Backend](https://github.com/baibhavbaidya/Abhyaan-Backend)

---

## What is this

In real CRM systems, messaging providers like WhatsApp Business, Twilio, or SendGrid handle delivery. They accept messages, attempt delivery, and fire webhook callbacks back to the CRM with status updates — delivered, opened, clicked, failed.

This service simulates exactly that behavior. It accepts send requests from the CRM, simulates realistic delivery outcomes asynchronously, and fires callbacks back to the CRM receipt endpoint. No real messages are sent.

---

## Architecture

![Abhyaan Architecture](./Abhyaan%20Architecture%20Diagram.jpg)

---

## How it works

```
CRM sends:
POST /send
{
  communication_id: "uuid",
  recipient: "9876543210",
  message: "Hey Rahul...",
  channel: "whatsapp",
  callback_url: "https://abhyaan-backend.onrender.com/api/receipts"
}

Stub accepts immediately → returns 200

Then asynchronously:
  t=1-3s:  POST callback_url → { status: "delivered" }  (or "failed")
  t=5-15s: POST callback_url → { status: "opened" }
  t=15-40s: POST callback_url → { status: "clicked" }
```

---

## Channel Probabilities

| Channel | Delivery | Open | Click |
|---|---|---|---|
| WhatsApp | 92% | 55% | 25% |
| SMS | 78% | 30% | 8% |
| Email | 65% | 22% | 5% |

---

## State Machine

Each message follows a strict lifecycle:

```
sent → delivered → opened → clicked
           ↓
         failed
```

A message can only progress forward. Clicked requires opened. Opened requires delivered. This mirrors real delivery infrastructure behavior.

---

## Retry Logic

If the CRM callback URL is unavailable, the stub retries 3 times with exponential backoff — 1s, 2s, 4s. After 3 failed attempts it logs permanently failed and moves on.

---

## Tech Stack

- Python 3.11
- FastAPI
- httpx (async HTTP client)
- Deployed on Render

---

## Local Setup

```bash
git clone https://github.com/baibhavbaidya/Abhyaan-Channel-Stub
cd Abhyaan-Channel-Stub
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create a `.env` file:
```
CRM_CALLBACK_URL=http://localhost:8000
```

Run:
```bash
uvicorn main:app --reload --port 8001
```

Make sure the CRM backend is running on port 8000 first.
