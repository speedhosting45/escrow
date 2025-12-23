#!/usr/bin/env python3
"""
Create escrow handlers
"""
from telethon.sessions import StringSession
from telethon.tl import functions, types
from telethon.errors import MessageNotModifiedError, FloodWaitError
from utils.texts import CREATE_MESSAGE, P2P_CREATED_MESSAGE
from utils.buttons import get_create_buttons, get_main_menu_buttons
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
        try:
            await event.answer("✅ Create escrow menu", alert=False)
        except:
            pass

async def handle_create_p2p(event):
    """
    Handle P2P deal selection - create private group
    """
    try:
        # First, send a new processing message
        processing_msg = await event.respond(
            "🔄 <b>Creating P2P Escrow Group...</b>\n\n<blockquote>Please wait while we set up your secure escrow group</blockquote>",
            parse_mode='html'
        )
        
        user_id = event.sender_id
        bot_username = (await event.client.get_me()).username
        group_link = await create_p2p_group(user_id, bot_username, event.client)
        
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

async def create_p2p_group(user_id, bot_username, bot_client):
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
        
        # METHOD 1: First try to get dialogs to populate entity cache
        try:
            print("🔄 Getting dialogs to populate entity cache...")
            dialogs = await user_client.get_dialogs(limit=10)
            print(f"✅ Got {len(dialogs)} dialogs")
        except Exception as e:
            print(f"⚠️ Could not get dialogs: {e}")
        
        # Get the bot entity using username (better than ID for first-time)
        print(f"🔄 Getting bot entity: @{bot_username}")
        try:
            # First try to get bot by username
            bot_entity = await user_client.get_entity(bot_username)
            print(f"✅ Got bot entity: {bot_entity.id}")
        except Exception as e:
            print(f"⚠️ Could not get bot by username: {e}")
            # Try to find bot in contacts or dialogs
            try:
                contacts = await user_client.get_contacts()
                for contact in contacts:
                    if hasattr(contact, 'bot') and contact.bot and contact.username == bot_username:
                        bot_entity = contact
                        print(f"✅ Found bot in contacts: {bot_entity.id}")
                        break
            except Exception as e2:
                print(f"⚠️ Could not find bot in contacts: {e2}")
                # Use InputPeerUser as last resort
                bot_entity = types.InputPeerUser(user_id=await get_bot_id(bot_username), access_hash=0)
                print(f"⚠️ Using fallback bot entity")
        
        # Get user entity
        print(f"🔄 Getting user entity: {user_id}")
        try:
            user_entity = await user_client.get_entity(user_id)
            print(f"✅ Got user entity: {user_id}")
        except Exception as e:
            print(f"⚠️ Could not get user entity by ID: {e}")
            # Try via dialogs
            try:
                for dialog in dialogs:
                    if dialog.entity.id == user_id:
                        user_entity = dialog.entity
                        print(f"✅ Found user in dialogs: {user_id}")
                        break
            except:
                pass
            
            # If still not found, use InputPeerUser
            if 'user_entity' not in locals():
                user_entity = types.InputPeerUser(user_id=user_id, access_hash=0)
                print(f"⚠️ Using fallback user entity")
        
        # Create the private group (supergroup)
        group_name = "P2P Escrow By @Siyorou #01"
        
        # Create a supergroup (megagroup)
        print("🔄 Creating supergroup...")
        try:
            created = await user_client(functions.channels.CreateChannelRequest(
                title=group_name,
                about="Secure P2P Escrow Group",
                megagroup=True,  # This makes it a supergroup (large group)
                broadcast=False
            ))
            
            # The result contains a list of chats
            chat = created.chats[0]
            chat_id = chat.id
            print(f"✅ Supergroup created: {group_name} (ID: {chat_id})")
            
            # Get the full channel entity
            channel = types.InputPeerChannel(channel_id=chat_id, access_hash=chat.access_hash)
            
            # Add the user to the group
            print("🔄 Adding user to group...")
            try:
                await user_client(functions.channels.InviteToChannelRequest(
                    channel=channel,
                    users=[user_entity]
                ))
                print(f"✅ User added to group")
            except Exception as e:
                print(f"⚠️ Could not add user to group: {e}")
            
            # Add the bot to the group
            print("🔄 Adding bot to group...")
            try:
                await user_client(functions.channels.InviteToChannelRequest(
                    channel=channel,
                    users=[bot_entity]
                ))
                print(f"✅ Bot added to group")
            except Exception as e:
                print(f"⚠️ Could not add bot to group: {e}")
                # Try alternative method
                try:
                    await user_client(functions.messages.AddChatUserRequest(
                        chat_id=chat_id,
                        user_id=bot_entity,
                        fwd_limit=100
                    ))
                    print(f"✅ Bot added via alternative method")
                except Exception as e2:
                    print(f"⚠️ Could not add bot via alternative method: {e2}")
            
            # Try to promote bot as admin
            print("🔄 Promoting bot as admin...")
            try:
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
            except Exception as e:
                print(f"⚠️ Could not promote bot as admin: {e}")
            
            # Create invite link
            print("🔄 Creating invite link...")
            try:
                invite_link = await user_client(functions.messages.ExportChatInviteRequest(
                    peer=channel
                ))
                invite_url = str(invite_link.link)
                print(f"✅ Invite link created: {invite_url}")
            except Exception as e:
                print(f"⚠️ Could not create invite link: {e}")
                # Create a basic link for supergroups
                try:
                    # For supergroups, the invite link is different
                    invite_link = await user_client(functions.channels.ExportInviteRequest(
                        channel=channel
                    ))
                    invite_url = str(invite_link.link)
                    print(f"✅ Supergroup invite link created: {invite_url}")
                except Exception as e2:
                    print(f"⚠️ Could not create supergroup invite link: {e2}")
                    # Create a basic t.me/c/ link
                    if str(chat_id).startswith('-100'):
                        short_id = str(chat_id)[4:]
                        invite_url = f"https://t.me/c/{short_id}"
                    else:
                        invite_url = f"https://t.me/c/{chat_id}"
                    print(f"✅ Basic link created: {invite_url}")
            
            return invite_url
            
        except FloodWaitError as e:
            print(f"⏳ Flood wait error: Need to wait {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return None
        except Exception as e:
            print(f"❌ Error creating group: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    except Exception as e:
        print(f"❌ Error in group creation process: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Always disconnect user client
        if user_client and user_client.is_connected():
            await user_client.disconnect()
            print(f"✅ User client disconnected")

async def get_bot_id(username):
    """
    Get bot ID from username (if needed)
    """
    # You can hardcode this or get it dynamically
    # For @AutoReqAccepterRobot, you need to find its ID
    # This is a placeholder - you should replace with actual logic
    return 1234567890  # Replace with actual bot ID

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
