import os
import asyncio
import random
import logging
import threading
from flask import Flask, jsonify
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# Flask app for health check
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "running"}), 200

# Logging setup
logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s", level=logging.INFO)

# Telegram API credentials (same for all sessions)
API_ID = 20061115
API_HASH = "c30d56d90d59b3efc7954013c580e076"

# Fetch session strings from environment variables
SESSION_STRINGS = [
    os.getenv("SESSION_1"),
    os.getenv("SESSION_2"),
    os.getenv("SESSION_3"),
    os.getenv("SESSION_4"),
    os.getenv("SESSION_5"),
    os.getenv("SESSION_6"),
    os.getenv("SESSION_7"),
    os.getenv("SESSION_8"),
    os.getenv("SESSION_9")
]

# Remove None values (if some sessions are missing)
SESSION_STRINGS = [s for s in SESSION_STRINGS if s]

# Create clients using StringSession
clients = {f"Session{i+1}": TelegramClient(StringSession(s), API_ID, API_HASH) for i, s in enumerate(SESSION_STRINGS)}

# Target group for spamming
TARGET_GROUP = -1002395952299  # Change as needed

# Spam settings
SPAM_MESSAGES = ["🎲", "🔥", "⚡", "💥", "✨"]
MIN_SPAM_DELAY, MAX_SPAM_DELAY = 6, 7
BREAK_PROBABILITY = 0.1  # 10% chance to take a break
BREAK_DURATION = (3, 4)

# Track spam state
spam_running = {session: False for session in clients}
spam_tasks = {}

# Admins who can control spam
AUTHORIZED_USERS = [7508462500, 1710597756, 6895497681, 7435756663]

async def auto_spam(client, session_name):
    """Handles sending spam messages with delays and flood wait handling."""
    while spam_running[session_name]:
        try:
            msg = random.choice(SPAM_MESSAGES)
            await client.send_message(TARGET_GROUP, msg)
            logging.info(f"{session_name}: Sent {msg}")

            async with client.action(TARGET_GROUP, "typing"):
                await asyncio.sleep(random.randint(2, 5))

            delay = random.randint(MIN_SPAM_DELAY, MAX_SPAM_DELAY)
            logging.info(f"{session_name}: Waiting {delay} sec before next message...")

            if random.random() < BREAK_PROBABILITY:
                break_time = random.randint(*BREAK_DURATION)
                logging.info(f"{session_name}: Taking a break for {break_time} sec...")
                await asyncio.sleep(break_time)

            await asyncio.sleep(delay)

        except FloodWaitError as e:
            logging.warning(f"{session_name}: FloodWait! Sleeping {e.seconds}s...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logging.error(f"{session_name}: Error - {e}")
            await asyncio.sleep(20)


async def start_spam(event, client, session_name):
    """Starts spamming when /startspam is received."""
    if event.sender_id in AUTHORIZED_USERS:
        logging.info(f"{session_name}: Received /startspam from {event.sender_id}")
        if not spam_running[session_name]:
            spam_running[session_name] = True
            spam_tasks[session_name] = asyncio.create_task(auto_spam(client, session_name))
            await event.reply("✅ Auto Spam Started!")
        else:
            await event.reply("⚠ Already Running!")


async def stop_spam(event, session_name):
    """Stops spamming when /stopspam is received."""
    if event.sender_id in AUTHORIZED_USERS:
        logging.info(f"{session_name}: Received /stopspam from {event.sender_id}")
        spam_running[session_name] = False
        if session_name in spam_tasks:
            spam_tasks[session_name].cancel()
            del spam_tasks[session_name]
        await event.reply("🛑 Stopping Spam!")


async def ensure_clients_connected():
    """Reconnects any disconnected clients."""
    for session_name, client in clients.items():
        if not client.is_connected():
            logging.warning(f"{session_name}: Disconnected, reconnecting...")
            try:
                await client.connect()
                logging.info(f"{session_name}: Reconnected successfully!")
            except Exception as e:
                logging.error(f"{session_name}: Failed to reconnect - {e}")


async def start_clients():
    """Starts all clients, registers event handlers, and starts spam."""
    for session_name, client in clients.items():
        try:
            await client.start()
            logging.info(f"{session_name}: Logged in successfully!")

            client.add_event_handler(lambda event, c=client, s=session_name: start_spam(event, c, s), events.NewMessage(pattern="/startspam"))
            client.add_event_handler(lambda event, s=session_name: stop_spam(event, s), events.NewMessage(pattern="/stopspam"))

            logging.info(f"{session_name}: Event handlers registered.")

        except Exception as e:
            logging.error(f"{session_name}: Failed to start - {e}")

    logging.info("✅ All bots started successfully.")

async def restart_spam():
    """Stops and restarts spam safely."""
    logging.info("🛑 Stopping spam...")
    for session_name in spam_running:
        spam_running[session_name] = False

    await asyncio.sleep(5)  # Small delay before restarting

    logging.info("♻ Restarting spam...")
    for session_name, client in clients.items():
        spam_running[session_name] = True
        spam_tasks[session_name] = asyncio.create_task(auto_spam(client, session_name))

async def monitor_clients():
    """Background task to ensure clients stay connected."""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        await ensure_clients_connected()


async def main():
    """Main entry point for running bots."""
    await start_clients()
    asyncio.create_task(monitor_clients())  # Start monitoring clients
    await asyncio.Future()  # Keep running indefinitely


def run_flask():
    """Runs the Flask app for health checks."""
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
