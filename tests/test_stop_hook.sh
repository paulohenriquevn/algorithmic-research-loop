#!/bin/bash

# Unit tests for the algorithmic research loop stop hook.
# Tests state file parsing, phase advancement, quality gates, hard blocks,
# loop-back mechanism, counter updates, and mode-specific behavior.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/../hooks/stop-hook.sh"

PASS=0
FAIL=0
TOTAL=0

# Colors
GREEN="\033[0;32m"
RED="\033[0;31m"
RESET="\033[0m"

assert_exit_code() {
  local test_name="$1"
  local expected="$2"
  local actual="$3"
  TOTAL=$((TOTAL + 1))
  if [[ "$actual" -eq "$expected" ]]; then
    echo -e "  ${GREEN}PASS${RESET} $test_name"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}FAIL${RESET} $test_name (expected exit $expected, got $actual)"
    FAIL=$((FAIL + 1))
  fi
}

assert_contains() {
  local test_name="$1"
  local needle="$2"
  local haystack="$3"
  TOTAL=$((TOTAL + 1))
  if echo "$haystack" | grep -q "$needle"; then
    echo -e "  ${GREEN}PASS${RESET} $test_name"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}FAIL${RESET} $test_name (expected to contain: '$needle')"
    FAIL=$((FAIL + 1))
  fi
}

assert_not_contains() {
  local test_name="$1"
  local needle="$2"
  local haystack="$3"
  TOTAL=$((TOTAL + 1))
  if ! echo "$haystack" | grep -q "$needle"; then
    echo -e "  ${GREEN}PASS${RESET} $test_name"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}FAIL${RESET} $test_name (expected NOT to contain: '$needle')"
    FAIL=$((FAIL + 1))
  fi
}

assert_state_field() {
  local test_name="$1"
  local state_file="$2"
  local field="$3"
  local expected="$4"
  TOTAL=$((TOTAL + 1))

  local actual
  actual=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$state_file" | grep "^${field}:" | sed "s/${field}: *//" | sed 's/^"\(.*\)"$/\1/')

  if [[ "$actual" == "$expected" ]]; then
    echo -e "  ${GREEN}PASS${RESET} $test_name"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}FAIL${RESET} $test_name (expected '$field' = '$expected', got '$actual')"
    FAIL=$((FAIL + 1))
  fi
}

# ---------------------------------------------------------------------------
# Setup / teardown
# ---------------------------------------------------------------------------
TMPDIR_BASE=$(mktemp -d)
cleanup() { rm -rf "$TMPDIR_BASE"; }
trap cleanup EXIT

setup_test() {
  local test_dir="$TMPDIR_BASE/$1"
  mkdir -p "$test_dir/.claude"
  echo "$test_dir"
}

create_state_file() {
  local dir="$1"
  local phase="${2:-1}"
  local phase_iter="${3:-1}"
  local global_iter="${4:-1}"
  local max_iter="${5:-60}"
  local promise="${6:-ALGORITHM RESEARCH COMPLETE}"
  local mode="${7:-innovation}"
  local language="${8:-python}"

  local phase_name="explore"
  case "$phase" in
    1) phase_name="explore" ;;
    2) phase_name="ideate" ;;
    3) phase_name="implement" ;;
    4) phase_name="benchmark" ;;
    5) phase_name="validate" ;;
    6) phase_name="analyze" ;;
    7) phase_name="report" ;;
  esac

  mkdir -p "$dir/algo-output"

  cat > "$dir/.claude/algo-loop.local.md" <<EOF
---
active: true
topic: "Test Topic"
current_phase: $phase
phase_name: "$phase_name"
phase_iteration: $phase_iter
global_iteration: $global_iter
max_global_iterations: $max_iter
completion_promise: "$promise"
started_at: "2026-03-28T10:00:00Z"
output_dir: "./algo-output"
mode: "$mode"
language: "$language"
codebase_path: ""
innovation_cycles: 0
max_innovation_cycles: 3
algorithms_found: 0
algorithms_invented: 0
algorithms_implemented: 0
benchmarks_run: 0
---

