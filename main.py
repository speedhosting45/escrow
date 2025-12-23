#!/usr/bin/env python3
"""
Main entry point for the Escrow Bot
"""
import asyncio
import logging
import sys
from telethon import TelegramClient, events
from telethon.tl import types
from telethon.tl import functions

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
                try:
                    await event.respond(
                        "Please use the buttons below to navigate:",
                        buttons=get_main_menu_buttons()
                    )
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
        
        # Chat Action Handler for join notifications
        @self.client.on(events.ChatAction())
        async def chat_action_handler(event):
            """
            Handle user joins to groups where bot is admin
            """
            try:
                # Check if it's a user join event
                if event.user_joined or event.user_added:
                    # Get the user who joined
                    user = await event.get_user()
                    chat = await event.get_chat()
                    
                    # Get user mention
                    if user.username:
                        mention = f"@{user.username}"
                    else:
                        mention = f"[{user.first_name or 'User'}](tg://user?id={user.id})"
                    
                    # Send join notification to the group
                    await event.respond(
                        f"<b>USER {mention} JOINED THE GROUP !</b>",
                        parse_mode='html'
                    )
                    
                    # Log to console
                    print(f"\n👤 USER {mention} JOINED GROUP: {chat.title}")
                    
                    # Check participant count for link revocation
                    await self.check_and_revoke_link(event, chat)
                    
            except Exception as e:
                # Silently ignore errors in event handler
                pass
        
        # Message event handler for group messages
        @self.client.on(events.NewMessage(incoming=True))
        async def new_message_handler(event):
            """Handle new messages in groups"""
            try:
                # This can be extended for group-specific commands
                pass
            except Exception as e:
                pass
    
    async def check_and_revoke_link(self, event, chat):
        """
        Check if link needs to be revoked after 2 users join
        """
        try:
            # Get current participants count
            participants = await event.client.get_participants(chat, limit=10)
            
            # Count actual users (excluding bots if needed)
            user_count = 0
            for participant in participants:
                if not participant.bot:
                    user_count += 1
            
            # If we have 3 or more users (creator + 2+ users)
            if user_count >= 3:
                print(f"🔒 Group has {user_count} users, checking for link revocation...")
                
                # Try to get current invite links
                try:
                    # Export a new invite link (this doesn't revoke old ones)
                    new_link = await event.client(functions.messages.ExportChatInviteRequest(
                        peer=chat
                    ))
                    
                    # Send message about security update
                    await event.respond(
                        f"<b>⚠️ SECURITY UPDATE</b>\n\n"
                        f"<blockquote>Group has reached {user_count} members.\n"
                        f"Please use new invite link for additional invites.</blockquote>\n\n"
                        f"New admin link: {new_link.link}",
                        parse_mode='html'
                    )
                    
                    print(f"🔒 New invite link generated for group: {chat.title}")
                    
                except Exception as e:
                    print(f"Could not generate new link: {e}")
                    
        except Exception as e:
            print(f"Error checking participant count: {e}")
    
    async def run(self):
        """Run the bot"""
        try:
            print("🔐 Secure Escrow Bot Starting...")
            
            # Check config
            if not API_ID or not API_HASH or not BOT_TOKEN:
                print("❌ Missing configuration in .env file")
                print("Please set API_ID, API_HASH, and BOT_TOKEN")
                sys.exit(1)
            
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
            print("\n⚡ Features:")
            print("   • Auto group creation")
            print("   • Bot added as admin")
            print("   • Join notifications")
            print("   • Sequential numbering")
            print("\n⚡ Bot is listening for messages...")
            print("   Press Ctrl+C to stop")
            
            # Run until disconnected
            await self.client.run_until_disconnected()
            
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
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
            import traceback
            traceback.print_exc()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")

if __name__ == '__main__':
    main()
