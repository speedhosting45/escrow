from telethon import events
from ..utils.texts import CREATE_MESSAGE
from ..utils.buttons import get_create_buttons

async def handle_create(event):
    """
    Handle create escrow button click
    """
    try:
        await event.edit(
            CREATE_MESSAGE,
            buttons=get_create_buttons(),
            parse_mode='html'
        )
    except Exception as e:
        print(f"Error in create handler: {e}")
        await event.answer("❌ An error occurred.", alert=True)

async def handle_create_p2p(event):
    """
    Handle P2P deal selection (placeholder)
    """
    try:
        await event.answer(
            "🤝 P2P Deal selected! This feature is coming soon...",
            alert=True
        )
    except Exception as e:
        print(f"Error in P2P handler: {e}")

async def handle_create_other(event):
    """
    Handle Other deal selection (placeholder)
    """
    try:
        await event.answer(
            "📦 Other Deal selected! This feature is coming soon...",
            alert=True
        )
    except Exception as e:
        print(f"Error in Other deal handler: {e}")
