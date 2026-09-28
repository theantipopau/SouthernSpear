#!/bin/bash
# Convert exactly one MLOD file to FBX, with a hard timeout so a hang cannot
# stall the batch. Prints RC=<code> <path> for the driver to collect.
set -u
WORK="$(cd "$(dirname "$0")" && pwd)"
SRC="E:/SouthernSpear/Saved/AdfrcLfsTemp/mlod_src"
DST="E:/SouthernSpear/Content/Sourced/ADF_Extracted/Models_FBX"
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
src="$1"
lst="$WORK/one_$$.txt"
printf '%s\n' "$src" > "$lst"
timeout 240 "$BLENDER" --background --python "$WORK/blender_models.py" \
  -- "$SRC" "$DST" "$lst" >> "$WORK/blender_run.log" 2>&1
rc=$?
rm -f "$lst"
echo "RC=$rc $src"
exit 0
