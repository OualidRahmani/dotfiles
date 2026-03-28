from libqtile import bar, layout, widget, hook, qtile
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy
import psutil
import time
import subprocess
import os
import json
import re

# ─── Autostart ───────────────────────────────────────────────────────────────


@hook.subscribe.startup_once
def autostart():
    script = os.path.expanduser("~/.config/qtile/autostart.sh")
    if os.path.exists(script):
        subprocess.Popen([script])


# ─── Sysmon Helpers ───────────────────────────────────────────────────────────

SYSMON = os.path.expanduser("~/.local/bin/sysmon")


def get_gpu_usage():
    try:
        return subprocess.check_output([SYSMON, "gpu"], timeout=2).decode().strip()
    except Exception:
        return "GPU [Error]"


def get_battery():
    try:
        return subprocess.check_output([SYSMON, "bat"], timeout=2).decode().strip()
    except Exception:
        return "BAT --%"


def get_cpu_usage():
    try:
        return subprocess.check_output([SYSMON, "cpu"], timeout=2).decode().strip()
    except Exception:
        return "CPU [Error]"


def get_ram_usage():
    try:
        return subprocess.check_output([SYSMON, "ram"], timeout=2).decode().strip()
    except Exception:
        return "RAM [Error]"


last_net_recv = psutil.net_io_counters().bytes_recv
last_net_sent = psutil.net_io_counters().bytes_sent
last_net_time = time.time()

def get_net():
    global last_net_recv, last_net_sent, last_net_time
    
    current_time = time.time()
    current_net = psutil.net_io_counters()
    interval = current_time - last_net_time
    
    if interval <= 0:
        return "↓ 0K ↑ 0K"
        
    down = (current_net.bytes_recv - last_net_recv) / interval / 1024
    up = (current_net.bytes_sent - last_net_sent) / interval / 1024
    
    last_net_recv = current_net.bytes_recv
    last_net_sent = current_net.bytes_sent
    last_net_time = current_time
    
    return f"↓ {down:.1f}K ↑ {up:.1f}K"


def get_vol():
    try:
        out = subprocess.check_output(
            ["pactl", "get-sink-volume", "@DEFAULT_SINK@"], timeout=2
        ).decode()
        match = re.search(r"(\d+)%", out)
        return f"VOL {match.group(1)}%" if match else "VOL --%"
    except Exception:
        return "VOL --%"


def open_details(module_type):
    subprocess.Popen([os.path.expanduser("~/.local/bin/sys_popup"), module_type])


# ─── Core Config ─────────────────────────────────────────────────────────────

mod = "mod4"
terminal = "xfce4-terminal --hide-menubar --hide-scrollbar" 

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
    # Volume
    Key(
        [],
        "XF86AudioRaiseVolume",
        lazy.spawn(
            "bash -c 'pactl set-sink-volume @DEFAULT_SINK@ +5% && "
            'notify-send -t 1000 -h string:x-dunst-stack-tag:vol "Volume" "Increased"\''
        ),
    ),
    Key(
        [],
        "XF86AudioLowerVolume",
        lazy.spawn(
            "bash -c 'pactl set-sink-volume @DEFAULT_SINK@ -5% && "
            'notify-send -t 1000 -h string:x-dunst-stack-tag:vol "Volume" "Decreased"\''
        ),
    ),
    Key(
        [],
        "XF86AudioMute",
        lazy.spawn(
            "bash -c 'pactl set-sink-mute @DEFAULT_SINK@ toggle && "
            'notify-send -t 1000 -h string:x-dunst-stack-tag:vol "Volume" "Toggled Mute"\''
        ),
    ),
    # Media
    Key(
        [],
        "XF86AudioPlay",
        lazy.spawn(
            "bash -c 'playerctl play-pause && sleep 0.1 && "
            'notify-send -t 2000 -h string:x-dunst-stack-tag:media "Play/Pause" "$(playerctl metadata title)"\''
        ),
    ),
    Key(
        [],
        "XF86AudioNext",
        lazy.spawn(
            "bash -c 'playerctl next && sleep 0.1 && "
            'notify-send -t 2000 -h string:x-dunst-stack-tag:media "Next Track" "$(playerctl metadata title)"\''
        ),
    ),
    Key(
        [],
        "XF86AudioPrev",
        lazy.spawn(
            "bash -c 'playerctl previous && sleep 0.1 && "
            'notify-send -t 2000 -h string:x-dunst-stack-tag:media "Previous Track" "$(playerctl metadata title)"\''
        ),
    ),
    # Window / Session
    Key(["mod1"], "F4", lazy.window.kill()),
    Key([mod, "control"], "r", lazy.reload_config()),
    Key([mod, "control"], "q", lazy.shutdown()),
    Key(["mod1"], "Tab", lazy.layout.next()),
    Key([mod, "shift"], "f", lazy.window.toggle_floating()),
    Key([], "Print", lazy.spawn("flameshot gui")),
    Key([mod], "Tab", lazy.screen.next_group()),
    Key([mod, "shift"], "Tab", lazy.screen.prev_group()),
    Key([mod], "space", lazy.next_layout()),
    # Dynamic Wallpaper Picker
    Key([mod], "w", lazy.spawn(os.path.expanduser("~/.local/bin/wall_picker"))),
    # Apps
    Key([mod], "Return", lazy.spawn(terminal)),
    Key([mod], "r", lazy.spawncmd()),
    Key([mod], "b", lazy.spawn("brave-browser")),
    Key(["mod1"], "space", lazy.spawn("bash -c 'rofi -show drun -theme ~/.cache/wal/colors-rofi-dark.rasi'")),
    Key([mod], "f", lazy.spawn("env MOZ_X11_EGL=1 firefox")),
]

