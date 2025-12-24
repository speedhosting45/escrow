#!/usr/bin/env python3
"""
Main entry point for the Escrow Bot - Fixed version
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
    WELCOME_MESSAGE, SESSION_INITIATED_MESSAGE, INSUFFICIENT_MEMBERS_MESSAGE,
    WAITING_PARTICIPANTS_MESSAGE, SESSION_ALREADY_INITIATED_MESSAGE,
    GROUP_NOT_FOUND_MESSAGE, ERROR_MESSAGE
)
from utils.buttons import get_main_menu_buttons

# Setup logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
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
    if hasattr(user_obj, 'username') and user_obj.username:
        return f"@{user_obj.username}"
    else:
        name = getattr(user_obj, 'first_name', '') or f"User_{user_obj.id}"
        if hasattr(user_obj, 'last_name') and user_obj.last_name:
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
        
        # Handle role selection buttons
        @self.client.on(events.CallbackQuery(pattern=rb'role_'))
        async def role_handler(event):
            await self.handle_role_selection(event)
        
        # Delete system messages
        @self.client.on(events.NewMessage)
        async def handle_all_messages(event):
            """Handle all messages with complete logic"""
            try:
                # Get basic info
                message_text = event.text or ""
                
                # Get chat info safely
                try:
                    chat = await event.get_chat()
                    chat_id = str(chat.id)
                    chat_title = getattr(chat, 'title', 'Unknown Group')
                except:
                    return
                
                # Get user info safely
                try:
                    user = await event.get_sender()
                    user_id = user.id if user else 0
                except:
                    return
                
                # Skip if message is from a bot
                if hasattr(user, 'bot') and user.bot:
                    return
                
                # Clean chat ID for lookup
                if chat_id.startswith('-100'):
                    clean_chat_id = chat_id[4:]
                else:
                    clean_chat_id = chat_id
                
                # Load groups data
                groups = load_groups()
                
                # Find group data
                group_data = None
                group_key = None
                
                # Method 1: By clean ID
                if clean_chat_id in groups:
                    group_data = groups[clean_chat_id]
                    group_key = clean_chat_id
                # Method 2: By original ID
                elif chat_id in groups:
                    group_data = groups[chat_id]
                    group_key = chat_id
                # Method 3: By group name
                else:
                    for key, data in groups.items():
                        if data.get("name") == chat_title:
                            group_data = data
                            group_key = key
                            break
                
                # If this is not one of our managed groups, skip
                if not group_data:
                    return
                
                # 1. DELETE TELEGRAM SYSTEM MESSAGES
                system_patterns = [
                    "joined the group via invite link",
                    "was added",
                    "created the group",
                    "added ",
                    "left the group",
                    "pinned a message",
                    "changed the group name",
                    "changed the group photo"
                ]
                
                is_system_message = False
                # Check if from Telegram
                if event.sender_id == 777000 or event.sender_id == 1087968824:
                    is_system_message = True
                # Check for system patterns
                elif any(pattern in message_text.lower() for pattern in system_patterns):
                    is_system_message = True
                
                if is_system_message:
                    try:
                        await event.delete()
                    except:
                        pass
                    return
                
                # 2. Handle /begin command
                if message_text == '/begin':
                    # Delete the /begin message first
                    try:
                        await event.delete()
                    except:
                        pass
                    
                    # Then handle the command
                    await self.handle_begin_command(event)
                    return
                    
            except Exception as e:
                # Ignore errors in message handler
                pass
    
    async def handle_begin_command(self, event):
        """Handle /begin command - Only works with 2+ members (excluding creator)"""
        try:
            # Get chat info
            chat = await event.get_chat()
            chat_id = str(chat.id)
            chat_title = getattr(chat, 'title', 'Unknown Group')
            
            # Get user info safely
            try:
                user = await event.get_sender()
                user_display = get_user_display(user)
            except:
                user_display = "Unknown User"
            
            # Clean chat ID
            if chat_id.startswith('-100'):
                clean_chat_id = chat_id[4:]
            else:
                clean_chat_id = chat_id
            
            # Load groups data
            groups = load_groups()
            group_data = None
            group_key = None
            
            # Find group
            if clean_chat_id in groups:
                group_data = groups[clean_chat_id]
                group_key = clean_chat_id
            elif chat_id in groups:
                group_data = groups[chat_id]
                group_key = chat_id
            else:
                # Try by name
                for key, data in groups.items():
                    if data.get("name") == chat_title:
                        group_data = data
                        group_key = key
                        break
            
            if not group_data:
                # Send error message once
                try:
                    await event.respond(GROUP_NOT_FOUND_MESSAGE, parse_mode='html')
                except:
                    pass
                return
            
            # Check if session already initiated
            if group_data.get("session_initiated", False):
                try:
                    await event.respond(SESSION_ALREADY_INITIATED_MESSAGE, parse_mode='html')
                except:
                    pass
                return
            
            # Get actual participants (EXCLUDING CREATOR)
            try:
                participants = await self.client.get_participants(chat)
                real_users = []
                
                creator_user_id = group_data.get("creator_user_id")
                
                for participant in participants:
                    # Skip bots
                    if hasattr(participant, 'bot') and participant.bot:
                        continue
                    
                    # Skip creator if known
                    if creator_user_id and participant.id == creator_user_id:
                        print(f"[DEBUG] Skipping creator: {get_user_display(participant)}")
                        continue
                    
                    real_users.append(participant)
                
                member_count = len(real_users)
                print(f"[BEGIN] Real users (excluding creator): {member_count}")
                
                # Check if we have exactly 2 real users (not including creator)
                if member_count < 2:
                    # Send ONE message about insufficient participants
                    try:
                        message = INSUFFICIENT_MEMBERS_MESSAGE.format(current_count=member_count)
                        await event.respond(message, parse_mode='html')
                    except:
                        pass
                    return
                
                # Update stored members
                group_data["members"] = [u.id for u in real_users]
                groups[group_key] = group_data
                save_groups(groups)
                
                # Get user displays for the message
                user_displays = []
                for user_obj in real_users[:2]:  # First 2 users
                    user_displays.append(get_user_display(user_obj))
                
                display_text = " • ".join(user_displays)
                
                # Send session initiation message
                message = SESSION_INITIATED_MESSAGE.format(
                    participants_display=display_text
                )
                
                # Create role selection buttons
                buttons = [
                    [
                        Button.inline("🧑‍💼 Buyer", f"role_buyer_{group_key}".encode()),
                        Button.inline("🧑‍💼 Seller", f"role_seller_{group_key}".encode())
                    ]
                ]
                
                # Send message
                sent_message = await self.client.send_message(
                    chat,
                    message,
                    parse_mode='html',
                    buttons=buttons
                )
                
                # Mark session as initiated
                group_data["session_initiated"] = True
                group_data["session_message_id"] = sent_message.id
                groups[group_key] = group_data
                save_groups(groups)
                
                print(f"[SUCCESS] Escrow session initiated in: {chat_title}")
                print(f"[USERS] {display_text}")
                
            except Exception as e:
                print(f"[ERROR] In /begin: {e}")
                try:
                    await event.respond(ERROR_MESSAGE, parse_mode='html')
                except:
                    pass
                
        except Exception as e:
            print(f"[ERROR] Handling /begin: {e}")
    
    async def handle_role_selection(self, event):
        """Handle role selection (buyer/seller)"""
        try:
            # Get user info
            sender = await event.get_sender()
            if not sender:
                await event.answer("❌ Cannot identify user", alert=True)
                return
            
            data = event.data.decode('utf-8')
            
            # Get chat info
            chat = await event.get_chat()
            chat_id = str(chat.id)
            chat_title = getattr(chat, 'title', 'Unknown Group')
            
            # Clean chat ID
            if chat_id.startswith('-100'):
                clean_chat_id = chat_id[4:]
            else:
                clean_chat_id = chat_id
            
            # Parse role from callback data
            if data.startswith('role_buyer_'):
                role = "buyer"
                role_name = "Buyer"
                group_id = data.replace('role_buyer_', '')
            elif data.startswith('role_seller_'):
                role = "seller"
                role_name = "Seller"
                group_id = data.replace('role_seller_', '')
            else:
                return
            
            # Load groups and roles
            groups = load_groups()
            roles = load_user_roles()
            
            # Find correct group
            if group_id not in groups:
                # Try to find by name
                for key, data in groups.items():
                    if data.get("name") == chat_title:
                        group_id = key
                        break
            
            if group_id not in groups:
                await event.answer("❌ Group not found", alert=True)
                return
            
            # Initialize roles dict if needed
            if group_id not in roles:
                roles[group_id] = {}
            
            # Check if user already selected a role
            if str(sender.id) in roles[group_id]:
                await event.answer("⛔ Role Already Chosen", alert=True)
                return
            
            # Check if role is already taken by someone else
            role_taken = any(u.get("role") == role for u in roles[group_id].values())
            if role_taken:
                await event.answer("⚠️ Role Already Taken", alert=True)
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
            await event.answer(f"✅ {role_name} role selected", alert=False)
            
            # Send confirmation to group
            if role == "buyer":
                confirm_msg = f"✅ <a href='tg://user?id={sender.id}'>{get_user_display(sender)}</a> confirmed as <b>Buyer</b>."
            else:
                confirm_msg = f"✅ <a href='tg://user?id={sender.id}'>{get_user_display(sender)}</a> confirmed as <b>Seller</b>."
            
            await self.client.send_message(
                chat,
                confirm_msg,
                parse_mode='html'
            )
            
            print(f"[ROLE] {get_user_display(sender)} selected as {role_name} in {chat_title}")
            
            # Check if both roles are selected
            buyer_count = sum(1 for u in roles[group_id].values() if u.get("role") == "buyer")
            seller_count = sum(1 for u in roles[group_id].values() if u.get("role") == "seller")
            
            if buyer_count >= 1 and seller_count >= 1:
                await self.send_wallet_setup(chat, group_id, roles[group_id])
                
        except Exception as e:
            print(f"[ERROR] Role selection: {e}")
            await event.answer("❌ Error selecting role", alert=True)
    
    async def send_wallet_setup(self, chat, group_id, user_roles):
        """Send wallet setup message when both roles selected"""
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
            
            # Format message
            message = f"""
<b>✅ Participants Confirmed</b>

<blockquote>
<b>Buyer:</b> {buyer['name']}
<b>Seller:</b> {seller['name']}
</blockquote>

<b>Next Step:</b> Wallet setup will begin shortly.
"""
            
            await self.client.send_message(
                chat,
                message,
                parse_mode='html'
            )
            
            print(f"[SETUP] Both roles confirmed in group ID: {group_id}")
            
        except Exception as e:
            print(f"[ERROR] Sending setup: {e}")

    async def run(self):
        """Run the bot"""
        try:
            print("═"*50)
            print("🔐 Secure Escrow Bot Starting...")
            print("═"*50)
            
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
            print("═"*50)
            
            print("\n📋 BOT FEATURES:")
            print("   1️⃣ Simple group creation")
            print("   2️⃣ Creator as anonymous admin")
            print("   3️⃣ Auto-delete system messages")
            print("   4️⃣ /begin with 2 real users (excluding creator)")
            print("   5️⃣ Role selection system")
            print("\n⚡ Bot is ready...")
            print("   Press Ctrl+C to stop\n")
            
            # Run until disconnected
            await self.client.run_until_disconnected()
            
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
        except Exception as e:
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
