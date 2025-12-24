#!/usr/bin/env python3
"""
Main entry point for the Escrow Bot - Fixed with proper text imports
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
from utils.texts import (
    START_MESSAGE, CREATE_MESSAGE, P2P_CREATED_MESSAGE, OTHER_CREATED_MESSAGE,
    WELCOME_MESSAGE, SESSION_INITIATED_MESSAGE, ROLE_ANNOUNCEMENT_MESSAGE,
    BUYER_CONFIRMED_MESSAGE, SELLER_CONFIRMED_MESSAGE, 
    ROLE_ALREADY_CHOSEN_MESSAGE, ROLE_ALREADY_TAKEN_MESSAGE,
    WALLET_SETUP_MESSAGE, ESCROW_READY_MESSAGE, STATS_MESSAGE,
    ABOUT_MESSAGE, HELP_MESSAGE
)
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
    os.makedirs('data', exist_ok=True)
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
    os.makedirs('data', exist_ok=True)
    with open(USER_ROLES_FILE, 'w') as f:
        json.dump(roles, f, indent=2)

def get_user_display(user_obj):
    """Get clean display name for user"""
    if user_obj.username:
        return f"@{user_obj.username}"
    else:
        name = user_obj.first_name or f"User_{user_obj.id}"
        if user_obj.last_name:
            name = f"{name} {user_obj.last_name}"
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
        
        # Delete system messages and track user joins
        @self.client.on(events.NewMessage)
        async def handle_all_messages(event):
            """Handle all messages: delete system messages and track user joins"""
            try:
                message_text = event.text or ""
                chat = await event.get_chat()
                chat_id = str(chat.id)
                
                # Clean chat ID for lookup
                if chat_id.startswith('-100'):
                    clean_chat_id = chat_id[4:]
                else:
                    clean_chat_id = chat_id
                
                # 1. DELETE DUPLICATE /BEGIN MESSAGES
                if message_text == '/begin':
                    groups = load_groups()
                    group_data = None
                    
                    if clean_chat_id in groups:
                        group_data = groups[clean_chat_id]
                    elif chat_id in groups:
                        group_data = groups[chat_id]
                    else:
                        for key, data in groups.items():
                            if data.get("name") == chat.title:
                                group_data = data
                                break
                    
                    if group_data and group_data.get("session_initiated", False):
                        await event.delete()
                        return
                
                # 2. DELETE SYSTEM MESSAGES
                system_patterns = [
                    "created the group",
                    "added ",
                    "joined the group via invite link",
                    "left the group",
                    "was added",
                    "pinned a message"
                ]
                
                is_system_message = False
                if event.sender_id == 777000 or event.sender_id == 1087968824:
                    is_system_message = True
                elif any(pattern in message_text.lower() for pattern in system_patterns):
                    is_system_message = True
                
                if is_system_message:
                    await event.delete()
                    
                    # 3. TRACK USER JOINS
                    if "joined the group via invite link" in message_text or "was added" in message_text:
                        await self.track_user_join_from_message(message_text, chat, clean_chat_id)
                    
                    return
                
                # 4. Handle /begin command normally
                if message_text == '/begin':
                    await self.handle_begin_command(event)
                
            except Exception as e:
                pass
        
        # Handle role selection buttons
        @self.client.on(events.CallbackQuery(pattern=rb'role_'))
        async def role_handler(event):
            """Handle role selection (buyer/seller)"""
            try:
                sender = await event.get_sender()
                if not sender:
                    await event.answer("❌ Cannot identify user", alert=True)
                    return
                
                data = event.data.decode('utf-8')
                chat = await event.get_chat()
                chat_id = str(chat.id)
                
                # Clean chat ID
                if chat_id.startswith('-100'):
                    clean_chat_id = chat_id[4:]
                else:
                    clean_chat_id = chat_id
                
                # Parse role from callback data
                if data.startswith('role_buyer_'):
                    role = "buyer"
                    role_name = "Buyer"
                    role_emoji = "🧑‍💼"
                    success_alert = "🔐 Buyer Role Selected\nBuyer role confirmed."
                    group_id = data.replace('role_buyer_', '')
                elif data.startswith('role_seller_'):
                    role = "seller"
                    role_name = "Seller"
                    role_emoji = "🧑‍💼"
                    success_alert = "🔐 Seller Role Selected\nSeller role confirmed."
                    group_id = data.replace('role_seller_', '')
                else:
                    return
                
                # Check group ID
                if group_id != clean_chat_id and group_id != chat_id:
                    groups = load_groups()
                    found = False
                    for key, data in groups.items():
                        if data.get("name") == chat.title:
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
                    await event.answer(ROLE_ALREADY_CHOSEN_MESSAGE, alert=True, parse_mode='html')
                    return
                
                # Check if role is already taken
                role_taken = any(u.get("role") == role for u in roles[group_id].values())
                if role_taken:
                    await event.answer(ROLE_ALREADY_TAKEN_MESSAGE, alert=True, parse_mode='html')
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
                
                # Send role confirmation message using imported text
                if role == "buyer":
                    confirm_msg = BUYER_CONFIRMED_MESSAGE.format(
                        buyer_id=sender.id,
                        buyer_name=get_user_display(sender)
                    )
                else:
                    confirm_msg = SELLER_CONFIRMED_MESSAGE.format(
                        seller_id=sender.id,
                        seller_name=get_user_display(sender)
                    )
                
                await event.client.send_message(
                    chat,
                    confirm_msg,
                    parse_mode='html'
                )
                
                print(f"✅ {get_user_display(sender)} selected as {role_name} in group: {chat.title}")
                
                # Check if both roles are selected
                buyer_count = sum(1 for u in roles[group_id].values() if u.get("role") == "buyer")
                seller_count = sum(1 for u in roles[group_id].values() if u.get("role") == "seller")
                
                if buyer_count >= 1 and seller_count >= 1:
                    await self.send_roles_confirmed(event.client, chat, group_id, roles[group_id])
                
            except Exception as e:
                print(f"Error in role handler: {e}")
                await event.answer("❌ Error selecting role", alert=True)
    
    async def track_user_join_from_message(self, message_text, chat, clean_chat_id):
        """Track user join from system message"""
        try:
            groups = load_groups()
            group_data = None
            group_key = None
            
            if clean_chat_id in groups:
                group_data = groups[clean_chat_id]
                group_key = clean_chat_id
            else:
                for key, data in groups.items():
                    if data.get("name") == chat.title:
                        group_data = data
                        group_key = key
                        break
            
            if not group_data:
                return
            
            # Get actual participants
            try:
                participants = await self.client.get_participants(chat)
                real_users = []
                
                for participant in participants:
                    if participant.bot:
                        continue
                    if group_data.get("creator_id") and participant.id == group_data["creator_id"]:
                        continue
                    real_users.append(participant.id)
                
                group_data["members"] = list(set(real_users))
                groups[group_key] = group_data
                save_groups(groups)
                
                member_count = len(group_data["members"])
                print(f"📊 Updated member count for {chat.title}: {member_count} real users")
                
                if member_count >= 2:
                    await self.delete_invite_link(self.client, chat)
                    print(f"✅ Auto-deleted invite link for {chat.title} (2+ users)")
                
            except Exception as e:
                print(f"Error getting participants: {e}")
                
        except Exception as e:
            print(f"Error tracking user join: {e}")
    
    async def handle_begin_command(self, event):
        """Handle /begin command to start escrow session"""
        try:
            chat = await event.get_chat()
            user = await event.get_sender()
            chat_id = str(chat.id)
            
            # Clean chat ID
            if chat_id.startswith('-100'):
                clean_chat_id = chat_id[4:]
            else:
                clean_chat_id = chat_id
            
            # Load groups data
            groups = load_groups()
            group_data = None
            group_key = None
            
            if clean_chat_id in groups:
                group_data = groups[clean_chat_id]
                group_key = clean_chat_id
            elif chat_id in groups:
                group_data = groups[chat_id]
                group_key = chat_id
            else:
                for key, data in groups.items():
                    if data.get("name") == chat.title:
                        group_data = data
                        group_key = key
                        break
            
            if not group_data:
                await event.reply("❌ Group not found in system. Wait a moment and try again.")
                return
            
            # Check if session already initiated
            if group_data.get("session_initiated", False):
                await event.reply("⚠️ Escrow session has already been initiated.")
                return
            
            # Get actual participant count
            try:
                participants = await self.client.get_participants(chat)
                real_users = []
                
                for participant in participants:
                    if participant.bot:
                        continue
                    if group_data.get("creator_id") and participant.id == group_data["creator_id"]:
                        continue
                    real_users.append(participant.id)
                
                member_count = len(real_users)
                print(f"🔍 Actual member count for {chat.title}: {member_count} real users")
                
                if member_count < 2:
                    await event.reply(f"⏳ Waiting for both participants to join... (Current: {member_count}/2)")
                    return
                
                # Update stored members list
                group_data["members"] = real_users
                groups[group_key] = group_data
                save_groups(groups)
                
                # Get bot username
                bot_username = group_data.get("bot_username", BOT_USERNAME)
                if not bot_username:
                    me = await self.client.get_me()
                    bot_username = me.username
                
                # Get user displays
                user_displays = []
                for user_id in real_users[:2]:
                    try:
                        user_obj = await self.client.get_entity(user_id)
                        user_displays.append(get_user_display(user_obj))
                    except:
                        user_displays.append(f"User_{user_id}")
                
                display_text = " • ".join(user_displays)
                
                # Use SESSION_INITIATED_MESSAGE from texts.py
                message = SESSION_INITIATED_MESSAGE.format(
                    participants_display=display_text
                )
                
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
                print(f"Error getting participants: {e}")
                await event.reply("❌ Error checking participants. Please try again.")
                
        except Exception as e:
            print(f"Error handling /begin command: {e}")
            await event.reply("❌ Error processing command.")
    
    async def send_roles_confirmed(self, client, chat, group_id, user_roles):
        """Send roles confirmed message"""
        try:
            # Find buyer and seller
            buyer = None
            seller = None
            
            for user_id, data in user_roles.items():
                if data.get("role") == "buyer" and not buyer:
                    buyer = data
                elif data.get("role") == "seller" and not seller:
                    seller = data
            
            if not buyer or not seller:
                return
            
            # Format message using WALLET_SETUP_MESSAGE
            message = WALLET_SETUP_MESSAGE.format(
                buyer_name=buyer['name'],
                seller_name=seller['name'],
                buyer_wallet_address="[address_placeholder]",
                seller_wallet_address="[address_placeholder]"
            )
            
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
                print(f"✅ Invite permissions disabled for {chat.title}")
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
            print("   • Auto-delete system messages")
            print("   • REAL-TIME member tracking")
            print("   • Working /begin with actual participant count")
            print("   • Role selection system")
            print("   • Auto invite link deletion")
            print("\n⚡ Bot is listening for commands...")
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
        # Create data directory
        os.makedirs('data', exist_ok=True)
        
        # Run the bot
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot.run())
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            print("\n👋 Bot stopped")
        else:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")

if __name__ == '__main__':
    main()
