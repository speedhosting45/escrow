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
        await event.edit(
            CREATE_MESSAGE,
            buttons=get_create_buttons(),
            parse_mode='html'
        )
    except Exception as e:
        print(f"Error in create handler: {e}")
        try:
            await event.answer("✅ Create escrow menu", alert=False)
        except:
            pass

async def handle_create_p2p(event):
    """
    Handle P2P deal selection - create private group
    """
    try:
        # First, send a new processing message instead of editing
        processing_msg = await event.respond(
            "🔄 <b>Creating P2P Escrow Group...</b>\n\n<blockquote>Please wait while we set up your secure escrow group</blockquote>",
            parse_mode='html'
        )
        
        user_id = event.sender_id
        group_link = await create_p2p_group(user_id, event.client)
        
        # Delete the processing message
        await processing_msg.delete()
        
        # Send success message with group link
        if group_link:
            message = P2P_CREATED_MESSAGE.format(GROUP_INVITE_LINK=group_link)
            await event.respond(
                message,
                parse_mode='html',
                link_preview=False,
                buttons=get_main_menu_buttons()
            )
        else:
            await event.answer("❌ Failed to create group. Please try again.", alert=True)
            
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
        
        # Create the private group
        group_name = "P2P Escrow By @Siyorou #01"
        
        # METHOD 1: Try CreateChatRequest first
        try:
            created = await user_client(functions.messages.CreateChatRequest(
                users=[user_entity],
                title=group_name
            ))
            
            chat_id = created.chats[0].id
            print(f"✅ Group created via CreateChatRequest: {group_name} (ID: {chat_id})")
            
        except Exception as e:
            print(f"⚠️ CreateChatRequest failed: {e}")
            # METHOD 2: Try CreateChannelRequest for supergroups
            try:
                created = await user_client(functions.channels.CreateChannelRequest(
                    title=group_name,
                    about="P2P Escrow Group",
                    megagroup=True,  # This makes it a supergroup
                    broadcast=False
                ))
                
                chat_id = created.chats[0].id
                print(f"✅ Group created via CreateChannelRequest: {group_name} (ID: {chat_id})")
                
                # Add user to the new supergroup
                await user_client(functions.channels.InviteToChannelRequest(
                    channel=created.chats[0],
                    users=[user_entity]
                ))
                
            except Exception as e2:
                print(f"❌ All group creation methods failed: {e2}")
                return None
        
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
                fwd_limit=100
            ))
            print(f"✅ Bot added to group")
        except Exception as e:
            print(f"⚠️ Could not add bot via AddChatUserRequest: {e}")
            # Try alternative method for supergroups
            try:
                await user_client(functions.channels.InviteToChannelRequest(
                    channel=chat_entity,
                    users=[bot_entity]
                ))
                print(f"✅ Bot added via InviteToChannelRequest")
            except Exception as e2:
                print(f"⚠️ Could not add bot at all: {e2}")
        
        # Try to promote bot as admin
        try:
            # For regular groups
            await user_client(functions.messages.EditChatAdminRequest(
                chat_id=chat_id,
                user_id=bot_entity,
                is_admin=True
            ))
            print(f"✅ Bot promoted as admin")
        except Exception as e:
            print(f"⚠️ Could not promote bot as admin: {e}")
            # For supergroups, use different method
            try:
                await user_client(functions.channels.EditAdminRequest(
                    channel=chat_entity,
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
                print(f"✅ Bot promoted as admin in supergroup")
            except Exception as e2:
                print(f"⚠️ Could not promote bot in supergroup: {e2}")
        
        # Create invite link
        try:
            invite_link = await user_client(functions.messages.ExportChatInviteRequest(
                peer=chat_entity
            ))
            invite_url = str(invite_link.link)
            print(f"✅ Invite link created: {invite_url}")
        except Exception as e:
            print(f"⚠️ Could not create invite link: {e}")
            # Try supergroup method
            try:
                invite_link = await user_client(functions.channels.ExportInviteRequest(
                    channel=chat_entity
                ))
                invite_url = str(invite_link.link)
                print(f"✅ Supergroup invite link created: {invite_url}")
            except Exception as e2:
                print(f"⚠️ Could not create any invite link: {e2}")
                # Create a basic link
                try:
                    # Remove the -100 prefix for t.me/c/ links
                    if str(chat_id).startswith('-100'):
                        short_id = str(chat_id)[4:]
                        invite_url = f"https://t.me/c/{short_id}"
                    else:
                        invite_url = f"https://t.me/c/{chat_id}"
                    print(f"✅ Basic link created: {invite_url}")
                except:
                    invite_url = f"Group created! Please check your Telegram chats."
        
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
        try:
            await event.respond("📦 Other Deal selected! This feature is coming soon...")
        except:
            pass
