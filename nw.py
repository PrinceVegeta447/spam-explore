import os
import asyncio
import random
import logging
import threading
from flask import Flask, jsonify
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

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

# Fetch session strings from environment variables
SESSION_STRINGS = [os.getenv(f"SESSION_{i+1}") for i in range(8)]
SESSION_STRINGS = [s for s in SESSION_STRINGS if s]  # Remove None values

# Create clients using StringSession
clients = {f"Session{i+1}": TelegramClient(StringSession(s), API_ID, API_HASH) for i, s in enumerate(SESSION_STRINGS)}

# Target groups
SPAM_GROUP_ID = -1002258939999 # Change as needed
EXPLORE_GROUP_ID = -1002377798958 # Change as needed

# Spam settings
SPAM_MESSAGES = ["🎲", "🔥", "⚡", "💥", "✨"]
MIN_SPAM_DELAY, MAX_SPAM_DELAY = 6, 7
BREAK_PROBABILITY = 0.1  # 10% chance to take a break
BREAK_DURATION = (3, 4)

# Control flags for spam and explore
spam_running = {session: False for session in clients}
explore_running = {session: False for session in clients}
spam_tasks = {session: None for session in clients}
explore_tasks = {session: None for session in clients}

# Admins who can control the bot
AUTHORIZED_USERS = [7508462500, 1710597756, 6895497681, 7435756663, 6523029979]


async def auto_spam(client, session_name):
    """Sends randomized spam messages."""
    while spam_running[session_name]:
        try:
            msg = random.choice(SPAM_MESSAGES)
            await client.send_message(SPAM_GROUP_ID, msg)
            logging.info(f"{session_name}: Sent {msg}")

            delay = random.randint(MIN_SPAM_DELAY, MAX_SPAM_DELAY)
            if random.random() < BREAK_PROBABILITY:
                break_time = random.randint(*BREAK_DURATION)
                await asyncio.sleep(break_time)

            await asyncio.sleep(delay)

        except Exception as e:
            logging.error(f"{session_name}: Spam error - {e}")
            await asyncio.sleep(5)


async def start_spam(event, client, session_name):
    """Handles /startspam command."""
    if event.sender_id in AUTHORIZED_USERS:
        if not spam_running[session_name]:
            spam_running[session_name] = True
            spam_tasks[session_name] = asyncio.create_task(auto_spam(client, session_name))
            await event.reply("✅ Auto Spam Started!")
        else:
            await event.reply("⚠ Already Running!")


async def stop_spam(event, session_name):
    """Handles /stopspam command."""
    if event.sender_id in AUTHORIZED_USERS:
        spam_running[session_name] = False
        if spam_tasks[session_name]:
            spam_tasks[session_name].cancel()
            spam_tasks[session_name] = None
        await event.reply("🛑 Stopping Spam!")


async def handle_buttons(event, client):
    """Clicks a random inline button when a bot sends a message with buttons."""
    if event.reply_markup and hasattr(event.reply_markup, 'rows'):
        buttons = [btn for row in event.reply_markup.rows for btn in row.buttons if hasattr(btn, "data")]
        if buttons:
            button = random.choice(buttons)
            await asyncio.sleep(random.randint(3, 6))  # Human-like delay
            try:
                await event.click(buttons.index(button))
                logging.info(f"Session ({session_name}): Clicked button '{button.text}'")
            except Exception as e:
                logging.error(f"Session ({session_name}): Failed to click button - {e}")


async def auto_explore(client, session_name):
    """Handles the /explore automation."""
    @client.on(events.NewMessage(chats=EXPLORE_GROUP_ID))
    async def button_click_listener(event):
        if event.sender and event.sender.bot:
            await handle_buttons(event, client)

    while explore_running[session_name]:
        try:
            await client.send_message(EXPLORE_GROUP_ID, "/explore")
            logging.info(f"{session_name}: Sent /explore command")

            await asyncio.sleep(5)  # Wait for bot response
            delay = random.randint(305, 310)
            await asyncio.sleep(delay)

        except Exception as e:
            logging.error(f"{session_name}: Explore error - {e}")
            await asyncio.sleep(60)  # Retry after 60 seconds if there's an error


async def start_explore(event, client, session_name):
    """Handles /startexplore command."""
    if event.sender_id in AUTHORIZED_USERS:
        if not explore_running[session_name]:
            explore_running[session_name] = True
            explore_tasks[session_name] = asyncio.create_task(auto_explore(client, session_name))
            await event.reply("✅ Explore Automation Started!")
        else:
            await event.reply("⚠ Already Running!")


async def stop_explore(event, session_name):
    """Handles /stopexplore command."""
    if event.sender_id in AUTHORIZED_USERS:
        explore_running[session_name] = False
        if explore_tasks[session_name]:
            explore_tasks[session_name].cancel()
            explore_tasks[session_name] = None
        await event.reply("🛑 Stopping Explore!")


async def start_clients():
    """Starts all clients and registers event handlers."""
    for session_name, client in clients.items():
        await client.start()
        logging.info(f"{session_name}: Logged in successfully!")

        client.add_event_handler(lambda event, c=client, s=session_name: start_spam(event, c, s), events.NewMessage(pattern="/startspam"))
        client.add_event_handler(lambda event, s=session_name: stop_spam(event, s), events.NewMessage(pattern="/stopspam"))
        client.add_event_handler(lambda event, c=client, s=session_name: start_explore(event, c, s), events.NewMessage(pattern="/startexplore"))
        client.add_event_handler(lambda event, s=session_name: stop_explore(event, s), events.NewMessage(pattern="/stopexplore"))

        logging.info(f"{session_name}: Event handlers registered.")

    logging.info("✅ All bots started successfully.")


async def restart_disconnected_clients():
    """Checks if clients are disconnected and restarts them automatically."""
    while True:
        for session_name, client in clients.items():
            if not await client.is_user_authorized():
                logging.warning(f"{session_name}: Disconnected! Restarting...")
                try:
                    await client.connect()
                    if not await client.is_user_authorized():
                        logging.error(f"{session_name}: Reconnection failed.")
                    else:
                        logging.info(f"{session_name}: Reconnected successfully!")
                except Exception as e:
                    logging.error(f"{session_name}: Reconnection error - {e}")

        await asyncio.sleep(30)  # Check every 30 seconds


async def main():
    """Main entry point for running bots."""
    await start_clients()
    asyncio.create_task(restart_disconnected_clients())
    await asyncio.Future()  # Keep running indefinitely


def run_flask():
    """Runs the Flask app for health checks."""
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
