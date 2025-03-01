import os
import asyncio
import random
import logging
import threading
from flask import Flask, jsonify
from telethon import TelegramClient, events
from telethon.errors import RPCError, ConnectionError, SessionPasswordNeededError

# Flask app for health check
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "running"}), 200

# Logging setup
logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s", level=logging.INFO)

# Telegram API credentials
API_ID = 20061115  # Replace with your API ID
API_HASH = "c30d56d90d59b3efc7954013c580e076"

# Session files
SESSIONS = ["session1", "session2", "session3", "session4", "session5", "session6", "session7", "session8", "session9"]

# Target group
TARGET_GROUP = -1002395952299  # Change as needed

# Spam messages and delays
SPAM_MESSAGES = ["🎲", "🔥", "⚡", "💥", "✨"]
MIN_SPAM_DELAY, MAX_SPAM_DELAY = 6, 7
BREAK_PROBABILITY = 0.1  # 10% chance to take a break
BREAK_DURATION = (10, 20)

# Track spam state and clients
spam_running = {session: False for session in SESSIONS}
clients = {}

async def start_client(session_name):
    """Start a TelegramClient session with auto-reconnect."""
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logging.warning(f"{session_name}: Not authorized! Login manually first.")
            return None

        logging.info(f"{session_name}: Logged in successfully!")
        clients[session_name] = client
        return client
    except SessionPasswordNeededError:
        logging.error(f"{session_name}: Two-factor authentication required!")
    except ConnectionError:
        logging.warning(f"{session_name}: Connection error. Retrying in 10 seconds...")
        await asyncio.sleep(10)
        return await start_client(session_name)
    except Exception as e:
        logging.error(f"{session_name}: Unexpected error - {e}")
    
    return None

async def auto_spam(client, session_name):
    """Sends spam messages with human-like behavior."""
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

        except Exception as e:
            error_msg = str(e)
            if "A wait of" in error_msg:  # FloodWait handling
                wait_time = int(error_msg.split()[3]) * 2
                logging.warning(f"{session_name}: FloodWait! Sleeping {wait_time} sec...")
                await asyncio.sleep(wait_time)
            else:
                logging.error(f"{session_name}: Error - {e}")
                await asyncio.sleep(20)

async def start_spam(event, client, session_name):
    """Starts spamming when /startspam is received."""
    if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:  
        if not spam_running[session_name]:
            spam_running[session_name] = True
            asyncio.create_task(auto_spam(client, session_name))
            await event.reply("✅ Auto Spam Started!")
        else:
            await event.reply("⚠ Already Running!")

async def stop_spam(event, session_name):
    """Stops spamming when /stopspam is received."""
    if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:  
        spam_running[session_name] = False
        await event.reply("🛑 Stopping Spam!")

async def monitor_clients():
    """Monitors and restarts disconnected clients."""
    while True:
        logging.info("🔍 Checking session status...")
        for session_name in SESSIONS:
            client = clients.get(session_name)
            if not client or not client.is_connected():
                logging.warning(f"{session_name} is disconnected! Restarting...")
                new_client = await start_client(session_name)
                if new_client:
                    clients[session_name] = new_client
                    new_client.add_event_handler(lambda event, c=new_client, s=session_name: start_spam(event, c, s), events.NewMessage(pattern="/startspam"))
                    new_client.add_event_handler(lambda event, s=session_name: stop_spam(event, s), events.NewMessage(pattern="/stopspam"))
        
        await asyncio.sleep(30)  # Check every 30 seconds

async def start_clients():
    """Starts all sessions and registers event handlers."""
    for session_name in SESSIONS:
        client = await start_client(session_name)
        if client:
            client.add_event_handler(lambda event, c=client, s=session_name: start_spam(event, c, s), events.NewMessage(pattern="/startspam"))
            client.add_event_handler(lambda event, s=session_name: stop_spam(event, s), events.NewMessage(pattern="/stopspam"))

    logging.info("✅ All bots started successfully.")
    asyncio.create_task(monitor_clients())  # Start monitoring loop

async def main():
    """Main function for running all bots."""
    await start_clients()
    logging.info("Bots are running safely...")
    await asyncio.Future()  # Keep running indefinitely

def run_flask():
    """Runs the Flask app for health checks."""
    app.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
