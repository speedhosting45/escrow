#!/usr/bin/env python3
"""
Create escrow handlers
"""
from telethon.sessions import StringSession
from telethon.tl import functions
from telethon.errors import MessageNotModifiedError
from utils.texts import CREATE_MESSAGE, P2P_CREATED_MESSAGE
from utils.buttons import get_create_buttons, get_main_menu_buttons
from config import STRING_SESSION1, API_ID, API_HASH
from telethon import TelegramClient
import asyncio

async def handle_create(event):
    """
    Handle create escrow button click
    """
    try:
        # Try to edit the message
        await event.edit(
            CREATE_MESSAGE,
            buttons=get_create_buttons(),
            parse_mode='html'
        )
    except MessageNotModifiedError:
        # Message already has this content, send a new one instead
        try:
            await event.delete()
            await event.respond(
                CREATE_MESSAGE,
                buttons=get_create_buttons(),
                parse_mode='html'
            )
        except Exception as e:
            print(f"Error sending new message in create: {e}")
            await event.answer("✅ Create escrow menu", alert=False)
    except Exception as e:
        print(f"Error in create handler: {e}")
        try:
            await event.answer("❌ An error occurred.", alert=True)
        except:
            pass

async def handle_create_p2p(event):
    """
    Handle P2P deal selection - create private group
    """
    try:
        # Delete the "Creating..." popup after a delay
        await event.delete()
        
        # Show processing message
        processing_msg = await event.respond(
            "🔄 Creating P2P escrow group... Please wait."
        )
        
        user_id = event.sender_id
        group_link = await create_p2p_group(user_id, event.client)
        
        # Delete processing message
        await processing_msg.delete()
        
        # Send success message with group link
        if group_link:
            message = P2P_CREATED_MESSAGE.format(GROUP_INVITE_LINK=group_link)
            
            # Try to edit the original message first
            try:
                await event.edit(
                    message,
                    parse_mode='html',
                    link_preview=False
                )
            except (MessageNotModifiedError, ValueError):
                # If can't edit, send as new message
                await event.respond(
                    message,
                    parse_mode='html',
                    link_preview=False,
                    buttons=get_main_menu_buttons()
                )
        else:
            try:
                await event.answer("❌ Failed to create group. Please try again.", alert=True)
            except:
                await event.respond("❌ Failed to create group. Please try again.")
            
    except Exception as e:
        print(f"Error in P2P handler: {e}")
        try:
            await event.answer("❌ An error occurred. Please try again.", alert=True)
        except:
            await event.respond("❌ An error occurred. Please try again.")

async def create_p2p_group(user_id, bot_client):
    """
    Create a private Telegram group using user session
    """
    if not STRING_SESSION1:
        print("❌ STRING_SESSION1 not configured in .env")
        return None
    
    if not API_ID or not API_HASH:
        print("❌ API_ID or API_HASH not configured")
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
        
        # First, get the user entity
        try:
            user_entity = await user_client.get_entity(user_id)
            users_to_add = [user_entity]
        except:
            users_to_add = [user_id]
        
        group = await user_client.create_group(
            title=group_name,
            users=users_to_add
        )
        print(f"✅ Group created: {group_name}")
        
        # Get the bot's entity
        bot_me = await bot_client.get_me()
        
        # Add the bot to the group
        try:
            await user_client.add_participants(group, bot_me.username)
            print(f"✅ Bot added to group")
        except Exception as e:
            print(f"⚠️ Could not add bot: {e}")
            # Continue anyway
        
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
        try:
            invite_link = await user_client(
                functions.messages.ExportChatInviteRequest(
                    peer=group
                )
            )
            invite_url = str(invite_link.link)
            print(f"✅ Invite link created: {invite_url}")
        except Exception as e:
            print(f"⚠️ Could not create invite link: {e}")
            # Get the group link as fallback
            try:
                entity = await user_client.get_entity(group)
                invite_url = f"https://t.me/c/{entity.id}"
            except:
                invite_url = "Group created but could not get invite link"
        
        # Disconnect user client
        await user_client.disconnect()
        
        return invite_url
        
    except Exception as e:
        print(f"❌ Error creating group: {e}")
        import traceback
        traceback.print_exc()
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
        await event.respond("📦 Other Deal selected! This feature is coming soon...")
