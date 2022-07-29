import os, configparser
from telethon import TelegramClient, events

# Read configs
config = configparser.ConfigParser()
CONFIG_FILE = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, "config", "config_IDs.ini"))
config.read(CONFIG_FILE)

# Define the usernames
phone = config['Telegram']['phone']
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

# Create the client and connect
client = TelegramClient(session = "bot",
                        api_id = api_id,
                        api_hash= api_hash)

# async def test():
#     async for dialog in client.iter_dialogs():
#         print(f'{dialog.id}:{dialog.title}')
#
# client.start()
# client.loop.run_until_complete(test())