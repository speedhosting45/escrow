from utils.texts import HELP_MESSAGE
from utils.buttons import get_back_button

async def handle_help(event):
    """
    Handle help button click
    """
    try:
        await event.edit(
            HELP_MESSAGE,
            buttons=get_back_button(),
            parse_mode='html'
        )
    except Exception as e:
        print(f"Error in help handler: {e}")
        await event.answer("❌ An error occurred.", alert=True)
