#!/bin/bash

# Try to find any BAT device
batt_path=$(upower -e 2>/dev/null | grep -i bat | head -1)

if [ -z "$batt_path" ]; then
    # No battery found (desktop or broken detection)
    echo "N/A"
    exit 0
fi

info=$(upower -i "$batt_path" 2>/dev/null | grep -E "state|percentage")
status=$(echo "$info" | grep state | awk '{print $2}')
percent=$(echo "$info" | grep percentage | awk '{print $2}' | sed 's/%//')

if [[ $status == "charging" ]]; then
    icon="⚡ "
else
    icon=""
fi

echo "${icon}${percent}%"
exit 0

