import os, logging

from connectors.telegram_connector import client
from message_parser.text_parser import MessageParser
from telethon import events
from telethon.tl.types import PeerUser
from blotter.daily_blotter import DailyBlotter
from datetime import datetime
import json

# Chat ID = -1001238535538
# -1001633536129:Test
# Global objects
blotter = DailyBlotter()

# Default position size
POSITION_SIZE = 25
message_parser = MessageParser(size = POSITION_SIZE)

# Initialize logger
logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), "logging", 'trades.log'))

@client.on(event=events.NewMessage(chats=[-1001238535538, -1001633536129]))
@client.on(event=events.MessageEdited(chats=[-1001238535538, -1001633536129]))
async def handler(event):
    # Get the time the trade was executed
    message_reception_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S .%f") + "MS"

    # Raw input text
    input_text = event.raw_text

    # Parse message parameters
    message_json = message_parser.get_trade_info(input_text, edited_message=isinstance(event,
                                                                                       events.messageedited.MessageEdited.Event))

    # Use parameters to implement trade
    blotter_message_json = blotter.trade_position(message_json)

    # Define message reception stamp
    blotter_message_json["PYTHON_message_reception_timestamp"] = message_reception_stamp

    # Prettify final json message
    final_message = json.dumps(blotter_message_json, indent=4, sort_keys=True)

    # Print message
    print(final_message)

    # Send message or file depending on size
    if len(final_message) < 4096:
        message_sent = await client.send_message(PeerUser(user_id=-1001633536129), final_message)
    else:
        # Write file to location
        with open("message.json", "w") as outfile:
            outfile.write(final_message)

        # Send file
        message_sent = await client.send_file(PeerUser(user_id=-1001633536129), file="message.json",
                                              force_document=True)

        # Delete file
        os.remove('message.json')

client.start()
client.run_until_disconnected()
