#!/bin/bash

# Algorithmic Research Loop - Phase-Aware Stop Hook
# Extends Ralph Wiggum's stop hook with a 7-phase algorithmic R&D pipeline.
# Phases: explore → ideate → implement → benchmark → validate → analyze → report
# Key feature: LOOP-BACK mechanism from analyze → ideate for innovation cycles.

set -euo pipefail

HOOK_INPUT=$(cat)

STATE_FILE=".claude/algo-loop.local.md"

if [[ ! -f "$STATE_FILE" ]]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# Parse state file frontmatter
# ---------------------------------------------------------------------------
FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$STATE_FILE")

parse_field() {
  local field="$1"
  echo "$FRONTMATTER" | grep "^${field}:" | sed "s/${field}: *//" | sed 's/^"\(.*\)"$/\1/'
}

CURRENT_PHASE=$(parse_field "current_phase")
PHASE_NAME=$(parse_field "phase_name")
PHASE_ITERATION=$(parse_field "phase_iteration")
GLOBAL_ITERATION=$(parse_field "global_iteration")
MAX_GLOBAL_ITERATIONS=$(parse_field "max_global_iterations")
COMPLETION_PROMISE=$(parse_field "completion_promise")
TOPIC=$(parse_field "topic")
OUTPUT_DIR=$(parse_field "output_dir")
MODE=$(parse_field "mode")
LANGUAGE=$(parse_field "language")
CODEBASE_PATH=$(parse_field "codebase_path")
INNOVATION_CYCLES=$(parse_field "innovation_cycles")
MAX_INNOVATION_CYCLES=$(parse_field "max_innovation_cycles")
ALGORITHMS_FOUND=$(parse_field "algorithms_found")
ALGORITHMS_INVENTED=$(parse_field "algorithms_invented")
ALGORITHMS_IMPLEMENTED=$(parse_field "algorithms_implemented")
BENCHMARKS_RUN=$(parse_field "benchmarks_run")

# Phase max iterations (bash associative array)
declare -A PHASE_MAX_ITER
PHASE_MAX_ITER[1]=3   # explore
PHASE_MAX_ITER[2]=3   # ideate
PHASE_MAX_ITER[3]=5   # implement
PHASE_MAX_ITER[4]=4   # benchmark
PHASE_MAX_ITER[5]=3   # validate
PHASE_MAX_ITER[6]=3   # analyze
PHASE_MAX_ITER[7]=2   # report

# Standard mode: skip ideate phase (auto-advance from explore to implement)
if [[ "$MODE" == "standard" ]]; then
  PHASE_MAX_ITER[2]=0
fi

# Phase names lookup
declare -A PHASE_NAMES
PHASE_NAMES[1]="explore"
PHASE_NAMES[2]="ideate"
PHASE_NAMES[3]="implement"
PHASE_NAMES[4]="benchmark"
PHASE_NAMES[5]="validate"
PHASE_NAMES[6]="analyze"
PHASE_NAMES[7]="report"

# Quality gate: phases that require quality evaluation before advancing
declare -A PHASE_QUALITY_GATE
PHASE_QUALITY_GATE[1]=0   # explore — no gate
PHASE_QUALITY_GATE[2]=1   # ideate — quality of ideas matters
PHASE_QUALITY_GATE[3]=1   # implement — code quality matters
PHASE_QUALITY_GATE[4]=1   # benchmark — results quality matters
PHASE_QUALITY_GATE[5]=1   # validate — analysis quality matters
PHASE_QUALITY_GATE[6]=1   # analyze — forensics quality matters
PHASE_QUALITY_GATE[7]=0   # report — final pass, no gate

