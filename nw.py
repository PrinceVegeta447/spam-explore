import os
import asyncio
import random
import logging
import threading
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

# Session files for multiple accounts
SESSIONS = ["session1.session", "session2.session", "session3.session", "session4.session", "session5.session", "session6.session", "session7.session", "session8.session", "session9.session"]

# Target group and explore group
TARGET_GROUP = -1002395952299  # Change as needed
EXPLORE_GROUP = -1002377798958  # Group where explore commands are sent

# Messages and delays
SPAM_MESSAGES = ["💫", "🔥", "⚡", "💥", "✨", "🎲"]
MIN_SPAM_DELAY, MAX_SPAM_DELAY = 4, 7
MIN_EXPLORE_DELAY, MAX_EXPLORE_DELAY = 305, 310
BREAK_PROBABILITY = 0.1
BREAK_DURATION = (10, 20)

# Spam and explore control per client
spam_running = {session: False for session in SESSIONS}
explore_running = {session: True for session in SESSIONS}

# Create clients for multiple sessions
clients = {session: TelegramClient(session, API_ID, API_HASH) for session in SESSIONS}

async def auto_spam(client, session_name):
    """Sends spam messages while ensuring explore is paused."""
    global explore_running
    explore_running[session_name] = False  # Stop exploring when spam starts
    while spam_running[session_name]:
        try:
            msg = random.choice(SPAM_MESSAGES)
            await client.send_message(TARGET_GROUP, msg)
            async with client.action(TARGET_GROUP, "typing"):
                await asyncio.sleep(random.randint(2, 5))

            delay = random.randint(MIN_SPAM_DELAY, MAX_SPAM_DELAY)  
            logging.info(f"{session_name}: Sent {msg} | Waiting {delay} sec...")  
            
            if random.random() < BREAK_PROBABILITY:  
                break_time = random.randint(*BREAK_DURATION)  
                logging.info(f"{session_name}: Taking a break for {break_time} sec...")  
                await asyncio.sleep(break_time)  
            
            await asyncio.sleep(delay)  
        except Exception as e:  
            logging.error(f"{session_name}: Error - {e}")  
            await asyncio.sleep(20)  
    
    explore_running[session_name] = True  # Resume explore when spam stops

async def send_explore(client, session_name):
    """Sends /explore command only when exploring is active."""
    while True:
        if explore_running[session_name]:
            try:
                await client.send_message(EXPLORE_GROUP, "/explore")
                logging.info(f"{session_name}: Sent /explore")
            except Exception as e:
                logging.error(f"{session_name}: Failed to send /explore - {e}")

            delay = random.randint(MIN_EXPLORE_DELAY, MAX_EXPLORE_DELAY)
            logging.info(f"{session_name}: Waiting {delay} sec before next /explore...")
            await asyncio.sleep(delay)
        else:
            await asyncio.sleep(5)  # Check again after 5 sec if explore is paused

async def handle_buttons(event):
    """Clicks a random inline button only in the explore group."""
    if event.chat_id == EXPLORE_GROUP and event.reply_markup and hasattr(event.reply_markup, 'rows'):
        buttons = [btn for row in event.reply_markup.rows for btn in row.buttons if hasattr(btn, "data")]

        if buttons:
            button = random.choice(buttons)
            await asyncio.sleep(random.randint(2, 5))  # Random delay before clicking
            try:
                await event.click(buttons.index(button))
                logging.info(f"Clicked a button in response to {event.sender_id} in explore group")
            except Exception as e:
                logging.error(f"Failed to click a button: {e}")

async def start_spam(event, client, session_name):
    """Starts spam and pauses explore."""
    if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:
        if not spam_running[session_name]:
            spam_running[session_name] = True
            explore_running[session_name] = False  # Pause explore
            asyncio.create_task(auto_spam(client, session_name))
            await event.reply("✅ Auto Spam Started! (Explore Paused)")
        else:
            await event.reply("⚠ Already Running!")

async def stop_spam(event, session_name):
    """Stops spam and resumes explore."""
    if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:
        spam_running[session_name] = False
        explore_running[session_name] = True  # Resume explore
        await event.reply("🛑 Stopping Spam! (Explore Resumed)")

async def start_clients():
    """Starts all clients and registers event handlers."""
    tasks = []
    for session_name, client in clients.items():
        await client.start()
        client.add_event_handler(lambda event, c=client, s=session_name: start_spam(event, c, s), events.NewMessage(pattern=r"\?startspam"))
        client.add_event_handler(lambda event, s=session_name: stop_spam(event, s), events.NewMessage(pattern=r"\?stopspam"))
        client.add_event_handler(handle_buttons, events.NewMessage())  # Handle button clicks only in explore group
        tasks.append(asyncio.create_task(send_explore(client, session_name)))
    
    logging.info("All bots started successfully.")  
    await asyncio.gather(*tasks)

async def main():
    """Main entry point for running bots."""
    await start_clients()
    logging.info("Bots are running safely...")
    await asyncio.Future()

# Start the Flask health check in the background
def run_flask():
    app.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
