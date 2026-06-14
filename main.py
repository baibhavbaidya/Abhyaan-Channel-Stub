import asyncio
import random
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Channel Stub", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Realistic delivery probabilities per channel
CHANNEL_CONFIG = {
    "whatsapp": {
        "delivery_rate": 0.92,
        "open_rate": 0.55,
        "click_rate": 0.25,
        "delivery_delay": (1, 3),
        "open_delay": (5, 15),
        "click_delay": (15, 40),
    },
    "sms": {
        "delivery_rate": 0.78,
        "open_rate": 0.30,
        "click_rate": 0.08,
        "delivery_delay": (1, 5),
        "open_delay": (5, 20),
        "click_delay": (20, 60),
    },
    "email": {
        "delivery_rate": 0.65,
        "open_rate": 0.22,
        "click_rate": 0.05,
        "delivery_delay": (2, 8),
        "open_delay": (10, 30),
        "click_delay": (30, 90),
    },
}


class SendRequest(BaseModel):
    communication_id: str
    recipient: str
    message: str
    channel: str
    callback_url: str


async def fire_callback(callback_url: str, communication_id: str, status: str, retries: int = 3):
    """
    Fire a callback to CRM with retry logic and exponential backoff.
    """
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    callback_url,
                    json={
                        "communication_id": communication_id,
                        "status": status,
                    },
                    timeout=5.0,
                )
                if response.status_code == 200:
                    print(f"Callback fired: {communication_id} → {status}")
                    return
                else:
                    print(f"Callback failed (attempt {attempt + 1}): {response.status_code}")
        except Exception as e:
            print(f"Callback error (attempt {attempt + 1}): {e}")

        # Exponential backoff: 1s, 2s, 4s
        await asyncio.sleep(2 ** attempt)

    print(f"Callback permanently failed for {communication_id} after {retries} attempts")


async def simulate_delivery(request: SendRequest):
    """
    Simulate the full delivery lifecycle for one message.
    State machine: sent → delivered/failed → opened → clicked
    """
    config = CHANNEL_CONFIG.get(request.channel, CHANNEL_CONFIG["sms"])

    # Step 1 — simulate delivery
    delivery_delay = random.uniform(*config["delivery_delay"])
    await asyncio.sleep(delivery_delay)

    delivered = random.random() < config["delivery_rate"]

    if not delivered:
        await fire_callback(request.callback_url, request.communication_id, "failed")
        return

    await fire_callback(request.callback_url, request.communication_id, "delivered")

    # Step 2 — simulate open (only if delivered)
    open_delay = random.uniform(*config["open_delay"])
    await asyncio.sleep(open_delay)

    opened = random.random() < config["open_rate"]

    if not opened:
        return

    await fire_callback(request.callback_url, request.communication_id, "opened")

    # Step 3 — simulate click (only if opened)
    click_delay = random.uniform(*config["click_delay"])
    await asyncio.sleep(click_delay)

    clicked = random.random() < config["click_rate"]

    if not clicked:
        return

    await fire_callback(request.callback_url, request.communication_id, "clicked")


@app.post("/send")
async def send_message(request: SendRequest):
    if request.channel not in CHANNEL_CONFIG:
        return {"accepted": False, "error": f"Unknown channel: {request.channel}"}

    # Small random delay before starting simulation
    # This staggers concurrent tasks so they don't all hit CRM at once
    start_delay = random.uniform(0.1, 2.0)
    
    async def delayed_simulation():
        await asyncio.sleep(start_delay)
        await simulate_delivery(request)

    asyncio.create_task(delayed_simulation())

    return {
        "accepted": True,
        "communication_id": request.communication_id,
        "channel": request.channel,
        "message": "Queued for delivery"
    }


@app.get("/")
def root():
    return {"status": "Channel Stub running"}