#!/usr/bin/env python3
"""
Create escrow handlers
"""
from telethon.sessions import StringSession
from telethon.tl import functions, types
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
        # Edit the original message to show "creating" status
        await event.edit(
            "🔄 <b>Creating P2P Escrow Group...</b>\n\n<blockquote>Please wait while we set up your secure escrow group</blockquote>",
            parse_mode='html'
        )
        
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
            # Restore original create menu on failure
            await event.edit(
                CREATE_MESSAGE,
                buttons=get_create_buttons(),
                parse_mode='html'
            )
            await event.answer("❌ Failed to create group. Please try again.", alert=True)
            
    except Exception as e:
        print(f"Error in P2P handler: {e}")
        # Restore original menu on error
        try:
            await event.edit(
                CREATE_MESSAGE,
                buttons=get_create_buttons(),
                parse_mode='html'
            )
            await event.answer("❌ An error occurred. Please try again.", alert=True)
        except:
            pass

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
    
    user_client = None
    try:
        # Create user client using the session string
        user_client = TelegramClient(
            StringSession(STRING_SESSION1), 
            API_ID, 
            API_HASH
        )
        
        await user_client.start()
        print(f"✅ User client started for group creation")
        
        # Get the user entity
        try:
            user_entity = await user_client.get_entity(user_id)
        except Exception as e:
            print(f"⚠️ Could not get user entity: {e}")
            # Use InputPeerUser as fallback
            user_entity = types.InputPeerUser(user_id=user_id, access_hash=0)
        
        # Create the private group using messages.CreateChatRequest
        group_name = "P2P Escrow By @Siyorou #01"
        
        # First, create the chat
        created = await user_client(functions.messages.CreateChatRequest(
            users=[user_entity],
            title=group_name
        ))
        
        # Extract the chat ID from the result
        chat_id = created.chats[0].id
        print(f"✅ Group created: {group_name} (ID: {chat_id})")
        
        # Get the chat entity
        chat_entity = await user_client.get_entity(chat_id)
        
        # Get the bot's entity
        bot_me = await bot_client.get_me()
        
        # Add the bot to the group
        try:
            bot_entity = await user_client.get_entity(bot_me.username)
            await user_client(functions.messages.AddChatUserRequest(
                chat_id=chat_id,
                user_id=bot_entity,
                fwd_limit=100  # Number of recent messages to forward
            ))
            print(f"✅ Bot added to group")
        except Exception as e:
            print(f"⚠️ Could not add bot: {e}")
            # Continue anyway - group is still created
        
        # Promote bot as admin
        try:
            # First, we need to get the bot participant in the chat
            # Get full chat info
            full_chat = await user_client(functions.messages.GetFullChatRequest(
                chat_id=chat_id
            ))
            
            # Find bot participant
            bot_participant = None
            for participant in full_chat.full_chat.participants.participants:
                if hasattr(participant, 'user_id') and participant.user_id == bot_me.id:
                    bot_participant = participant
                    break
            
            if bot_participant:
                # Promote bot as admin using EditChatAdminRequest
                await user_client(functions.messages.EditChatAdminRequest(
                    chat_id=chat_id,
                    user_id=bot_entity,
                    is_admin=True
                ))
                print(f"✅ Bot promoted as admin")
        except Exception as e:
            print(f"⚠️ Could not promote bot as admin: {e}")
            # Some chats might not support admin promotion
        
        # Create invite link
        try:
            invite_link = await user_client(functions.messages.ExportChatInviteRequest(
                peer=chat_entity
            ))
            invite_url = str(invite_link.link)
            print(f"✅ Invite link created: {invite_url}")
        except Exception as e:
            print(f"⚠️ Could not create invite link: {e}")
            # Create a basic invite link as fallback
            try:
                # Try to get the chat's username for public link
                if hasattr(chat_entity, 'username') and chat_entity.username:
                    invite_url = f"https://t.me/{chat_entity.username}"
                else:
                    # For private chats/groups
                    invite_url = f"https://t.me/c/{str(chat_id).replace('-100', '')}"
            except:
                invite_url = f"Group created successfully! ID: {chat_id}"
        
        return invite_url
        
    except Exception as e:
        print(f"❌ Error creating group: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Always disconnect user client
        if user_client and user_client.is_connected():
            await user_client.disconnect()
            print(f"✅ User client disconnected")

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
        # Fallback to editing message if answer fails
        try:
            await event.edit(
                "<b>📦 Other Deal</b>\n\n<blockquote>This feature is coming soon...</blockquote>",
                parse_mode='html',
                buttons=get_main_menu_buttons()
            )
        except:
            pass
