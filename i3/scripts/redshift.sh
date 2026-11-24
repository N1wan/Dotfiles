#!/bin/sh

STEP=200
DEFAULT=6500
MIN=3500
MAX=6500
STATE="$HOME/.cache/redshift-temp"

[ -f "$STATE" ] || echo "$DEFAULT" > "$STATE"
TEMP=$(cat "$STATE")

case "$1" in
  refresh)
    ;;
  up)
    TEMP=$((TEMP + STEP))
    ;;
  down)
    TEMP=$((TEMP - STEP))
    ;;
  reset)
    echo "$DEFAULT" > "$STATE"
    redshift -P -x
	pkill -RTMIN+2 i3blocks
    exit 0
    ;;
esac

# clamp
[ "$TEMP" -gt "$MAX" ] && TEMP="$MAX"
[ "$TEMP" -lt "$MIN" ] && TEMP="$MIN"

echo "$TEMP" > "$STATE"
redshift -P -O "$TEMP"

pkill -RTMIN+2 i3blocks

