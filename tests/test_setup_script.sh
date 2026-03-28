#!/bin/bash

# Unit tests for the algorithmic research loop setup script (setup-algo-loop.sh).
# Tests argument parsing, directory creation, database initialization, and error handling.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETUP_SCRIPT="$SCRIPT_DIR/../scripts/setup-algo-loop.sh"

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

assert_file_exists() {
  local test_name="$1"
  local file_path="$2"
  TOTAL=$((TOTAL + 1))
  if [[ -e "$file_path" ]]; then
    echo -e "  ${GREEN}PASS${RESET} $test_name"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}FAIL${RESET} $test_name (file not found: $file_path)"
    FAIL=$((FAIL + 1))
  fi
}

assert_dir_exists() {
  local test_name="$1"
  local dir_path="$2"
  TOTAL=$((TOTAL + 1))
  if [[ -d "$dir_path" ]]; then
    echo -e "  ${GREEN}PASS${RESET} $test_name"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}FAIL${RESET} $test_name (directory not found: $dir_path)"
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
  mkdir -p "$test_dir"
  echo "$test_dir"
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
echo "=== Setup Script Tests ==="
echo ""

# ---- Test: Creates state file with correct frontmatter ----
echo "Test: Creates state file with correct frontmatter"
TEST_DIR=$(setup_test "state_file")
cd "$TEST_DIR"
OUTPUT=$(bash "$SETUP_SCRIPT" Sorting algorithms for nearly-sorted data --output-dir "$TEST_DIR/algo-output" 2>&1) || true
STATE="$TEST_DIR/.claude/algo-loop.local.md"
assert_file_exists "state file exists" "$STATE"
assert_state_field "active is true" "$STATE" "active" "true"
assert_state_field "topic is set" "$STATE" "topic" "Sorting algorithms for nearly-sorted data"
assert_state_field "current_phase is 1" "$STATE" "current_phase" "1"
assert_state_field "phase_name is explore" "$STATE" "phase_name" "explore"
assert_state_field "phase_iteration is 1" "$STATE" "phase_iteration" "1"
assert_state_field "global_iteration is 1" "$STATE" "global_iteration" "1"
assert_state_field "mode is innovation" "$STATE" "mode" "innovation"
assert_state_field "language is python" "$STATE" "language" "python"
assert_state_field "innovation_cycles is 0" "$STATE" "innovation_cycles" "0"
assert_state_field "algorithms_found is 0" "$STATE" "algorithms_found" "0"

# ---- Test: Creates output directory structure ----
echo ""
echo "Test: Creates output directory structure"
TEST_DIR=$(setup_test "output_dirs")
cd "$TEST_DIR"
bash "$SETUP_SCRIPT" "Graph search" --output-dir "$TEST_DIR/algo-output" > /dev/null 2>&1 || true
assert_dir_exists "algorithms/known dir" "$TEST_DIR/algo-output/algorithms/known"
assert_dir_exists "algorithms/invented dir" "$TEST_DIR/algo-output/algorithms/invented"
assert_dir_exists "algorithms/tests dir" "$TEST_DIR/algo-output/algorithms/tests"
assert_dir_exists "benchmarks/generators dir" "$TEST_DIR/algo-output/benchmarks/generators"
assert_dir_exists "benchmarks/results dir" "$TEST_DIR/algo-output/benchmarks/results"
assert_dir_exists "analysis/curve_fits dir" "$TEST_DIR/algo-output/analysis/curve_fits"
assert_dir_exists "state/meetings dir" "$TEST_DIR/algo-output/state/meetings"
assert_dir_exists "figures dir" "$TEST_DIR/algo-output/figures"

# ---- Test: Initializes database ----
echo ""
echo "Test: Initializes database"
TEST_DIR=$(setup_test "init_db")
cd "$TEST_DIR"
bash "$SETUP_SCRIPT" "Hash table variants" --output-dir "$TEST_DIR/algo-output" > /dev/null 2>&1 || true
assert_file_exists "algo.db exists" "$TEST_DIR/algo-output/algo.db"
# Verify database has tables
TABLE_COUNT=$(python3 -c "import sqlite3; db=sqlite3.connect('$TEST_DIR/algo-output/algo.db'); print(len(db.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()))" 2>/dev/null || echo "0")
TOTAL=$((TOTAL + 1))
if [[ "$TABLE_COUNT" -gt 5 ]]; then
  echo -e "  ${GREEN}PASS${RESET} database has tables ($TABLE_COUNT)"
  PASS=$((PASS + 1))
