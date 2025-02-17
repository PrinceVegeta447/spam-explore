import os
import asyncio
import random
import logging
import threading
from telethon import TelegramClient, events
from fastapi import FastAPI
import uvicorn
from telethon.sessions import StringSession

# Configure logging
logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s", level=logging.INFO)

# Load API credentials for 5 accounts
API_IDS = [int(os.getenv(f"API_ID_{i}")) for i in range(1, 6)]
API_HASHES = [os.getenv(f"API_HASH_{i}") for i in range(1, 6)]
SESSION_STRINGS = [os.getenv(f"SESSION_{i}") for i in range(1, 6)]
clients = [TelegramClient(StringSession(SESSION_STRINGS[i]), API_IDS[i], API_HASHES[i]) for i in range(5)]

# Group and target chat IDs
GROUP_ID = -1002348881334  # Group where /explore is sent
TARGET = -1002395952299    # Group where spam messages are sent

# Bots to send /explore
BOTS = ["@CollectCricketersBot", "@CollectYourPlayerxBot"]

# Spam messages and delay settings
MESSAGES = ["🎲"]
MIN_DELAY, MAX_DELAY = 6, 7

# Initialize clients
clients = [TelegramClient(SESSION_NAMES[i], API_IDS[i], API_HASHES[i]) for i in range(5)]

# Dictionary to manage spam status for each session
spam_running = {client.session.filename: False for client in clients}

async def send_explore(client):
    """ Sends /explore to bots in the group with randomized delay """
    while True:
        for bot in BOTS:
            try:
                await client.send_message(GROUP_ID, f"/explore {bot}")
                logging.info(f"Sent /explore to {bot}")
            except Exception as e:
                logging.error(f"Failed to send /explore to {bot}: {e}")
            delay = random.randint(310, 330)
            logging.info(f"Waiting {delay} seconds before next /explore...")
            await asyncio.sleep(delay)

async def handle_buttons(event):
    """ Clicks random inline buttons """
    if event.reply_markup and hasattr(event.reply_markup, 'rows'):
        buttons = [btn for row in event.reply_markup.rows for btn in row.buttons if hasattr(btn, "data")]
        if buttons:
            button = random.choice(buttons)
            await asyncio.sleep(random.randint(3, 6))
            try:
                await event.click(buttons.index(button))
                logging.info(f"Clicked a button in response to {event.sender_id}")
            except Exception as e:
                logging.error(f"Failed to click a button: {e}")

async def auto_spam(client):
    """ Sends messages to the target chat with delay """
    session_name = client.session.filename
    spam_running[session_name] = True
    while spam_running[session_name]:
        try:
            msg = random.choice(MESSAGES)
            await client.send_message(TARGET, msg)
            delay = random.randint(MIN_DELAY, MAX_DELAY)
            logging.info(f"Sent: {msg} | Waiting {delay} sec...")
            await asyncio.sleep(delay)
        except Exception as e:
            logging.error(f"Error: {e}")
            await asyncio.sleep(10)

@events.register(events.NewMessage(pattern="/startspam"))
async def start_spam(event):
    """ Starts spamming """
    for client in clients:
        if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:
            if not spam_running[client.session.filename]:
                await event.reply("✅ Auto Spam Started!")
                asyncio.create_task(auto_spam(client))
            else:
                await event.reply("⚠ Already Running!")

@events.register(events.NewMessage(pattern="/stopspam"))
async def stop_spam(event):
    """ Stops spamming """
    for client in clients:
        if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:
            spam_running[client.session.filename] = False
            await event.reply("🛑 Stopping Spam!")

async def run_client(client):
    """ Starts a single client """
    await client.start()
    client.add_event_handler(handle_buttons, events.NewMessage(chats=GROUP_ID))
    client.add_event_handler(start_spam)
    client.add_event_handler(stop_spam)
    asyncio.create_task(send_explore(client))
    await client.run_until_disconnected()

async def main():
    """ Runs all clients concurrently """
    await asyncio.gather(*[run_client(client) for client in clients])

# FastAPI for Health Check
app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "OK"}

def start_health_server():
    """ Runs FastAPI server on a separate thread """
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Run FastAPI in a separate thread
threading.Thread(target=start_health_server, daemon=True).start()

# Run Telegram bot clients
asyncio.run(main())
