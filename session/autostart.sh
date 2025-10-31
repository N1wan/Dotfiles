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
CONNECTED_OUTPUTS=$(xrandr | awk '/ connected/{print $1}' | grep -E '^HDMI|^DP')
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

# input changes for all pointer devices,
ids=$(xinput list | grep -i 'slave.*pointer' || true)
ids=$(echo "$ids" | sed -n 's/.*id=\([0-9]\+\).*/\1/p')
for id in $ids; do
  name=$(xinput list --name-only "$id" 2>/dev/null || echo "id=$id")
  echo "Configuring device id=$id — $name"

  props=$(xinput list-props "$id" 2>/dev/null || true)

  # --- Common: disable accel (flat) ---
  if echo "$props" | grep -q "libinput Accel Profile Enabled"; then
    xinput set-prop "$id" "libinput Accel Profile Enabled" 0, 1, 0
  fi

  if echo "$props" | grep -q "libinput Accel Speed"; then
    xinput set-prop "$id" "libinput Accel Speed" 0
  fi

  if echo "$props" | grep -q "libinput Disable While Typing Enabled"; then
    xinput set-prop "$id" "libinput Disable While Typing Enabled" 0
  fi

  # --- Detect touchpad vs mouse ---
  is_touchpad=0
  # check the device name
  if echo "$name" | grep -qi "touchpad\|touch pad\|synaptics\|libinput"; then
    is_touchpad=1
  fi
  # check properties for touchpad hints
  if echo "$props" | grep -qi "touchpad\|Synaptics"; then
    is_touchpad=1
  fi

  # --- Touchpad-only: enable natural scrolling ---
  if [ "$is_touchpad" -eq 1 ]; then
    if echo "$props" | grep -q "libinput Natural Scrolling Enabled"; then
      echo " → touchpad detected: enabling libinput Natural Scrolling"
      xinput set-prop "$id" "libinput Natural Scrolling Enabled" 1
    elif echo "$props" | grep -q "Evdev Scrolling Distance"; then
      echo " → touchpad uses evdev: inverting Evdev Scrolling Distance"
      # read current two values and negate them
      vals=$(echo "$props" | sed -n 's/.*Evdev Scrolling Distance.*:\s*\(-\{0,1\}[0-9]\+\)\s*\(-\{0,1\}[0-9]\+\).*/\1 \2/p')
      if [ -n "$vals" ]; then
        a=$(echo "$vals" | awk '{print $1}')
        b=$(echo "$vals" | awk '{print $2}')
        na=$(( -1 * a ))
        nb=$(( -1 * b ))
        xinput set-prop "$id" "Evdev Scrolling Distance" "$na" "$nb"
      else
        echo "   ! could not parse Evdev Scrolling Distance for $name"
      fi
    else
      echo " → touchpad detected but no supported natural-scrolling property found for $name."
      echo "   (libinput Natural Scrolling / Evdev Scrolling Distance not present)"
    fi
  else
    # Not a touchpad: ensure natural scrolling is disabled if property exists
    if echo "$props" | grep -q "libinput Natural Scrolling Enabled"; then
      xinput set-prop "$id" "libinput Natural Scrolling Enabled" 0
    fi
  fi
done
