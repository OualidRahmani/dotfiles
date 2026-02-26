# Dotfiles

A highly customized, ground-up Linux desktop environment built on **Qtile**. This setup moves away from bloated stock widgets, relying instead on custom, lightweight Python/Tkinter modules for system monitoring, theming, and aesthetics.

### Architecture
- **Window Manager:** Qtile
- **Language:** Python 3 & Bash
- **Theme Engine:** Dynamic Catppuccin
- **Hardware Profile:** Optimized for Intel i7 & NVIDIA RTX 3050 Ti Mobile

---

### Usage & Commands
All custom scripts are located in `~/.local/bin/` and are globally accessible from the terminal or Qtile keybinds.

* **`sys_popup <mode>`**
  * **What it does:** Spawns a lightweight, borderless Tkinter window with live hardware stats. Auto-closes on focus loss.
  * **Usage:** Run `sys_popup cpu`, `sys_popup ram`, `sys_popup gpu`, or `sys_popup net`.
* **`power_menu`**
  * **What it does:** Opens a centralized, floating power control hub in the middle of the screen.
* **`theme_manager`**
  * **What it does:** GUI to instantly swap Qtile themes and update component colors.
* **`fetchman`**
  * **What it does:** Custom wrapper for Fastfetch with dynamic image rendering.
* **`wallman`**
  * **What it does:** Advanced wallpaper manager (Source in `~/.local/share/wallman`).
* **`restart-wallpaper` / `wallpaper-launcher`**
  * **What it does:** Manages the `xwinwrap` engine for animated wallpapers.

---

### Custom "From Scratch" Features

#### System & UI
* **Dynamic Theme Manager:** Instantly swaps Qtile themes, rewriting `qtile_theme.json` for live updates.
* **Minimalist Power Menu:** Frameless UI featuring an auto-inverting contrast close button (`✕`).
* **Tkinter System Popups:**
  * **CPU:** Live per-core frequency, load, and performance/powersave governors.
  * **RAM:** Live usage statistics and a real-time feed of the Top 5 memory-heavy processes.
  * **GPU:** Live temperature, VRAM, and power draw metrics (nvidia-smi).
  * **Network:** Real-time, mathematically calculated upload/download throughput.

#### Environment
* **Terminal Engine:** Integrated Fastfetch with isolated asset management in `~/Pictures/fastfetch`.
* **Advanced Wallpaper Engine:** Custom scripts paired with compiled `xwinwrap`.

---

### Installation (Bare Git Repository)
```bash
git clone --bare [https://github.com/OualidRahmani/dotfiles.git](https://github.com/OualidRahmani/dotfiles.git) $HOME/.dotfiles
alias dotconfig='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
dotconfig checkout
# Re-link Wallman
sudo ln -s ~/.local/share/wallman/main.py /usr/local/bin/wallman
