#!/usr/bin/env python3
"""
Main entry point for the Escrow Bot
"""
import asyncio
import logging
import sys
from telethon import TelegramClient, events
from telethon.errors import MessageNotModifiedError

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
            except MessageNotModifiedError:
                # Message already has this content
                await event.answer("✅ Main menu", alert=False)
            except Exception as e:
                logger.error(f"Error in back handler: {e}")
                try:
                    await event.answer("❌ An error occurred.", alert=True)
                except:
                    pass
        # Add this to your main.py in the setup_handlers() method:

@self.client.on(events.ChatAction)
async def chat_action_handler(event):
    """
    Handle user joins to groups
    """
    try:
        # Check if it's a user join
        if event.user_joined or event.user_added:
            user = await event.get_user()
            chat = await event.get_chat()
            
            # Get user info
            username = f"@{user.username}" if user.username else f"User_{user.id}"
            
            # Send notification to the group
            await event.reply(
                f"<b>USER {username} JOINED THE GROUP !</b>\n\n"
                f"Welcome to the escrow group!",
                parse_mode='html'
            )
            print(f"👤 {username} joined group: {chat.title}")
            
            # Check if we need to revoke link after 2 users join
            await check_and_revoke_link(event, chat)
            
    except Exception as e:
        print(f"Error in chat action handler: {e}")

async def check_and_revoke_link(event, chat):
    """
    Check if link needs to be revoked after 2 users join
    """
    try:
        # Get current participants count
        participants = await event.client.get_participants(chat)
        
        # If we have 3 participants (creator + 2 users)
        if len(participants) >= 3:
            # Try to revoke the current invite link
            try:
                await event.client(functions.messages.EditChatDefaultBannedRightsRequest(
                    peer=chat,
                    banned_rights=types.ChatBannedRights(
                        until_date=0,
                        view_messages=True,
                        send_messages=True,
                        send_media=True,
                        send_stickers=True,
                        send_gifs=True,
                        send_games=True,
                        send_inline=True,
                        embed_links=True,
                        send_polls=True,
                        change_info=True,
                        invite_users=False,  # Keep invite ability for admin
                        pin_messages=True
                    )
                ))
                
                # Create new invite link
                new_link = await event.client(functions.messages.ExportChatInviteRequest(
                    peer=chat
                ))
                
                # Send message about new link
                await event.respond(
                    f"<b>⚠️ SECURITY UPDATE</b>\n\n"
                    f"<blockquote>Old invite link has been revoked.\n"
                    f"New invite link generated for admin use.</blockquote>\n\n"
                    f"New link: {new_link.link}",
                    parse_mode='html'
                )
                print(f"🔒 Invite link revoked for group: {chat.title}")
                
            except Exception as e:
                print(f"Could not revoke link: {e}")
                
    except Exception as e:
        print(f"Error checking participant count: {e}")
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
