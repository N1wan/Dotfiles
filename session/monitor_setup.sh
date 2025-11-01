#!/usr/bin/env bash

# Set monitor resolution and refresh rate
# Detect any connected display(s)
CONNECTED_OUTPUTS=$(xrandr | awk '/ connected/{print $1}' | grep -E '^HDMI|^DP|^eDP' || true)

for OUTPUT in $CONNECTED_OUTPUTS; do
    # Extract all mode lines for this output and expand each refresh rate into its own line.
    # Output format: "<resolution> <rate>"
    MODES=$(xrandr | awk -v out="$OUTPUT" '
        $1 == out && $2 == "connected" {flag=1; next}
        /^[A-Z]/ {flag=0}
        flag && /^[[:space:]]*[0-9]/ {
            res = $1
            for (i = 2; i <= NF; i++) {
                rate = $i
                gsub(/[*+]/, "", rate)    # remove * and +
                if (rate ~ /^[0-9]+(\.[0-9]+)?$/) print res, rate
            }
        }
    ')

    # Find the best mode (highest width, then height, then refresh)
    BEST_MODE=$(echo "$MODES" | awk '
        {
            split($1, r, "x");
            w = r[1] + 0; h = r[2] + 0; hz = $2 + 0;
            if (w > maxW || (w == maxW && h > maxH) || (w == maxW && h == maxH && hz > maxHz)) {
                maxW = w; maxH = h; maxHz = hz;
                best = $1 " " $2;
            }
        }
        END {print best}
    ')

    if [ -z "$BEST_MODE" ]; then
        echo "No modes found for $OUTPUT, skipping."
        continue
    fi

    RES=$(echo "$BEST_MODE" | awk '{print $1}')
    RATE=$(echo "$BEST_MODE" | awk '{print $2}')

    # Find current active mode and rate by searching for the '*' marker anywhere in the mode block
    CURRENT=$(xrandr | awk -v out="$OUTPUT" '
        $1 == out && $2 == "connected" {flag=1; next}
        /^[A-Z]/ {flag=0}
        flag && /^[[:space:]]*[0-9]/ {
            res = $1
            for (i = 2; i <= NF; i++) {
                if ($i ~ /\*/) {
                    rate = $i
                    gsub(/[*+]/, "", rate)
                    print res, rate
                    exit
                }
            }
        }
    ')

    CURRENT_RES=$(echo "$CURRENT" | awk '{print $1}' 2>/dev/null || echo "")
    CURRENT_RATE=$(echo "$CURRENT" | awk '{print $2}' 2>/dev/null || echo "")

    echo "all modes are"
    echo "$MODES"
    echo "the best mode is"
    echo "${RES} ${RATE}"
    echo "the current res is"
    echo "${CURRENT_RES}"
    echo "and the current rate is"
    echo "${CURRENT_RATE}"

    # Only set mode if different (compare numeric strings)
    if [ "$RES" != "$CURRENT_RES" ] || [ "$RATE" != "$CURRENT_RATE" ]; then
        echo "Changing $OUTPUT: ${CURRENT_RES}@${CURRENT_RATE}Hz → ${RES}@${RATE}Hz"
        xrandr --output "$OUTPUT" --mode "$RES" --rate "$RATE"
    else
        echo "$OUTPUT is already at ${RES}@${RATE}Hz — skipping"
    fi
done

