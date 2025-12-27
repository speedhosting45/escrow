#!/usr/bin/env python3
"""
Logo Generator for Escrow Groups
"""
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

class LogoGenerator:
    def __init__(self, template_path="assets/logo_template.png", font_path="assets/Skynight.otf"):
        self.config = {
            "BUYER": {
                "start_x": 250,
                "start_y": 312,
                "max_width": 260
            },
            "SELLER": {
                "start_x": 250,
                "start_y": 356,
                "max_width": 260
            }
        }
        self.font_size = 40
        self.font_path = font_path
        self.image_path = template_path
        self.baseline_fix = -12
        self.text_color = (0, 0, 0)  # BLACK
        self.font = None
        self.template = None
        
        # Ensure assets directory exists
        os.makedirs("assets", exist_ok=True)
        
    def load_resources(self):
        """Load font and template image"""
        try:
            # Check if files exist
            if not os.path.exists(self.font_path):
                return False, f"❌ Font file not found: {self.font_path}"
            
            if not os.path.exists(self.image_path):
                return False, f"❌ Template image not found: {self.image_path}"
            
            self.font = ImageFont.truetype(self.font_path, self.font_size)
            self.template = Image.open(self.image_path)
            return True, "✅ Resources loaded"
        except Exception as e:
            return False, f"❌ Failed to load resources: {e}"
    
    def generate_logo(self, buyer_text, seller_text):
        """
        Generate logo with given usernames
        
        Args:
            buyer_text: Buyer username (e.g., "@username")
            seller_text: Seller username (e.g., "@username")
            
        Returns:
            tuple: (success: bool, image_bytes: BytesIO or None, message: str)
        """
        if not self.font or not self.template:
            success, msg = self.load_resources()
            if not success:
                return False, None, msg
        
        try:
            # Create fresh copy of template
            img = self.template.copy()
            draw = ImageDraw.Draw(img)
            
            # Get coordinates from config
            buyer_x = self.config["BUYER"]["start_x"]
            buyer_y = self.config["BUYER"]["start_y"]
            seller_x = self.config["SELLER"]["start_x"]
            seller_y = self.config["SELLER"]["start_y"]
            
            # Draw text with baseline fix
            draw.text(
                (buyer_x, buyer_y + self.baseline_fix),
                buyer_text,
                font=self.font,
                fill=self.text_color
            )
            
            draw.text(
                (seller_x, seller_y + self.baseline_fix),
                seller_text,
                font=self.font,
                fill=self.text_color
            )
            
            # Convert to bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return True, img_bytes, "✅ Logo generated successfully"
            
        except Exception as e:
            return False, None, f"❌ Error generating logo: {e}"
    
    def generate_and_save(self, buyer_text, seller_text, output_path="generated_logo.png"):
        """Generate logo and save to file"""
        success, image_bytes, message = self.generate_logo(buyer_text, seller_text)
        
        if success:
            with open(output_path, "wb") as f:
                f.write(image_bytes.getvalue())
            return True, f"✅ Logo saved as {output_path}"
        else:
            return False, message
    
    def get_config_info(self):
        """Get formatted configuration info"""
        info = "📋 **Current Configuration:**\n"
        info += f"```json\n{json.dumps(self.config, indent=2)}\n```\n"
        info += f"**Font:** {self.font_path} ({self.font_size}px)\n"
        info += f"**Text Color:** BLACK (0,0,0)\n"
        info += f"**Baseline Fix:** {self.baseline_fix}px\n"
        return info
    
    def update_config(self, new_config):
        """Update configuration"""
        try:
            # Validate config structure
            if "BUYER" not in new_config or "SELLER" not in new_config:
                return False, "❌ Invalid config format"
            
            # Update config
            self.config = new_config
            return True, "✅ Configuration updated"
        except Exception as e:
            return False, f"❌ Error updating config: {e}"
