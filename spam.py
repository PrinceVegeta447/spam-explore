import os
import asyncio
import random
import logging
from flask import Flask, jsonify
from telethon import TelegramClient, events

# Flask app for health checks
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "running"}), 200

# Logging setup
logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s", level=logging.INFO)

# Telegram API credentials
API_ID = 20061115  # Replace with your API ID
API_HASH = "c30d56d90d59b3efc7954013c580e076"

# Session files for 5 accounts (store them in the same directory)
SESSIONS = ["session_1.session", "session_2.session", "session_3.session", "session_4.session", "session_5.session"]

# Target group and bot interactions
TARGET_GROUP = -1002395952299  # Change as needed
EXPLORE_GROUP = -1002348881334  # Group where explore commands are sent
BOTS = ["@CollectCricketersBot", "@CollectYourPlayerxBot"]

# Spam messages list
SPAM_MESSAGES = ["🎲"]
MIN_SPAM_DELAY, MAX_SPAM_DELAY = 6, 7  # Delay range for spamming
MIN_EXPLORE_DELAY, MAX_EXPLORE_DELAY = 310, 330  # Delay range for /explore

# Spam control flag
spam_running = False

# Create clients for multiple sessions
clients = [TelegramClient(session, API_ID, API_HASH) for session in SESSIONS]

async def auto_spam(client):
    """Sends random spam messages in the target group."""
    global spam_running
    spam_running = True
    while spam_running:
        try:
            msg = random.choice(SPAM_MESSAGES)
            await client.send_message(TARGET_GROUP, msg)
            delay = random.randint(MIN_SPAM_DELAY, MAX_SPAM_DELAY)
            logging.info(f"Sent: {msg} | Waiting {delay} sec...")
            await asyncio.sleep(delay)
        except Exception as e:
            error_msg = str(e)
            if "A wait of" in error_msg:  # FloodWait handling
                wait_time = int(error_msg.split()[3])
                logging.warning(f"FloodWait triggered! Sleeping for {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logging.error(f"Unexpected error: {e}")
                await asyncio.sleep(10)

async def send_explore(client):
    """Sends /explore command to bots at regular intervals."""
    while True:
        for bot in BOTS:
            try:
                await client.send_message(EXPLORE_GROUP, f"/explore {bot}")
                logging.info(f"Sent /explore to {bot}")
            except Exception as e:
                logging.error(f"Failed to send /explore to {bot}: {e}")
            delay = random.randint(MIN_EXPLORE_DELAY, MAX_EXPLORE_DELAY)
            logging.info(f"Waiting {delay} seconds before next /explore...")
            await asyncio.sleep(delay)

async def handle_buttons(event):
    """Clicks random inline buttons when bots send messages with buttons."""
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

async def start_clients():
    """Starts all clients and registers event handlers."""
    tasks = []
    for client in clients:
        await client.start()
        client.add_event_handler(handle_buttons, events.NewMessage(chats=EXPLORE_GROUP))
        tasks.append(asyncio.create_task(send_explore(client)))
    
    logging.info("All bots started successfully.")
    await asyncio.gather(*tasks)

async def main():
    """Main entry point for running bots."""
    await start_clients()
    logging.info("Bots are running...")
    await asyncio.Future()  # Keep running indefinitely

# Start the Flask health check in the background
def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
