import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# Import configuration
from config import API_ID, API_HASH, BOT_TOKEN

# Import handlers
from handlers.start import handle_start
from handlers.create import handle_create, handle_create_p2p, handle_create_other
from handlers.stats import handle_stats
from handlers.about import handle_about
from handlers.help import handle_help

# Import utilities
from utils.texts import START_MESSAGE
from utils.buttons import get_main_menu_buttons

# Initialize the client
bot = TelegramClient('escrow_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

print("🔐 Secure Escrow Bot Starting...")

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command"""
    await handle_start(event)

@bot.on(events.CallbackQuery(pattern=b'create'))
async def create_handler(event):
    """Handle create button"""
    await handle_create(event)

@bot.on(events.CallbackQuery(pattern=b'create_p2p'))
async def create_p2p_handler(event):
    """Handle P2P deal selection"""
    await handle_create_p2p(event)

@bot.on(events.CallbackQuery(pattern=b'create_other'))
async def create_other_handler(event):
    """Handle other deal selection"""
    await handle_create_other(event)

@bot.on(events.CallbackQuery(pattern=b'stats'))
async def stats_handler(event):
    """Handle stats button"""
    await handle_stats(event)

@bot.on(events.CallbackQuery(pattern=b'about'))
async def about_handler(event):
    """Handle about button"""
    await handle_about(event)

@bot.on(events.CallbackQuery(pattern=b'help'))
async def help_handler(event):
    """Handle help button"""
    await handle_help(event)

@bot.on(events.CallbackQuery(pattern=b'back_to_main'))
async def back_handler(event):
    """Handle back to main menu"""
    try:
        await event.edit(
            START_MESSAGE,
            buttons=get_main_menu_buttons(),
            parse_mode='html'
        )
    except Exception as e:
        print(f"Error in back handler: {e}")
        await event.answer("❌ An error occurred.", alert=True)

@bot.on(events.NewMessage)
async def message_handler(event):
    """Handle other messages"""
    if event.text and not event.text.startswith('/'):
        # If it's a regular message (not a command), show main menu
        await event.respond(
            "Please use the buttons below to navigate:",
            buttons=get_main_menu_buttons()
        )

async def main():
    """Main function to run the bot"""
    print("✅ Bot is running...")
    print("🤖 Bot Info:")
    me = await bot.get_me()
    print(f"   Username: @{me.username}")
    print(f"   ID: {me.id}")
    print(f"   Name: {me.first_name}")
    print("\n📋 Commands available:")
    print("   /start - Start the bot")
    print("   📊 Stats - View statistics")
    print("   ➕ Create - Create new escrow")
    print("   ℹ️ About - About the bot")
    print("   ❓ Help - Help and support")
    print("\n⚡ Press Ctrl+C to stop")

    await bot.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped.")
