#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1

# Helper: start a process if not already running
run_once() {
    if ! pgrep -x "$(basename "$1")" >/dev/null 2>&1; then
        "$@" &
    fi
}

../i3/scripts/redshift.sh refresh
run_once picom
run_once nm-applet
run_once blueman-applet
run_once dunst
run_once batsignal -b
run_once udiskie --automount --notify --tray
run_once unclutter --timeout 1 --jitter 5 --ignore-scrolling --start-hidden
feh --bg-fill ~/Dotfiles/resources/current_background

if ! pgrep -f gnome-keyring-daemon >/dev/null 2>&1; then
    eval $(/usr/bin/gnome-keyring-daemon --start --components=secrets,ssh,gpg)
    export SSH_AUTH_SOCK
    export GPG_AGENT_INFO
    export GNOME_KEYRING_CONTROL
fi

./monitor_setup.sh
./libinput_setup.sh

