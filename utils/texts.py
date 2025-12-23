# Text messages for the bot

START_MESSAGE = """
<b>🔐 Secure Escrow Bot</b>

<blockquote>
Safe • Transparent • Trusted
</blockquote>

Welcome! This bot helps you create secure escrow deals between buyers and sellers.

Choose an option below to continue ⬇️
"""
# Add this to your texts.py file

OTHER_CREATED_MESSAGE = """
<b>📦 Other Deal Escrow Created</b>

<blockquote>
Your private escrow group has been created successfully
</blockquote>

• Group Name: <b>{GROUP_NAME}</b>  
• Type: <b>Other Deal</b>  

Please continue your deal inside the group.

🔗 <b>Group Link:</b>  
<a href="{GROUP_INVITE_LINK}">{GROUP_INVITE_LINK}</a>
"""
CREATE_MESSAGE = """
<b>➕ Create Escrow</b>

<blockquote>
Select the type of deal you want to create
</blockquote>
"""
# Add this new template to texts.py

ROLE_ANNOUNCEMENT_MESSAGE = """
{mention} declared as {role_emoji} <b>{role_name}</b>

<blockquote>
👥 Status: Buyers: {buyer_count} | Sellers: {seller_count}
</blockquote>
"""

STATS_MESSAGE = """
<b>📊 Your Stats</b>

<blockquote>
Escrow statistics will appear here soon
</blockquote>

• Total Escrows: 0  
• Completed: 0  
• Disputes: 0  
• Success Rate: 0%
"""
P2P_CREATED_MESSAGE = """
<b>🤝 P2P Escrow Created</b>

<blockquote>
Your private escrow group has been created successfully
</blockquote>

• Group Name: <b>P2P Escrow By @Siyorou #01</b>  
• Type: <b>P2P Deal</b>  

Please continue your deal inside the group.

🔗 <b>Group Link:</b>  
<a href="{GROUP_INVITE_LINK}">{GROUP_INVITE_LINK}</a>
"""

ABOUT_MESSAGE = """
<b>ℹ️ About This Bot</b>

<blockquote>
A secure escrow solution built for Telegram
</blockquote>

• Supports P2P deals  
• Transparent escrow flow  
• Admin-controlled dispute resolution  

More features coming soon 🚀
"""
# Welcome message that gets pinned
WELCOME_MESSAGE = """
🤝 <b>Welcome to P2P Escrow by @{bot_username}</b>

To initiate this deal:
<code>/begin</code>
"""

# Session initiation message
SESSION_INITIATED_MESSAGE = """
<b>🔐 @{bot_username} P2P Escrow Session Initiated</b>

Participants:
<a href="tg://user?id={user1_id}">{user1_name}</a> • <a href="tg://user?id={user2_id}">{user2_name}</a>

This escrow session is governed by verified rules to ensure a fair and secure trade.

<b>Please declare your role to proceed:</b>

<code>
Buyer  → Select Buyer role
Seller → Select Seller role
</code>

<b>Important:</b>
Role selection is final and cannot be modified once confirmed.
"""

# Buyer role confirmation
BUYER_CONFIRMED_MESSAGE = """
<b>Buyer Role Confirmed</b>

<a href="tg://user?id={buyer_id}">{buyer_name}</a> has been registered as the <b>Buyer</b> for this escrow session.

This role is now <b>locked</b> and cannot be changed.
"""

# Seller role confirmation  
SELLER_CONFIRMED_MESSAGE = """
<b>Seller Role Confirmed</b>

<a href="tg://user?id={seller_id}">{seller_name}</a> has been registered as the <b>Seller</b> for this escrow session.

This role is now <b>locked</b> and cannot be changed.
"""

# Role already chosen (same user)
ROLE_ALREADY_CHOSEN_MESSAGE = """
⛔ Role Already Chosen (Blocked)
Action denied.

Your role has already been declared and cannot be changed.
"""

# Role already taken (other user)
ROLE_ALREADY_TAKEN_MESSAGE = """
⚠️ Role Already Taken
This role has already been assigned.

Please select the remaining available role.
"""

# Wallet setup message
WALLET_SETUP_MESSAGE = """
<b>✅ Roles Are Confirmed</b>

<blockquote>
<b>Buyer:</b> {buyer_name}  
<b>Seller:</b> {seller_name}
</blockquote>

<b>Please set your wallets to continue:</b>

<code>
Buyer  : /buyer {{buyer_wallet_address}}
Seller : /seller {{seller_wallet_address}}
</code>

<blockquote>
⚠️ Make sure the wallet addresses are correct.
Once submitted, they <b>cannot be changed</b>.
</blockquote>
"""

# Escrow ready message
ESCROW_READY_MESSAGE = """
🎉 <b>ESCROW READY TO START!</b> 🎉

<blockquote>
✅ <b>All Requirements Met</b> ✅
</blockquote>

════════════════════════════════════

<b>👤 PARTICIPANTS:</b>
🛒 <b>Buyer:</b> {buyer_name}
💰 <b>Seller:</b> {seller_name}

════════════════════════════════════

<b>🔗 WALLET ADDRESSES:</b>
• <b>Buyer Wallet:</b> <code>{buyer_wallet}</code>
• <b>Seller Wallet:</b> <code>{seller_wallet}</code>

════════════════════════════════════

<b>📝 NEXT STEPS:</b>
1. Buyer sends funds to escrow
2. Seller confirms item/service delivery
3. Buyer confirms receipt
4. Funds released to seller

<blockquote>
⚠️ <b>IMPORTANT:</b> All communications and transactions should happen in this group for transparency and security.
</blockquote>

🔒 <b>SECURE ESCROW ACTIVE</b>
"""

HELP_MESSAGE = """
<b>❓ Help & Support</b>

<blockquote>
How this escrow bot works
</blockquote>

1️⃣ Buyer creates escrow  
2️⃣ Funds are secured  
3️⃣ Seller delivers  
4️⃣ Buyer confirms  
5️⃣ Funds released safely  

Need help? Contact admin.
"""
