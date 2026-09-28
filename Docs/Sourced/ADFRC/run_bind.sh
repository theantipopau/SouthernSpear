#!/bin/bash
# Resumable parallel driver: bind PNG textures into every FBX material.
# Waits for stragglers, rebuilds the pending list, fans it out to N workers.
set -u
WORK="$(cd "$(dirname "$0")" && pwd)"
SRC="E:/SouthernSpear/Content/Sourced/ADF_Extracted/Models_FBX"
DST="E:/SouthernSpear/Content/Sourced/ADF_Extracted/Models_UE"
TEX="E:/SouthernSpear/Content/Sourced/ADF_Extracted/Textures"
LIST="$WORK/fbx_list.txt"
LOG="$WORK/blender_bind.log"
WORKERS="${1:-5}"
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"

while tasklist //FI "IMAGENAME eq blender.exe" 2>/dev/null | grep -qi blender.exe; do
  echo "waiting for running blender instance(s)..."; sleep 10
done

# Full list, once.
if [ ! -s "$LIST" ]; then
  ( cd "$SRC" && find . -name '*.fbx' ! -name '*.part.fbx' ) > "$LIST"
fi

# Pending = FBX whose bound output is missing/empty.
: > "$WORK/pending.txt"
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  [ -s "$DST/$rel" ] || echo "$SRC/${rel#./}" >> "$WORK/pending.txt"
done < "$LIST"

total=$(wc -l < "$WORK/pending.txt")
done_cnt=$(find "$DST" -name '*.fbx' ! -name '*.part.fbx' 2>/dev/null | wc -l)
echo "DONE_SO_FAR=$done_cnt PENDING=$total WORKERS=$WORKERS"
[ "$total" -eq 0 ] && { echo "ALL_BINDING_COMPLETE"; exit 0; }

rm -f "$WORK"/chunk_*
split -n "l/$WORKERS" -d -a 2 "$WORK/pending.txt" "$WORK/chunk_"

pids=()
for ch in "$WORK"/chunk_*; do
  [ -s "$ch" ] || continue
  "$BLENDER" --background --python "$WORK/bind_materials.py" \
    -- "$SRC" "$DST" "$TEX" "$ch" >> "$LOG" 2>&1 &
  pids+=($!)
done
wait "${pids[@]}"
echo "WAVE_DONE: $(find "$DST" -name '*.fbx' ! -name '*.part.fbx' 2>/dev/null | wc -l) fbx so far"
