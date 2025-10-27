#!/usr/bin/env bash

# Helper: start a process if not already running
run_once() {
    if ! pgrep -x "$(basename "$1")" >/dev/null 2>&1; then
        "$@" &
    fi
}

run_once nm-applet
run_once blueman-applet
run_once dunst
run_once batsignal -b
run_once unclutter --timeout 1 --jitter 5 --ignore-scrolling --start-hidden
feh --bg-fill ~/Dotfiles/resources/current_background

# Freedesktop secrets API (keyring daemon)
if ! pgrep -x gnome-keyring-daemon >/dev/null 2>&1; then
    eval $(/usr/bin/gnome-keyring-daemon --start --components=secrets)
fi

# Set monitor resolution and refresh rate
# (only apply if HDMI-0 is connected)
if xrandr | grep -q "HDMI-0 connected"; then
    current_mode=$(xrandr --query | grep "HDMI-0 connected" -A1 | tail -n1)
    if [[ "$current_mode" != *"2560x1440"* || "$current_mode" != *"144.00"* ]]; then
        xrandr --output HDMI-0 --mode 2560x1440 --rate 144.00
    fi
fi

# Disable mouse acceleration (only if the device exists)
TOUCHPAD="SYNA32D3:00 06CB:CED1 Touchpad"
if xinput list --name-only | grep -q "$TOUCHPAD"; then
    xinput set-prop "$TOUCHPAD" "libinput Accel Profile Enabled" 0, 1, 0
    xinput set-prop "$TOUCHPAD" "libinput Accel Speed" 0.5
    xinput set-prop "$TOUCHPAD" "libinput Disable While Typing Enabled" 0
fi

# Keyboard remap (Caps → Escape)
if ! setxkbmap -query | grep -q "caps:escape"; then
    setxkbmap -option caps:escape
fi

