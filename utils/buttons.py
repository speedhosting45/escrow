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
            Button.inline("🤝 P2P Deal", b"create_p2p"),
            Button.inline("📦 Other Deal", b"create_other")
        ],
        [
            Button.inline("🔙 Back", b"back_to_main")
        ]
    ]

# Back button for various sections
def get_back_button():
    return [
        [Button.inline("🔙 Back", b"back_to_main")]
    ]
