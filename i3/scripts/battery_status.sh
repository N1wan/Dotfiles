#!/bin/bash

# Get status and percentage from upower
info=$(upower -i $(upower -e | grep BAT) | grep -E "state|percentage")

status=$(echo "$info" | grep state | awk '{print $2}')
percent=$(echo "$info" | grep percentage | awk '{print $2}' | sed 's/%//')

# Set icon
if [[ $status == "charging" ]]; then
    icon="⚡ "
else
    icon=""
fi

echo "$icon$percent%"