Algorithm research prompt text here
EOF
}

# Helper to set specific field in state file
set_state_field() {
  local dir="$1"
  local field="$2"
  local value="$3"
  local state="$dir/.claude/algo-loop.local.md"
  sed -i "s/^${field}:.*/${field}: ${value}/" "$state"
}

init_test_db() {
  local dir="$1"
  mkdir -p "$dir/algo-output"
  python3 "$SCRIPT_DIR/../scripts/algo_database.py" init --db-path "$dir/algo-output/algo.db" > /dev/null 2>&1
}

add_test_algorithm() {
  local dir="$1"
  local category="${2:-known}"
  local with_components="${3:-true}"
  local components='{}'
  if [[ "$with_components" == "true" ]]; then
    components='{"paradigm":"divide_conquer","data_structure":"array"}'
  fi
  python3 "$SCRIPT_DIR/../scripts/algo_database.py" add-algorithm --db-path "$dir/algo-output/algo.db" \
    --algo-json "{\"id\":\"test-algo-$RANDOM\",\"name\":\"Test Algo\",\"category\":\"$category\",\"description\":\"Test\",\"components\":$components,\"status\":\"proposed\"}" > /dev/null 2>&1
}

add_test_implementation() {
  local dir="$1"
  local status="${2:-tests_pass}"
  local algo_id
  algo_id=$(python3 -c "import sqlite3; db=sqlite3.connect('$dir/algo-output/algo.db'); print(db.execute('SELECT id FROM algorithms LIMIT 1').fetchone()[0])" 2>/dev/null)
  python3 "$SCRIPT_DIR/../scripts/algo_database.py" add-implementation --db-path "$dir/algo-output/algo.db" \
    --algo-id "$algo_id" --impl-json "{\"file_path\":\"test.py\",\"status\":\"$status\"}" > /dev/null 2>&1
}

add_test_benchmark_result() {
  local dir="$1"
  local algo_id
  algo_id=$(python3 -c "import sqlite3; db=sqlite3.connect('$dir/algo-output/algo.db'); print(db.execute('SELECT id FROM algorithms LIMIT 1').fetchone()[0])" 2>/dev/null)
  python3 "$SCRIPT_DIR/../scripts/algo_database.py" add-benchmark --db-path "$dir/algo-output/algo.db" \
    --benchmark-json '{"id":"bench-1","name":"Test Bench","description":"Test","input_sizes":[100],"metrics":["time_ms"]}' > /dev/null 2>&1 || true
  python3 "$SCRIPT_DIR/../scripts/algo_database.py" add-benchmark-result --db-path "$dir/algo-output/algo.db" \
    --result-json "{\"benchmark_id\":\"bench-1\",\"algorithm_id\":\"$algo_id\",\"input_size\":100,\"metric\":\"time_ms\",\"value\":1.5}" > /dev/null 2>&1
}

add_test_complexity() {
  local dir="$1"
  local algo_id
  algo_id=$(python3 -c "import sqlite3; db=sqlite3.connect('$dir/algo-output/algo.db'); print(db.execute('SELECT id FROM algorithms LIMIT 1').fetchone()[0])" 2>/dev/null)
  python3 "$SCRIPT_DIR/../scripts/algo_database.py" add-complexity --db-path "$dir/algo-output/algo.db" \
    --complexity-json "{\"algorithm_id\":\"$algo_id\",\"analysis_type\":\"theoretical\",\"metric\":\"time\",\"complexity_class\":\"O(n log n)\"}" > /dev/null 2>&1
}

add_test_invention_outcome() {
  local dir="$1"
  python3 "$SCRIPT_DIR/../scripts/algo_database.py" add-invention --db-path "$dir/algo-output/algo.db" \
    --invention-json '{"cycle":1,"strategy":"mutation","hypothesis":"Test hypothesis","outcome":"success","result_summary":"It worked"}' > /dev/null 2>&1
}

