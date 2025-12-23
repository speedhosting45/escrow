#!/usr/bin/env python3
"""
Main entry point for the Escrow Bot
"""
import asyncio
import logging
from telethon import TelegramClient, events

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

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class EscrowBot:
    def __init__(self):
        self.client = TelegramClient('escrow_bot', API_ID, API_HASH)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all event handlers"""
        
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await handle_start(event)
        
        @self.client.on(events.CallbackQuery(pattern=b'create'))
        async def create_handler(event):
            await handle_create(event)
        
        @self.client.on(events.CallbackQuery(pattern=b'create_p2p'))
        async def create_p2p_handler(event):
            await handle_create_p2p(event)
        
        @self.client.on(events.CallbackQuery(pattern=b'create_other'))
        async def create_other_handler(event):
            await handle_create_other(event)
        
        @self.client.on(events.CallbackQuery(pattern=b'stats'))
        async def stats_handler(event):
            await handle_stats(event)
        
        @self.client.on(events.CallbackQuery(pattern=b'about'))
        async def about_handler(event):
            await handle_about(event)
        
        @self.client.on(events.CallbackQuery(pattern=b'help'))
        async def help_handler(event):
            await handle_help(event)
        
        @self.client.on(events.CallbackQuery(pattern=b'back_to_main'))
        async def back_handler(event):
            try:
                await event.edit(
                    START_MESSAGE,
                    buttons=get_main_menu_buttons(),
                    parse_mode='html'
                )
            except Exception as e:
                logger.error(f"Error in back handler: {e}")
                await event.answer("❌ An error occurred.", alert=True)
        
        @self.client.on(events.NewMessage)
        async def message_handler(event):
            """Handle other messages"""
            if event.text and not event.text.startswith('/'):
                await event.respond(
                    "Please use the buttons below to navigate:",
                    buttons=get_main_menu_buttons()
                )
    
    async def run(self):
        """Run the bot"""
        try:
            print("🔐 Secure Escrow Bot Starting...")
            
            # Start the client
            await self.client.start(bot_token=BOT_TOKEN)
            
            # Get bot info
            me = await self.client.get_me()
            
            print(f"✅ Bot is running as @{me.username}")
            print(f"🤖 Bot ID: {me.id}")
            print(f"📛 Name: {me.first_name}")
            
            print("\n📋 Available Commands:")
            print("   /start - Start the bot")
            print("   📊 Stats - View statistics")
            print("   ➕ Create - Create new escrow")
            print("   ℹ️ About - About the bot")
            print("   ❓ Help - Help and support")
            print("\n⚡ Bot is listening for messages...")
            print("   Press Ctrl+C to stop")
            
            # Run until disconnected
            await self.client.run_until_disconnected()
            
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            print(f"\n❌ Error: {e}")
        finally:
            print("\n🔴 Bot shutdown complete")

def main():
    """Main function"""
    bot = EscrowBot()
    
    try:
        # Run the bot with proper event loop handling
        asyncio.run(bot.run())
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            # This is expected when stopping the bot
            print("\n👋 Bot stopped")
        else:
            print(f"\n❌ Unexpected error: {e}")

if __name__ == '__main__':
    main()
