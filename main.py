#!/usr/bin/env python3
"""
Main entry point for the Escrow Bot
"""
import asyncio
import logging
import sys
from telethon import TelegramClient, events
from telethon.tl import functions
import json
import os

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

# Track groups for invite management
GROUPS_FILE = 'data/active_groups.json'

def load_groups():
    """Load active groups data"""
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_groups(groups):
    """Save active groups data"""
    with open(GROUPS_FILE, 'w') as f:
        json.dump(groups, f, indent=2)

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
                    
                    # Format user mention properly
                    if user.username:
                        mention = f"@{user.username}"
                    else:
                        # Clean formatting for name
                        name = user.first_name or "User"
                        # Remove any markdown/formatting from name
                        name = name.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
                        mention = f"{name}"
                    
                    # Send clean join notification
                    await event.respond(
                        f"<b>USER {mention} JOINED THE GROUP!</b>",
                        parse_mode='html'
                    )
                    
                    # Log to console
                    print(f"\n👤 USER {user.id} JOINED GROUP: {chat.title}")
                    
                    # Update join count and check for link revocation
                    await self.update_join_count(chat, user)
                    
            except Exception as e:
                print(f"Error in chat action handler: {e}")
    
    async def update_join_count(self, chat, new_user):
        """Update join count and revoke link if needed"""
        try:
            chat_id = str(chat.id)
            groups = load_groups()
            
            if chat_id in groups:
                group_data = groups[chat_id]
                
                # Increment join count
                if "joins" not in group_data:
                    group_data["joins"] = 0
                
                # Don't count the creator or bot
                if new_user.id != group_data.get("creator_id") and not new_user.bot:
                    group_data["joins"] += 1
                    print(f"📊 Group {chat.title}: {group_data['joins']} user(s) joined")
                
                # If 2 real users joined (not counting creator/bot)
                if group_data["joins"] >= 2 and not group_data.get("link_revoked", False):
                    print(f"🔒 Revoking invite link for group {chat.title}")
                    
                    # Revoke all invite links
                    await self.revoke_invite_links(chat)
                    
                    # Mark as revoked
                    group_data["link_revoked"] = True
                    group_data["revoked_at"] = asyncio.get_event_loop().time()
                    
                    # Save updated data
                    groups[chat_id] = group_data
                    save_groups(groups)
                    
                    # Notify in group
                    await self.client.send_message(
                        chat,
                        "⚠️ <b>SECURITY UPDATE</b>\n\n"
                        "<blockquote>Invite link has been revoked for security.</blockquote>",
                        parse_mode='html'
                    )
                
                # Save updated count
                groups[chat_id] = group_data
                save_groups(groups)
                
        except Exception as e:
            print(f"Error updating join count: {e}")
    
    async def revoke_invite_links(self, chat):
        """Revoke all invite links in the group"""
        try:
            # Revoke all invite links
            await self.client(functions.messages.EditChatDefaultBannedRightsRequest(
                peer=chat,
                banned_rights=types.ChatBannedRights(
                    until_date=0,
                    invite_users=True  # Disable inviting users
                )
            ))
            
            # Get and delete any existing invite links
            try:
                invites = await self.client(functions.messages.GetExportedChatInvitesRequest(
                    peer=chat,
                    admin_id=await self.client.get_me(),
                    limit=100
                ))
                
                for invite in invites.invites:
                    try:
                        await self.client(functions.messages.DeleteExportedChatInviteRequest(
                            peer=chat,
                            link=invite.link
                        ))
                    except:
                        pass
            except:
                pass
                
        except Exception as e:
            print(f"Error revoking links: {e}")

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
            print("\n⚡ Security Features:")
            print("   • Creator auto-promotion (anonymous)")
            print("   • Auto link revocation after 2 users")
            print("   • No new links shared publicly")
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
