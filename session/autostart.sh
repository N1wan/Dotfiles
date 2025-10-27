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
# Detect any connected display(s)
CONNECTED_OUTPUTS=$(xrandr | awk '/ connected/{print $1}')
for OUTPUT in $CONNECTED_OUTPUTS; do
    # Extract all available mode lines for this output
    MODES=$(xrandr | awk -v out="$OUTPUT" '
        $1 == out && $2 == "connected" {flag=1; next}
        /^[A-Z]/ {flag=0}
        flag && /^[[:space:]]*[0-9]/ {print $1, $2}
    ')

    # Parse and find the highest resolution and refresh rate
    BEST_MODE=$(echo "$MODES" | awk '
        {
            split($1, res, "x");
            width = res[1];
            height = res[2];
            hz = ($2 ~ /[0-9.]+/) ? $2 : 0;
            if (width > maxW || (width == maxW && height > maxH) || (width == maxW && height == maxH && hz > maxHz)) {
                maxW = width;
                maxH = height;
                maxHz = hz;
                best = $1 " " hz;
            }
        }
        END {print best}
    ')

    # Apply the best mode if found
    if [ -n "$BEST_MODE" ]; then
        RES=$(echo "$BEST_MODE" | awk '{print $1}')
        RATE=$(echo "$BEST_MODE" | awk '{print $2}')
        echo "Setting $OUTPUT to ${RES} @ ${RATE}Hz"
        xrandr --output "$OUTPUT" --mode "$RES" --rate "$RATE"
    fi
done

# Disable mouse acceleration (only if the device exists)
TOUCHPAD="SYNA32D3:00 06CB:CED1 Touchpad"
if xinput list --name-only | grep -q "$TOUCHPAD"; then
    xinput set-prop "$TOUCHPAD" "libinput Accel Profile Enabled" 0, 1, 0
    xinput set-prop "$TOUCHPAD" "libinput Accel Speed" 0.5
    xinput set-prop "$TOUCHPAD" "libinput Disable While Typing Enabled" 0
fi
