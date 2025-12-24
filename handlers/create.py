#!/usr/bin/env python3
"""
Create escrow handlers - Version with delayed welcome message
"""
from telethon.sessions import StringSession
from telethon.tl import functions, types
from telethon import Button
from telethon.tl.types import ChatAdminRights
from config import STRING_SESSION1, API_ID, API_HASH, set_bot_username
from telethon import TelegramClient
import asyncio
import json
import os
from datetime import datetime
import time

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
        
        # Create animation sequence
        animation_messages = [
            f"<b>🔐 Creating Group</b>\n\n<blockquote>Creating group please wait {mention}.</blockquote>",
            f"<b>🔐 Creating Group</b>\n\n<blockquote>Creating group please wait {mention}..</blockquote>",
            f"<b>🔐 Creating Group</b>\n\n<blockquote>Creating group please wait {mention}...</blockquote>",
            f"<b>✅ Group Created Successfully</b>\n\n<blockquote>Setting up escrow features...</blockquote>"
        ]
        
        # Show animation
        for msg in animation_messages:
            await event.edit(msg, parse_mode='html')
            await asyncio.sleep(0.8)
        
        # Get bot info
        bot = await event.client.get_me()
        bot_username = bot.username
        set_bot_username(bot_username)
        
        # Get group number
        group_number = get_next_number("p2p")
        group_name = f"P2P Escrow #{group_number:02d}"
        
        # Create group
        result = await create_escrow_group(group_name, bot_username, "p2p", event.client, user.id)
        
        if result and "invite_url" in result:
            from utils.texts import P2P_CREATED_MESSAGE
            
            # Create message with join button
            message = P2P_CREATED_MESSAGE.format(
                GROUP_NAME=group_name,
                GROUP_INVITE_LINK=result["invite_url"]
            )
            
            join_button = [
                [Button.url("🔗 Join Group Now", result["invite_url"])]
            ]
            
            await event.edit(
                message,
                parse_mode='html',
                link_preview=False,
                buttons=join_button
            )
            
            # Professional console log
            print("\n" + "═"*60)
            print("📊 ESCROW GROUP CREATION REPORT")
            print("═"*60)
            print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"👤 Created by: {mention}")
            print(f"🆔 Creator ID: {user.id}")
            print(f"📛 Group Name: {group_name}")
            print(f"🔗 Invite Link: {result['invite_url']}")
            print(f"🆔 Group ID: {result.get('group_id', 'N/A')}")
            print(f"🤖 Bot: @{bot_username}")
            print(f"🔧 Features:")
            print(f"   ✓ History hidden until first join")
            print(f"   ✓ Creator as Anonymous Admin")
            print(f"   ✓ Bot added as admin")
            print(f"   ✓ Welcome message ready (will pin on first join)")
            print("═"*60)
            
        else:
            await event.edit(
                "<b>❌ Failed to Create Group</b>\n\n<blockquote>Please try again later</blockquote>",
                parse_mode='html',
                buttons=[Button.inline("🔄 Try Again", b"create")]
            )
            
    except Exception as e:
        print(f"[ERROR] P2P handler: {e}")
        await event.edit(
            "<b>❌ Error Creating Group</b>\n\n<blockquote>Technical issue detected</blockquote>",
            parse_mode='html',
            buttons=[Button.inline("🔄 Try Again", b"create")]
        )

async def handle_create_other(event):
    """
    Handle Other deal selection with animation
    """
    try:
        # Get user mention
        user = await event.get_sender()
        mention = user.first_name
        if user.username:
            mention = f"@{user.username}"
        
        # Create animation sequence
        animation_messages = [
            f"<b>🔐 Creating Deal Group</b>\n\n<blockquote>Creating group please wait {mention}.</blockquote>",
            f"<b>🔐 Creating Deal Group</b>\n\n<blockquote>Creating group please wait {mention}..</blockquote>",
            f"<b>🔐 Creating Deal Group</b>\n\n<blockquote>Creating group please wait {mention}...</blockquote>",
            f"<b>✅ Group Created Successfully</b>\n\n<blockquote>Setting up escrow features...</blockquote>"
        ]
        
        # Show animation
        for msg in animation_messages:
            await event.edit(msg, parse_mode='html')
            await asyncio.sleep(0.8)
        
        # Get bot info
        bot = await event.client.get_me()
        bot_username = bot.username
        set_bot_username(bot_username)
        
        # Get group number
        group_number = get_next_number("other")
        group_name = f"Other Deal #{group_number:02d}"
        
        # Create group
        result = await create_escrow_group(group_name, bot_username, "other", event.client, user.id)
        
        if result and "invite_url" in result:
            from utils.texts import OTHER_CREATED_MESSAGE
            
            # Create message with join button
            message = OTHER_CREATED_MESSAGE.format(
                GROUP_NAME=group_name,
                GROUP_INVITE_LINK=result["invite_url"]
            )
            
            join_button = [
                [Button.url("🔗 Join Group Now", result["invite_url"])]
            ]
            
            await event.edit(
                message,
                parse_mode='html',
                link_preview=False,
                buttons=join_button
            )
            
            # Professional console log
            print("\n" + "═"*60)
            print("📊 DEAL GROUP CREATION REPORT")
            print("═"*60)
            print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"👤 Created by: {mention}")
            print(f"🆔 Creator ID: {user.id}")
            print(f"📛 Group Name: {group_name}")
            print(f"🔗 Invite Link: {result['invite_url']}")
            print(f"🆔 Group ID: {result.get('group_id', 'N/A')}")
            print(f"🤖 Bot: @{bot_username}")
            print(f"🔧 Features:")
            print(f"   ✓ History hidden until first join")
            print(f"   ✓ Creator as Anonymous Admin")
            print(f"   ✓ Bot added as admin")
            print(f"   ✓ Welcome message ready (will pin on first join)")
            print("═"*60)
            
        else:
            await event.edit(
                "<b>❌ Failed to Create Group</b>\n\n<blockquote>Please try again later</blockquote>",
                parse_mode='html',
                buttons=[Button.inline("🔄 Try Again", b"create")]
            )
            
    except Exception as e:
        print(f"[ERROR] Other deal handler: {e}")
        await event.edit(
            "<b>❌ Error Creating Group</b>\n\n<blockquote>Technical issue detected</blockquote>",
            parse_mode='html',
            buttons=[Button.inline("🔄 Try Again", b"create")]
        )

