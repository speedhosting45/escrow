#!/usr/bin/env python3
"""
Main entry point for the Escrow Bot - Complete logic implementation
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
    WELCOME_MESSAGE, SESSION_INITIATED_MESSAGE
)
from utils.buttons import get_main_menu_buttons

# Setup logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
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
        
        # MAIN LOGIC: Handle ALL messages
        @self.client.on(events.NewMessage)
        async def handle_all_messages(event):
            """Handle all messages with complete logic"""
            try:
                message_text = event.text or ""
                chat = await event.get_chat()
                user = await event.get_sender()
                chat_id = str(chat.id)
                
                # Skip if message is from a bot
                if user and user.bot:
                    return
                
                # Clean chat ID for lookup
                if chat_id.startswith('-100'):
                    clean_chat_id = chat_id[4:]
                else:
                    clean_chat_id = chat_id
                
                # Load groups data
                groups = load_groups()
                
                # Find group data (try multiple methods)
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
                        if data.get("name") == chat.title:
                            group_data = data
                            group_key = key
                            break
                
                # If this is not one of our managed groups, skip
                if not group_data:
                    return
                
                print(f"\n[GROUP] Processing message in {chat.title}")
                print(f"[USER] {get_user_display(user)} ({user.id})")
                print(f"[TEXT] {message_text[:50]}...")
                
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
                    print(f"[SYSTEM] Telegram system message detected (sender: {event.sender_id})")
                # Check for system patterns
                elif any(pattern in message_text.lower() for pattern in system_patterns):
                    is_system_message = True
                    print(f"[SYSTEM] System pattern detected in message")
                
                if is_system_message:
                    print(f"[ACTION] Deleting system message: {message_text[:30]}...")
                    try:
                        await event.delete()
                        print(f"[SUCCESS] System message deleted")
                        
                        # 2. TRACK USER JOIN FROM SYSTEM MESSAGE
                        if "joined the group via invite link" in message_text or "was added" in message_text:
                            await self.process_user_join(event, chat, group_data, group_key, groups)
                        
                    except Exception as e:
                        print(f"[ERROR] Could not delete message: {e}")
                    return
                
                # 3. BLOCK COMMANDS IF NOT ENOUGH MEMBERS
                if message_text.startswith('/'):
                    # Get actual member count (excluding bot)
                    try:
                        participants = await self.client.get_participants(chat)
                        real_users = []
                        
                        for participant in participants:
                            # Skip bots
                            if participant.bot:
                                continue
                            
                            # Skip creator if they're anonymous admin
                            if group_data.get("creator_user_id") and participant.id == group_data["creator_user_id"]:
                                continue
                            
                            real_users.append(participant.id)
                        
                        member_count = len(real_users)
                        print(f"[MEMBERS] Current member count: {member_count} real users")
                        
                        # Update stored members list
                        group_data["members"] = real_users
                        groups[group_key] = group_data
                        save_groups(groups)
                        
                        # Block commands if less than 2 members
                        if member_count < 2:
                            print(f"[BLOCK] Command blocked - Only {member_count}/2 members")
                            await event.reply(
                                f"⏳ <b>Waiting for Participants</b>\n\n"
                                f"<blockquote>Commands available when 2 participants join (Current: {member_count}/2)</blockquote>",
                                parse_mode='html'
                            )
                            await event.delete()
                            return
                        
                        # If we have 2+ members and /begin command
                        if message_text == '/begin' and member_count >= 2:
                            print(f"[PROCEED] /begin command with {member_count} members")
                            await self.handle_begin_command(event)
                            return
                            
                    except Exception as e:
                        print(f"[ERROR] Checking members: {e}")
                
            except Exception as e:
                print(f"[ERROR] Main handler: {e}")
    
    async def process_user_join(self, event, chat, group_data, group_key, groups):
        """Process when a user joins the group"""
        try:
            print(f"\n[USER JOIN] Processing new user join")
            
            # Get current participants
            participants = await self.client.get_participants(chat)
            
            # Count real users (excluding bots and creator)
            real_users = []
            for participant in participants:
                # Skip bots
                if participant.bot:
                    continue
                
                # Skip creator if known (from bot client perspective)
                if group_data.get("creator_user_id") and participant.id == group_data["creator_user_id"]:
                    print(f"[SKIP] Creator detected: {get_user_display(participant)}")
                    continue
                
                real_users.append({
                    "id": participant.id,
                    "name": get_user_display(participant)
                })
            
            member_count = len(real_users)
            print(f"[MEMBERS] Total real users: {member_count}")
            
            # Update stored members
            group_data["members"] = [user["id"] for user in real_users]
            
            # 1. IF FIRST USER JOINED AND WELCOME NOT SENT
            if member_count == 1 and not group_data.get("welcome_sent", False):
                print(f"[WELCOME] First user joined! Sending welcome message...")
                
                # Send welcome message
                from utils.texts import WELCOME_MESSAGE
                welcome_msg = WELCOME_MESSAGE.format(bot_username=group_data.get("bot_username", BOT_USERNAME))
                
                sent_message = await self.client.send_message(
                    chat,
                    welcome_msg,
                    parse_mode='html'
                )
                
                # Pin the welcome message
                await self.client.pin_message(chat, sent_message, notify=False)
                
                # Update group data
                group_data["welcome_sent"] = True
                group_data["welcome_message_id"] = sent_message.id
                group_data["first_join_processed"] = True
                
                print(f"[SUCCESS] Welcome message sent and pinned (Message ID: {sent_message.id})")
            
            # 2. IF 2 USERS JOINED, DELETE INVITE LINK
            if member_count >= 2:
                print(f"[SECURITY] {member_count} users joined, deleting invite link...")
                await self.delete_invite_link(chat)
                
                # Also check if history is still hidden and make it visible
                if group_data.get("history_hidden", True):
                    print(f"[HISTORY] Making history visible for {member_count} users...")
                    # Note: We can't unhide history from bot client, 
                    # but users can now see messages since welcome was sent
                    group_data["history_hidden"] = False
            
            # Save updated group data
            groups[group_key] = group_data
            save_groups(groups)
            
            print(f"[UPDATED] Group data saved: {member_count} members")
            
        except Exception as e:
            print(f"[ERROR] Processing user join: {e}")
            import traceback
            traceback.print_exc()
    
    async def handle_begin_command(self, event):
        """Handle /begin command - Only works with 2+ members"""
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
                await event.reply("❌ Group not found in system.")
                return
            
            # Check if session already initiated
            if group_data.get("session_initiated", False):
                await event.reply("⚠️ Escrow session has already been initiated.")
                return
            
            # Verify we have at least 2 members (excluding bot)
            try:
                participants = await self.client.get_participants(chat)
                real_users = []
                
                for participant in participants:
                    if participant.bot:
                        continue
                    if group_data.get("creator_user_id") and participant.id == group_data["creator_user_id"]:
                        continue
                    real_users.append(participant)
                
                member_count = len(real_users)
                print(f"[BEGIN] Checking members for /begin: {member_count} real users")
                
                if member_count < 2:
                    await event.reply(
                        f"⏳ <b>Insufficient Participants</b>\n\n"
                        f"<blockquote>Require 2 participants to begin (Current: {member_count}/2)</blockquote>",
                        parse_mode='html'
                    )
                    return
                
                # Update stored members
                group_data["members"] = [u.id for u in real_users]
                groups[group_key] = group_data
                save_groups(groups)
                
                # Get user displays
                user_displays = []
                for user_obj in real_users[:2]:  # First 2 users
                    user_displays.append(get_user_display(user_obj))
                
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
                sent_message = await self.client.send_message(
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
                print(f"[ERROR] Getting participants: {e}")
                await event.reply("❌ Error checking participants. Please try again.")
                
        except Exception as e:
            print(f"[ERROR] Handling /begin command: {e}")
            await event.reply("❌ Error processing command.")
    
    async def delete_invite_link(self, chat):
        """Delete invite link when 2 users join"""
        try:
            print(f"[SECURITY] Disabling invite permissions for group: {chat.title}")
            
            # Disable inviting for everyone
            try:
                await self.client(functions.messages.EditChatDefaultBannedRightsRequest(
                    peer=chat,
                    banned_rights=types.ChatBannedRights(
                        until_date=0,
                        invite_users=True
                    )
                ))
                print(f"[SUCCESS] Invite permissions disabled")
            except Exception as e:
                print(f"[WARNING] Could not disable invites: {e}")
            
        except Exception as e:
            print(f"[ERROR] Deleting invite link: {e}")

    async def run(self):
        """Run the bot"""
        try:
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
            print("   1️⃣ Create groups with hidden history")
            print("   2️⃣ Creator as anonymous admin")
            print("   3️⃣ Auto-delete Telegram system messages")
            print("   4️⃣ Welcome message sent & pinned on first join")
            print("   5️⃣ Commands blocked until 2 members join")
            print("   6️⃣ Auto-delete invite links at 2 members")
            print("   7️⃣ Secure role selection system")
            print("\n⚡ Bot is listening for commands...")
            print("   Press Ctrl+C to stop\n")
            
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
