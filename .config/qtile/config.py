from libqtile import bar, layout, widget, hook, qtile, extension
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy
import subprocess
import os
import json
import psutil

@hook.subscribe.startup_once
def autostart():
    subprocess.Popen(["picom", "--config", os.path.expanduser("~/.config/picom.conf")])
    subprocess.run(["pkill", "-f", "xfwm4"])
    subprocess.run(["pkill", "-f", "xfce4-keyboard-shortcuts"])
    subprocess.Popen(["dunst"]) 
    subprocess.Popen(["/usr/libexec/xdg-desktop-portal"])
    subprocess.Popen(["/usr/libexec/xdg-desktop-portal-gtk"])

def get_bar(percent, width=5):
    full = "█"
    empty = "░"
    filled_width = int(percent / 100 * width)
    return f"[{full * filled_width}{empty * (width - filled_width)}]"

SYSMON = os.path.expanduser("~/.local/bin/sysmon")

def get_gpu_usage():
    try:
        return subprocess.check_output([SYSMON, "gpu"]).decode().strip()
    except Exception:
        return "GPU [Error]"

def get_battery():
    try:
        return subprocess.check_output([SYSMON, "bat"]).decode().strip()
    except Exception:
        return "BAT --%"

def get_cpu_usage():
    try:
        return subprocess.check_output([SYSMON, "cpu"]).decode().strip()
    except Exception:
        return "CPU [Error]"

def get_ram_usage():
    try:
        return subprocess.check_output([SYSMON, "ram"]).decode().strip()
    except Exception:
        return "RAM [Error]"

def get_vol():
    try:
        out = subprocess.check_output(["pactl", "get-sink-volume", "@DEFAULT_SINK@"]).decode()
        return "VOL " + out.split('%')[0].split('/')[-1].strip() + "%"
    except Exception:
        return "VOL --%"

def open_details(module_type):
    subprocess.Popen([os.path.expanduser("~/.local/bin/sys_popup"), module_type])

mod = "mod4"  
terminal = "xfce4-terminal"

keys = [
    Key([mod, "control"], "l", lazy.spawn(os.path.expanduser("~/.local/bin/lock.sh"))),

    Key([mod], "Left", lazy.layout.left()),
    Key([mod], "Right", lazy.layout.right()),
    Key([mod], "Down", lazy.layout.down()),
    Key([mod], "Up", lazy.layout.up()),

    Key([mod, "shift"], "Left", lazy.layout.shuffle_left()),
    Key([mod, "shift"], "Right", lazy.layout.shuffle_right()),
    Key([mod, "shift"], "Down", lazy.layout.shuffle_down()),
    Key([mod, "shift"], "Up", lazy.layout.shuffle_up()),

    Key([mod, "control"], "Left", lazy.layout.grow_left()),
    Key([mod, "control"], "Right", lazy.layout.grow_right()),
    Key([mod, "control"], "Down", lazy.layout.grow_down()),
    Key([mod, "control"], "Up", lazy.layout.grow_up()),

    Key([], "XF86AudioRaiseVolume", lazy.spawn("bash -c 'pactl set-sink-volume @DEFAULT_SINK@ +5% && notify-send -t 1000 -h string:x-dunst-stack-tag:vol \"Volume\" \"Increased\"'")),
    Key([], "XF86AudioLowerVolume", lazy.spawn("bash -c 'pactl set-sink-volume @DEFAULT_SINK@ -5% && notify-send -t 1000 -h string:x-dunst-stack-tag:vol \"Volume\" \"Decreased\"'")),
    Key([], "XF86AudioMute", lazy.spawn("bash -c 'pactl set-sink-mute @DEFAULT_SINK@ toggle && notify-send -t 1000 -h string:x-dunst-stack-tag:vol \"Volume\" \"Toggled Mute\"'")),

    Key([], "XF86AudioPlay", lazy.spawn("bash -c 'playerctl play-pause && sleep 0.1 && notify-send -t 2000 -h string:x-dunst-stack-tag:media \"Play/Pause\" \"$(playerctl metadata title)\"'")),
    Key([], "XF86AudioNext", lazy.spawn("bash -c 'playerctl next && sleep 0.1 && notify-send -t 2000 -h string:x-dunst-stack-tag:media \"Next Track\" \"$(playerctl metadata title)\"'")),
    Key([], "XF86AudioPrev", lazy.spawn("bash -c 'playerctl previous && sleep 0.1 && notify-send -t 2000 -h string:x-dunst-stack-tag:media \"Previous Track\" \"$(playerctl metadata title)\"'")),

    Key(["mod1"], "F4", lazy.window.kill()),
    Key([mod, "control"], "r", lazy.reload_config()),
    Key([mod, "control"], "q", lazy.shutdown()),
    Key(["mod1"], "Tab", lazy.layout.next()),
    Key([mod, "shift"], "f", lazy.window.toggle_floating()),
    Key([], "Print", lazy.spawn("flameshot gui")),
    Key([mod], "Tab", lazy.screen.next_group(skip_empty=True)),
    Key([mod, "shift"], "Tab", lazy.screen.prev_group(skip_empty=True)),
    Key([mod], "space", lazy.next_layout()),

    Key([mod], "Return", lazy.spawn(terminal)),
    Key([mod], "r", lazy.spawncmd()),
    Key([mod], "b", lazy.spawn("brave-browser")),
    Key(["mod1"], "space", lazy.spawn("bash -c 'rofi -show drun'")),
    Key([mod], "f", lazy.spawn("firefox")),
]

