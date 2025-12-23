#!/usr/bin/env python3
"""
Create escrow handlers with enhanced logging
"""
from telethon.sessions import StringSession
from telethon.tl import functions, types
from telethon.errors import MessageNotModifiedError, FloodWaitError
from telethon import Button
from utils.texts import CREATE_MESSAGE, P2P_CREATED_MESSAGE
from utils.buttons import get_create_buttons, get_main_menu_buttons
from config import STRING_SESSION1, API_ID, API_HASH, BOT_TOKEN, increment_group_count, add_active_group, get_group_count
from telethon import TelegramClient
import asyncio
import time

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
        user_entity = await event.client.get_entity(user_id)
        user_username = f"@{user_entity.username}" if user_entity.username else f"User_{user_id}"
        bot_username = (await event.client.get_me()).username
        group_link = await create_p2p_group(user_id, user_username, bot_username, event.client)
        
        # Delete the processing message
        await processing_msg.delete()
        
        # Send success message with group link
        if group_link:
            message = P2P_CREATED_MESSAGE.format(GROUP_INVITE_LINK=group_link)
            # Create join button
            join_button = [
                [Button.url("🔗 Join Now", group_link)],
                [Button.inline("🏠 Main Menu", b"back_to_main")]
            ]
            
            await event.respond(
                message,
                parse_mode='html',
                link_preview=False,
                buttons=join_button
            )
        else:
            await event.answer("❌ Failed to create group. Please try again.", alert=True)
            
    except Exception as e:
        print(f"Error in P2P handler: {e}")
        try:
            await event.answer("❌ An error occurred. Please try again.", alert=True)
        except:
            await event.respond("❌ An error occurred. Please try again.")

async def create_p2p_group(user_id, user_username, bot_username, bot_client):
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
    invite_url = None
    chat_id = None
    
    try:
        # Create user client using the session string
        user_client = TelegramClient(
            StringSession(STRING_SESSION1), 
            API_ID, 
            API_HASH
        )
        
        await user_client.start()
        print(f"✅ User client started for group creation")
        
        # Get dialogs to populate entity cache
        try:
            print("🔄 Getting dialogs to populate entity cache...")
            dialogs = await user_client.get_dialogs(limit=10)
            print(f"✅ Got {len(dialogs)} dialogs")
        except Exception as e:
            print(f"⚠️ Could not get dialogs: {e}")
        
        # Get the bot entity
        print(f"🔄 Getting bot entity: @{bot_username}")
        bot_entity = await user_client.get_entity(bot_username)
        print(f"✅ Got bot entity: {bot_entity.id}")
        
        # Get user entity
        print(f"🔄 Getting user entity: {user_id}")
        user_entity = await user_client.get_entity(user_id)
        print(f"✅ Got user entity: {user_id}")
        
        # Create the private group (supergroup)
        group_name = "P2P Escrow By @Siyorou #01"
        
        # Create a supergroup
        print("🔄 Creating supergroup...")
        created = await user_client(functions.channels.CreateChannelRequest(
            title=group_name,
            about="Secure P2P Escrow Group",
            megagroup=True,
            broadcast=False
        ))
        
        # The result contains a list of chats
        chat = created.chats[0]
        chat_id = chat.id
        channel = types.InputPeerChannel(channel_id=chat.id, access_hash=chat.access_hash)
        print(f"✅ Supergroup created: {group_name} (ID: {chat_id})")
        
        # LOG: Send creation log
        total_groups = increment_group_count()
        add_active_group(str(chat_id), user_username)
        
        # Send log message to channel or group
        await send_creation_log(bot_client, chat_id, user_username, total_groups)
        
        # Add the user to the group
        print("🔄 Adding user to group...")
        await user_client(functions.channels.InviteToChannelRequest(
            channel=channel,
            users=[user_entity]
        ))
        print(f"✅ User added to group")
        
        # Add the bot to the group
        print("🔄 Adding bot to group...")
        await user_client(functions.channels.InviteToChannelRequest(
            channel=channel,
            users=[bot_entity]
        ))
        print(f"✅ Bot added to group")
        
        # Create invite link
        print("🔄 Creating invite link...")
        invite_link = await user_client(functions.messages.ExportChatInviteRequest(
            peer=channel
        ))
        invite_url = str(invite_link.link)
        print(f"✅ Invite link created: {invite_url}")
        
        # Store invite link for future revocation
        store_invite_link(str(chat_id), invite_url)
        
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
    finally:
        # Always disconnect user client
        if user_client and user_client.is_connected():
            await user_client.disconnect()
            print(f"✅ User client disconnected")

async def send_creation_log(bot_client, chat_id, created_by, total_groups):
    """
    Send group creation log
    """
    try:
        log_message = f"""
<b>#NEW_GROUP_CREATED</b>

<blockquote>
New P2P Escrow Group Created Successfully!
</blockquote>

• <b>CREATED BY</b> : {created_by}
• <b>GROUP ID</b> : <code>{chat_id}</code>
• <b>GROUPS CREATED TILL NOW</b> : {total_groups}

Group is ready for secure transactions.
"""
        
        # Send to a specific log channel/group (you can configure this)
        # For now, send to the bot's log
        print(f"📝 Log: {log_message}")
        
        # You can also send to your own user ID or a channel
        # await bot_client.send_message(YOUR_LOG_CHAT_ID, log_message, parse_mode='html')
        
    except Exception as e:
        print(f"Error sending creation log: {e}")

def store_invite_link(group_id, invite_url):
    """
    Store invite link for future revocation
    """
    try:
        import json
        data = {}
        if os.path.exists('data/invite_links.json'):
            with open('data/invite_links.json', 'r') as f:
                data = json.load(f)
        
        data[group_id] = {
            "link": invite_url,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "revoked": False,
            "users_joined": 0
        }
        
        with open('data/invite_links.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Invite link stored for group {group_id}")
    except Exception as e:
        print(f"Error storing invite link: {e}")

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
