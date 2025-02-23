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
SESSIONS = ["session1.session", "session2.session", "session3.session", "session4.session", "session5.session", "session6.session", "session7.session"]

# Target group and bot interactions
TARGET_GROUP = -1002395952299  # Change as needed
EXPLORE_GROUP = -1002377798958  # Group where explore commands are sent
BOTS = ["@CollectCricketersBot", "@CollectYourPlayerxBot"]

# Messages and delays
SPAM_MESSAGES = ["🎲", "🔥", "⚡", "💥", "✨"]  # More variety
MIN_SPAM_DELAY, MAX_SPAM_DELAY = 6, 8  # Increased delay for safety
MIN_EXPLORE_DELAY, MAX_EXPLORE_DELAY = 310, 325  # More delay for exploration
BREAK_PROBABILITY = 0.4  # 80% chance of taking a longer break
BREAK_DURATION = (30, 60)  # Break time range (10-20 min)

# Control flags
spam_running = {session: False for session in SESSIONS}
explore_running = {session: False for session in SESSIONS}

# Create clients for multiple sessions
clients = {session: TelegramClient(session, API_ID, API_HASH) for session in SESSIONS}

async def auto_spam(client, session_name):
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

async def send_explore(client, session_name):
    while explore_running[session_name]:
        for bot in BOTS:
            try:
                await client.send_message(EXPLORE_GROUP, f"/explore {bot}")
                logging.info(f"{session_name}: Sent /explore to {bot}")
            except Exception as e:
                logging.error(f"{session_name}: Failed to send /explore - {e}")
            delay = random.randint(MIN_EXPLORE_DELAY, MAX_EXPLORE_DELAY)
            logging.info(f"{session_name}: Waiting {delay} sec before next /explore...")
            await asyncio.sleep(delay)

async def handle_buttons(event):
    if event.reply_markup and hasattr(event.reply_markup, 'rows'):
        buttons = [btn for row in event.reply_markup.rows for btn in row.buttons if hasattr(btn, "data")]
        if buttons:
            button = random.choice(buttons)
            await asyncio.sleep(random.randint(3, 6))
            try:
                await event.click(buttons.index(button))
                logging.info(f"Clicked a button in response to {event.sender_id}")
            except Exception as e:
                logging.error(f"Failed to click button: {e}")

async def start_spam(event, client, session_name):
    if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:
        if not spam_running[session_name]:
            spam_running[session_name] = True
            asyncio.create_task(auto_spam(client, session_name))
            await event.reply("✅ Safe Auto Spam Started!")
        else:
            await event.reply("⚠ Already Running!")

async def stop_spam(event, session_name):
    if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:
        spam_running[session_name] = False
        await event.reply("🛑 Stopping Spam!")

async def start_explore(event, client, session_name):
    if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:
        if not explore_running[session_name]:
            explore_running[session_name] = True
            asyncio.create_task(send_explore(client, session_name))
            await event.reply("✅ Explore Mode Started!")
        else:
            await event.reply("⚠ Already Running!")

async def stop_explore(event, session_name):
    if event.sender_id in [7508462500, 1710597756, 6895497681, 7435756663]:
        explore_running[session_name] = False
        await event.reply("🛑 Stopping Explore Mode!")

async def start_clients():
    tasks = []
    for session_name, client in clients.items():
        await client.start()
        client.add_event_handler(handle_buttons, events.NewMessage(chats=EXPLORE_GROUP))
        client.add_event_handler(lambda event, c=client, s=session_name: start_spam(event, c, s), events.NewMessage(pattern="/startspam"))
        client.add_event_handler(lambda event, s=session_name: stop_spam(event, s), events.NewMessage(pattern="/stopspam"))
        client.add_event_handler(lambda event, c=client, s=session_name: start_explore(event, c, s), events.NewMessage(pattern="/startexplore"))
        client.add_event_handler(lambda event, s=session_name: stop_explore(event, s), events.NewMessage(pattern="/stopexplore"))
        tasks.append(asyncio.create_task(send_explore(client, session_name)))
    logging.info("All bots started successfully.")
    await asyncio.gather(*tasks)

async def main():
    await start_clients()
    logging.info("Bots are running safely...")
    await asyncio.Future()

def run_flask():
    app.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
