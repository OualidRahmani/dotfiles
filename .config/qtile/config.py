from libqtile import bar, layout, widget, hook
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy
import subprocess
import os
import json
import psutil

@hook.subscribe.startup_once
def autostart():
    subprocess.Popen(["picom", "--config", os.path.expanduser("~/.config/picom.conf")])
    subprocess.Popen(["dunst"]) # Starts the notification daemon


# Helper to create the progress bar string
def get_bar(percent, width=5):
    full = "█"
    empty = "░"
    filled_width = int(percent / 100 * width)
    return f"[{full * filled_width}{empty * (width - filled_width)}]"

# Function to launch the detail popup
def open_details(module_type):
    # This launches our custom Python script (Phase 2) with an argument
    subprocess.Popen([os.path.expanduser("~/.local/bin/sys_popup"), module_type])


mod = "mod4"  # Windows/Super key
terminal = "xfce4-terminal"

# Keybindings
keys = [
    # Lock Screen
    Key([mod, "control"], "l", lazy.spawn(os.path.expanduser("~/.local/bin/lock.sh"))),

    # Window focus
    Key([mod], "Left", lazy.layout.left()),
    Key([mod], "Right", lazy.layout.right()),
    Key([mod], "Down", lazy.layout.down()),
    Key([mod], "Up", lazy.layout.up()),

    # Move windows
    Key([mod, "shift"], "Left", lazy.layout.shuffle_left()),
    Key([mod, "shift"], "Right", lazy.layout.shuffle_right()),
    Key([mod, "shift"], "Down", lazy.layout.shuffle_down()),
    Key([mod, "shift"], "Up", lazy.layout.shuffle_up()),

    # Resize windows
    Key([mod, "control"], "Left", lazy.layout.grow_left()),
    Key([mod, "control"], "Right", lazy.layout.grow_right()),
    Key([mod, "control"], "Down", lazy.layout.grow_down()),
    Key([mod, "control"], "Up", lazy.layout.grow_up()),

    # Volume Controls with Notifications
    Key([], "XF86AudioRaiseVolume", lazy.spawn("bash -c 'pactl set-sink-volume @DEFAULT_SINK@ +5% && notify-send -t 1000 -h string:x-dunst-stack-tag:vol \"Volume\" \"Increased\"'")),
    Key([], "XF86AudioLowerVolume", lazy.spawn("bash -c 'pactl set-sink-volume @DEFAULT_SINK@ -5% && notify-send -t 1000 -h string:x-dunst-stack-tag:vol \"Volume\" \"Decreased\"'")),
    Key([], "XF86AudioMute", lazy.spawn("bash -c 'pactl set-sink-mute @DEFAULT_SINK@ toggle && notify-send -t 1000 -h string:x-dunst-stack-tag:vol \"Volume\" \"Toggled Mute\"'")),

    # Media Controls with Notifications (Pulls song title via playerctl)
    Key([], "XF86AudioPlay", lazy.spawn("bash -c 'playerctl play-pause && sleep 0.1 && notify-send -t 2000 -h string:x-dunst-stack-tag:media \"Play/Pause\" \"$(playerctl metadata title)\"'")),
    Key([], "XF86AudioNext", lazy.spawn("bash -c 'playerctl next && sleep 0.1 && notify-send -t 2000 -h string:x-dunst-stack-tag:media \"Next Track\" \"$(playerctl metadata title)\"'")),
    Key([], "XF86AudioPrev", lazy.spawn("bash -c 'playerctl previous && sleep 0.1 && notify-send -t 2000 -h string:x-dunst-stack-tag:media \"Previous Track\" \"$(playerctl metadata title)\"'")),

    # Layout / window controls 
    Key(["mod1"], "F4", lazy.window.kill()),
    Key([mod, "control"], "r", lazy.reload_config()),
    Key([mod, "control"], "q", lazy.shutdown()),
    Key(["mod1"], "Tab", lazy.layout.next()),
    Key([mod, "shift"], "f", lazy.window.toggle_floating()),
    Key([], "Print", lazy.spawn("flameshot gui")),
        # Workspace navigation (skip empty)
    Key([mod], "Tab", lazy.screen.next_group(skip_empty=True)),
    Key([mod, "shift"], "Tab", lazy.screen.prev_group(skip_empty=True)),
        # Layout control (moved from Super + Tab)
    Key([mod], "space", lazy.next_layout()),

    # Apps
    Key([mod], "Return", lazy.spawn(terminal)),
    Key([mod], "r", lazy.spawncmd()),
    Key([mod], "b", lazy.spawn("brave-browser")),
    Key(["mod1"], "space", lazy.spawn("ulauncher")),
    Key([mod], "f", lazy.spawn("firefox")),
]

