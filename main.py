#!/usr/bin/env python3
"""
Main entry point for the Escrow Bot
"""
import asyncio
import logging
import sys
from telethon import TelegramClient, events
from telethon.tl import functions, types
import json
import os
import html

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

def sanitize_text(text):
    """Remove markdown and clean text for HTML display"""
    if not text:
        return "User"
    
    # Remove markdown brackets and other formatting
    text = str(text)
    text = html.escape(text)  # Escape HTML
    text = text.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
    text = text.replace('*', '').replace('_', '').replace('`', '').replace('~', '')
    
    # Remove any remaining special characters that break formatting
    text = ''.join(char for char in text if ord(char) < 128 or char.isspace())
    
    return text.strip() or "User"

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
                    
                    # Clean and sanitize the user's name
                    user_name = user.first_name or "User"
                    clean_name = sanitize_text(user_name)
                    
                    # Use username if available, otherwise use cleaned name
                    if user.username:
                        mention = f"@{user.username}"
                    else:
                        mention = clean_name
                    
                    # Send clean join notification
                    join_message = f"<b>USER {mention} JOINED THE GROUP!</b>"
                    await event.respond(
                        join_message,
                        parse_mode='html'
                    )
                    
                    # Log to console
                    print(f"\n👤 USER {user.id} ({clean_name}) JOINED GROUP: {chat.title}")
                    
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
                
                # Initialize joins if not exists
                if "joins" not in group_data:
                    group_data["joins"] = 0
                if "members" not in group_data:
                    group_data["members"] = []
                
                # Don't count the creator or bot
                creator_id = group_data.get("creator_id")
                if (creator_id and new_user.id == creator_id) or new_user.bot:
                    return  # Don't count creator or bot
                
                # Count unique users only once
                if new_user.id not in group_data["members"]:
                    group_data["joins"] += 1
                    group_data["members"].append(new_user.id)
                    print(f"📊 Group {chat.title}: {group_data['joins']} user(s) joined")
                
                # If 2 real users joined (not counting creator/bot)
                if group_data["joins"] >= 2 and not group_data.get("link_revoked", False):
                    print(f"🔒 REVOKING invite link for group {chat.title}")
                    
                    # REVOKE the invite link (delete it)
                    revoked = await self.revoke_invite_link(chat)
                    
                    if revoked:
                        # Mark as revoked
                        group_data["link_revoked"] = True
                        group_data["revoked_at"] = asyncio.get_event_loop().time()
                        
                        # Save updated data
                        groups[chat_id] = group_data
                        save_groups(groups)
                        
                        # Send notification WITHOUT new link
                        await self.client.send_message(
                            chat,
                            "⚠️ <b>SECURITY UPDATE</b>\n\n"
                            "<blockquote>Invite link has been revoked and deleted.\n"
                            "No new links will be generated.</blockquote>",
                            parse_mode='html'
                        )
                        print(f"✅ Link revoked for group: {chat.title}")
                    else:
                        print(f"❌ Failed to revoke link for group: {chat.title}")
                
                # Save updated count
                groups[chat_id] = group_data
                save_groups(groups)
                
        except Exception as e:
            print(f"Error updating join count: {e}")
    
    async def revoke_invite_link(self, chat):
        """Revoke and delete the current invite link"""
        try:
            # First, disable invite permissions for everyone
            await self.client(functions.messages.EditChatDefaultBannedRightsRequest(
                peer=chat,
                banned_rights=types.ChatBannedRights(
                    until_date=0,
                    invite_users=True  # Disable inviting users for everyone
                )
            ))
            
            # Try to get and delete any existing invite links
            try:
                # Get all invite links
                result = await self.client(functions.messages.GetExportedChatInvitesRequest(
                    peer=chat,
                    admin_id=await self.client.get_me(),
                    limit=100
                ))
                
                if hasattr(result, 'invites') and result.invites:
                    for invite in result.invites:
                        try:
                            # Delete the invite link
                            await self.client(functions.messages.DeleteExportedChatInviteRequest(
                                peer=chat,
                                link=invite.link
                            ))
                            print(f"🗑️ Deleted invite link: {invite.link}")
                        except Exception as e:
                            print(f"⚠️ Could not delete link {invite.link}: {e}")
                else:
                    print(f"ℹ️ No existing invite links found for {chat.title}")
                    
            except Exception as e:
                print(f"⚠️ Could not get existing invites: {e}")
            
            # Also disable admin's ability to create new invites
            try:
                # Get bot's current admin rights
                me = await self.client.get_me()
                
                # Update bot's admin rights to remove invite permission
                await self.client(functions.channels.EditAdminRequest(
                    channel=chat,
                    user_id=me,
                    admin_rights=types.ChatAdminRights(
                        change_info=True,
                        post_messages=True,
                        edit_messages=True,
                        delete_messages=True,
                        ban_users=True,
                        invite_users=False,  # CRITICAL: Disable invite permission
                        pin_messages=True,
                        add_admins=False,
                        anonymous=False,
                        manage_call=True,
                        other=True
                    ),
                    rank="Bot Admin"
                ))
                print(f"🔒 Disabled bot's invite permission for {chat.title}")
            except Exception as e:
                print(f"⚠️ Could not update bot permissions: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error revoking link: {e}")
            return False

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
            print("   • NO NEW LINKS generated")
            print("   • Clean join announcements")
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
