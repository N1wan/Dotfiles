#!/bin/sh

STEP=200
DEFAULT=6500
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
[ "$TEMP" -gt 6500 ] && TEMP=6500
[ "$TEMP" -lt 3500 ] && TEMP=3500

echo "$TEMP" > "$STATE"
redshift -P -O "$TEMP"

pkill -RTMIN+2 i3blocks

