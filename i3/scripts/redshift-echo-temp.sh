#!/bin/sh

DEFAULT=6500
STATE="$HOME/.cache/redshift-temp"

[ -f "$STATE" ] || echo "$DEFAULT" > "$STATE"
TEMP=$(cat "$STATE")

cat "$STATE"