def add_group(qtile):
    def cb(text):
        if text:
            qtile.add_group(text)
            qtile.groups_map[text].toscreen()
    
    qtile.cmd_spawn_extension(extension.CommandSet(
        commands={
            "Create Workspace": "echo",
        },
        pre_commands=["Enter Workspace Name: "],
        callback=cb
    ))

def delete_group(qtile):
    group = qtile.current_group
    if group.name not in "123456789": 
        qtile.del_group(group.name)

keys.extend([
    Key([mod, "control"], "n", lazy.function(add_group), desc="Create new workspace"),
    Key([mod, "control"], "x", lazy.function(delete_group), desc="Delete current workspace"),
])

groups = [Group(i) for i in "123456789"]

for i in groups:
    keys.extend([
        Key([mod], i.name, 
            lazy.group[i.name].toscreen(),
            desc=f"Switch to group {i.name}"),
            
        Key([mod, "shift"], i.name, 
            lazy.window.togroup(i.name, switch_group=True),
            desc="Move focused window to group " + i.name),
    ])

theme_file = os.path.expanduser("~/.config/qtile_theme.json")
try:
    with open(theme_file, "r") as f:
        colors = json.load(f)
except FileNotFoundError:
    colors = {
        "bg": "#1e1e2e", "fg": "#cdd6f4", "surface": "#313244",
        "blue": "#89b4fa", "green": "#a6e3a1", "red": "#f38ba8",
        "yellow": "#f9e2af", "mauve": "#cba6f7",
    }

layout_theme = {
    "border_width": 3,
    "margin": 8,
    "border_focus": colors["blue"],
    "border_normal": colors["surface"],
}

layouts = [
    layout.Columns(**layout_theme),
    layout.Max(**layout_theme),
]

floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="SysPopup"),
        Match(wm_class="PowerMenu"),
        Match(wm_class="WSHud"),
        Match(wm_class="AudioMenu"),
    ]
)

widget_defaults = {
    'font': "JetBrains Mono",
    'fontsize': 13,
    'padding': 6,
    'foreground': colors["fg"],
    'background': colors["bg"],
}

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
                    visible_groups=None, 
                    hide_unused=False,    
                ),
                widget.Prompt(),
                widget.WindowName(foreground=colors["mauve"]),
                widget.Spacer(),

                widget.GenPollText(
                    func=get_cpu_usage,
                    update_interval=1,
                    mouse_callbacks={'Button1': lambda: open_details('cpu')},
                    foreground=colors['mauve'], 
                ), 
                widget.Sep(padding=10, foreground=colors["surface"]),

                widget.GenPollText(
                    func=get_ram_usage,
                    update_interval=1,
                    mouse_callbacks={'Button1': lambda: open_details('ram')},
                    foreground=colors['blue'],
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),

                widget.GenPollText(
                    func=get_gpu_usage,
                    update_interval=2,
                    mouse_callbacks={'Button1': lambda: open_details('gpu')},
                    foreground=colors['yellow'],
                ),

                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.GenPollText(
                    func=get_vol,
                    update_interval=1,
                    foreground=colors['blue'],
                    mouse_callbacks={'Button1': lambda: subprocess.Popen(["bash", "-c", f"sleep 0.15 && python3 {os.path.expanduser('~/.local/bin/audio_menu')}"])}
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
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.GenPollText(
                    func=get_battery,
                    update_interval=10,
                    foreground=colors["green"],
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),

                widget.GenPollText(
                    func=lambda: "↑ ↓",
                    update_interval=1,
                    mouse_callbacks={'Button1': lambda: open_details('net')},
                    foreground=colors['green'],
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),

                widget.TextBox(
                    text="⏻", 
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

mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

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

@hook.subscribe.setgroup
def group_changed():
    group_name = qtile.current_group.name
    subprocess.Popen([os.path.expanduser("~/.local/bin/ws_hud"), group_name])