# Workspaces
groups = [Group(i) for i in "123456789"]

for i in groups:
    keys.extend([
        Key([mod], i.name, lazy.group[i.name].toscreen()),
        Key([mod, "shift"], i.name, lazy.window.togroup(i.name, switch_group=True)),
    ])

# Dynamic Theme Loading
theme_file = os.path.expanduser("~/.config/qtile_theme.json")
try:
    with open(theme_file, "r") as f:
        colors = json.load(f)
except FileNotFoundError:
    # Fallback if the GUI hasn't been run yet
    colors = {
        "bg": "#1e1e2e", "fg": "#cdd6f4", "surface": "#313244",
        "blue": "#89b4fa", "green": "#a6e3a1", "red": "#f38ba8",
        "yellow": "#f9e2af", "mauve": "#cba6f7",
    }

# Layouts with gaps
layout_theme = {
    "border_width": 3,
    "margin": 8,
    "border_focus": colors["blue"],
    "border_normal": colors["surface"],
}

layouts = [
    layout.Columns(**layout_theme),
    layout.Max(**layout_theme),
    layout.Floating(
        border_width=3,
        border_focus=colors["blue"],
        border_normal=colors["surface"],
        float_rules=[
            *layout.Floating.default_float_rules,
            Match(wm_class="xfce4-terminal"),
        ],
    ),
]

floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="SysPopup"), # This matches the title/class we set in Tkinter
        Match(wm_class="PowerMenu"),
    ]
)

# Bar / widgets
widget_defaults = dict(
    font="JetBrains Mono",
    fontsize=13,
    padding=6,
    foreground=colors["fg"],
    background=colors["bg"],
)
extension_defaults = widget_defaults.copy()

screens = [
    Screen(
        top=bar.Bar(
            [
                widget.GroupBox(
                    active=colors["fg"],
                    inactive=colors["surface"],
                    highlight_method="block",
                    this_current_screen_border=colors["blue"],
                    urgent_border=colors["red"],
                    padding=6,
                ),
                widget.Prompt(),
                widget.WindowName(foreground=colors["mauve"]),
                widget.Spacer(),

                # CPU Widget
                widget.GenPollText(
                    func=lambda: f"CPU {get_bar(psutil.cpu_percent())}",
                    update_interval=1,
                    mouse_callbacks={'Button1': lambda: open_details('cpu')},
                    foreground=colors['mauve'], # Using your dynamic colors
                ), 
                widget.Sep(padding=10, foreground=colors["surface"]),

                # RAM Widget
                widget.GenPollText(
                    func=lambda: f"RAM {get_bar(psutil.virtual_memory().percent)}",
                    update_interval=1,
                    mouse_callbacks={'Button1': lambda: open_details('ram')},
                    foreground=colors['blue'],
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),

                # GPU Widget
                widget.GenPollText(
                    func=lambda: f"GPU {get_bar(int(subprocess.check_output(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits']).decode().strip()))}",
                    update_interval=2,
                    mouse_callbacks={'Button1': lambda: open_details('gpu')},
                    foreground=colors['yellow'], # Using your dynamic yellow
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.Clock(
                    format="%a %d %b  %H:%M",
                    foreground=colors["blue"],
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.Systray(),
                widget.QuickExit(
                    default_text=" Quit Qtile ",
                    foreground=colors["red"],
                ),
                widget.Battery(
                    battery="BAT0",
                    format="BAT {percent:2.0%}",
                    foreground=colors["green"],
                    update_interval=10,
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),

                # Net Widget
                widget.GenPollText(
                    func=lambda: "↑ ↓",
                    update_interval=1,
                    mouse_callbacks={'Button1': lambda: open_details('net')},
                    foreground=colors['green'],
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),

                widget.TextBox(
                    text="⏻", # Or use "PWR" if your font doesn't have the icon
                    font="JetBrains Mono",
                    fontsize=18,
                    foreground=colors['red'],
                    padding=10,
                    mouse_callbacks={'Button1': lambda: subprocess.Popen([os.path.expanduser("~/.local/bin/power_menu")])}
                ),
            ],
            28,
            background=colors["bg"],
            margin=[4, 8, 0, 8],
        ),
    ),
]

# Mouse bindings
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

# Misc
dgroups_key_binder = None
dgroups_app_rules: list = []
follow_mouse_focus = False
bring_front_click = True
floats_kept_above = True
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True
auto_minimize = True
wl_input_rules = None
wmname = "LG3D"
