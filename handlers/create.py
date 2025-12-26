#!/usr/bin/env python3
"""
Create escrow handlers - Fixed version
"""
from telethon.sessions import StringSession
from telethon.tl import functions, types
from telethon import Button
from telethon.tl.types import ChatAdminRights, KeyboardButtonCopy
from config import STRING_SESSION1, API_ID, API_HASH, set_bot_username
from telethon import TelegramClient
import asyncio
import json
import os
from datetime import datetime
import time

# Channel ID for logging
LOG_CHANNEL_ID = -1003631543074

# Image URLs from config
OTC_IMAGE = "https://files.catbox.moe/f6lzpr.png"
P2P_IMAGE = "https://files.catbox.moe/ieiejo.png"

# Define get_next_number locally
def get_next_number(group_type="p2p"):
    """Get next sequential group number"""
    COUNTER_FILE = 'data/counter.json'
    try:
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, 'r') as f:
                counter = json.load(f)
        else:
            counter = {"p2p": 1, "other": 1}
        
        number = counter.get(group_type, 1)
        counter[group_type] = number + 1
        
        with open(COUNTER_FILE, 'w') as f:
            json.dump(counter, f, indent=2)
        
        return number
    except Exception as e:
        print(f"[ERROR] get_next_number: {e}")
        return 1

async def handle_create(event):
    """
    Handle create escrow button click
    """
    try:
        from utils.texts import CREATE_MESSAGE
        from utils.buttons import get_create_buttons
        
        await event.edit(
            CREATE_MESSAGE,
            buttons=get_create_buttons(),
            parse_mode='html'
        )
    except Exception as e:
        print(f"[ERROR] create handler: {e}")
        await event.answer("✅ Create escrow menu", alert=False)

async def handle_create_p2p(event):
    """
    Handle P2P deal selection with animation
    """
    try:
        # Get user mention
        user = await event.get_sender()
        mention = user.first_name
        if user.username:
            mention = f"@{user.username}"
        
        # Get bot info
        bot = await event.client.get_me()
        bot_username = bot.username
        set_bot_username(bot_username)
        
        # Get group number
        group_number = get_next_number("p2p")
        group_name = f"𝖯2𝖯 𝘌𝘴𝘤𝘳𝘰𝘸 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 • #{group_number:02d}"
        
        # Create animation sequence
        animation_messages = [
            f"<b>🔐 Creating P2P Escrow</b>\n\n<blockquote>Creating group please wait {mention}.</blockquote>",
            f"<b>🔐 Creating P2P Escrow</b>\n\n<blockquote>Creating group please wait {mention}..</blockquote>",
            f"<b>🔐 Creating P2P Escrow</b>\n\n<blockquote>Creating group please wait {mention}...</blockquote>",
            f"<b>✅ Finalizing P2P Escrow</b>\n\n<blockquote>Setting up security features...</blockquote>"
        ]
        
        # Show animation
        for msg in animation_messages:
            try:
                await event.edit(msg, parse_mode='html')
            except:
                pass  # Ignore "message not modified" errors
            await asyncio.sleep(0.8)
        
        # Create group
        result = await create_escrow_group(group_name, bot_username, "p2p", event.client, user.id)
        
        if result and "invite_url" in result:
            from utils.texts import P2P_CREATED_MESSAGE
            from utils.buttons import get_p2p_created_buttons
            
            # Get buttons from buttons.py
            buttons = get_p2p_created_buttons(result["invite_url"])
            
            # Create message
            message = P2P_CREATED_MESSAGE.format(
                GROUP_NUMBER=group_number,
                GROUP_INVITE_LINK=result["invite_url"],
                P2P_IMAGE=P2P_IMAGE
            )
            
            # Send final message
            try:
                await event.edit(
                    message,
                    parse_mode='html',
                    link_preview=True,
                    buttons=buttons
                )
            except Exception as edit_error:
                # If edit fails, send as new message
                print(f"[WARNING] Edit failed, sending new message: {edit_error}")
                await event.respond(
                    message,
                    parse_mode='html',
                    link_preview=True,
                    buttons=buttons
                )
            
            print(f"[SUCCESS] P2P Escrow created: {group_name}")
            
        else:
            error_msg = "<b>❌ Failed to Create P2P Escrow</b>\n\n<blockquote>Please try again later</blockquote>"
            try:
                await event.edit(
                    error_msg,
                    parse_mode='html',
                    buttons=[Button.inline("🔄 Try Again", b"create")]
                )
            except:
                await event.respond(
                    error_msg,
                    parse_mode='html',
                    buttons=[Button.inline("🔄 Try Again", b"create")]
                )
            
    except Exception as e:
        print(f"[ERROR] P2P handler: {e}")
        error_msg = "<b>❌ Error Creating P2P Escrow</b>\n\n<blockquote>Technical issue detected</blockquote>"
        try:
            await event.edit(
                error_msg,
                parse_mode='html',
                buttons=[Button.inline("🔄 Try Again", b"create")]
            )
        except:
            await event.respond(
                error_msg,
                parse_mode='html',
                buttons=[Button.inline("🔄 Try Again", b"create")]
            )

