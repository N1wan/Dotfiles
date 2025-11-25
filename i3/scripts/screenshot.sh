#!/usr/bin/env bash

DIR="$HOME/Pictures/Screenshots"
LIMIT=30

mkdir -p "$DIR"

# filename
FILE="$DIR/$(date +%Y-%m-%d_%H-%M-%S).png"

# run scrot (pass through scrot arguments)
scrot "$@" "$FILE" -e "xclip -selection clipboard -t image/png -i \$f"

# count screenshots
COUNT=$(ls "$DIR"/*.png 2>/dev/null | wc -l)

# delete oldest if above limit
if [ "$COUNT" -gt "$LIMIT" ]; then
    # number to delete
    REMOVE=$((COUNT - LIMIT))
    ls -1t "$DIR"/*.png | tail -n "$REMOVE" | xargs rm --
fi