# ---------------------------------------------------------------------------
# Validate numeric fields
# ---------------------------------------------------------------------------
validate_numeric() {
  local field_name="$1"
  local field_value="$2"
  if [[ ! "$field_value" =~ ^[0-9]+$ ]]; then
    echo "⚠️  Algo loop: State file corrupted" >&2
    echo "   File: $STATE_FILE" >&2
    echo "   Problem: '$field_name' is not a valid number (got: '$field_value')" >&2
    echo "   Algo loop is stopping. Run /algo-loop again to start fresh." >&2
    rm "$STATE_FILE"
    exit 0
  fi
}

validate_numeric "current_phase" "$CURRENT_PHASE"
validate_numeric "phase_iteration" "$PHASE_ITERATION"
validate_numeric "global_iteration" "$GLOBAL_ITERATION"
validate_numeric "max_global_iterations" "$MAX_GLOBAL_ITERATIONS"
validate_numeric "innovation_cycles" "$INNOVATION_CYCLES"
validate_numeric "max_innovation_cycles" "$MAX_INNOVATION_CYCLES"

# ---------------------------------------------------------------------------
# Check global iteration limit
# ---------------------------------------------------------------------------
if [[ $MAX_GLOBAL_ITERATIONS -gt 0 ]] && [[ $GLOBAL_ITERATION -ge $MAX_GLOBAL_ITERATIONS ]]; then
  echo "🛑 Algo loop: Max global iterations ($MAX_GLOBAL_ITERATIONS) reached."
  echo "   Topic: $TOPIC"
  echo "   Final phase: $CURRENT_PHASE ($PHASE_NAME)"
  echo "   Algorithms: found=$ALGORITHMS_FOUND invented=$ALGORITHMS_INVENTED implemented=$ALGORITHMS_IMPLEMENTED"
  echo "   Benchmarks run: $BENCHMARKS_RUN | Innovation cycles: $INNOVATION_CYCLES/$MAX_INNOVATION_CYCLES"
  rm "$STATE_FILE"
  exit 0
fi

# ---------------------------------------------------------------------------
# Read transcript and extract last assistant output
# ---------------------------------------------------------------------------
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path')

if [[ ! -f "$TRANSCRIPT_PATH" ]]; then
  echo "⚠️  Algo loop: Transcript file not found at $TRANSCRIPT_PATH" >&2
  rm "$STATE_FILE"
  exit 0
fi

if ! grep -q '"role":"assistant"' "$TRANSCRIPT_PATH"; then
  echo "⚠️  Algo loop: No assistant messages found in transcript" >&2
  rm "$STATE_FILE"
  exit 0
fi

LAST_LINE=$(grep '"role":"assistant"' "$TRANSCRIPT_PATH" | tail -1)
if [[ -z "$LAST_LINE" ]]; then
  echo "⚠️  Algo loop: Failed to extract last assistant message" >&2
  rm "$STATE_FILE"
  exit 0
fi

