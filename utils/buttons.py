from telethon import Button

# Main menu buttons
def get_main_menu_buttons():
    return [
        [
            Button.inline("📊 Stats", b"stats"),
            Button.inline("➕ Create", b"create")
        ],
        [
            Button.inline("ℹ️ About", b"about"),
            Button.inline("❓ Help", b"help")
        ]
    ]

# Create escrow type buttons
def get_create_buttons():
    return [
        [
            Button.inline("P2P 𝘋𝘦𝘢𝘭", b"create_p2p"),
            Button.inline("Other 𝘋𝘦𝘢𝘭", b"create_other")
        ],
        [
            Button.inline("𝘉𝘢𝘤𝘬", b"back_to_main")
        ]
    ]

# Back button for various sections
def get_back_button():
    return [
        [Button.inline("𝘉𝘢𝘤𝘬", b"back_to_main")]
    ]
def get_p2p_created_buttons(invite_url):
    """Get buttons for P2P created message"""
    # Create KeyboardButtonCopy for copy functionality
    copy_button = KeyboardButtonCopy(
        text="📋 Copy Link",
        copy_text=invite_url
    )
    
    return [
        [
            Button.url("🔗 Join Now", invite_url),
            Button.url("📤 Share", f"https://t.me/share/url?url={invite_url}")
        ],
        [copy_button]  # This is the actual copy button
    ]

def get_otc_created_buttons(invite_url):
    """Get buttons for OTC created message"""
    # Create KeyboardButtonCopy for copy functionality
    copy_button = KeyboardButtonCopy(
        text="📋 Copy Link",
        copy_text=invite_url
    )
    
    return [
        [
            Button.url("🔗 Join Now", invite_url),
            Button.url("📤 Share", f"https://t.me/share/url?url={invite_url}")
        ],
        [copy_button]  # This is the actual copy button
    ]

def get_session_buttons(group_key):
    """Get buttons for session initiation"""
    return [
        [
            Button.inline("🧑‍💼 Buyer", f"role_buyer_{group_key}".encode()),
            Button.inline("🧑‍💼 Seller", f"role_seller_{group_key}".encode())
        ]
    ]
