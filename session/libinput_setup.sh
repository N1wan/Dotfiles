#!/usr/bin/env bash

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