else
  echo -e "  ${RED}FAIL${RESET} database has tables (expected >5, got $TABLE_COUNT)"
  FAIL=$((FAIL + 1))
fi

# ---- Test: Handles --mode standard ----
echo ""
echo "Test: Handles --mode standard"
TEST_DIR=$(setup_test "mode_standard")
cd "$TEST_DIR"
bash "$SETUP_SCRIPT" "Sorting" --mode standard --output-dir "$TEST_DIR/algo-output" > /dev/null 2>&1 || true
STATE="$TEST_DIR/.claude/algo-loop.local.md"
assert_state_field "mode is standard" "$STATE" "mode" "standard"

# ---- Test: Handles --mode innovation ----
echo ""
echo "Test: Handles --mode innovation"
TEST_DIR=$(setup_test "mode_innovation")
cd "$TEST_DIR"
bash "$SETUP_SCRIPT" "Sorting" --mode innovation --output-dir "$TEST_DIR/algo-output" > /dev/null 2>&1 || true
STATE="$TEST_DIR/.claude/algo-loop.local.md"
assert_state_field "mode is innovation" "$STATE" "mode" "innovation"

# ---- Test: Handles --mode applied ----
echo ""
echo "Test: Handles --mode applied"
TEST_DIR=$(setup_test "mode_applied")
cd "$TEST_DIR"
mkdir -p "$TEST_DIR/fake-codebase"
bash "$SETUP_SCRIPT" "Sorting" --mode applied --codebase "$TEST_DIR/fake-codebase" --output-dir "$TEST_DIR/algo-output" > /dev/null 2>&1 || true
STATE="$TEST_DIR/.claude/algo-loop.local.md"
assert_state_field "mode is applied" "$STATE" "mode" "applied"

# ---- Test: Handles --codebase validates path ----
echo ""
echo "Test: --codebase validates path exists"
TEST_DIR=$(setup_test "codebase_invalid")
cd "$TEST_DIR"
OUTPUT=$(bash "$SETUP_SCRIPT" "Sorting" --codebase "/nonexistent/path/that/does/not/exist" --output-dir "$TEST_DIR/algo-output" 2>&1 || true)
EXIT_CODE=$?
assert_contains "error on invalid codebase" "does not exist" "$OUTPUT"

# ---- Test: Handles --codebase sets mode to applied ----
echo ""
echo "Test: --codebase implies mode=applied"
TEST_DIR=$(setup_test "codebase_mode")
cd "$TEST_DIR"
mkdir -p "$TEST_DIR/my-project"
bash "$SETUP_SCRIPT" "Optimization" --codebase "$TEST_DIR/my-project" --output-dir "$TEST_DIR/algo-output" > /dev/null 2>&1 || true
STATE="$TEST_DIR/.claude/algo-loop.local.md"
assert_state_field "mode set to applied" "$STATE" "mode" "applied"

# ---- Test: Handles --language validation ----
echo ""
echo "Test: --language validation accepts valid languages"
TEST_DIR=$(setup_test "lang_valid")
cd "$TEST_DIR"
bash "$SETUP_SCRIPT" "Sorting" --language rust --output-dir "$TEST_DIR/algo-output" > /dev/null 2>&1 || true
STATE="$TEST_DIR/.claude/algo-loop.local.md"
assert_state_field "language is rust" "$STATE" "language" "rust"

echo ""
echo "Test: --language validation rejects invalid languages"
TEST_DIR=$(setup_test "lang_invalid")
cd "$TEST_DIR"
OUTPUT=$(bash "$SETUP_SCRIPT" "Sorting" --language java --output-dir "$TEST_DIR/algo-output" 2>&1 || true)
assert_contains "error on invalid language" "must be one of" "$OUTPUT"

# ---- Test: Error on missing topic ----
echo ""
echo "Test: Error on missing topic"
TEST_DIR=$(setup_test "no_topic")
cd "$TEST_DIR"
OUTPUT=$(bash "$SETUP_SCRIPT" --output-dir "$TEST_DIR/algo-output" 2>&1 || true)
assert_contains "error message" "No research topic" "$OUTPUT"

# ---- Test: Help flag works ----
echo ""
echo "Test: Help flag works"
TEST_DIR=$(setup_test "help")
cd "$TEST_DIR"
OUTPUT=$(bash "$SETUP_SCRIPT" --help 2>&1 || true)
assert_contains "shows usage" "USAGE" "$OUTPUT"
assert_contains "shows phases" "Explore" "$OUTPUT"
assert_contains "shows modes" "standard" "$OUTPUT"
assert_contains "shows examples" "EXAMPLES" "$OUTPUT"

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
