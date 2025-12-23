import os
import json
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# User session for group creation
STRING_SESSION1 = os.getenv('STRING_SESSION1', '')

# Stats file path
STATS_FILE = 'data/stats.json'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def load_stats():
    """Load statistics from file"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    return {"total_groups": 0, "active_groups": [], "users_joined": 0}

def save_stats(stats):
    """Save statistics to file"""
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)

def increment_group_count():
    """Increment total groups counter"""
    stats = load_stats()
    stats["total_groups"] = stats.get("total_groups", 0) + 1
    save_stats(stats)
    return stats["total_groups"]

def add_active_group(group_id, created_by):
    """Add group to active groups list"""
    stats = load_stats()
    if "active_groups" not in stats:
        stats["active_groups"] = []
    
    group_info = {
        "id": group_id,
        "created_by": created_by,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "link_revoked": False
    }
    stats["active_groups"].append(group_info)
    save_stats(stats)

def get_group_count():
    """Get total groups count"""
    stats = load_stats()
    return stats.get("total_groups", 0)

def increment_user_joined():
    """Increment users joined counter"""
    stats = load_stats()
    stats["users_joined"] = stats.get("users_joined", 0) + 1
    save_stats(stats)
    return stats["users_joined"]