async def create_escrow_group(group_name, bot_username, group_type, bot_client, creator_user_id):
    """
    Create a supergroup with:
    1. History hidden
    2. Creator as anonymous admin
    3. Bot added as admin
    4. Welcome message WILL BE SENT AND PINNED when first user joins
    """
    if not STRING_SESSION1:
        print("[ERROR] STRING_SESSION1 not configured in .env")
        return None
    
    user_client = None
    try:
        # Start user client (creator's account)
        user_client = TelegramClient(StringSession(STRING_SESSION1), API_ID, API_HASH)
        await user_client.start()
        
        print("[INFO] User client started (Creator)")
        
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
            about=f"🔐 Secure {group_type.upper()} Escrow Group\n\nEscrowed by @{bot_username}",
            megagroup=True,
            broadcast=False
        ))
        
        chat = created.chats[0]
        chat_id = chat.id
        channel = types.InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash)
        print(f"[SUCCESS] Supergroup created with ID: {chat_id}")
        
        # STEP 2: Hide history for ALL users (including new)
        print("[STEP 2/5] Hiding group history...")
        try:
            await user_client(functions.channels.TogglePreHistoryHiddenRequest(
                channel=channel,
                enabled=True  # True = Hide history for everyone
            ))
            print("[SUCCESS] Group history hidden (no one can see old messages)")
        except Exception as e:
            print(f"[WARNING] Could not hide history: {e}")
        
        # STEP 3: Promote creator as ANONYMOUS admin
        print("[STEP 3/5] Promoting creator as anonymous admin...")
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
                    anonymous=True,  # CRITICAL: Anonymous admin
                    manage_call=True,
                    other=True
                ),
                rank="Owner"
            ))
            print("[SUCCESS] Creator promoted as anonymous admin")
        except Exception as e:
            print(f"[ERROR] Could not promote creator: {e}")
        
        # STEP 4: Add bot and promote as admin
        print("[STEP 4/5] Adding and promoting bot...")
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
        
        # STEP 5: Create invite link
        print("[STEP 5/5] Creating invite link...")
        invite_link = await user_client(functions.messages.ExportChatInviteRequest(
            peer=channel
        ))
        invite_url = str(invite_link.link)
        
        print("[COMPLETE] Group setup finished - Waiting for first user to join")
        print(f"[NOTE] Welcome message will be sent and pinned when first user joins")
        print(f"[NOTE] Telegram service messages will be auto-deleted")
        print(f"[NOTE] Commands won't work until 2 members join (excluding bot)")
        
        # Store group data with special flag for first join
        store_group_data(chat_id, group_name, group_type, creator.id, bot_username, creator_name, creator_user_id)
        
        return {
            "group_id": chat_id,
            "invite_url": invite_url,
            "group_name": group_name,
            "creator_id": creator.id,
            "creator_user_id": creator_user_id,  # From bot client
            "creator_username": creator_name,
            "bot_username": bot_username,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "history_hidden": True,
            "welcome_sent": False  # Flag to track if welcome was sent
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
            "creator_user_id": creator_user_id,  # From bot client
            "creator_username": creator_username,
            "bot_username": bot_username,
            "original_id": str(group_id),
            "members": [],
            "history_hidden": True,
            "welcome_sent": False,  # Track if welcome message was sent
            "welcome_message_id": None,
            "first_join_processed": False,
            "session_initiated": False,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "created_timestamp": time.time()
        }
        
        with open(GROUPS_FILE, 'w') as f:
            json.dump(groups, f, indent=2)
            
        print(f"[INFO] Group data stored: {clean_group_id}")
        
    except Exception as e:
        print(f"[ERROR] Storing group data: {e}")