async def handle_create_other(event):
    """
    Handle OTC deal selection with animation
    """
    try:
        # Get user mention
        user = await event.get_sender()
        mention = user.first_name
        if user.username:
            mention = f"@{user.username}"
        
        # Get bot info
        bot = await event.client.get_me()
        bot_username = bot.username
        set_bot_username(bot_username)
        
        # Get group number
        group_number = get_next_number("other")
        group_name = f"𝖮𝖳𝖢 𝘌𝘴𝘤𝘳𝘰𝘸 𝘚𝘦𝘴𝘴𝘪𝘰𝘯 • #{group_number:02d}"
        
        # Create animation sequence
        animation_messages = [
            f"<b>🔐 Creating OTC Escrow</b>\n\n<blockquote>Creating group please wait {mention}.</blockquote>",
            f"<b>🔐 Creating OTC Escrow</b>\n\n<blockquote>Creating group please wait {mention}..</blockquote>",
            f"<b>🔐 Creating OTC Escrow</b>\n\n<blockquote>Creating group please wait {mention}...</blockquote>",
            f"<b>✅ Finalizing OTC Escrow</b>\n\n<blockquote>Setting up security features...</blockquote>"
        ]
        
        # Show animation
        for msg in animation_messages:
            try:
                await event.edit(msg, parse_mode='html')
            except:
                pass  # Ignore "message not modified" errors
            await asyncio.sleep(0.8)
        
        # Create group
        result = await create_escrow_group(group_name, bot_username, "other", event.client, user.id)
        
        if result and "invite_url" in result:
            from utils.texts import OTHER_CREATED_MESSAGE
            from utils.buttons import get_otc_created_buttons
            
            # Get buttons from buttons.py
            buttons = get_otc_created_buttons(result["invite_url"])
            
            # Create message
            message = OTHER_CREATED_MESSAGE.format(
                GROUP_NUMBER=group_number,
                GROUP_INVITE_LINK=result["invite_url"],
                OTC_IMAGE=OTC_IMAGE
            )
            
            # Send final message
            try:
                await event.edit(
                    message,
                    parse_mode='html',
                    link_preview=True,
                    buttons=buttons
                )
            except Exception as edit_error:
                # If edit fails, send as new message
                print(f"[WARNING] Edit failed, sending new message: {edit_error}")
                await event.respond(
                    message,
                    parse_mode='html',
                    link_preview=True,
                    buttons=buttons
                )
            
            print(f"[SUCCESS] OTC Escrow created: {group_name}")
            
        else:
            error_msg = "<b>❌ Failed to Create OTC Escrow</b>\n\n<blockquote>Please try again later</blockquote>"
            try:
                await event.edit(
                    error_msg,
                    parse_mode='html',
                    buttons=[Button.inline("🔄 Try Again", b"create")]
                )
            except:
                await event.respond(
                    error_msg,
                    parse_mode='html',
                    buttons=[Button.inline("🔄 Try Again", b"create")]
                )
            
    except Exception as e:
        print(f"[ERROR] OTC handler: {e}")
        error_msg = "<b>❌ Error Creating OTC Escrow</b>\n\n<blockquote>Technical issue detected</blockquote>"
        try:
            await event.edit(
                error_msg,
                parse_mode='html',
                buttons=[Button.inline("🔄 Try Again", b"create")]
            )
        except:
            await event.respond(
                error_msg,
                parse_mode='html',
                buttons=[Button.inline("🔄 Try Again", b"create")]
            )

