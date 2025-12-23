#!/usr/bin/env python3
"""
Create escrow handlers
"""
from telethon.sessions import StringSession
from telethon.tl import functions
from utils.texts import CREATE_MESSAGE, P2P_CREATED_MESSAGE
from utils.buttons import get_create_buttons
from config import STRING_SESSION1, API_ID, API_HASH, BOT_TOKEN
from telethon import TelegramClient
import asyncio

async def handle_create(event):
    """
    Handle create escrow button click
    """
    try:
        await event.edit(
            CREATE_MESSAGE,
            buttons=get_create_buttons(),
            parse_mode='html'
        )
    except Exception as e:
        print(f"Error in create handler: {e}")
        await event.answer("❌ An error occurred.", alert=True)

async def handle_create_p2p(event):
    """
    Handle P2P deal selection - create private group
    """
    try:
        # First show "processing" message
        await event.answer("Creating P2P escrow group...", alert=True)
        
        user_id = event.sender_id
        group_link = await create_p2p_group(user_id, event.client)
        
        # Send success message with group link
        if group_link:
            message = P2P_CREATED_MESSAGE.format(GROUP_INVITE_LINK=group_link)
            await event.edit(
                message,
                parse_mode='html',
                link_preview=False
            )
        else:
            await event.answer("❌ Failed to create group. Please try again.", alert=True)
            
    except Exception as e:
        print(f"Error in P2P handler: {e}")
        await event.answer("❌ An error occurred. Please try again.", alert=True)

async def create_p2p_group(user_id, bot_client):
    """
    Create a private Telegram group using user session
    """
    if not STRING_SESSION1:
        print("❌ STRING_SESSION1 not configured in .env")
        return None
    
    try:
        # Create user client using the session string
        user_client = TelegramClient(
            StringSession(STRING_SESSION1), 
            API_ID, 
            API_HASH
        )
        
        await user_client.start()
        print(f"✅ User client started for group creation")
        
        # Create the private group
        group_name = "P2P Escrow By @Siyorou #01"
        group = await user_client.create_group(
            title=group_name,
            users=[user_id]  # Add the user who clicked
        )
        print(f"✅ Group created: {group_name}")
        
        # Get the bot's entity
        bot_me = await bot_client.get_me()
        
        # Add the bot to the group
        await user_client.add_participants(group, bot_me.username)
        print(f"✅ Bot added to group")
        
        # Promote bot as admin
        try:
            # Get the bot's participant entity in the group
            participants = await user_client.get_participants(group)
            bot_participant = None
            for participant in participants:
                if participant.id == bot_me.id:
                    bot_participant = participant
                    break
            
            if bot_participant:
                # Set bot as admin
                await user_client.edit_admin(
                    group,
                    bot_participant,
                    is_admin=True,
                    add_admins=False,
                    change_info=True,
                    post_messages=True,
                    edit_messages=True,
                    delete_messages=True,
                    ban_users=True,
                    invite_users=True,
                    pin_messages=True,
                    add_admins=False
                )
                print(f"✅ Bot promoted as admin")
        except Exception as e:
            print(f"⚠️ Could not promote bot as admin: {e}")
        
        # Create invite link
        invite_link = await user_client(
            functions.messages.ExportChatInviteRequest(
                peer=group
            )
        )
        
        # Disconnect user client
        await user_client.disconnect()
        
        return str(invite_link.link)
        
    except Exception as e:
        print(f"❌ Error creating group: {e}")
        return None

async def handle_create_other(event):
    """
    Handle Other deal selection (placeholder)
    """
    try:
        await event.answer(
            "📦 Other Deal selected! This feature is coming soon...",
            alert=True
        )
    except Exception as e:
        print(f"Error in Other deal handler: {e}")
