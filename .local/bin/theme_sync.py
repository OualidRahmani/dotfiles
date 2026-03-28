#!/usr/bin/env python3
import json
import os

def brighten(hex_str, factor=0.3):
    """
    Takes a hex color and blends it with white to ensure high contrast.
    factor=0.3 means it moves the color 30% closer to pure white.
    """
    hex_str = hex_str.lstrip('#')
    # Convert hex to RGB
    r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    
    # Mix with white (255, 255, 255)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    
    # Convert back to hex
    return f"#{r:02x}{g:02x}{b:02x}"

# 1. Read the colors Pywal just generated
wal_file = os.path.expanduser("~/.cache/wal/colors.json")
try:
    with open(wal_file, "r") as f:
        wal = json.load(f)["colors"]
except FileNotFoundError:
    print("Pywal colors not found. Please run 'wal -i image.jpg' first.")
    exit(1)

# 2. Map the colors and apply the 'brighten' filter to text elements
qtile_theme = {
    "bg": wal["color0"],       
    "surface": wal["color8"],  
    "fg": wal["color15"],      
    "red": brighten(wal["color9"]),
    "green": brighten(wal["color10"]),
    "yellow": brighten(wal["color11"]),
    "blue": brighten(wal["color12"]),    
    "mauve": brighten(wal["color13"])    
}

# 3. Overwrite your Qtile theme file
out_file = os.path.expanduser("~/.config/qtile_theme.json")
with open(out_file, "w") as f:
    json.dump(qtile_theme, f, indent=4)