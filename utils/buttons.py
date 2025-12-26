from telethon import Button

# ======================================================
# MAIN MENU BUTTONS
# ======================================================

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


# ======================================================
# CREATE ESCROW TYPE BUTTONS
# ======================================================

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


# ======================================================
# BACK BUTTON (COMMON)
# ======================================================

def get_back_button():
    return [
        [Button.inline("𝘉𝘢𝘤𝘬", b"back_to_main")]
    ]


# ======================================================
# ESCROW CREATED BUTTONS (P2P / OTC)
# ======================================================

def get_p2p_created_buttons(invite_url):
    """
    Buttons shown after P2P escrow group creation
    """
    return [
        [
            Button.url("🔗 Join Now", invite_url),
            Button.url("📤 Share", f"https://t.me/share/url?url={invite_url}")
        ],
        [
            Button.inline("📋 Copy Link", b"copy_invite_link")
        ]
    ]


def get_otc_created_buttons(invite_url):
    """
    Buttons shown after OTC escrow group creation
    """
    return [
        [
            Button.url("🔗 Join Now", invite_url),
            Button.url("📤 Share", f"https://t.me/share/url?url={invite_url}")
        ],
        [
            Button.inline("📋 Copy Link", b"copy_invite_link")
        ]
    ]


# ======================================================
# ROLE SELECTION BUTTONS
# ======================================================

def get_session_buttons(group_key):
    """
    Buyer / Seller role selection buttons
    """
    return [
        [
            Button.inline("🧑‍💼 Buyer", f"role_buyer_{group_key}".encode()),
            Button.inline("🧑‍💼 Seller", f"role_seller_{group_key}".encode())
        ]
    ]
