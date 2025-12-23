import os
import json
import time  # ADD THIS IMPORT
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

# Counter for group numbers
GROUP_COUNTER_FILE = 'data/group_counter.json'

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

def get_next_group_number():
    """Get next sequential group number"""
    if os.path.exists(GROUP_COUNTER_FILE):
        with open(GROUP_COUNTER_FILE, 'r') as f:
            counter = json.load(f)
    else:
        counter = {"p2p": 1, "other": 1}
    
    return counter

def save_group_number(counter):
    """Save group counter"""
    with open(GROUP_COUNTER_FILE, 'w') as f:
        json.dump(counter, f, indent=2)

def increment_group_count(group_type="p2p"):
    """Increment total groups counter and get next number"""
    stats = load_stats()
    stats["total_groups"] = stats.get("total_groups", 0) + 1
    save_stats(stats)
    
    counter = get_next_group_number()
    next_number = counter.get(group_type, 1)
    counter[group_type] = next_number + 1
    save_group_number(counter)
    
    return {
        "total_groups": stats["total_groups"],
        "group_number": next_number,
        "counter": counter
    }

def add_active_group(group_id, created_by, group_type="p2p"):
    """Add group to active groups list"""
    stats = load_stats()
    if "active_groups" not in stats:
        stats["active_groups"] = []
    
    group_info = {
        "id": group_id,
        "created_by": created_by,
        "type": group_type,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "link_revoked": False
    }
    stats["active_groups"].append(group_info)
    save_stats(stats)

def get_group_count():
    """Get total groups count"""
    stats = load_stats()
    return stats.get("total_groups", 0)
