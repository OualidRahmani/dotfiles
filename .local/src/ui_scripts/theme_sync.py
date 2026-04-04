#!/usr/bin/env python3
import json
import os
import math
import sys
import subprocess
import time

FACTOR = 0.6

def brighten(hex_str, factor=FACTOR):
    hex_str = hex_str.lstrip("#")
    r, g, b = tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def get_closest_papirus_color(target_hex):
    papirus_colors = {
        "red": (244, 67, 54),
        "pink": (233, 30, 99),
        "violet": (156, 39, 176),
        "indigo": (63, 81, 181),
        "blue": (33, 150, 243),
        "cyan": (0, 188, 212),
        "teal": (0, 150, 136),
        "green": (76, 175, 80),
        "orange": (255, 152, 0),
        "brown": (121, 85, 72),
        "grey": (158, 158, 158),
        "bluegrey": (96, 125, 139),
    }
    target_rgb = hex_to_rgb(target_hex)
    closest_name = "blue"
    min_dist = float("inf")

    for name, rgb in papirus_colors.items():
        dist = math.dist(target_rgb, rgb)
        if dist < min_dist:
            min_dist = dist
            closest_name = name
    return closest_name


# --- 1. Setup Caching & Arguments ---
if len(sys.argv) < 2:
    print("Error: Please provide a wallpaper path.")
    sys.exit(1)

wall_path = os.path.abspath(sys.argv[1])
wall_name = os.path.basename(wall_path)

cache_dir = os.path.expanduser("~/.cache/theme_sync")
os.makedirs(cache_dir, exist_ok=True)
wall_cache_file = os.path.join(cache_dir, f"{wall_name}.json")
pywal_cache_file = os.path.join(cache_dir, f"{wall_name}_pywal.json")
state_file = os.path.join(cache_dir, "state.json")

# --- 2. Set the Wallpaper Globally ---
subprocess.run(["/usr/bin/feh", "--bg-fill", wall_path])

# --- 3. Check Current State ---
current_state = {"wallpaper": None, "folder_color": None}
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        current_state = json.load(f)

if current_state["wallpaper"] == wall_name:
    print(f"'{wall_name}' is already active. Nothing to do.")
    sys.exit(0)

# --- 4. Load from Cache OR Generate ---
if os.path.exists(wall_cache_file) and os.path.exists(pywal_cache_file):
    with open(wall_cache_file, "r") as f:
        cache_data = json.load(f)
        qtile_theme = cache_data["qtile_theme"]
        closest_color = cache_data["closest_color"]
    os.system(f"~/.local/bin/wal --theme '{pywal_cache_file}' -q")
else:
    os.system(
        f"~/.local/bin/wal -i '{wall_path}' -q --backend colorthief --saturate 0.6"
    )
    try:
        with open(os.path.expanduser("~/.cache/wal/colors.json"), "r") as f:
            wal_raw_data = f.read()
            wal = json.loads(wal_raw_data)["colors"]
    except FileNotFoundError:
        print("Pywal failed.")
        sys.exit(1)

    with open(pywal_cache_file, "w") as f:
        f.write(wal_raw_data)

    qtile_theme = {
        "bg": wal["color0"],
        "surface": wal["color8"],
        "fg": wal["color15"],
        "red": brighten(wal["color9"]),
        "green": brighten(wal["color10"]),
        "yellow": brighten(wal["color11"]),
        "blue": brighten(wal["color12"]),
        "mauve": brighten(wal["color13"]),
    }
    closest_color = get_closest_papirus_color(qtile_theme["blue"])

    with open(wall_cache_file, "w") as f:
        json.dump(
            {"qtile_theme": qtile_theme, "closest_color": closest_color}, f, indent=4
        )

# --- 5. Write Config Files ---
with open(os.path.expanduser("~/.config/qtile_theme.json"), "w") as f:
    json.dump(qtile_theme, f, indent=4)

dunst_config = f"""[global]
font = Sans 10
corner_radius = 15
origin = top-right
offset = 15x15
width = 300
height = 100
frame_width = 2
separator_color = frame
padding = 10
horizontal_padding = 12
separator_height = 2
format = "<b>%s</b>\\n%b"
icon_theme = Papirus-Dark, hicolor
enable_recursive_icon_lookup = true

[urgency_low]
background = "{qtile_theme['bg']}"
foreground = "{qtile_theme['fg']}"
frame_color = "{qtile_theme['surface']}"
highlight = "{qtile_theme['blue']}"
timeout = 3

[urgency_normal]
background = "{qtile_theme['bg']}"
foreground = "{qtile_theme['fg']}"
frame_color = "{qtile_theme['surface']}"
highlight = "{qtile_theme['mauve']}"
timeout = 5

[urgency_critical]
background = "{qtile_theme['bg']}"
foreground = "{qtile_theme['fg']}"
frame_color = "{qtile_theme['red']}"
highlight = "{qtile_theme['red']}"
timeout = 0
"""
dunst_dir = os.path.expanduser("~/.config/dunst")
os.makedirs(dunst_dir, exist_ok=True)
with open(os.path.join(dunst_dir, "dunstrc"), "w") as f:
    f.write(dunst_config)

