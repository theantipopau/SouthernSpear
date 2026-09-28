#!/bin/bash
# Resumable parallel driver: MLOD -> FBX via Blender + A3OB.
# Waits for stragglers, rebuilds the pending list, fans it out to N workers.
set -u
WORK="$(cd "$(dirname "$0")" && pwd)"
SRC="$WORK/mlod_src"
DST="E:/SouthernSpear/Content/Sourced/ADF_Extracted/Models_FBX"
LIST="$WORK/mlod_list.txt"
LOG="$WORK/blender_run.log"
WORKERS="${1:-5}"
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"

# Never start a second wave while earlier instances are alive.
while tasklist //FI "IMAGENAME eq blender.exe" 2>/dev/null | grep -qi blender.exe; do
  echo "waiting for running blender instance(s)..."; sleep 10
done

# Pending = sources whose final FBX is missing/empty.
: > "$WORK/pending.txt"
while IFS= read -r src; do
  rel="${src#*$SRC/}"
  rel="${rel%_MLOD.p3d}.fbx"
  [ -s "$DST/$rel" ] || echo "$src" >> "$WORK/pending.txt"
done < "$LIST"

total=$(wc -l < "$WORK/pending.txt")
done_cnt=$(find "$DST" -name '*.fbx' ! -name '*.part.fbx' | wc -l)
echo "DONE_SO_FAR=$done_cnt PENDING=$total WORKERS=$WORKERS"
[ "$total" -eq 0 ] && { echo "ALL_CONVERSIONS_COMPLETE"; exit 0; }

rm -f "$WORK"/chunk_*
split -n "l/$WORKERS" -d -a 2 "$WORK/pending.txt" "$WORK/chunk_"

pids=()
for ch in "$WORK"/chunk_*; do
  [ -s "$ch" ] || continue
  "$BLENDER" --background --python "$WORK/blender_models.py" \
    -- "$SRC" "$DST" "$ch" >> "$LOG" 2>&1 &
  pids+=($!)
done
wait "${pids[@]}"
echo "WAVE_DONE: $(find "$DST" -name '*.fbx' ! -name '*.part.fbx' | wc -l) fbx so far"