async def create_escrow_group(group_name, bot_username, group_type, bot_client, creator_user_id):
    """
    Create a supergroup with SIMPLE steps
    """
    if not STRING_SESSION1:
        print("[ERROR] STRING_SESSION1 not configured in .env")
        return None
    
    user_client = None
    try:
        # Start user client (creator's account)
        user_client = TelegramClient(StringSession(STRING_SESSION1), API_ID, API_HASH)
        await user_client.start()
        
        print(f"[INFO] User client started (Creator)")
        
        # Get bot entity
        bot_entity = await user_client.get_entity(bot_username)
        print(f"[INFO] Bot entity: @{bot_username}")
        
        # Get creator's entity
        creator = await user_client.get_me()
        creator_name = creator.username if creator.username else f"ID:{creator.id}"
        print(f"[INFO] Creator: @{creator_name}")
        
        # STEP 1: Create supergroup
        print("[STEP 1/5] Creating supergroup...")
        created = await user_client(functions.channels.CreateChannelRequest(
            title=group_name,
            about=f"🔐 Secure {group_type.upper()} Escrow Group\nEscrowed by @{bot_username}",
            megagroup=True,
            broadcast=False
        ))
        
        chat = created.chats[0]
        chat_id = chat.id
        channel = types.InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash)
        print(f"[SUCCESS] Supergroup created with ID: {chat_id}")
        
        # STEP 2: Promote creator as ANONYMOUS admin
        print("[STEP 2/5] Promoting creator as anonymous admin...")
        try:
            await user_client(functions.channels.EditAdminRequest(
                channel=channel,
                user_id=creator,
                admin_rights=ChatAdminRights(
                    change_info=True,
                    post_messages=True,
                    edit_messages=True,
                    delete_messages=True,
                    ban_users=True,
                    invite_users=True,
                    pin_messages=True,
                    add_admins=True,
                    anonymous=True,
                    manage_call=True,
                    other=True
                ),
                rank="Owner"
            ))
            print("[SUCCESS] Creator promoted as anonymous admin")
        except Exception as e:
            print(f"[ERROR] Could not promote creator: {e}")
            return None
        
        # STEP 3: Add bot and promote as admin
        print("[STEP 3/5] Adding and promoting bot...")
        await user_client(functions.channels.InviteToChannelRequest(
            channel=channel,
            users=[bot_entity]
        ))
        
        await user_client(functions.channels.EditAdminRequest(
            channel=channel,
            user_id=bot_entity,
            admin_rights=ChatAdminRights(
                change_info=True,
                post_messages=True,
                edit_messages=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                add_admins=False,
                anonymous=False,
                manage_call=True,
                other=True
            ),
            rank="Escrow Bot"
        ))
        print("[SUCCESS] Bot added and promoted")
        
        # STEP 4: Send welcome message and pin it
        print("[STEP 4/5] Sending and pinning welcome message...")
        from utils.texts import WELCOME_MESSAGE
        welcome_msg = WELCOME_MESSAGE.format(bot_username=bot_username)
        
        # Send welcome message
        sent_message = await user_client.send_message(
            channel,
            welcome_msg,
            parse_mode='html'
        )
        
        # Pin the welcome message
        await user_client.pin_message(channel, sent_message, notify=False)
        print("[SUCCESS] Welcome message sent and pinned")
        
        # STEP 5: Create invite link
        print("[STEP 5/5] Creating invite link...")
        invite_link = await user_client(functions.messages.ExportChatInviteRequest(
            peer=channel
        ))
        invite_url = str(invite_link.link)
        
        print("[COMPLETE] Group setup finished successfully")
        
        # Store group data
        store_group_data(chat_id, group_name, group_type, creator.id, bot_username, creator_name, creator_user_id)
        
        # Send log to channel
        await send_log_to_channel(user_client, group_name, group_type, creator, chat_id, invite_url, creator_user_id)
        
        return {
            "group_id": chat_id,
            "invite_url": invite_url,
            "group_name": group_name,
            "creator_id": creator.id,
            "creator_user_id": creator_user_id,
            "creator_username": creator_name,
            "bot_username": bot_username,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"[ERROR] Group creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        if user_client and user_client.is_connected():
            await user_client.disconnect()
            print("[INFO] User client disconnected")

async def send_log_to_channel(user_client, group_name, group_type, creator, chat_id, invite_url, creator_user_id):
    """Send creation log to the logging channel"""
    try:
        from utils.texts import CHANNEL_LOG_CREATION
        
        # Generate log ID
        import random
        log_id = f"{int(time.time())}{random.randint(1000, 9999)}"
        
        # Format timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Get creator display name
        creator_display = creator.first_name or f"User_{creator.id}"
        if creator.last_name:
            creator_display = f"{creator_display} {creator.last_name}"
        
        # Format escrow type
        escrow_type = "P2P Escrow" if "p2p" in group_type.lower() else "OTC Escrow"
        
        # Create log message
        log_message = CHANNEL_LOG_CREATION.format(
            log_id=log_id,
            GROUP_NAME=group_name,
            escrow_type=escrow_type,
            timestamp=timestamp,
            creator_id=creator_user_id,
            creator_name=creator_display,
            creator_username=creator.username if creator.username else "N/A",
            chat_id=chat_id,
            GROUP_INVITE_LINK=invite_url
        )
        
        # Send to log channel - FIXED: Get entity first
        try:
            # Get the channel entity
            channel_entity = await user_client.get_input_entity(LOG_CHANNEL_ID)
            await user_client.send_message(
                channel_entity,
                log_message,
                parse_mode='html'
            )
            print(f"[LOG] Creation log sent to channel")
        except Exception as e:
            print(f"[WARNING] Could not send log to channel: {e}")
            # Alternative: Join the channel first
            try:
                # Try to access the channel
                entity = await user_client.get_entity(LOG_CHANNEL_ID)
                await user_client.send_message(
                    entity,
                    log_message,
                    parse_mode='html'
                )
                print(f"[LOG] Creation log sent (alternative)")
            except Exception as e2:
                print(f"[ERROR] Failed to send log: {e2}")
        
    except Exception as e:
        print(f"[ERROR] Preparing log message: {e}")

def store_group_data(group_id, group_name, group_type, creator_id, bot_username, creator_username, creator_user_id):
    """Store group data for tracking"""
    try:
        GROUPS_FILE = 'data/active_groups.json'
        groups = {}
        
        if os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE, 'r') as f:
                groups = json.load(f)
        
        # Clean group ID
        clean_group_id = str(group_id)
        if clean_group_id.startswith('-100'):
            clean_group_id = clean_group_id[4:]
        
        groups[clean_group_id] = {
            "name": group_name,
            "type": group_type,
            "creator_id": creator_id,
            "creator_user_id": creator_user_id,
            "creator_username": creator_username,
            "bot_username": bot_username,
            "original_id": str(group_id),
            "members": [],
            "welcome_pinned": True,
            "session_initiated": False,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "created_timestamp": time.time(),
            "log_channel_id": LOG_CHANNEL_ID
        }
        
        with open(GROUPS_FILE, 'w') as f:
            json.dump(groups, f, indent=2)
            
        print(f"[INFO] Group data stored: {clean_group_id}")
        
    except Exception as e:
        print(f"[ERROR] Storing group data: {e}")
