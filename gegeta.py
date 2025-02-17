from telethon import TelegramClient, events
import asyncio

# Your API ID, Hash, Phone Number, and Bot Details
api_id = 2587846
api_hash = '3fa173b2763d7e47971573944bd0971a'
phone_number = '+91 9359068981'
chat_id_to_message = 572621020  # The chat ID where the bot sends messages
message_text = '/hunt'
stop_words = ['Daily hunt limit reached', '✨ Shiny Pokémon found!']

# State flags for auto-typing and pausing
auto_typing = False
paused = False

# Initialize the client
client = TelegramClient('session_name', api_id, api_hash)

# Listener to check for commands in Saved Messages
@client.on(events.NewMessage(from_users= 6845208187)) # Listening to your user ID in Saved Messages
async def handler(event):
    global auto_typing, paused
    received_message = event.message.message
    print(f"Message received: {received_message}")  # Logging received message

    # Command-based handling
    if received_message == '/shiny':
        auto_typing = True
        paused = False
        print("Auto-typing started.")
    elif received_message == '/stop':
        auto_typing = False
        print("Auto-typing stopped.")
    elif received_message == '/pause':
        paused = True
        print("Auto-typing paused.")
    elif received_message == '/resume':
        paused = False
        print("Auto-typing resumed.")

# Listener to check for stop words specifically from chat ID 572621020
@client.on(events.NewMessage(chats=572621020))  # Listening to the specific chat ID 572621020
async def response_handler(event):
    global auto_typing
    response_message = event.message.message
    print(f"Response received from chat {chat_id_to_message}: {response_message}")  # Logging the response

    # Check if the response message matches any stop word
    if response_message in stop_words:
        auto_typing = False
        print(f"Auto-typing stopped due to stop word in response from chat {chat_id_to_message}: {response_message}")

# Function to send messages
async def send_messages():
    global auto_typing, paused
    while True:
        if auto_typing and not paused:
            await client.send_message(chat_id_to_message, message_text)
            print(f"Sent message to chat {chat_id_to_message}: {message_text}")
            await asyncio.sleep(3)  # Delay between sending messages
        await asyncio.sleep(1)  # Delay to prevent blocking the event loop

# Main function to start the client and message sending loop
async def main():
    await client.start(phone=phone_number)
    print("Client started. Listening for commands and responses...")
    asyncio.create_task(send_messages())  # Start the message sending loop
    await client.run_until_disconnected()  # Keep the client running

# Run the client
with client:
    client.loop.run_until_complete(main())