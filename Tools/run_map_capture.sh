#!/usr/bin/env bash
# Southern Spear - launch the game on a map and capture a screenshot.
#
# The `-SSShotAt=<seconds>` flag is implemented in
# Plugins/SouthernSpearObjectives/.../SSObjectiveHudSubsystem.cpp and takes one
# viewport screenshot (with UI) to Saved/Screenshots/<platform>/SSShot.png, then
# the process is killed. It captures the viewport buffer directly, so it does not
# need window focus and does not disturb an editor session that is already open.
#
# Follows Docs/PLAYTEST_COMMANDS.md §3 exactly. Two of its rules exist because this
# script once broke by ignoring them:
#   - use UnrealEditor.exe, NOT UnrealEditor-Cmd.exe: the -Cmd binary takes a
#     different startup path in -game mode and never reaches module load here;
#   - always pass -abslog with our own file and -FORCELOGFLUSH: the default
#     Saved/Logs/SouthernSpear.log is clobbered by other agents' commandlets, and
#     a timeout kill without -FORCELOGFLUSH loses the log tail (which read as a
#     mysterious "stall at 32 lines" for a whole session).
#
#   Tools/run_map_capture.sh [map] [seconds] [timeout_seconds]
#
#   map    package path, default /Game/Maps/L_DryRiver_01
#
# Exit status is 0 only if the map loaded AND a screenshot was written. A run
# that produces a log but no image is a failure, not a partial success.
#
# Note: do NOT pass -unattended. It is a commandlet flag; a -game instance given
# it initialises the engine and then exits immediately, which looks like a stall
# in the log but is a silent no-op.

set -uo pipefail

MAP="${1:-/Game/Maps/L_DryRiver_01}"
SHOT_AT="${2:-8}"
TIMEOUT="${3:-420}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# The engine wants a drive-letter path; the shell gives us /e/SouthernSpear.
ROOT_WIN="$(cygpath -m "$ROOT" 2>/dev/null || echo "$ROOT")"
UPROJECT="$ROOT_WIN/SouthernSpear.uproject"
EDITOR="${SS_UNREAL_EDITOR:-E:/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe}"
SHOTS="$ROOT/Saved/Screenshots"
RESULT="$SHOTS/WindowsEditor/SSShot.png"
LOG="$ROOT/Saved/Logs/SouthernSpear.log"

if [ ! -f "$UPROJECT" ]; then
    echo "FAIL: no uproject at $UPROJECT" >&2
    exit 2
fi
if [ ! -f "$EDITOR" ]; then
    echo "FAIL: no editor at $EDITOR (override with SS_UNREAL_EDITOR)" >&2
    exit 2
fi

# Clear the previous capture so "a file exists" cannot be a stale success.
rm -f "$RESULT" 2>/dev/null

echo "== map        $MAP"
echo "== shot at    ${SHOT_AT}s"
echo "== editor     $EDITOR"
echo "== timeout    ${TIMEOUT}s"

# Git Bash rewrites any argument that looks like an absolute POSIX path, so
# /Game/Maps/L_DryRiver_01 silently becomes C:/Program Files/Git/Game/Maps/...
# and the game loads nothing while still writing a screenshot of an empty frame.
# Excluding only the /Game/* pattern fixes that while leaving the project path to
# convert normally. It must be exported, not set as a prefix assignment: the
# path-conversion step runs with the shell's own environment and never sees a
# variable that only exists in the child's.
RUNLOG="$ROOT/Saved/Logs/SS_capture_$(date +%Y%m%d_%H%M%S).log"
MSYS_NO_PATHCONV=1 timeout "$TIMEOUT" "$EDITOR" "$UPROJECT" "$MAP" \
    -game -windowed -ResX=1600 -ResY=900 \
    -nosplash -nosound -FORCELOGFLUSH \
    -abslog="$(cygpath -m "$RUNLOG")" \
    -SSShotAt="$SHOT_AT" > /tmp/ss_capture.log 2>&1
STATUS=$?
cp /tmp/ss_capture.log "$LOG.capture" 2>/dev/null

# Read progress from the -abslog file, not stdout: the engine buffers stdout and
# a killed run loses its tail (the misdiagnosed "stall").
LOADED=$(grep -c "up for play" "$RUNLOG" 2>/dev/null || echo 0)
LOADED_NAME=$(grep -o "LoadMap: [^?]*" "$RUNLOG" 2>/dev/null | tail -1)
SHOT_LINE=$(grep -o "Requested viewport screenshot at [0-9.]* s" "$RUNLOG" 2>/dev/null | tail -1)
# A run that never loaded the map still writes a screenshot of the empty frame,
# so a plausible-looking file is not evidence. Require the map line too.
if [ "$LOADED" -lt 1 ]; then
    echo "== note       the map argument may have been mangled - check the commandline echoed in the log"
fi

echo "== exit       $STATUS"
echo "== log        $RUNLOG"
echo "== map loads  $LOADED   ${LOADED_NAME}"
echo "== capture    ${SHOT_LINE:-<none>}"

if [ -f "$RESULT" ]; then
    SIZE=$(wc -c < "$RESULT")
    echo "== image      $RESULT ($SIZE bytes)"
    if [ "$LOADED" -ge 1 ] && [ "$SIZE" -gt 10000 ]; then
        echo "PASS"
        exit 0
    fi
    echo "FAIL: image written but the map did not load" >&2
    exit 1
fi

echo "FAIL: no screenshot at $RESULT" >&2
echo "---- last 30 log lines ($RUNLOG) ----" >&2
tail -30 "$RUNLOG" 2>/dev/null || tail -30 /tmp/ss_capture.log >&2
exit 1
