#!/usr/bin/env python3
"""
Create escrow handlers - Clean version (no user addition)
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
        print(f"Error in get_next_number: {e}")
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
        print(f"Error in create handler: {e}")
        await event.answer("✅ Create escrow menu", alert=False)

async def handle_create_p2p(event):
    """
    Handle P2P deal selection
    """
    try:
        # Show processing
        await event.edit(
            "🔄 <b>Creating P2P Escrow Group...</b>\n\n<blockquote>Please wait...</blockquote>",
            parse_mode='html'
        )
        
        # Get bot info
        bot = await event.client.get_me()
        bot_username = bot.username
        set_bot_username(bot_username)  # Set globally
        
        # Get group number
        group_number = get_next_number("p2p")
        group_name = f"P2P Escrow #{group_number:02d}"
        
        # Create group
        result = await create_escrow_group(group_name, bot_username, "p2p", event.client)
        
        if result and "invite_url" in result:
            from utils.texts import P2P_CREATED_MESSAGE
            
            # Create message with ONLY join button
            message = P2P_CREATED_MESSAGE.format(
                GROUP_NAME=group_name,
                GROUP_INVITE_LINK=result["invite_url"]
            )
            
            # Only show join button, no main menu
            join_button = [
                [Button.url("🔗 Join Group Now", result["invite_url"])]
            ]
            
            await event.edit(
                message,
                parse_mode='html',
                link_preview=False,
                buttons=join_button
            )
            
            # Print log to console
            print("\n" + "="*60)
            print(f"✅ P2P GROUP CREATED SUCCESSFULLY")
            print(f"📛 Group Name: {group_name}")
            print(f"🔗 Initial Invite: {result['invite_url']}")
            print(f"🆔 Group ID: {result.get('group_id', 'N/A')}")
            print(f"🤖 Bot Added: @{bot_username}")
            print(f"👑 Creator Promoted: YES (Anonymous Admin)")
            print(f"📌 Welcome Message Pinned: YES")
            print("="*60 + "\n")
            
        else:
            await event.edit(
                "❌ <b>Failed to create group</b>\n\n<blockquote>Please try again later</blockquote>",
                parse_mode='html',
                buttons=[Button.inline("🔄 Try Again", b"create")]
            )
            
    except Exception as e:
        print(f"Error in P2P handler: {e}")
        await event.edit(
            "❌ <b>Error creating group</b>\n\n<blockquote>Please try again</blockquote>",
            parse_mode='html',
            buttons=[Button.inline("🔄 Try Again", b"create")]
        )

async def handle_create_other(event):
    """
    Handle Other deal selection
    """
    try:
        # Show processing
        await event.edit(
            "🔄 <b>Creating Other Deal Escrow Group...</b>\n\n<blockquote>Please wait...</blockquote>",
            parse_mode='html'
        )
        
        # Get bot info
        bot = await event.client.get_me()
        bot_username = bot.username
        set_bot_username(bot_username)  # Set globally
        
        # Get group number
        group_number = get_next_number("other")
        group_name = f"Other Deal #{group_number:02d}"
        
        # Create group
        result = await create_escrow_group(group_name, bot_username, "other", event.client)
        
        if result and "invite_url" in result:
            from utils.texts import OTHER_CREATED_MESSAGE
            
            # Create message with ONLY join button
            message = OTHER_CREATED_MESSAGE.format(
                GROUP_NAME=group_name,
                GROUP_INVITE_LINK=result["invite_url"]
            )
            
            # Only show join button, no main menu
            join_button = [
                [Button.url("🔗 Join Group Now", result["invite_url"])]
            ]
            
            await event.edit(
                message,
                parse_mode='html',
                link_preview=False,
                buttons=join_button
            )
            
            # Print log to console
            print("\n" + "="*60)
            print(f"✅ OTHER DEAL GROUP CREATED SUCCESSFULLY")
            print(f"📛 Group Name: {group_name}")
            print(f"🔗 Initial Invite: {result['invite_url']}")
            print(f"🆔 Group ID: {result.get('group_id', 'N/A')}")
            print(f"🤖 Bot Added: @{bot_username}")
            print(f"👑 Creator Promoted: YES (Anonymous Admin)")
            print(f"📌 Welcome Message Pinned: YES")
            print("="*60 + "\n")
            
        else:
            await event.edit(
                "❌ <b>Failed to create group</b>\n\n<blockquote>Please try again later</blockquote>",
                parse_mode='html',
                buttons=[Button.inline("🔄 Try Again", b"create")]
            )
            
    except Exception as e:
        print(f"Error in Other deal handler: {e}")
        await event.edit(
            "❌ <b>Error creating group</b>\n\n<blockquote>Please try again</blockquote>",
            parse_mode='html',
            buttons=[Button.inline("🔄 Try Again", b"create")]
        )

async def create_escrow_group(group_name, bot_username, group_type, bot_client):
    """
    Create a supergroup, add bot ONLY, promote creator as anonymous admin, and pin welcome message
    """
    if not STRING_SESSION1:
        print("❌ STRING_SESSION1 not configured in .env")
        return None
    
    user_client = None
    try:
        # Start user client (creator's account)
        user_client = TelegramClient(StringSession(STRING_SESSION1), API_ID, API_HASH)
        await user_client.start()
        
        print(f"✅ User client started (Creator)")
        print(f"🔄 Creating group: {group_name}")
        
        # Get bot entity
        bot_entity = await user_client.get_entity(bot_username)
        print(f"✅ Got bot entity: @{bot_username}")
        
        # Get creator's own entity
        creator = await user_client.get_me()
        print(f"✅ Creator: @{creator.username if creator.username else creator.id}")
        
        # Create supergroup - EMPTY (no users added)
        created = await user_client(functions.channels.CreateChannelRequest(
            title=group_name,
            about=f"Secure {group_type.upper()} Escrow Group",
            megagroup=True,
            broadcast=False
        ))
        
        # Get channel info
        chat = created.chats[0]
        chat_id = chat.id
        channel = types.InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash)
        print(f"✅ Supergroup created: {chat_id}")
        
        # CRITICAL: Promote creator as ANONYMOUS admin
        print("🔄 Promoting creator as ANONYMOUS admin...")
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
                    anonymous=True,  # ANONYMOUS - MOST IMPORTANT
                    manage_call=True,
                    other=True
                ),
                rank="Owner"
            ))
            print(f"✅ Creator promoted as ANONYMOUS admin (hidden)")
        except Exception as e:
            print(f"⚠️ Could not promote creator as anonymous: {e}")
            # Try without anonymous flag
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
                        anonymous=False,
                        manage_call=True,
                        other=True
                    ),
                    rank="Owner"
                ))
                print(f"✅ Creator promoted as regular admin")
            except Exception as e2:
                print(f"❌ Could not promote creator at all: {e2}")
        
        # Add bot to group (NO USERS ADDED)
        print("🔄 Adding bot to group...")
        await user_client(functions.channels.InviteToChannelRequest(
            channel=channel,
            users=[bot_entity]
        ))
        print(f"✅ Bot added to group")
        
        # Promote bot as admin (not anonymous)
        print("🔄 Promoting bot as admin...")
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
        print(f"✅ Bot promoted as admin")
        
        # Create initial invite link
        print("🔄 Creating initial invite link...")
        invite_link = await user_client(functions.messages.ExportChatInviteRequest(
            peer=channel
        ))
        invite_url = str(invite_link.link)
        print(f"✅ Initial invite link created")
        
        # Send and PIN welcome message
        print("🔄 Sending and pinning welcome message...")
        from utils.texts import WELCOME_MESSAGE
        
        welcome_msg = WELCOME_MESSAGE.format(bot_username=bot_username)
        sent_message = await user_client.send_message(
            channel,
            welcome_msg,
            parse_mode='html'
        )
        
        # Pin the welcome message
        await user_client.pin_message(channel, sent_message, notify=False)
        print(f"✅ Welcome message pinned")
        
        # Store group data for tracking
        store_group_data(chat_id, group_name, group_type, creator.id, bot_username)
        
        # Return result
        return {
            "group_id": chat_id,
            "invite_url": invite_url,
            "group_name": group_name,
            "creator_id": creator.id,
            "bot_username": bot_username
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        if user_client and user_client.is_connected():
            await user_client.disconnect()
            print(f"✅ User client disconnected")

# In the store_group_data function, update to store clean IDs:

def store_group_data(group_id, group_name, group_type, creator_id, bot_username):
    """Store group data for tracking"""
    try:
        GROUPS_FILE = 'data/active_groups.json'
        groups = {}
        
        if os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE, 'r') as f:
                groups = json.load(f)
        
        # Clean group ID (remove -100 prefix for supergroups)
        clean_group_id = str(group_id)
        if clean_group_id.startswith('-100'):
            clean_group_id = clean_group_id[4:]
        
        groups[clean_group_id] = {
            "name": group_name,
            "type": group_type,
            "creator_id": creator_id,
            "bot_username": bot_username,
            "original_id": str(group_id),  # Store original for reference
            "members": [],  # Start empty, will be filled when users join
            "welcome_pinned": True,
            "session_initiated": False,  # Track if /begin has been used
            "created_at": asyncio.get_event_loop().time()
        }
        
        with open(GROUPS_FILE, 'w') as f:
            json.dump(groups, f, indent=2)
            
        print(f"✅ Group data stored: {clean_group_id} ({group_name})")
        
    except Exception as e:
        print(f"Error storing group data: {e}")
