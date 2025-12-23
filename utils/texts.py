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
# Add these new text templates to your existing texts.py

ROLE_SELECTION_MESSAGE = """
<b>👋 Welcome!</b>

<blockquote>
Participants:
• {user1}  
• {user2}
</blockquote>

<b>Please choose your role:</b>
🛒 Buyer  
💼 Seller  

<blockquote>
⚠️ <b>Note:</b> Once a role is selected, it <b>cannot be changed</b>.
</blockquote>
"""

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

WALLET_SAVED_MESSAGE = """
✅ {role} wallet address saved!

<code>{wallet_preview}</code>

{status_message}
"""

BUYER_ONLY_MESSAGE = "❌ Only the buyer can set the buyer wallet address."
SELLER_ONLY_MESSAGE = "❌ Only the seller can set the seller wallet address."
NO_ROLE_MESSAGE = "❌ You haven't selected a role in this group yet."
INVALID_WALLET_MESSAGE = "❌ Wallet address seems too short. Please check and try again."

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
