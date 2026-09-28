#!/bin/bash
# Resumable driver: bake every ADFRC rig + clip to UE-importable FBX.
set -u
WORK="$(cd "$(dirname "$0")" && pwd)"
ANIM="E:/SouthernSpear/Content/Sourced/ADF_Extracted/Animations"
DST="E:/SouthernSpear/Content/Sourced/ADF_Extracted/Animations_UE"
LIST="$WORK/rig_list.txt"
LOG="$WORK/blender_anim.log"
WORKERS="${1:-4}"
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"

while tasklist //FI "IMAGENAME eq blender.exe" 2>/dev/null | grep -qi blender.exe; do
  echo "waiting for running blender instance(s)..."; sleep 10
done

# Rig skeletons are the natural resumable unit; a rig is re-done whole.
: > "$WORK/pending_rigs.txt"
while IFS= read -r rig; do
  [ -n "$rig" ] || continue
  key=$(basename "$rig" .json)
  [ -s "$DST/$key/${key}_skeleton.fbx" ] || echo "$rig" >> "$WORK/pending_rigs.txt"
done < "$LIST"

total=$(wc -l < "$WORK/pending_rigs.txt")
echo "PENDING_RIGS=$total WORKERS=$WORKERS"
[ "$total" -eq 0 ] && { echo "ALL_ANIM_BAKES_COMPLETE"; exit 0; }

rm -f "$WORK"/achunk_*
split -n "l/$WORKERS" -d -a 2 "$WORK/pending_rigs.txt" "$WORK/achunk_"

pids=()
for ch in "$WORK"/achunk_*; do
  [ -s "$ch" ] || continue
  "$BLENDER" --background --python "$WORK/anim_to_fbx.py" \
    -- "$ANIM" "$DST" "$ch" >> "$LOG" 2>&1 &
  pids+=($!)
done
wait "${pids[@]}"
echo "WAVE_DONE: $(find "$DST" -name '*.fbx' 2>/dev/null | wc -l) fbx so far"
