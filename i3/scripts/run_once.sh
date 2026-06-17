#!/usr/bin/env bash

lock="/tmp/$(basename "$1").lock"

if [ -e "$lock" ]; then
    exit 0
fi

touch "$lock"

cleanup() {
    rm -f "$lock"
}
trap cleanup EXIT

"$@" &
wait $!
