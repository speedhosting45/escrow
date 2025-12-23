import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# User session for group creation
STRING_SESSION1 = os.getenv('STRING_SESSION1', '')

# Database path (for future use)
DB_PATH = 'data/escrow.db'

# Admin ID (for future use)
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Counter for group numbers (can be replaced with database later)
GROUP_COUNTER = 1