create_transcript() {
  local dir="$1"
  local assistant_text="${2:-I finished some work.}"
  local transcript_file="$dir/transcript.jsonl"

  cat > "$transcript_file" <<EOF
{"role":"user","message":{"content":[{"type":"text","text":"Start research"}]}}
{"role":"assistant","message":{"content":[{"type":"text","text":"$assistant_text"}]}}
EOF
  echo "$transcript_file"
}

run_hook() {
  local dir="$1"
  local transcript="$2"
  cd "$dir"
  echo '{"transcript_path":"'"$transcript"'"}' | bash "$HOOK_SCRIPT" 2>&1 || true
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
echo "=== Algo Stop Hook Tests ==="
echo ""

# ---- Test: No state file allows exit ----
echo "Test: No state file allows exit"
TEST_DIR=$(setup_test "no_state")
TRANSCRIPT=$(create_transcript "$TEST_DIR")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
EXIT_CODE=$?
assert_exit_code "exit code is 0" 0 $EXIT_CODE
assert_not_contains "no block decision" "block" "$OUTPUT"

# ---- Test: State file parsing reads all fields ----
echo ""
echo "Test: State file parsing reads all fields correctly"
TEST_DIR=$(setup_test "parsing")
create_state_file "$TEST_DIR" 3 2 15 60 "ALGORITHM RESEARCH COMPLETE" "innovation" "python"
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
add_test_implementation "$TEST_DIR" "tests_pass"
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Working on implementation.")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_contains "blocks exit" '"decision": "block"' "$OUTPUT"
assert_contains "has system message" "systemMessage" "$OUTPUT"
assert_contains "shows phase 3" "Phase 3" "$OUTPUT"

# ---- Test: Phase advancement on PHASE_N_COMPLETE marker ----
echo ""
echo "Test: Phase advancement on PHASE_N_COMPLETE marker"
TEST_DIR=$(setup_test "phase_advance")
create_state_file "$TEST_DIR" 1 1 1
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Survey done. <!-- PHASE_1_COMPLETE -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_contains "blocks exit" '"decision": "block"' "$OUTPUT"
assert_state_field "phase advanced to 2" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "2"
assert_state_field "phase name is ideate" "$TEST_DIR/.claude/algo-loop.local.md" "phase_name" "ideate"

# ---- Test: Quality gate blocks advancement when QUALITY_PASSED:0 ----
echo ""
echo "Test: Quality gate blocks advancement when QUALITY_PASSED:0"
TEST_DIR=$(setup_test "quality_fail")
create_state_file "$TEST_DIR" 2 1 5
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "invented"
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Done ideating. <!-- PHASE_2_COMPLETE --> <!-- QUALITY_SCORE:0.45 --> <!-- QUALITY_PASSED:0 -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_state_field "phase stays at 2" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "2"
assert_contains "quality failed msg" "Quality gate FAILED" "$OUTPUT"

# ---- Test: Counter updates from markers ----
echo ""
echo "Test: Counter updates from output markers"
TEST_DIR=$(setup_test "counters")
create_state_file "$TEST_DIR" 1 1 1
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Found algorithms. <!-- ALGORITHMS_FOUND:5 --> <!-- ALGORITHMS_INVENTED:2 --> <!-- ALGORITHMS_IMPLEMENTED:1 --> <!-- BENCHMARKS_RUN:3 -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_state_field "algorithms_found updated" "$TEST_DIR/.claude/algo-loop.local.md" "algorithms_found" "5"
assert_state_field "algorithms_invented updated" "$TEST_DIR/.claude/algo-loop.local.md" "algorithms_invented" "2"
assert_state_field "algorithms_implemented updated" "$TEST_DIR/.claude/algo-loop.local.md" "algorithms_implemented" "1"
assert_state_field "benchmarks_run updated" "$TEST_DIR/.claude/algo-loop.local.md" "benchmarks_run" "3"

# ---- Test: Hard block Phase 1->2 requires decomposed algorithms ----
echo ""
echo "Test: Hard block Phase 1->2 requires decomposed algorithms"
TEST_DIR=$(setup_test "hard_block_1")
create_state_file "$TEST_DIR" 1 1 1
init_test_db "$TEST_DIR"
# Do NOT add any algorithm with components
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Survey complete. <!-- PHASE_1_COMPLETE -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_state_field "phase stays at 1" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "1"
assert_contains "hard block message" "HARD BLOCK" "$OUTPUT"

# ---- Test: Hard block Phase 2->3 requires inventions ----
echo ""
echo "Test: Hard block Phase 2->3 requires inventions (innovation mode)"
TEST_DIR=$(setup_test "hard_block_2")
create_state_file "$TEST_DIR" 2 1 5 60 "ALGORITHM RESEARCH COMPLETE" "innovation"
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
# Do NOT add invented algorithm
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Ideation complete. <!-- PHASE_2_COMPLETE --> <!-- QUALITY_PASSED:1 -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_state_field "phase stays at 2" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "2"
assert_contains "hard block inventions" "HARD BLOCK" "$OUTPUT"

# ---- Test: Hard block Phase 3->4 requires passing tests ----
echo ""
echo "Test: Hard block Phase 3->4 requires passing tests"
TEST_DIR=$(setup_test "hard_block_3")
create_state_file "$TEST_DIR" 3 1 10
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
add_test_implementation "$TEST_DIR" "draft"  # draft, not tests_pass
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Implementation done. <!-- PHASE_3_COMPLETE --> <!-- QUALITY_PASSED:1 -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_state_field "phase stays at 3" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "3"
assert_contains "hard block tests" "HARD BLOCK" "$OUTPUT"

# ---- Test: Hard block Phase 4->5 requires benchmark results ----
echo ""
echo "Test: Hard block Phase 4->5 requires benchmark results"
TEST_DIR=$(setup_test "hard_block_4")
create_state_file "$TEST_DIR" 4 1 15
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
# Do NOT add benchmark results
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Benchmarking done. <!-- PHASE_4_COMPLETE --> <!-- QUALITY_PASSED:1 -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_state_field "phase stays at 4" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "4"
assert_contains "hard block benchmarks" "HARD BLOCK" "$OUTPUT"

# ---- Test: Hard block Phase 5->6 requires complexity analysis ----
echo ""
echo "Test: Hard block Phase 5->6 requires complexity analysis"
TEST_DIR=$(setup_test "hard_block_5")
create_state_file "$TEST_DIR" 5 1 20
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
# Do NOT add complexity analysis
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Validation done. <!-- PHASE_5_COMPLETE --> <!-- QUALITY_PASSED:1 -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_state_field "phase stays at 5" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "5"
assert_contains "hard block complexity" "HARD BLOCK" "$OUTPUT"

# ---- Test: Hard block Phase 6->7 requires invention outcomes ----
echo ""
echo "Test: Hard block Phase 6->7 requires invention outcomes"
TEST_DIR=$(setup_test "hard_block_6")
create_state_file "$TEST_DIR" 6 1 25
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
# Do NOT add invention with outcome
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Analysis done. <!-- PHASE_6_COMPLETE --> <!-- QUALITY_PASSED:1 -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_state_field "phase stays at 6" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "6"
assert_contains "hard block outcomes" "HARD BLOCK" "$OUTPUT"

# ---- Test: Loop-back LOOP_BACK_TO_IDEATE resets to phase 2 ----
echo ""
echo "Test: Loop-back LOOP_BACK_TO_IDEATE resets to phase 2"
TEST_DIR=$(setup_test "loop_back")
create_state_file "$TEST_DIR" 6 1 25
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
add_test_invention_outcome "$TEST_DIR"
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Analysis reveals opportunities. <!-- PHASE_6_COMPLETE --> <!-- QUALITY_PASSED:1 --> <!-- LOOP_BACK_TO_IDEATE -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_state_field "phase reset to 2" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "2"
assert_state_field "phase name is ideate" "$TEST_DIR/.claude/algo-loop.local.md" "phase_name" "ideate"
assert_contains "loop back message" "LOOP-BACK" "$OUTPUT"

# ---- Test: Loop-back respects max_innovation_cycles ----
echo ""
echo "Test: Loop-back respects max_innovation_cycles"
TEST_DIR=$(setup_test "loop_back_max")
create_state_file "$TEST_DIR" 6 1 30
set_state_field "$TEST_DIR" "innovation_cycles" "3"
set_state_field "$TEST_DIR" "max_innovation_cycles" "3"
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
add_test_invention_outcome "$TEST_DIR"
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Analysis done. <!-- PHASE_6_COMPLETE --> <!-- QUALITY_PASSED:1 --> <!-- LOOP_BACK_TO_IDEATE -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
# Should advance to phase 7 instead of looping back
assert_state_field "phase advances to 7" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "7"
assert_not_contains "no loop back" "LOOP-BACK" "$OUTPUT"

# ---- Test: Standard mode skips Phase 2 (ideate) ----
echo ""
echo "Test: Standard mode skips Phase 2 (ideate)"
TEST_DIR=$(setup_test "standard_skip")
create_state_file "$TEST_DIR" 1 1 1 60 "ALGORITHM RESEARCH COMPLETE" "standard"
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Survey done. <!-- PHASE_1_COMPLETE -->")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
# Should skip phase 2 and go straight to phase 3
assert_state_field "phase skips to 3" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "3"
assert_state_field "phase name is implement" "$TEST_DIR/.claude/algo-loop.local.md" "phase_name" "implement"

# ---- Test: Global iteration limit ----
echo ""
echo "Test: Global iteration limit reached allows exit"
TEST_DIR=$(setup_test "max_iter")
create_state_file "$TEST_DIR" 3 1 60 60
TRANSCRIPT=$(create_transcript "$TEST_DIR")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_contains "reports max iterations" "Max global iterations" "$OUTPUT"

# ---- Test: Completion promise detection ----
echo ""
echo "Test: Completion promise detection allows exit"
TEST_DIR=$(setup_test "promise")
create_state_file "$TEST_DIR" 7 1 30 60 "ALGORITHM RESEARCH COMPLETE"
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Research is finished. <promise>ALGORITHM RESEARCH COMPLETE</promise>")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_contains "reports completion" "Algo loop complete" "$OUTPUT"

# ---- Test: Forced advancement on phase timeout ----
echo ""
echo "Test: Forced advancement on phase timeout"
TEST_DIR=$(setup_test "timeout")
create_state_file "$TEST_DIR" 1 3 10   # phase_iter=3, which is >= PHASE_MAX_ITER[1]=3
init_test_db "$TEST_DIR"
add_test_algorithm "$TEST_DIR" "known" "true"
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Still exploring...")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_state_field "phase forced to 2" "$TEST_DIR/.claude/algo-loop.local.md" "current_phase" "2"
assert_contains "forced advance msg" "forced advancement" "$OUTPUT"

# ---- Test: Normal iteration blocks exit and re-injects prompt ----
echo ""
echo "Test: Normal iteration blocks exit and re-injects prompt"
TEST_DIR=$(setup_test "normal")
create_state_file "$TEST_DIR" 1 1 1
init_test_db "$TEST_DIR"
TRANSCRIPT=$(create_transcript "$TEST_DIR" "Searching for algorithms.")
OUTPUT=$(run_hook "$TEST_DIR" "$TRANSCRIPT")
assert_contains "blocks exit" '"decision": "block"' "$OUTPUT"
assert_contains "contains prompt" "Algorithm research prompt text here" "$OUTPUT"
assert_contains "has system message" "systemMessage" "$OUTPUT"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "=== Results ==="
echo -e "Total: $TOTAL  ${GREEN}Passed: $PASS${RESET}  ${RED}Failed: $FAIL${RESET}"
echo ""

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
exit 0
