#!/usr/bin/env python3
"""
Main entry point for the Escrow Bot
"""
import asyncio
import logging
import sys
from telethon import TelegramClient, events, Button
from telethon.tl import functions, types
import json
import os
import html
import time

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

def sanitize_text(text):
    """Remove markdown and clean text for HTML display"""
    if not text:
        return "User"
    
    text = str(text)
    # Remove markdown and special characters but keep emojis
    text = html.escape(text)
    # Remove problematic characters but keep normal text
    import re
    text = re.sub(r'[^\w\s@#:.!?\-]', '', text)
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
                    # Get the user who joined - FIXED METHOD
                    user = event.user_id
                    if not user:
                        return
                    
                    chat = await event.get_chat()
                    
                    # Skip if bot
                    try:
                        user_obj = await event.client.get_entity(user)
                        if user_obj.bot:
                            return
                    except:
                        pass
                    
                    # Get group data
                    chat_id = str(chat.id)
                    groups = load_groups()
                    
                    if chat_id not in groups:
                        return
                    
                    group_data = groups[chat_id]
                    
                    # Initialize members list if not exists
                    if "members" not in group_data:
                        group_data["members"] = []
                    
                    # Add user if not already in list
                    if user not in group_data["members"]:
                        group_data["members"].append(user)
                        
                        # Get user display name
                        try:
                            user_obj = await event.client.get_entity(user)
                            if user_obj.username:
                                display_name = f"@{user_obj.username}"
                            else:
                                display_name = user_obj.first_name or f"User_{user}"
                        except:
                            display_name = f"User_{user}"
                        
                        # Clean display name
                        clean_display = sanitize_text(display_name)
                        
                        # Update group data
                        groups[chat_id] = group_data
                        save_groups(groups)
                        
                        # Check if we have 2 members (excluding creator/bot)
                        member_count = len(group_data["members"])
                        print(f"👤 {clean_display} joined group: {chat.title} (Total: {member_count})")
                        
                        # When 2 real users join, send role selection
                        if member_count == 2:
                            await self.send_role_selection(event.client, chat, group_data)
                        
                        # When 2 users join, delete invite link
                        if member_count >= 2:
                            await self.delete_invite_link(event.client, chat)
                    
            except Exception as e:
                print(f"Error in chat action handler: {e}")
        
        # Handle role selection buttons - FIXED VERSION
        @self.client.on(events.CallbackQuery(pattern=rb'role_'))
        async def role_handler(event):
            """Handle role selection (buyer/seller)"""
            try:
                # Get the user who clicked - FIXED METHOD
                sender = await event.get_sender()
                if not sender:
                    await event.answer("❌ Cannot identify user", alert=True)
                    return
                
                data = event.data.decode('utf-8')
                chat = await event.get_chat()
                
                # Parse role from callback data
                if data.startswith('role_buyer_'):
                    role = "buyer"
                    group_id = data.replace('role_buyer_', '')
                elif data.startswith('role_seller_'):
                    role = "seller"
                    group_id = data.replace('role_seller_', '')
                else:
                    return
                
                # Get user display
                if sender.username:
                    mention = f"@{sender.username}"
                else:
                    mention = sender.first_name or f"User_{sender.id}"
                clean_mention = sanitize_text(mention)
                
                # Load roles
                roles = load_user_roles()
                if group_id not in roles:
                    roles[group_id] = {}
                
                # Save user's role
                roles[group_id][str(sender.id)] = {
                    "role": role,
                    "name": clean_mention,
                    "selected_at": time.time()
                }
                save_user_roles(roles)
                
                # Get group members
                groups = load_groups()
                if group_id in groups:
                    group_data = groups[group_id]
                    
                    # Count roles
                    buyer_count = sum(1 for u in roles[group_id].values() if u["role"] == "buyer")
                    seller_count = sum(1 for u in roles[group_id].values() if u["role"] == "seller")
                    
                    # Send update message
                    if role == "buyer":
                        role_text = "🛒 BUYER"
                        emoji = "🛒"
                    else:
                        role_text = "💰 SELLER"
                        emoji = "💰"
                    
                    await event.client.send_message(
                        chat,
                        f"{emoji} <b>{clean_mention} declared as {role_text}</b>\n\n"
                        f"<blockquote>👥 Status: Buyers: {buyer_count} | Sellers: {seller_count}</blockquote>",
                        parse_mode='html'
                    )
                    
                    # Check if both roles are selected
                    if buyer_count >= 1 and seller_count >= 1:
                        await self.send_trade_started(event.client, chat, group_id, roles[group_id])
                
                await event.answer(f"✅ You selected: {role}", alert=False)
                
            except Exception as e:
                print(f"Error in role handler: {e}")
                import traceback
                traceback.print_exc()
                await event.answer("❌ Error selecting role", alert=True)
    
    async def send_role_selection(self, client, chat, group_data):
        """Send BIG role selection message when 2 users join"""
        try:
            chat_id = str(chat.id)
            
            # Get the two users who joined
            members = group_data.get("members", [])[:2]  # First 2 users
            
            # Get user mentions
            user_mentions = []
            for user_id in members:
                try:
                    user = await client.get_entity(user_id)
                    if user.username:
                        mention = f"@{user.username}"
                    else:
                        mention = user.first_name or f"User_{user_id}"
                    clean_mention = sanitize_text(mention)
                    user_mentions.append(clean_mention)
                except:
                    user_mentions.append(f"User_{user_id}")
            
            # Create BIG welcome message with mentions
            mentions_text = " 👈 AND 👉 ".join(user_mentions)
            
            # Create BIG role selection buttons
            buttons = [
                [
                    Button.inline("I AM BUYER", f"role_buyer_{chat_id}".encode())
                ],
                [
                    Button.inline("I AM SELLER", f"role_seller_{chat_id}".encode())
                ]
            ]
            
            # Send BIG role selection message
            welcome_text = f"""
🎊🎊🎊 <b>WELCOME TO ESCROW GROUP!</b> 🎊🎊🎊

<blockquote>
🌟 <b>TRADE PARTNERS HAVE ARRIVED!</b> 🌟
</blockquote>

✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨

👥 <b>PARTICIPANTS:</b>
<b>{mentions_text}</b>

✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨

🎯 <b>NOW SELECT YOUR ROLE:</b>
<blockquote>
Choose your role carefully to start the secure escrow trade!
</blockquote>

🔒 <b>SECURE • TRANSPARENT • TRUSTED</b>
"""
            
            await client.send_message(
                chat,
                welcome_text,
                parse_mode='html',
                buttons=buttons
            )
            
            print(f"📝 Sent BIG role selection for group: {chat.title}")
            
        except Exception as e:
            print(f"Error sending role selection: {e}")
    
    async def send_trade_started(self, client, chat, group_id, user_roles):
        """Send trade started message when both roles selected"""
        try:
            # Get buyer and seller info
            buyers = []
            sellers = []
            
            for user_id, data in user_roles.items():
                if data["role"] == "buyer":
                    buyers.append(data["name"])
                elif data["role"] == "seller":
                    sellers.append(data["name"])
            
            buyers_text = " 🫂 ".join(buyers) if buyers else "Not selected"
            sellers_text = " 🫂 ".join(sellers) if sellers else "Not selected"
            
            trade_text = f"""
🎉🎉🎉 <b>TRADE OFFICIALLY STARTED!</b> 🎉🎉🎉

<blockquote>
✅ <b>ROLES CONFIRMED & LOCKED!</b> ✅
</blockquote>

════════════════════════════════════

🛒 <b>BUYER(S):</b> {buyers_text}

════════════════════════════════════

💰 <b>SELLER(S):</b> {sellers_text}

════════════════════════════════════

🔒 <b>ESCROW IS NOW ACTIVE!</b>
<blockquote>
• Funds are secured
• Trade is monitored
• Safe transaction guaranteed
</blockquote>

⚠️ <b>NEXT STEPS:</b>
1. Discuss trade details
2. Confirm terms
3. Proceed with transaction
4. Escrow protects both parties

🚀 <b>HAPPY TRADING!</b> 🚀
"""
            
            await client.send_message(
                chat,
                trade_text,
                parse_mode='html'
            )
            
            print(f"✅ Trade officially started in group: {chat.title}")
            
        except Exception as e:
            print(f"Error sending trade started: {e}")
    
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
                        invite_users=True  # Disable inviting
                    )
                ))
                print(f"✅ Invite permissions disabled for {chat.title}")
                
                # Send brief security update
                await client.send_message(
                    chat,
                    "🔒 <b>SECURITY:</b> Invite system locked.",
                    parse_mode='html'
                )
                
            except Exception as e:
                print(f"⚠️ Could not disable invites: {e}")
            
            print(f"✅ Invite system secured for {chat.title}")
            
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
            print("   📊 Stats - View statistics")
            print("   ➕ Create - Create new escrow")
            print("   ℹ️ About - About the bot")
            print("   ❓ Help - Help and support")
            print("\n⚡ Advanced Features:")
            print("   • Auto group creation")
            print("   • BIG role selection interface")
            print("   • Auto invite link deletion")
            print("   • Official trade start confirmation")
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
