#!/usr/bin/env python3
"""
Main entry point for the Escrow Bot - Fixed tracking
"""
import asyncio
import logging
import sys
from telethon import TelegramClient, events, Button
from telethon.tl import functions, types
import json
import os
import time
import re

# Import configuration
from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME

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
USER_ROLES_FILE = 'data/user_roles.json'

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

def load_user_roles():
    """Load user roles data"""
    if os.path.exists(USER_ROLES_FILE):
        with open(USER_ROLES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_roles(roles):
    """Save user roles data"""
    with open(USER_ROLES_FILE, 'w') as f:
        json.dump(roles, f, indent=2)

def get_user_display(user_obj):
    """Get clean display name for user"""
    if user_obj.username:
        return f"@{user_obj.username}"
    else:
        name = user_obj.first_name or f"User_{user_obj.id}"
        # Clean special characters
        name = re.sub(r'[^\w\s@#]', '', name)
        return name.strip() or f"User_{user_obj.id}"

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
        
        # Handle /begin command
        @self.client.on(events.NewMessage(pattern='/begin'))
        async def begin_handler(event):
            await self.handle_begin_command(event)
        
        # Delete Telegram system messages (group created, user added messages)
        @self.client.on(events.NewMessage)
        async def delete_system_messages(event):
            """Delete Telegram system messages automatically"""
            try:
                # Check if message is from Telegram (system message)
                if event.sender_id == 777000 or event.sender_id == 1087968824:  # Telegram IDs
                    print(f"🗑️ Deleting system message: {event.text[:50]}...")
                    await event.delete()
                    return
                
                # Also delete common system message patterns
                message_text = event.text or ""
                system_patterns = [
                    "created the group",
                    "added ",
                    "joined the group",
                    "left the group",
                    "was added",
                    "pinned a message"
                ]
                
                if any(pattern in message_text for pattern in system_patterns):
                    print(f"🗑️ Deleting system-like message: {message_text[:50]}...")
                    await event.delete()
                    return
                    
            except Exception as e:
                # Silently ignore errors when deleting messages
                pass
        
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
                    user_id = event.user_id
                    if not user_id:
                        return
                    
                    chat = await event.get_chat()
                    chat_id = str(chat.id)
                    
                    # Convert to string for negative IDs (groups)
                    if chat_id.startswith('-100'):
                        # For supergroups, store without -100 prefix for consistency
                        clean_chat_id = chat_id[4:]
                    else:
                        clean_chat_id = chat_id
                    
                    # Skip if bot
                    try:
                        user_obj = await event.client.get_entity(user_id)
                        if user_obj.bot:
                            return
                    except:
                        pass
                    
                    # Load groups data
                    groups = load_groups()
                    
                    # Try to find group by both ID formats
                    group_data = None
                    group_key = None
                    
                    # Try exact match first
                    if clean_chat_id in groups:
                        group_data = groups[clean_chat_id]
                        group_key = clean_chat_id
                    elif chat_id in groups:
                        group_data = groups[chat_id]
                        group_key = chat_id
                    else:
                        # Try to find by group name
                        for key, data in groups.items():
                            if data.get("name") == chat.title:
                                group_data = data
                                group_key = key
                                break
                    
                    if not group_data:
                        print(f"❌ Group {clean_chat_id} ({chat.title}) not found in groups data")
                        return
                    
                    # Initialize members list if not exists
                    if "members" not in group_data:
                        group_data["members"] = []
                    
                    # Add user if not already in list
                    if user_id not in group_data["members"]:
                        group_data["members"].append(user_id)
                        
                        # Update group data
                        groups[group_key] = group_data
                        save_groups(groups)
                        
                        # Check member count
                        member_count = len(group_data["members"])
                        print(f"👤 User {user_id} joined group: {chat.title} (Total: {member_count})")
                        
                        # When 2 users join, delete invite link
                        if member_count >= 2:
                            await self.delete_invite_link(event.client, chat)
                    
            except Exception as e:
                print(f"Error in chat action handler: {e}")
        
        # Handle role selection buttons
        @self.client.on(events.CallbackQuery(pattern=rb'role_'))
        async def role_handler(event):
            """Handle role selection (buyer/seller)"""
            try:
                # Get the user who clicked
                sender = await event.get_sender()
                if not sender:
                    await event.answer("❌ Cannot identify user", alert=True)
                    return
                
                data = event.data.decode('utf-8')
                chat = await event.get_chat()
                chat_id = str(chat.id)
                
                # Clean chat ID for comparison
                if chat_id.startswith('-100'):
                    clean_chat_id = chat_id[4:]
                else:
                    clean_chat_id = chat_id
                
                # Parse role from callback data
                if data.startswith('role_buyer_'):
                    role = "buyer"
                    role_name = "Buyer"
                    success_alert = "🔐 Buyer Role Selected\nBuyer role confirmed."
                    group_id = data.replace('role_buyer_', '')
                elif data.startswith('role_seller_'):
                    role = "seller"
                    role_name = "Seller"
                    success_alert = "🔐 Seller Role Selected\nSeller role confirmed."
                    group_id = data.replace('role_seller_', '')
                else:
                    return
                
                # Check if group_id matches (try both formats)
                if group_id != clean_chat_id and group_id != chat_id:
                    # Try to find group by name or other identifier
                    groups = load_groups()
                    found = False
                    for key, data in groups.items():
                        if key == group_id or data.get("name") == chat.title:
                            group_id = key
                            found = True
                            break
                    
                    if not found:
                        return
                
                # Load roles
                roles = load_user_roles()
                if group_id not in roles:
                    roles[group_id] = {}
                
                # Check if user already selected a role
                if str(sender.id) in roles[group_id]:
                    await event.answer(
                        "⛔ Role Already Chosen\nYour role has already been declared.",
                        alert=True
                    )
                    return
                
                # Check if role is already taken by someone else
                role_taken = any(u["role"] == role for u in roles[group_id].values())
                if role_taken:
                    await event.answer(
                        "⚠️ Role Already Taken\nPlease select the remaining role.",
                        alert=True
                    )
                    return
                
                # Save user's role
                roles[group_id][str(sender.id)] = {
                    "role": role,
                    "name": get_user_display(sender),
                    "user_id": sender.id,
                    "selected_at": time.time()
                }
                save_user_roles(roles)
                
                # Send success alert
                await event.answer(success_alert, alert=True)
                
                # Send role confirmation message to group
                if role == "buyer":
                    confirm_msg = f"""
<b>Buyer Role Confirmed</b>

<a href="tg://user?id={sender.id}">{get_user_display(sender)}</a> registered as <b>Buyer</b>.

Role cannot be changed.
"""
                else:
                    confirm_msg = f"""
<b>Seller Role Confirmed</b>

<a href="tg://user?id={sender.id}">{get_user_display(sender)}</a> registered as <b>Seller</b>.

Role cannot be changed.
"""
                
                await event.client.send_message(
                    chat,
                    confirm_msg,
                    parse_mode='html'
                )
                
                print(f"✅ {get_user_display(sender)} selected as {role_name} in group: {chat.title}")
                
                # Check if both roles are selected
                buyer_count = sum(1 for u in roles[group_id].values() if u["role"] == "buyer")
                seller_count = sum(1 for u in roles[group_id].values() if u["role"] == "seller")
                
                # When both buyer and seller have selected roles
                if buyer_count >= 1 and seller_count >= 1:
                    await self.send_roles_confirmed(event.client, chat, group_id, roles[group_id])
                
            except Exception as e:
                print(f"Error in role handler: {e}")
                await event.answer("❌ Error selecting role", alert=True)
    
    async def handle_begin_command(self, event):
        """Handle /begin command to start escrow session"""
        try:
            chat = await event.get_chat()
            user = await event.get_sender()
            chat_id = str(chat.id)
            
            # Clean chat ID for lookup
            if chat_id.startswith('-100'):
                clean_chat_id = chat_id[4:]
            else:
                clean_chat_id = chat_id
            
            # Load groups data
            groups = load_groups()
            
            # Try both ID formats
            group_data = None
            group_key = None
            
            if clean_chat_id in groups:
                group_data = groups[clean_chat_id]
                group_key = clean_chat_id
            elif chat_id in groups:
                group_data = groups[chat_id]
                group_key = chat_id
            else:
                # Try to find by group name
                for key, data in groups.items():
                    if data.get("name") == chat.title:
                        group_data = data
                        group_key = key
                        break
            
            if not group_data:
                print(f"❌ Group {clean_chat_id} ({chat.title}) not found in groups data")
                await event.reply("❌ Group not found in system.")
                return
            
            # Check if session already initiated
            if group_data.get("session_initiated", False):
                await event.reply("⚠️ Escrow session has already been initiated.")
                return
            
            # Check if we have 2 members
            members = group_data.get("members", [])
            if len(members) < 2:
                await event.reply("⏳ Waiting for both participants to join...")
                return
            
            # Get bot username
            bot_username = group_data.get("bot_username", BOT_USERNAME)
            if not bot_username:
                me = await self.client.get_me()
                bot_username = me.username
            
            # Get the two users
            user1_id = members[0]
            user2_id = members[1]
            
            try:
                user1 = await self.client.get_entity(user1_id)
                user2 = await self.client.get_entity(user2_id)
                
                user1_display = get_user_display(user1)
                user2_display = get_user_display(user2)
                
                # Format display
                display_text = f"{user1_display} • {user2_display}"
                
                # Format session initiation message
                message = f"""
<b>🔐 @{bot_username} P2P Escrow Session Initiated</b>

Participants: {display_text}

This escrow session is governed by verified rules.

<b>Please declare your role:</b>

<code>
Buyer  → Select Buyer role
Seller → Select Seller role
</code>

<b>Important:</b>
Role selection is final.
"""
                
                # Create role selection buttons
                buttons = [
                    [
                        Button.inline("Buyer", f"role_buyer_{group_key}".encode()),
                        Button.inline("Seller", f"role_seller_{group_key}".encode())
                    ]
                ]
                
                # Send session initiation message
                await self.client.send_message(
                    chat,
                    message,
                    parse_mode='html',
                    buttons=buttons
                )
                
                # Mark session as initiated
                group_data["session_initiated"] = True
                groups[group_key] = group_data
                save_groups(groups)
                
                print(f"🚀 Escrow session initiated by {get_user_display(user)} in group: {chat.title}")
                
            except Exception as e:
                print(f"Error getting user entities: {e}")
                await event.reply("❌ Error starting escrow session.")
                
        except Exception as e:
            print(f"Error handling /begin command: {e}")
    
    async def send_roles_confirmed(self, client, chat, group_id, user_roles):
        """Send roles confirmed message"""
        try:
            # Find buyer and seller
            buyer = None
            seller = None
            
            for user_id, data in user_roles.items():
                if data["role"] == "buyer" and not buyer:
                    buyer = data
                elif data["role"] == "seller" and not seller:
                    seller = data
            
            if not buyer or not seller:
                return
            
            # Format message
            message = f"""
<b>✅ Roles Confirmed</b>

<blockquote>
<b>Buyer:</b> {buyer['name']}  
<b>Seller:</b> {seller['name']}
</blockquote>

Wallet setup will be handled in next phase.
"""
            
            await client.send_message(
                chat,
                message,
                parse_mode='html'
            )
            
            print(f"💰 Roles confirmed in group: {chat.title}")
            
        except Exception as e:
            print(f"Error sending confirmation: {e}")
    
    async def delete_invite_link(self, client, chat):
        """Delete invite link when 2 users join"""
        try:
            print(f"🔒 Deleting invite link for group: {chat.title}")
            
            # Disable inviting for everyone
            try:
                await client(functions.messages.EditChatDefaultBannedRightsRequest(
                    peer=chat,
                    banned_rights=types.ChatBannedRights(
                        until_date=0,
                        invite_users=True
                    )
                ))
                print(f"✅ Invite permissions disabled")
            except Exception as e:
                print(f"⚠️ Could not disable invites: {e}")
            
        except Exception as e:
            print(f"❌ Error deleting invite link: {e}")

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
            print("   /begin - Initiate escrow session (in groups)")
            print("\n⚡ Features:")
            print("   • Auto-delete Telegram system messages")
            print("   • Creator anonymous admin")
            print("   • Clean group creation")
            print("   • Working /begin command")
            print("   • Role selection system")
            print("   • No auto-response to messages")
            print("\n⚡ Bot is listening for commands only...")
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
