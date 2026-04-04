#!/usr/bin/env bash

picom --config ~/.config/picom.conf &
dunst -conf ~/.config/dunst/dunstrc &
randomize-wallpaper &
setxkbmap us &
~/.local/bin/lock.sh &