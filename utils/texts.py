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
