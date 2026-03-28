#!/usr/bin/env bash

picom --config ~/.config/picom.conf &
dunst -conf ~/.config/dunst/dunstrc &
feh --bg-fill ~/wallpapers/* &