from utils.texts import STATS_MESSAGE
from utils.buttons import get_back_button

async def handle_stats(event):
    """
    Handle stats button click
    """
    try:
        await event.edit(
            STATS_MESSAGE,
            buttons=get_back_button(),
            parse_mode='html'
        )
    except Exception as e:
        print(f"Error in stats handler: {e}")
        await event.answer("❌ An error occurred.", alert=True)
