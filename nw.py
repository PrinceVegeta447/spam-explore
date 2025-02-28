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

# Session files for multiple accounts
SESSIONS = ["session1.session", "session3.session", "session4.session", "session5.session", "session6.session", "session7.session", "session8.session", "session9.session", "session2.session"]

# Target group and bot interactions
TARGET_GROUP = -1002395952299  # Change as needed
EXPLORE_GROUP = -1002348881334  # Group where explore commands are sent

# Messages and delays
SPAM_MESSAGES = ["🎲", "🔥", "⚡", "💥", "✨"]  # More variety
MIN_SPAM_DELAY, MAX_SPAM_DELAY = 6, 8  # Increased delay for safety
MIN_EXPLORE_DELAY, MAX_EXPLORE_DELAY = 310, 325  # More delay for exploration
BREAK_PROBABILITY = 0.1  # 80% chance of taking a longer break
BREAK_DURATION = (10, 20)  # Break time range (10-20 min)

# Spam control per client
spam_running = {session: False for session in SESSIONS}

# Create clients for multiple sessions
clients = {session: TelegramClient(session, API_ID, API_HASH) for session in SESSIONS}

async def auto_spam(client, session_name):
    """Sends randomized spam messages with human-like behavior."""
    while spam_running[session_name]:
        try:
            msg = random.choice(SPAM_MESSAGES)
            await client.send_message(TARGET_GROUP, msg)
            
            # Mimic human behavior with typing action
            async with client.action(TARGET_GROUP, "typing"):
                await asyncio.sleep(random.randint(2, 5))  
            
            delay = random.randint(MIN_SPAM_DELAY, MAX_SPAM_DELAY)
            logging.info(f"{session_name}: Sent {msg} | Waiting {delay} sec...")
            
            if random.random() < BREAK_PROBABILITY:  # Introduce occasional breaks
                break_time = random.randint(*BREAK_DURATION)
                logging.info(f"{session_name}: Taking a break for {break_time} sec...")
                await asyncio.sleep(break_time)
            
            await asyncio.sleep(delay)
        except Exception as e:
            error_msg = str(e)
            if "A wait of" in error_msg:  # FloodWait handling
                wait_time = int(error_msg.split()[3]) * 2  # Double the wait time
                logging.warning(f"{session_name}: FloodWait! Sleeping {wait_time} sec...")
                await asyncio.sleep(wait_time)
            else:
                logging.error(f"{session_name}: Error - {e}")
                await asyncio.sleep(20)

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
    """Starts spam when /startspam is received, ensuring safe limits."""
    global spam_running
    if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:  # Replace with authorized user IDs
        if not spam_running[session_name]:
            spam_running[session_name] = True
            asyncio.create_task(auto_spam(client, session_name))
            await event.reply("✅ Safe Auto Spam Started!")
        else:
            await event.reply("⚠ Already Running!")

async def stop_spam(event, session_name):
    """Stops spam when /stopspam is received."""
    global spam_running
    if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:  # Replace with authorized user IDs
        spam_running[session_name] = False
        await event.reply("🛑 Stopping Spam!")

async def start_clients():
    """Starts all clients and registers event handlers."""
    tasks = []
    for session_name, client in clients.items():
        await client.start()
        client.add_event_handler(handle_buttons, events.NewMessage(chats=EXPLORE_GROUP))
        client.add_event_handler(lambda event, c=client, s=session_name: start_spam(event, c, s), events.NewMessage(pattern="/startspam"))
        client.add_event_handler(lambda event, s=session_name: stop_spam(event, s), events.NewMessage(pattern="/stopspam"))
        tasks.append(asyncio.create_task(send_explore(client, session_name)))
    
    logging.info("All bots started successfully.")
    await asyncio.gather(*tasks)

async def main():
    """Main entry point for running bots."""
    await start_clients()
    logging.info("Bots are running safely...")
    await asyncio.Future()  # Keep running indefinitely

# Start the Flask health check in the background
def run_flask():
    app.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
