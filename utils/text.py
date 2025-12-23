# Text messages for the bot

START_MESSAGE = """
<b>🔐 Secure Escrow Bot</b>

<blockquote>
Safe • Transparent • Trusted
</blockquote>

Welcome! This bot helps you create secure escrow deals between buyers and sellers.

Choose an option below to continue ⬇️
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

ERROR_MESSAGES = {
    'unknown': "❌ An error occurred. Please try again.",
    'access_denied': "⛔ You don't have permission to perform this action.",
    'invalid_input': "⚠️ Invalid input. Please check and try again.",
}
