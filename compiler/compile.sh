#!/usr/bin/env bash

if [[ "$1" == "" ]] || [[ "$2" == "" ]] || [[ "$3" == "" ]] || [[ "$4" == "" ]] || [[ "$5" != "" ]]
then
    echo 'usage: compile.sh <vertex.glsl> <fragment.glsl> <vertex.bin> <fragment.bin>' >&2
    exit 1
fi

SELF="$0"
CWD="${SELF%%compile.sh}"

if [[ "$CWD" == "" ]]
then CWD=.
fi

TEMP="$(mktemp -d)"

while true; do
    LD_PRELOAD="$CWD/libpreload.so" R600_DEBUG=vs "$CWD/victim" "$1" "$2" 2>&1 | python3 "$CWD/postprocess.py" -v "$TEMP/shader.s" "$TEMP/shader.t" || break
    clrxasm -g Bonaire -b raw "$TEMP/shader.s" -o "$TEMP/shader.bin" || break
    python3 "$CWD/../template.py" "$TEMP/shader.t" "$TEMP/shader.bin" "$3" || break
    LD_PRELOAD="$CWD/libpreload.so" R600_DEBUG=ps "$CWD/victim" "$1" "$2" 2>&1 | python3 "$CWD/postprocess.py" "$TEMP/shader.s" "$TEMP/shader.t" || break
    clrxasm -g Bonaire -b raw "$TEMP/shader.s" -o "$TEMP/shader.bin" || break
    python3 "$CWD/../template.py" "$TEMP/shader.t" "$TEMP/shader.bin" "$4" || break
    rm -rf "$TEMP"
    exit 0
done

rm -rf "$TEMP"
exit 1
