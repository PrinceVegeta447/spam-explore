import os
import asyncio
import random
import logging
import threading
from telethon import TelegramClient, events
from flask import Flask
from telethon.sessions import SQLiteSession

# Configure logging
logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s", level=logging.INFO)

# API Credentials
API_IDS = 20118977  # Replace with your actual API ID
API_HASHES = "c88e99dd46c405f7357acef8ccc92f85"

# Session file names (should be in your root directory or specify path)
SESSION_FILES = [
    "session_1.session",  # Replace with actual session filenames
    "session_2.session", 
    "session_3.session",
    "session_4.session",
    "session_5.session"
]

# Initialize clients with FileSession (session files should be in the current directory or full path provided)
clients = [TelegramClient(SQLiteSession(session_file), API_IDS, API_HASHES) for session_file in SESSION_FILES]

# Group and target chat IDs
GROUP_ID = -1002348881334
TARGET = -1002395952299

# Bots to send /explore
BOTS = ["@CollectCricketersBot", "@CollectYourPlayerxBot"]

# Spam messages and delay settings
MESSAGES = ["🎲"]
MIN_DELAY, MAX_DELAY = 6, 7

# Dictionary to manage spam status using session filename
spam_running = {session_file: False for session_file in SESSION_FILES}

async def send_explore(client):
    """ Sends /explore to bots in the group with randomized delay """
    while True:
        for bot in BOTS:
            try:
                await client.send_message(GROUP_ID, f"/explore {bot}")
                logging.info(f"Sent /explore to {bot}")
            except Exception as e:
                logging.error(f"Failed to send /explore to {bot}: {e}")
            await asyncio.sleep(random.randint(310, 330))

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
    session_filename = client.session.session_file.name  # Use the session file name
    spam_running[session_filename] = True
    while spam_running[session_filename]:
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
    """ Starts spamming for all clients """
    for client in clients:
        if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:
            session_filename = client.session.session_file.name
            if not spam_running[session_filename]:
                await event.reply("✅ Auto Spam Started!")
                asyncio.create_task(auto_spam(client))
                asyncio.create_task(send_explore(client))  # Also start explore concurrently
            else:
                await event.reply("⚠ Already Running!")

@events.register(events.NewMessage(pattern="/stopspam"))
async def stop_spam(event):
    """ Stops spamming for all clients """
    for client in clients:
        if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:
            session_filename = client.session.session_file.name
            spam_running[session_filename] = False
            await event.reply("🛑 Stopping Spam!")

async def run_client(client):
    """ Starts a single client, running both spam and explore functions concurrently """
    await client.start()
    client.add_event_handler(handle_buttons, events.NewMessage(chats=GROUP_ID))
    client.add_event_handler(start_spam)
    client.add_event_handler(stop_spam)
    await asyncio.gather(
        send_explore(client),  # Run explore concurrently
        auto_spam(client)      # Run spam concurrently
    )
    await client.run_until_disconnected()

async def main():
    """ Runs all clients concurrently """
    await asyncio.gather(*[run_client(client) for client in clients])

# Flask Health Check
app = Flask(__name__)

@app.route("/health")
def health_check():
    return {"status": "OK"}

def start_health_server():
    app.run(host="0.0.0.0", port=8000, threaded=True)

# Start Flask before running the bot
thread = threading.Thread(target=start_health_server, daemon=True)
thread.start()

# Ensure Flask starts before running the bot
import time
time.sleep(2)

# Run Telegram bot clients
asyncio.run(main())