LAST_OUTPUT=$(echo "$LAST_LINE" | jq -r '
  .message.content |
  map(select(.type == "text")) |
  map(.text) |
  join("\n")
' 2>&1)

if [[ $? -ne 0 ]] || [[ -z "$LAST_OUTPUT" ]]; then
  echo "⚠️  Algo loop: Failed to parse assistant message" >&2
  rm "$STATE_FILE"
  exit 0
fi

# ---------------------------------------------------------------------------
# Check for completion promise
# ---------------------------------------------------------------------------
if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  PROMISE_TEXT=$(echo "$LAST_OUTPUT" | perl -0777 -pe 's/.*?<promise>(.*?)<\/promise>.*/$1/s; s/^\s+|\s+$//g; s/\s+/ /g' 2>/dev/null || echo "")

  if [[ -n "$PROMISE_TEXT" ]] && [[ "$PROMISE_TEXT" = "$COMPLETION_PROMISE" ]]; then
    echo "✅ Algo loop complete: <promise>$COMPLETION_PROMISE</promise>"
    echo "   Topic: $TOPIC"
    echo "   Total iterations: $GLOBAL_ITERATION"
    echo "   Final phase: $CURRENT_PHASE ($PHASE_NAME)"
    echo "   Algorithms: found=$ALGORITHMS_FOUND invented=$ALGORITHMS_INVENTED implemented=$ALGORITHMS_IMPLEMENTED"
    echo "   Benchmarks run: $BENCHMARKS_RUN | Innovation cycles: $INNOVATION_CYCLES/$MAX_INNOVATION_CYCLES"
    echo "   Output: $OUTPUT_DIR/"
    rm "$STATE_FILE"
    exit 0
  fi
fi

# ---------------------------------------------------------------------------
# Detect phase completion markers and update counters from output
# ---------------------------------------------------------------------------
PHASE_ADVANCED=false
FORCED_ADVANCE=false

# Check for explicit phase completion marker: <!-- PHASE_N_COMPLETE -->
if echo "$LAST_OUTPUT" | grep -qE "<!--\s*PHASE_${CURRENT_PHASE}_COMPLETE\s*-->"; then
  PHASE_ADVANCED=true
fi

# Update counters from output markers (if present)
NEW_ALGORITHMS_FOUND=$(echo "$LAST_OUTPUT" | grep -oP '<!--\s*ALGORITHMS_FOUND:(\d+)\s*-->' | grep -oP '\d+' | tail -1 || echo "")
NEW_ALGORITHMS_INVENTED=$(echo "$LAST_OUTPUT" | grep -oP '<!--\s*ALGORITHMS_INVENTED:(\d+)\s*-->' | grep -oP '\d+' | tail -1 || echo "")
NEW_ALGORITHMS_IMPLEMENTED=$(echo "$LAST_OUTPUT" | grep -oP '<!--\s*ALGORITHMS_IMPLEMENTED:(\d+)\s*-->' | grep -oP '\d+' | tail -1 || echo "")
NEW_BENCHMARKS_RUN=$(echo "$LAST_OUTPUT" | grep -oP '<!--\s*BENCHMARKS_RUN:(\d+)\s*-->' | grep -oP '\d+' | tail -1 || echo "")
NEW_INNOVATION_CYCLE=$(echo "$LAST_OUTPUT" | grep -oP '<!--\s*INNOVATION_CYCLE:(\d+)\s*-->' | grep -oP '\d+' | tail -1 || echo "")

[[ -n "$NEW_ALGORITHMS_FOUND" ]] && ALGORITHMS_FOUND="$NEW_ALGORITHMS_FOUND"
[[ -n "$NEW_ALGORITHMS_INVENTED" ]] && ALGORITHMS_INVENTED="$NEW_ALGORITHMS_INVENTED"
[[ -n "$NEW_ALGORITHMS_IMPLEMENTED" ]] && ALGORITHMS_IMPLEMENTED="$NEW_ALGORITHMS_IMPLEMENTED"
[[ -n "$NEW_BENCHMARKS_RUN" ]] && BENCHMARKS_RUN="$NEW_BENCHMARKS_RUN"
[[ -n "$NEW_INNOVATION_CYCLE" ]] && INNOVATION_CYCLES="$NEW_INNOVATION_CYCLE"

# ---------------------------------------------------------------------------
# Quality gate: check if phase completion passed quality evaluation
# ---------------------------------------------------------------------------
QUALITY_FAILED=false

if [[ "$PHASE_ADVANCED" == "true" ]]; then
  HAS_GATE=${PHASE_QUALITY_GATE[$CURRENT_PHASE]:-0}

  if [[ "$HAS_GATE" == "1" ]]; then
    # Check for quality score in output: <!-- QUALITY_SCORE:0.75 --> <!-- QUALITY_PASSED:1 -->
    QUALITY_SCORE=$(echo "$LAST_OUTPUT" | grep -oP '<!--\s*QUALITY_SCORE:([\d.]+)\s*-->' | grep -oP '[\d.]+' | tail -1 || echo "")
    QUALITY_PASSED=$(echo "$LAST_OUTPUT" | grep -oP '<!--\s*QUALITY_PASSED:(\d)\s*-->' | grep -oP '\d' | tail -1 || echo "")

    if [[ -n "$QUALITY_PASSED" ]] && [[ "$QUALITY_PASSED" == "0" ]]; then
      # Quality gate FAILED — repeat this phase
      PHASE_ADVANCED=false
      QUALITY_FAILED=true
    fi
  fi
fi

# Check for phase timeout (forced advancement)
CURRENT_PHASE_MAX=${PHASE_MAX_ITER[$CURRENT_PHASE]:-3}
if [[ "$PHASE_ADVANCED" != "true" ]] && [[ "$QUALITY_FAILED" != "true" ]] && [[ $PHASE_ITERATION -ge $CURRENT_PHASE_MAX ]]; then
  PHASE_ADVANCED=true
  FORCED_ADVANCE=true
fi

# ---------------------------------------------------------------------------
# HARD BLOCKS — verify mandatory work BEFORE allowing phase advancement
# The agent CANNOT bypass these. No evidence = no advancement. Period.
# ---------------------------------------------------------------------------
HARD_BLOCK=false
HARD_BLOCK_MSG=""

if [[ "$PHASE_ADVANCED" == "true" ]]; then
  # Resolve OUTPUT_DIR to absolute path for reliable DB access
  if [[ "$OUTPUT_DIR" == ./* ]] || [[ "$OUTPUT_DIR" != /* ]]; then
    ABS_OUTPUT_DIR="$(pwd)/$OUTPUT_DIR"
  else
    ABS_OUTPUT_DIR="$OUTPUT_DIR"
  fi
  DB_PATH="$ABS_OUTPUT_DIR/algo.db"

  # HARD BLOCK 1: Phase 1→2 — algorithms table must have entries with components NOT NULL
  if [[ $CURRENT_PHASE -eq 1 ]] && [[ "$HARD_BLOCK" != "true" ]]; then
    if [[ -f "$DB_PATH" ]]; then
      DECOMPOSED_COUNT=$(python3 -c "import sqlite3; db=sqlite3.connect('$DB_PATH'); print(db.execute(\"SELECT COUNT(*) FROM algorithms WHERE components IS NOT NULL\").fetchone()[0])" 2>/dev/null || echo "0")
    else
      DECOMPOSED_COUNT=0
    fi
    if [[ "$DECOMPOSED_COUNT" -eq 0 ]]; then
      HARD_BLOCK=true
      HARD_BLOCK_MSG="🚫 HARD BLOCK: Phase 1 (explore) cannot advance — algorithms table has 0 entries with components (DB: $DB_PATH). You MUST decompose discovered algorithms into their components before advancing. Store algorithm entries with 'components' field populated."
    fi
  fi

  # HARD BLOCK 2: Phase 2→3 — algorithms table must have entries with category='invented'
  # Skipped in standard mode (inventions not required)
  if [[ $CURRENT_PHASE -eq 2 ]] && [[ "$MODE" != "standard" ]] && [[ "$HARD_BLOCK" != "true" ]]; then
    if [[ -f "$DB_PATH" ]]; then
      INVENTED_COUNT=$(python3 -c "import sqlite3; db=sqlite3.connect('$DB_PATH'); print(db.execute(\"SELECT COUNT(*) FROM algorithms WHERE category='invented'\").fetchone()[0])" 2>/dev/null || echo "0")
    else
      INVENTED_COUNT=0
    fi
    if [[ "$INVENTED_COUNT" -eq 0 ]]; then
      HARD_BLOCK=true
      HARD_BLOCK_MSG="🚫 HARD BLOCK: Phase 2 (ideate) cannot advance — algorithms table has 0 entries with category='invented' (DB: $DB_PATH). You MUST invent at least one novel algorithm before advancing. Store algorithm entries with category='invented'."
    fi
  fi

  # HARD BLOCK 3: Phase 3→4 — implementations table must have entries with status='tests_pass'
  if [[ $CURRENT_PHASE -eq 3 ]] && [[ "$HARD_BLOCK" != "true" ]]; then
    if [[ -f "$DB_PATH" ]]; then
      TESTS_PASS_COUNT=$(python3 -c "import sqlite3; db=sqlite3.connect('$DB_PATH'); print(db.execute(\"SELECT COUNT(*) FROM implementations WHERE status='tests_pass'\").fetchone()[0])" 2>/dev/null || echo "0")
    else
      TESTS_PASS_COUNT=0
    fi
    if [[ "$TESTS_PASS_COUNT" -eq 0 ]]; then
      HARD_BLOCK=true
      HARD_BLOCK_MSG="🚫 HARD BLOCK: Phase 3 (implement) cannot advance — implementations table has 0 entries with status='tests_pass' (DB: $DB_PATH). You MUST implement algorithms with passing tests before advancing. Store implementation entries with status='tests_pass'."
    fi
  fi

  # HARD BLOCK 4: Phase 4→5 — benchmark_results table must have entries
  if [[ $CURRENT_PHASE -eq 4 ]] && [[ "$HARD_BLOCK" != "true" ]]; then
    if [[ -f "$DB_PATH" ]]; then
      BENCHMARK_COUNT=$(python3 -c "import sqlite3; db=sqlite3.connect('$DB_PATH'); print(db.execute('SELECT COUNT(*) FROM benchmark_results').fetchone()[0])" 2>/dev/null || echo "0")
    else
      BENCHMARK_COUNT=0
    fi
    if [[ "$BENCHMARK_COUNT" -eq 0 ]]; then
      HARD_BLOCK=true
      HARD_BLOCK_MSG="🚫 HARD BLOCK: Phase 4 (benchmark) cannot advance — benchmark_results table has 0 entries (DB: $DB_PATH). You MUST execute benchmarks and store results before advancing."
    fi
  fi

  # HARD BLOCK 5: Phase 5→6 — complexity_analysis table must have entries
  if [[ $CURRENT_PHASE -eq 5 ]] && [[ "$HARD_BLOCK" != "true" ]]; then
    if [[ -f "$DB_PATH" ]]; then
      COMPLEXITY_COUNT=$(python3 -c "import sqlite3; db=sqlite3.connect('$DB_PATH'); print(db.execute('SELECT COUNT(*) FROM complexity_analysis').fetchone()[0])" 2>/dev/null || echo "0")
    else
      COMPLEXITY_COUNT=0
    fi
    if [[ "$COMPLEXITY_COUNT" -eq 0 ]]; then
      HARD_BLOCK=true
      HARD_BLOCK_MSG="🚫 HARD BLOCK: Phase 5 (validate) cannot advance — complexity_analysis table has 0 entries (DB: $DB_PATH). You MUST analyze algorithm complexity and store results before advancing."
    fi
  fi

  # HARD BLOCK 6: Phase 6→7 — invention_log table must have entries with outcome NOT NULL
  if [[ $CURRENT_PHASE -eq 6 ]] && [[ "$HARD_BLOCK" != "true" ]]; then
    if [[ -f "$DB_PATH" ]]; then
      OUTCOME_COUNT=$(python3 -c "import sqlite3; db=sqlite3.connect('$DB_PATH'); print(db.execute(\"SELECT COUNT(*) FROM invention_log WHERE outcome IS NOT NULL\").fetchone()[0])" 2>/dev/null || echo "0")
    else
      OUTCOME_COUNT=0
    fi
    if [[ "$OUTCOME_COUNT" -eq 0 ]]; then
      HARD_BLOCK=true
      HARD_BLOCK_MSG="🚫 HARD BLOCK: Phase 6 (analyze) cannot advance — invention_log table has 0 entries with outcome (DB: $DB_PATH). You MUST record invention outcomes before advancing. Store entries in invention_log with 'outcome' field populated."
    fi
  fi

  # If hard blocked, prevent advancement and repeat the phase
  if [[ "$HARD_BLOCK" == "true" ]]; then
    PHASE_ADVANCED=false
    FORCED_ADVANCE=false
    QUALITY_FAILED=false
    echo "🚫 HARD BLOCK ACTIVATED — Phase $CURRENT_PHASE cannot advance. DB: $DB_PATH" >&2
  fi
fi

# ---------------------------------------------------------------------------
# LOOP-BACK MECHANISM — analyze → ideate for innovation cycles
# When Phase 6 (analyze) outputs <!-- LOOP_BACK_TO_IDEATE -->, loop back
# to Phase 2 (ideate) if innovation cycles remain.
# ---------------------------------------------------------------------------
LOOP_BACK=false

if [[ "$PHASE_ADVANCED" == "true" ]] && [[ $CURRENT_PHASE -eq 6 ]]; then
  if echo "$LAST_OUTPUT" | grep -qE "<!--\s*LOOP_BACK_TO_IDEATE\s*-->"; then
    if [[ $INNOVATION_CYCLES -lt $MAX_INNOVATION_CYCLES ]]; then
      LOOP_BACK=true
      CURRENT_PHASE=2
      PHASE_NAME="ideate"
      PHASE_ITERATION=0  # Will be incremented to 1 below
      INNOVATION_CYCLES=$((INNOVATION_CYCLES + 1))
      PHASE_ADVANCED=false  # Prevent normal advancement logic below
    fi
    # If innovation_cycles >= max_innovation_cycles, fall through to normal
    # advancement which will move to Phase 7 (report)
  fi
fi

# ---------------------------------------------------------------------------
# Advance phase if needed
# ---------------------------------------------------------------------------
MAX_PHASE=7

if [[ "$PHASE_ADVANCED" == "true" ]]; then
  if [[ $CURRENT_PHASE -ge $MAX_PHASE ]]; then
    echo "🛑 Algo loop: All $MAX_PHASE phases complete but no completion promise detected."
    echo "   Topic: $TOPIC"
    echo "   Algorithms: found=$ALGORITHMS_FOUND invented=$ALGORITHMS_INVENTED implemented=$ALGORITHMS_IMPLEMENTED"
    echo "   Benchmarks run: $BENCHMARKS_RUN | Innovation cycles: $INNOVATION_CYCLES/$MAX_INNOVATION_CYCLES"
    echo "   Output should be in: $OUTPUT_DIR/"
    rm "$STATE_FILE"
    exit 0
  fi

  CURRENT_PHASE=$((CURRENT_PHASE + 1))
  PHASE_NAME="${PHASE_NAMES[$CURRENT_PHASE]}"
  PHASE_ITERATION=0  # Will be incremented to 1 below

  # Standard mode: auto-skip Phase 2 (ideate) — advance directly to Phase 3
  if [[ "$MODE" == "standard" ]] && [[ $CURRENT_PHASE -eq 2 ]]; then
    CURRENT_PHASE=3
    PHASE_NAME="${PHASE_NAMES[$CURRENT_PHASE]}"
  fi
fi

# ---------------------------------------------------------------------------
# Increment counters
# ---------------------------------------------------------------------------
NEXT_GLOBAL=$((GLOBAL_ITERATION + 1))
NEXT_PHASE_ITER=$((PHASE_ITERATION + 1))

# ---------------------------------------------------------------------------
# Extract prompt text (everything after second ---)
# ---------------------------------------------------------------------------
PROMPT_TEXT=$(awk '/^---$/{i++; next} i>=2' "$STATE_FILE")

if [[ -z "$PROMPT_TEXT" ]]; then
  echo "⚠️  Algo loop: No prompt text found in state file" >&2
  rm "$STATE_FILE"
  exit 0
fi

# ---------------------------------------------------------------------------
# Update state file atomically
# ---------------------------------------------------------------------------
TEMP_FILE="${STATE_FILE}.tmp.$$"
cat > "$TEMP_FILE" <<EOF
---
active: true
topic: "$TOPIC"
current_phase: $CURRENT_PHASE
phase_name: "$PHASE_NAME"
phase_iteration: $NEXT_PHASE_ITER
global_iteration: $NEXT_GLOBAL
max_global_iterations: $MAX_GLOBAL_ITERATIONS
completion_promise: "$(echo "$COMPLETION_PROMISE" | sed 's/"/\\"/g')"
started_at: "$(parse_field "started_at")"
output_dir: "$OUTPUT_DIR"
mode: "$MODE"
language: "$LANGUAGE"
codebase_path: "$CODEBASE_PATH"
innovation_cycles: $INNOVATION_CYCLES
max_innovation_cycles: $MAX_INNOVATION_CYCLES
algorithms_found: $ALGORITHMS_FOUND
algorithms_invented: $ALGORITHMS_INVENTED
algorithms_implemented: $ALGORITHMS_IMPLEMENTED
benchmarks_run: $BENCHMARKS_RUN
---

$PROMPT_TEXT
EOF
mv "$TEMP_FILE" "$STATE_FILE"

# ---------------------------------------------------------------------------
# Build system message with phase context
# ---------------------------------------------------------------------------
PHASE_MAX_FOR_CURRENT=${PHASE_MAX_ITER[$CURRENT_PHASE]:-3}

SYSTEM_MSG="🔬 Algo Loop | Phase $CURRENT_PHASE/$MAX_PHASE: $PHASE_NAME | Phase iter $NEXT_PHASE_ITER/$PHASE_MAX_FOR_CURRENT | Global iter $NEXT_GLOBAL"
SYSTEM_MSG="$SYSTEM_MSG | Mode: $MODE | Lang: $LANGUAGE"
SYSTEM_MSG="$SYSTEM_MSG | Algorithms: found=$ALGORITHMS_FOUND invented=$ALGORITHMS_INVENTED implemented=$ALGORITHMS_IMPLEMENTED"
SYSTEM_MSG="$SYSTEM_MSG | Benchmarks: $BENCHMARKS_RUN | Innovation cycles: $INNOVATION_CYCLES/$MAX_INNOVATION_CYCLES"

if [[ "$FORCED_ADVANCE" == "true" ]]; then
  SYSTEM_MSG="$SYSTEM_MSG | ⚠️ Previous phase timed out — forced advancement to $PHASE_NAME"
fi

if [[ "$QUALITY_FAILED" == "true" ]]; then
  SYSTEM_MSG="$SYSTEM_MSG | ❌ Quality gate FAILED — repeating phase. Review evaluator feedback and improve output."
fi

if [[ "$HARD_BLOCK" == "true" ]]; then
  SYSTEM_MSG="$SYSTEM_MSG | $HARD_BLOCK_MSG"
fi

if [[ "$LOOP_BACK" == "true" ]]; then
  SYSTEM_MSG="$SYSTEM_MSG | 🔄 LOOP-BACK: Returning to ideate phase for innovation cycle $INNOVATION_CYCLES/$MAX_INNOVATION_CYCLES"
fi

if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  SYSTEM_MSG="$SYSTEM_MSG | To finish: <promise>$COMPLETION_PROMISE</promise> (ONLY when TRUE)"
fi

# ---------------------------------------------------------------------------
# Block exit and re-inject prompt
# ---------------------------------------------------------------------------
jq -n \
  --arg prompt "$PROMPT_TEXT" \
  --arg msg "$SYSTEM_MSG" \
  '{
    "decision": "block",
    "reason": $prompt,
    "systemMessage": $msg
  }'

exit 0
