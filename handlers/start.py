from telethon import events
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.texts import START_MESSAGE
from utils.buttons import get_main_menu_buttons

async def handle_start(event):
    """
    Handle /start command
    """
    try:
        await event.respond(
            START_MESSAGE,
            buttons=get_main_menu_buttons(),
            parse_mode='html'
        )
    except Exception as e:
        print(f"Error in start handler: {e}")
        await event.respond("❌ An error occurred. Please try again.")
