#!/usr/bin/env python3
"""
Create escrow handlers - Professional version with animated progress
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
        result = await create_escrow_group(group_name, bot_username, "p2p", event.client)
        
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
            print(f"   ✓ Creator promoted as Anonymous Admin")
            print(f"   ✓ Welcome message pinned")
            print(f"   ✓ History hidden for new users")
            print(f"   ✓ Custom bio configured")
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
        result = await create_escrow_group(group_name, bot_username, "other", event.client)
        
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
            print(f"   ✓ Creator promoted as Anonymous Admin")
            print(f"   ✓ Welcome message pinned")
            print(f"   ✓ History hidden for new users")
            print(f"   ✓ Custom bio configured")
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

async def create_escrow_group(group_name, bot_username, group_type, bot_client):
    """
    Create a supergroup with hidden history and custom bio
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
        print(f"[STEP 1/6] Creating supergroup: {group_name}")
        created = await user_client(functions.channels.CreateChannelRequest(
            title=group_name,
            about=f"Secure {group_type.upper()} Escrow Group",
            megagroup=True,
            broadcast=False
        ))
        
        chat = created.chats[0]
        chat_id = chat.id
        channel = types.InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash)
        print(f"[SUCCESS] Supergroup created with ID: {chat_id}")
        
        # STEP 2: Hide pre-history for new users
        print("[STEP 2/6] Hiding pre-history for new users...")
        try:
            await user_client(functions.channels.TogglePreHistoryHiddenRequest(
                channel=channel,
                enabled=True
            ))
            print("[SUCCESS] History hidden for new users")
        except Exception as e:
            print(f"[WARNING] Could not hide history: {e}")
        
        # STEP 3: Set custom group bio (using EditTitle/EditAbout)
        print("[STEP 3/6] Setting custom group bio...")
        try:
            # Try different methods to set bio
            custom_bio = f"🔐 This group is being escrowed by @{bot_username}\n\n🧑‍💼 Seller : \n🧑‍💼 Buyer  :"
            
            # Method 1: EditAbout (for channels/supergroups)
            await user_client(functions.channels.EditAboutRequest(
                channel=channel,
                about=custom_bio
            ))
            print("[SUCCESS] Custom bio set using EditAbout")
        except Exception as e:
            print(f"[WARNING] Could not set custom bio: {e}")
            try:
                # Method 2: Edit channel info
                await user_client(functions.channels.EditChannelRequest(
                    channel=channel,
                    title=group_name,
                    about=custom_bio
                ))
                print("[SUCCESS] Custom bio set using EditChannel")
            except Exception as e2:
                print(f"[WARNING] Alternative method failed: {e2}")
        
        # STEP 4: Promote creator as ANONYMOUS admin
        print("[STEP 4/6] Promoting creator as anonymous admin...")
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
            print(f"[WARNING] Anonymous admin failed: {e}")
            try:
                # Fallback to regular admin
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
                        anonymous=False,
                        manage_call=True,
                        other=True
                    ),
                    rank="Owner"
                ))
                print("[SUCCESS] Creator promoted as regular admin")
            except Exception as e2:
                print(f"[ERROR] Could not promote creator: {e2}")
        
        # STEP 5: Add and promote bot
        print("[STEP 5/6] Adding and promoting bot...")
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
        
        # STEP 6: Create invite and send welcome message
        print("[STEP 6/6] Finalizing setup...")
        invite_link = await user_client(functions.messages.ExportChatInviteRequest(
            peer=channel
        ))
        invite_url = str(invite_link.link)
        
        # Send and pin welcome message
        from utils.texts import WELCOME_MESSAGE
        welcome_msg = WELCOME_MESSAGE.format(bot_username=bot_username)
        sent_message = await user_client.send_message(
            channel,
            welcome_msg,
            parse_mode='html'
        )
        
        await user_client.pin_message(channel, sent_message, notify=False)
        print("[SUCCESS] Welcome message pinned")
        
        # Store group data
        store_group_data(chat_id, group_name, group_type, creator.id, bot_username)
        
        print(f"[COMPLETE] Group setup finished successfully")
        
        return {
            "group_id": chat_id,
            "invite_url": invite_url,
            "group_name": group_name,
            "creator_id": creator.id,
            "creator_username": creator_name,
            "bot_username": bot_username
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

def store_group_data(group_id, group_name, group_type, creator_id, bot_username):
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
            "bot_username": bot_username,
            "original_id": str(group_id),
            "members": [],
            "welcome_pinned": True,
            "history_hidden": True,
            "custom_bio_set": True,
            "session_initiated": False,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "created_timestamp": time.time()
        }
        
        with open(GROUPS_FILE, 'w') as f:
            json.dump(groups, f, indent=2)
            
        print(f"[INFO] Group data stored: {clean_group_id}")
        
    except Exception as e:
        print(f"[ERROR] Storing group data: {e}")