gtk_css = f"""
@define-color accent_color {qtile_theme['blue']};
@define-color sidebar_bg_color {qtile_theme['bg']};
@define-color sidebar_fg_color {qtile_theme['fg']};
@define-color sidebar_backdrop_color {qtile_theme['bg']};
@define-color accent_bg_color {qtile_theme['blue']};
@define-color window_bg_color {qtile_theme['bg']};
@define-color window_fg_color {qtile_theme['fg']};
@define-color view_bg_color {qtile_theme['bg']};
@define-color view_fg_color {qtile_theme['fg']};
@define-color headerbar_bg_color {qtile_theme['surface']};
@define-color headerbar_fg_color {qtile_theme['fg']};
@define-color popover_bg_color {qtile_theme['surface']};
@define-color popover_fg_color {qtile_theme['fg']};
@define-color card_bg_color {qtile_theme['surface']};
@define-color card_fg_color {qtile_theme['fg']};
@define-color dialog_bg_color {qtile_theme['bg']};
@define-color dialog_fg_color {qtile_theme['fg']};
"""
for gtk_dir in ["gtk-4.0", "gtk-3.0"]:
    css_path = os.path.expanduser(f"~/.config/{gtk_dir}")
    os.makedirs(css_path, exist_ok=True)
    with open(os.path.join(css_path, "gtk.css"), "w") as f:
        f.write(gtk_css)

spicetify_ini = f"""[Dynamic]
text               = {qtile_theme['fg'].lstrip('#')}
subtext            = {qtile_theme['blue'].lstrip('#')}
main               = {qtile_theme['bg'].lstrip('#')}
sidebar            = {qtile_theme['bg'].lstrip('#')}
player             = {qtile_theme['surface'].lstrip('#')}
card               = {qtile_theme['surface'].lstrip('#')}
shadow             = {qtile_theme['bg'].lstrip('#')}
selected-row       = {qtile_theme['surface'].lstrip('#')}
button             = {qtile_theme['blue'].lstrip('#')}
button-active      = {qtile_theme['mauve'].lstrip('#')}
button-disabled    = {qtile_theme['surface'].lstrip('#')}
tab-active         = {qtile_theme['blue'].lstrip('#')}
notification       = {qtile_theme['blue'].lstrip('#')}
notification-error = {qtile_theme['red'].lstrip('#')}
misc               = {qtile_theme['surface'].lstrip('#')}
"""
spicetify_dir = os.path.expanduser("~/.config/spicetify/Themes/Dynamic")
os.makedirs(spicetify_dir, exist_ok=True)
with open(os.path.join(spicetify_dir, "color.ini"), "w") as f:
    f.write(spicetify_ini)

# --- 6. The Smart Folder Update ---
if current_state["folder_color"] != closest_color:
    papirus_bin = "/usr/bin/papirus-folders"
    folder_cmd = f"sudo {papirus_bin} -C {closest_color} --theme Papirus-Dark && sudo gtk-update-icon-cache -f /usr/share/icons/Papirus-Dark && killall nautilus"
    subprocess.Popen(
        folder_cmd, 
        shell=True, 
        stdin=subprocess.DEVNULL, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )

# --- 7. Restart Services & Notify ---
with open(state_file, "w") as f:
    json.dump({"wallpaper": wall_name, "folder_color": closest_color}, f)

subprocess.run(["killall", "dunst"], capture_output=True)
subprocess.Popen(
    ["dunst", "-conf", os.path.expanduser("~/.config/dunst/dunstrc")],
    start_new_session=True,
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

subprocess.Popen(
    ["qtile", "cmd-obj", "-o", "cmd", "-f", "reload_config"],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# Give Dunst half a second to boot up before sending the notification
time.sleep(0.5)
subprocess.run(["notify-send", "Theme Updated", f"Matched colors to {wall_name}"])

# --- 8. Reload Spotify UI ---
SPICETIFY = os.path.expanduser("~/.spicetify/spicetify")
if (
    subprocess.run(
        ["pgrep", "-f", "/usr/share/spotify/spotify"], capture_output=True
    ).returncode
    == 0
):
    subprocess.run(["killall", "spotify"], capture_output=True)
    time.sleep(1)
    subprocess.Popen(
        f"{SPICETIFY} apply && sleep 2 && /usr/bin/spotify",
        shell=True,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
else:
    subprocess.Popen(
        f"{SPICETIFY} apply",
        shell=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )