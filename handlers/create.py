#!/usr/bin/env python3
"""
Create escrow handlers - Simplified version
"""
from telethon.sessions import StringSession
from telethon.tl import functions, types
from telethon import Button
from config import STRING_SESSION1, API_ID, API_HASH
from telethon import TelegramClient
import asyncio
import json
import os

# Define get_next_number locally if import fails
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
        
        # Get bot username
        bot_username = (await event.client.get_me()).username
        
        # Get group number
        group_number = get_next_number("p2p")
        group_name = f"P2P Escrow By @Siyorou #{group_number:02d}"
        
        # Create group
        result = await create_escrow_group(group_name, bot_username, "p2p")
        
        if result and "invite_url" in result:
            from utils.texts import P2P_CREATED_MESSAGE
            
            # Create message with join button
            message = P2P_CREATED_MESSAGE.format(
                GROUP_NAME=group_name,
                GROUP_INVITE_LINK=result["invite_url"]
            )
            
            join_button = [
                [Button.url("🔗 Join Group", result["invite_url"])],
                [Button.inline("🏠 Main Menu", b"back_to_main")]
            ]
            
            await event.edit(
                message,
                parse_mode='html',
                link_preview=False,
                buttons=join_button
            )
            
            # Print log to console
            print("\n" + "="*60)
            print(f"✅ GROUP CREATED SUCCESSFULLY")
            print(f"📛 Group Name: {group_name}")
            print(f"🔗 Invite Link: {result['invite_url']}")
            print(f"🆔 Group ID: {result.get('group_id', 'N/A')}")
            print(f"🤖 Bot Added: @{bot_username}")
            print(f"👑 Bot Promoted: YES")
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
        
        # Get bot username
        bot_username = (await event.client.get_me()).username
        
        # Get group number
        group_number = get_next_number("other")
        group_name = f"Other Deal Escrow #{group_number:02d}"
        
        # Create group
        result = await create_escrow_group(group_name, bot_username, "other")
        
        if result and "invite_url" in result:
            from utils.texts import OTHER_CREATED_MESSAGE
            
            # Create message with join button
            message = OTHER_CREATED_MESSAGE.format(
                GROUP_NAME=group_name,
                GROUP_INVITE_LINK=result["invite_url"]
            )
            
            join_button = [
                [Button.url("🔗 Join Group", result["invite_url"])],
                [Button.inline("🏠 Main Menu", b"back_to_main")]
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
            print(f"🔗 Invite Link: {result['invite_url']}")
            print(f"🆔 Group ID: {result.get('group_id', 'N/A')}")
            print(f"🤖 Bot Added: @{bot_username}")
            print(f"👑 Bot Promoted: YES")
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

async def create_escrow_group(group_name, bot_username, group_type):
    """
    Create a supergroup, add bot, and promote it
    """
    if not STRING_SESSION1:
        print("❌ STRING_SESSION1 not configured in .env")
        return None
    
    user_client = None
    try:
        # Start user client
        user_client = TelegramClient(StringSession(STRING_SESSION1), API_ID, API_HASH)
        await user_client.start()
        
        print(f"✅ User client started")
        print(f"🔄 Creating group: {group_name}")
        
        # Get bot entity
        bot_entity = await user_client.get_entity(bot_username)
        print(f"✅ Got bot entity: @{bot_username}")
        
        # Create supergroup
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
        
        # Add bot to group
        print("🔄 Adding bot to group...")
        await user_client(functions.channels.InviteToChannelRequest(
            channel=channel,
            users=[bot_entity]
        ))
        print(f"✅ Bot added to group")
        
        # Promote bot as admin
        print("🔄 Promoting bot as admin...")
        await user_client(functions.channels.EditAdminRequest(
            channel=channel,
            user_id=bot_entity,
            admin_rights=types.ChatAdminRights(
                change_info=True,
                post_messages=True,
                edit_messages=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                add_admins=False,
                anonymous=False
            ),
            rank="Bot Admin"
        ))
        print(f"✅ Bot promoted as admin")
        
        # Create invite link
        print("🔄 Creating invite link...")
        invite_link = await user_client(functions.messages.ExportChatInviteRequest(
            peer=channel
        ))
        invite_url = str(invite_link.link)
        print(f"✅ Invite link created")
        
        # Return result
        return {
            "group_id": chat_id,
            "invite_url": invite_url,
            "group_name": group_name
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
