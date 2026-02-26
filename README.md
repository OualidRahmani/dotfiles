# Ouali's Dotfiles 🚀

A highly customized, ground-up Linux desktop environment built on **Qtile**. This setup moves away from bloated stock widgets, relying instead on custom, lightweight Python/Tkinter modules for system monitoring and theming.

### 🖥️ The Architecture
- **Window Manager:** Qtile
- **Language:** Python 3 (Configurations & Custom Widgets)
- **Theme Engine:** Dynamic Catppuccin (Custom script)
- **Hardware Profile:** Optimized for Intel i7 & NVIDIA RTX 3050 Ti Mobile

### ✨ Custom "From Scratch" Features

* **Dynamic Theme Manager:** A custom GUI to instantly swap Qtile themes and update component colors on the fly.
* **Tkinter System Popups:** Lightweight, borderless floating windows that trigger from the Qtile bar:
  * **CPU:** Live per-core frequency, load, and performance/powersave governors.
  * **RAM:** Live usage statistics and a real-time feed of the Top 5 memory-heavy processes.
  * **GPU:** Live temperature, VRAM, and power draw metrics hooked directly into `nvidia-smi`.
  * **Network:** Real-time, mathematically calculated upload/download throughput.
* **Minimalist Power Menu:** A centered, floating power control hub built entirely in Python, replacing standard messy bar icons.

### ⚙️ Installation (Bare Git Repository)
```bash
git clone --bare [https://github.com/OualidRahmani/dotfiles.git](https://github.com/OualidRahmani/dotfiles.git) $HOME/.dotfiles
alias dotconfig='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
dotconfig checkout
