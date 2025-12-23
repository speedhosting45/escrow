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
from utils.texts import (
    START_MESSAGE, ROLE_SELECTION_MESSAGE, WALLET_SETUP_MESSAGE,
    ESCROW_READY_MESSAGE, WALLET_SAVED_MESSAGE, BUYER_ONLY_MESSAGE,
    SELLER_ONLY_MESSAGE, NO_ROLE_MESSAGE, INVALID_WALLET_MESSAGE,
    ROLE_ANNOUNCEMENT_MESSAGE
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
WALLETS_FILE = 'data/wallets.json'

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

def load_wallets():
    """Load wallet addresses"""
    if os.path.exists(WALLETS_FILE):
        with open(WALLETS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_wallets(wallets):
    """Save wallet addresses"""
    with open(WALLETS_FILE, 'w') as f:
        json.dump(wallets, f, indent=2)

def get_user_display(user_obj):
    """Get clean display name for user"""
    if user_obj.username:
        return f"@{user_obj.username}"
    else:
        return user_obj.first_name or f"User_{user_obj.id}"

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
            """Handle wallet address commands"""
            try:
                # Handle /buyer command
                if event.text and event.text.startswith('/buyer '):
                    await self.handle_buyer_wallet(event)
                
                # Handle /seller command
                elif event.text and event.text.startswith('/seller '):
                    await self.handle_seller_wallet(event)
                
                # Handle other messages
                elif event.text and not event.text.startswith('/'):
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
                    user_id = event.user_id
                    if not user_id:
                        return
                    
                    chat = await event.get_chat()
                    
                    # Skip if bot
                    try:
                        user_obj = await event.client.get_entity(user_id)
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
                    if user_id not in group_data["members"]:
                        group_data["members"].append(user_id)
                        
                        # Update group data
                        groups[chat_id] = group_data
                        save_groups(groups)
                        
                        # Check if we have 2 members
                        member_count = len(group_data["members"])
                        print(f"👤 User {user_id} joined group: {chat.title} (Total: {member_count})")
                        
                        # When 2 real users join, send role selection
                        if member_count == 2:
                            await self.send_role_selection(event.client, chat, group_data)
                        
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
                
                # Parse role from callback data
                if data.startswith('role_buyer_'):
                    role = "buyer"
                    role_emoji = "🛒"
                    role_name = "BUYER"
                    group_id = data.replace('role_buyer_', '')
                elif data.startswith('role_seller_'):
                    role = "seller"
                    role_emoji = "💰"
                    role_name = "SELLER"
                    group_id = data.replace('role_seller_', '')
                else:
                    return
                
                # Load roles
                roles = load_user_roles()
                if group_id not in roles:
                    roles[group_id] = {}
                
                # Check if user already selected a role
                if str(sender.id) in roles[group_id]:
                    await event.answer("⚠️ You have already selected a role!", alert=True)
                    return
                
                # Get user mention
                mention = get_user_display(sender)
                
                # Save user's role
                roles[group_id][str(sender.id)] = {
                    "role": role,
                    "name": mention,
                    "user_id": sender.id,
                    "selected_at": time.time()
                }
                save_user_roles(roles)
                
                await event.answer(f"✅ You selected: {role_name}", alert=False)
                
                # Count roles
                buyer_count = sum(1 for u in roles[group_id].values() if u["role"] == "buyer")
                seller_count = sum(1 for u in roles[group_id].values() if u["role"] == "seller")
                
                # ANNOUNCE role selection in group
                announcement = ROLE_ANNOUNCEMENT_MESSAGE.format(
                    mention=mention,
                    role_emoji=role_emoji,
                    role_name=role_name,
                    buyer_count=buyer_count,
                    seller_count=seller_count
                )
                
                await event.client.send_message(
                    chat,
                    announcement,
                    parse_mode='html'
                )
                
                print(f"📢 {mention} selected role: {role_name} in group: {chat.title}")
                
                # Check if both roles are selected
                if buyer_count >= 1 and seller_count >= 1:
                    await self.send_wallet_setup(event.client, chat, group_id, roles[group_id])
                
            except Exception as e:
                print(f"Error in role handler: {e}")
                await event.answer("❌ Error selecting role", alert=True)
    
    async def send_role_selection(self, client, chat, group_data):
        """Send role selection message when 2 users join"""
        try:
            chat_id = str(chat.id)
            
            # Get the two users who joined
            members = group_data.get("members", [])[:2]
            
            # Get user display names
            user_displays = []
            for user_id in members:
                try:
                    user = await client.get_entity(user_id)
                    user_displays.append(get_user_display(user))
                except:
                    user_displays.append(f"User_{user_id}")
            
            # Format message using template
            message = ROLE_SELECTION_MESSAGE.format(
                user1=user_displays[0],
                user2=user_displays[1]
            )
            
            # Create role selection buttons
            buttons = [
                [
                    Button.inline("Buyer", f"role_buyer_{chat_id}".encode()),
                    Button.inline("Seller", f"role_seller_{chat_id}".encode())
                ]
            ]
            
            await client.send_message(
                chat,
                message,
                parse_mode='html',
                buttons=buttons
            )
            
            print(f"📝 Sent role selection for group: {chat.title}")
            
        except Exception as e:
            print(f"Error sending role selection: {e}")
    
    async def send_wallet_setup(self, client, chat, group_id, user_roles):
        """Send wallet setup instructions after roles confirmed"""
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
            
            # Format message using template
            message = WALLET_SETUP_MESSAGE.format(
                buyer_name=buyer['name'],
                seller_name=seller['name']
            )
            
            await client.send_message(
                chat,
                message,
                parse_mode='html'
            )
            
            print(f"💰 Sent wallet setup for group: {chat.title}")
            
        except Exception as e:
            print(f"Error sending wallet setup: {e}")
    
    async def handle_buyer_wallet(self, event):
        """Handle /buyer wallet address command"""
        try:
            chat = await event.get_chat()
            user = await event.get_sender()
            chat_id = str(chat.id)
            
            # Extract wallet address
            parts = event.text.split(' ', 1)
            if len(parts) < 2:
                await event.reply("❌ Please provide a wallet address: `/buyer YOUR_WALLET_ADDRESS`")
                return
            
            wallet_address = parts[1].strip()
            
            # Validate wallet address
            if len(wallet_address) < 10:
                await event.reply(INVALID_WALLET_MESSAGE)
                return
            
            # Load roles and wallets
            roles = load_user_roles()
            wallets = load_wallets()
            
            # Check if user is buyer in this group
            if chat_id not in roles or str(user.id) not in roles[chat_id]:
                await event.reply(NO_ROLE_MESSAGE)
                return
            
            if roles[chat_id][str(user.id)]["role"] != "buyer":
                await event.reply(BUYER_ONLY_MESSAGE)
                return
            
            # Save wallet address
            if chat_id not in wallets:
                wallets[chat_id] = {}
            
            wallets[chat_id]["buyer"] = {
                "address": wallet_address,
                "set_by": user.id,
                "set_at": time.time(),
                "name": get_user_display(user)
            }
            
            save_wallets(wallets)
            
            # Check if both wallets are set
            both_set = False
            if "buyer" in wallets.get(chat_id, {}) and "seller" in wallets.get(chat_id, {}):
                both_set = True
            
            # Format wallet preview
            if len(wallet_address) > 30:
                wallet_preview = f"{wallet_address[:20]}...{wallet_address[-10:]}"
            else:
                wallet_preview = wallet_address
            
            # Send confirmation
            status_message = '✅ Both wallets set! Ready for escrow.' if both_set else '⏳ Waiting for seller wallet...'
            
            reply_message = WALLET_SAVED_MESSAGE.format(
                role="Buyer",
                wallet_preview=wallet_preview,
                status_message=status_message
            )
            
            await event.reply(reply_message, parse_mode='html')
            
            # If both wallets are set, proceed to next step
            if both_set:
                await self.start_escrow(event.client, chat, chat_id)
            
        except Exception as e:
            print(f"Error handling buyer wallet: {e}")
            await event.reply("❌ Error saving wallet address. Please try again.")
    
    async def handle_seller_wallet(self, event):
        """Handle /seller wallet address command"""
        try:
            chat = await event.get_chat()
            user = await event.get_sender()
            chat_id = str(chat.id)
            
            # Extract wallet address
            parts = event.text.split(' ', 1)
            if len(parts) < 2:
                await event.reply("❌ Please provide a wallet address: `/seller YOUR_WALLET_ADDRESS`")
                return
            
            wallet_address = parts[1].strip()
            
            # Validate wallet address
            if len(wallet_address) < 10:
                await event.reply(INVALID_WALLET_MESSAGE)
                return
            
            # Load roles and wallets
            roles = load_user_roles()
            wallets = load_wallets()
            
            # Check if user is seller in this group
            if chat_id not in roles or str(user.id) not in roles[chat_id]:
                await event.reply(NO_ROLE_MESSAGE)
                return
            
            if roles[chat_id][str(user.id)]["role"] != "seller":
                await event.reply(SELLER_ONLY_MESSAGE)
                return
            
            # Save wallet address
            if chat_id not in wallets:
                wallets[chat_id] = {}
            
            wallets[chat_id]["seller"] = {
                "address": wallet_address,
                "set_by": user.id,
                "set_at": time.time(),
                "name": get_user_display(user)
            }
            
            save_wallets(wallets)
            
            # Check if both wallets are set
            both_set = False
            if "buyer" in wallets.get(chat_id, {}) and "seller" in wallets.get(chat_id, {}):
                both_set = True
            
            # Format wallet preview
            if len(wallet_address) > 30:
                wallet_preview = f"{wallet_address[:20]}...{wallet_address[-10:]}"
            else:
                wallet_preview = wallet_address
            
            # Send confirmation
            status_message = '✅ Both wallets set! Ready for escrow.' if both_set else '⏳ Waiting for buyer wallet...'
            
            reply_message = WALLET_SAVED_MESSAGE.format(
                role="Seller",
                wallet_preview=wallet_preview,
                status_message=status_message
            )
            
            await event.reply(reply_message, parse_mode='html')
            
            # If both wallets are set, proceed to next step
            if both_set:
                await self.start_escrow(event.client, chat, chat_id)
            
        except Exception as e:
            print(f"Error handling seller wallet: {e}")
            await event.reply("❌ Error saving wallet address. Please try again.")
    
    async def start_escrow(self, client, chat, group_id):
        """Start the escrow process after both wallets set"""
        try:
            # Load wallets and roles
            wallets = load_wallets()
            roles = load_user_roles()
            
            if group_id not in wallets:
                return
            
            buyer_wallet = wallets[group_id].get("buyer", {})
            seller_wallet = wallets[group_id].get("seller", {})
            
            if not buyer_wallet or not seller_wallet:
                return
            
            # Get buyer and seller names from roles
            buyer_name = "Buyer"
            seller_name = "Seller"
            
            if group_id in roles:
                for user_data in roles[group_id].values():
                    if user_data["role"] == "buyer":
                        buyer_name = user_data["name"]
                    elif user_data["role"] == "seller":
                        seller_name = user_data["name"]
            
            # Format wallet previews
            buyer_wallet_preview = f"{buyer_wallet['address'][:15]}...{buyer_wallet['address'][-10:]}"
            seller_wallet_preview = f"{seller_wallet['address'][:15]}...{seller_wallet['address'][-10:]}"
            
            # Format message using template
            message = ESCROW_READY_MESSAGE.format(
                buyer_name=buyer_name,
                seller_name=seller_name,
                buyer_wallet=buyer_wallet_preview,
                seller_wallet=seller_wallet_preview
            )
            
            await client.send_message(
                chat,
                message,
                parse_mode='html'
            )
            
            print(f"🚀 Escrow ready in group: {chat.title}")
            
        except Exception as e:
            print(f"Error starting escrow: {e}")
    
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
            print("   📊 Stats - View statistics")
            print("   ➕ Create - Create new escrow")
            print("   ℹ️ About - About the bot")
            print("   ❓ Help - Help and support")
            print("\n⚡ Features:")
            print("   • Auto group creation")
            print("   • Role selection with announcements")
            print("   • Wallet address collection")
            print("   • Auto invite link deletion")
            print("   • Escrow setup completion")
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
