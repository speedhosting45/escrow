from utils.texts import ABOUT_MESSAGE
from utils.buttons import get_back_button

async def handle_about(event):
    """
    Handle about button click
    """
    try:
        await event.edit(
            ABOUT_MESSAGE,
            buttons=get_back_button(),
            parse_mode='html'
        )
    except Exception as e:
        print(f"Error in about handler: {e}")
        await event.answer("❌ An error occurred.", alert=True)