# ─── Dynamic Workspace Management ────────────────────────────────────────────

group_names = list("123456789")


def add_group(qtile):
    try:
        group_name = (
            subprocess.check_output(
                'rofi -dmenu -p "New Workspace Name:" -theme ~/.cache/wal/colors-rofi-dark.rasi -theme-str "window {width: 20%;}"',
                shell=True,
            )
            .decode("utf-8")
            .strip()
        )

        if not group_name:
            return

        if group_name in qtile.groups_map:
            subprocess.Popen(
                ["notify-send", "Workspace Exists", f'"{group_name}" already exists.']
            )
            return

        qtile.add_group(group_name)
        qtile.groups_map[group_name].toscreen()
    except subprocess.CalledProcessError:
        pass


def delete_group(qtile):
    group = qtile.current_group
    if group.name in group_names:
        subprocess.Popen(
            [
                "notify-send",
                "Cannot Delete",
                "Default workspaces 1-9 cannot be deleted.",
            ]
        )
        return
    if len(group.windows) > 0:
        subprocess.Popen(
            ["notify-send", "Workspace Busy", "Close all windows before deleting."]
        )
        return
    qtile.groups_map["1"].toscreen()
    qtile.del_group(group.name)


groups = [Group(i) for i in group_names]


@hook.subscribe.startup_complete
def restore_groups():
    for window in qtile.windows_map.values():
        if (
            hasattr(window, "group")
            and window.group
            and window.group.name not in group_names
            and window.group.name not in qtile.groups_map
        ):
            qtile.add_group(window.group.name)


keys.extend(
    [
        Key(
            [mod, "control"], "n", lazy.function(add_group), desc="Create new workspace"
        ),
        Key(
            [mod, "control"],
            "x",
            lazy.function(delete_group),
            desc="Delete current workspace",
        ),
        *[Key([mod], i.name, lazy.group[i.name].toscreen()) for i in groups],
        *[
            Key([mod, "shift"], i.name, lazy.window.togroup(i.name, switch_group=True))
            for i in groups
        ],
    ]
)

# ─── Theme & Layouts ──────────────────────────────────────────────────────────

theme_file = os.path.expanduser("~/.config/qtile_theme.json")
try:
    with open(theme_file, "r") as f:
        colors = json.load(f)
except FileNotFoundError:
    colors = {
        "bg": "#1e1e2e",
        "fg": "#cdd6f4",
        "surface": "#313244",
        "blue": "#89b4fa",
        "mauve": "#cba6f7",
        "red": "#f38ba8",
        "green": "#a6e3a1",
        "yellow": "#f9e2af",
    }

layout_theme = {
    "border_width": 0,
    "margin": 8,
    "border_focus": colors["blue"],
    "border_normal": colors["surface"],
}
layouts = [layout.Columns(**layout_theme), layout.Max(**layout_theme)]

floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="SysPopup"),
        Match(wm_class="PowerMenu"),
        Match(wm_class="WSHud"),
        Match(wm_class="AudioMenu"),
    ]
)

# ─── Widgets & Screens ────────────────────────────────────────────────────────

widget_defaults = {
    "font": "JetBrains Mono",
    "fontsize": 13,
    "padding": 6,
    "foreground": colors["fg"],
    "background": colors["bg"],
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
                    hide_unused=False,
                ),
                widget.Prompt(),
                widget.WindowName(foreground=colors["mauve"]),
                widget.Spacer(),
                widget.GenPollText(
                    func=get_cpu_usage,
                    update_interval=1,
                    mouse_callbacks={"Button1": lambda: open_details("cpu")},
                    foreground=colors["mauve"],
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.GenPollText(
                    func=get_ram_usage,
                    update_interval=1,
                    mouse_callbacks={"Button1": lambda: open_details("ram")},
                    foreground=colors["blue"],
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.GenPollText(
                    func=get_gpu_usage,
                    update_interval=2,
                    mouse_callbacks={"Button1": lambda: open_details("gpu")},
                    foreground=colors["yellow"],
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.GenPollText(
                    func=get_net,
                    update_interval=1,
                    mouse_callbacks={"Button1": lambda: open_details("net")},
                    foreground=colors["green"],
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.GenPollText(
                    func=get_vol,
                    update_interval=1,
                    foreground=colors["blue"],
                    mouse_callbacks={
                        "Button1": lambda: subprocess.Popen(
                            ["python3", os.path.expanduser("~/.local/bin/audio_menu")]
                        )
                    },
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.Clock(format="%a %d %b  %H:%M", foreground=colors["blue"]),
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.GenPollText(
                    func=get_battery, update_interval=10, foreground=colors["green"]
                ),
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.Systray(),
                widget.Sep(padding=10, foreground=colors["surface"]),
                widget.TextBox(
                    text="⏻",
                    font="JetBrains Mono",
                    fontsize=18,
                    foreground=colors["red"],
                    padding=10,
                    mouse_callbacks={
                        "Button1": lambda: subprocess.Popen(
                            [os.path.expanduser("~/.local/bin/power_menu")]
                        )
                    },
                ),
            ],
            28,
            background=colors["bg"],
            margin=[4, 8, 4, 8],
        ),
    ),
]

mouse = [
    Drag(
        [mod],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position(),
    ),
    Drag(
        [mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()
    ),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]
dgroups_key_binder = None
dgroups_app_rules = []
follow_mouse_focus = True
bring_front_click = True
floats_kept_above = True
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "focus"
reconfigure_screens = True
auto_minimize = True
wmname = "LG3D"


@hook.subscribe.setgroup
def group_changed():
    group_name = qtile.current_group.name
    subprocess.Popen([os.path.expanduser("~/.local/bin/ws_hud"), group_name])
