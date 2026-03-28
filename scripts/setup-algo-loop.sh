#!/bin/bash

# Algorithmic Research Loop - Setup Script
# Creates state file and output directory for the algorithm research pipeline.

set -euo pipefail

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
TOPIC_PARTS=()
MODE="innovation"
CODEBASE_PATH=""
MAX_ITERATIONS=60
OUTPUT_DIR="./algo-output"
LANGUAGE="python"
MAX_INNOVATION_CYCLES=3
COMPLETION_PROMISE="ALGORITHM RESEARCH COMPLETE"

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      cat << 'HELP_EOF'
Algorithmic Research Loop - Autonomous algorithm research pipeline

USAGE:
  /algo-loop [TOPIC...] [OPTIONS]

ARGUMENTS:
  TOPIC...    Computational problem or algorithm topic (can be multiple words)

OPTIONS:
  --mode <standard|innovation|applied>
                                 Research mode (default: innovation)
  --codebase <path>              Path to target project (implies mode=applied)
  --max-iterations <n>           Max global iterations (default: 60)
  --output-dir <path>            Output directory (default: ./algo-output)
  --language <python|rust|go|typescript>
                                 Implementation language (default: python)
  --max-innovation-cycles <n>    Max invention cycles (default: 3)
  --completion-promise '<text>'  Promise phrase (default: "ALGORITHM RESEARCH COMPLETE")
  -h, --help                     Show this help message

DESCRIPTION:
  Starts an autonomous algorithm research pipeline that iterates through
  7 phases: explore, ideate, implement, benchmark, validate, analyze, report.

  The agent surveys known algorithms, invents novel approaches, implements
  them with tests, benchmarks against baselines, validates correctness,
  analyzes complexity curves, and produces a complete research report.

MODES:
  standard     Survey and catalog known algorithms for the problem.
  innovation   Survey known algorithms, then invent and benchmark novel
               approaches (default).
  applied      Analyze a codebase, identify algorithmic bottlenecks, and
               propose optimized replacements backed by benchmarks.

PHASES:
  1. Explore     (survey)      Search for known algorithms, papers, implementations
  2. Ideate      (invent)      Design novel algorithmic approaches
  3. Implement   (code)        Implement algorithms with tests (TDD)
  4. Benchmark   (measure)     Run benchmarks against baselines and known solutions
  5. Validate    (prove)       Verify correctness, edge cases, invariants
  6. Analyze     (complexity)  Fit complexity curves, compare asymptotic behavior
  7. Report      (write)       Produce final research report with figures and data

EXAMPLES:
  /algo-loop Sorting algorithms for nearly-sorted data
  /algo-loop Graph shortest path with negative weights --language rust
  /algo-loop String matching --mode standard --max-iterations 30
  /algo-loop "Cache eviction policies" --codebase ~/projects/my-cache --output-dir ./cache-research
  /algo-loop Convex hull algorithms --language go --max-innovation-cycles 5

OUTPUT:
  algo-output/
  ├── algo.db                    SQLite database (source of truth)
  ├── algorithms/
  │   ├── known/                 Implementations of known algorithms
  │   ├── invented/              Novel algorithm implementations
  │   └── tests/                 Test suites for all algorithms
  ├── benchmarks/
  │   ├── generators/            Input data generators
  │   └── results/               Benchmark results and raw data
  ├── analysis/
  │   └── curve_fits/            Complexity curve fitting data
  ├── state/
  │   └── meetings/              Agent meeting minutes
  └── figures/                   Generated figures and plots
HELP_EOF
      exit 0
      ;;
    --mode)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --mode requires an argument (standard|innovation|applied)" >&2
        exit 1
      fi
      case "$2" in
        standard|innovation|applied)
          MODE="$2"
          ;;
        *)
          echo "Error: --mode must be one of: standard, innovation, applied (got: '$2')" >&2
          exit 1
          ;;
      esac
      shift 2
      ;;
    --codebase)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --codebase requires a path to a project directory" >&2
        exit 1
      fi
      CODEBASE_PATH="$(cd "$2" 2>/dev/null && pwd)" || {
        echo "Error: --codebase path does not exist: $2" >&2
        exit 1
      }
      MODE="applied"
      shift 2
      ;;
    --max-iterations)
      if [[ -z "${2:-}" ]] || ! [[ "$2" =~ ^[0-9]+$ ]]; then
        echo "Error: --max-iterations requires a positive integer (got: '${2:-}')" >&2
        exit 1
      fi
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --output-dir)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --output-dir requires a path argument" >&2
        exit 1
      fi
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --language)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --language requires an argument (python|rust|go|typescript)" >&2
        exit 1
      fi
      case "$2" in
        python|rust|go|typescript)
          LANGUAGE="$2"
          ;;
        *)
          echo "Error: --language must be one of: python, rust, go, typescript (got: '$2')" >&2
          exit 1
          ;;
      esac
      shift 2
      ;;
    --max-innovation-cycles)
      if [[ -z "${2:-}" ]] || ! [[ "$2" =~ ^[0-9]+$ ]]; then
        echo "Error: --max-innovation-cycles requires a positive integer (got: '${2:-}')" >&2
        exit 1
      fi
      MAX_INNOVATION_CYCLES="$2"
      shift 2
      ;;
    --completion-promise)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --completion-promise requires a text argument" >&2
        exit 1
      fi
      COMPLETION_PROMISE="$2"
      shift 2
      ;;
    *)
      TOPIC_PARTS+=("$1")
      shift
      ;;
  esac
done

TOPIC="${TOPIC_PARTS[*]}"

if [[ -z "$TOPIC" ]]; then
  echo "Error: No research topic provided" >&2
  echo "" >&2
  echo "   Examples:" >&2
  echo "     /algo-loop Sorting algorithms for nearly-sorted data" >&2
  echo "     /algo-loop Graph shortest path --language rust" >&2
  echo "" >&2
  echo "   For all options: /algo-loop --help" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Resolve prompt template
# ---------------------------------------------------------------------------
PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROMPT_TEMPLATE="$PLUGIN_ROOT/templates/algo-prompt.md"

if [[ ! -f "$PROMPT_TEMPLATE" ]]; then
  echo "Error: Algorithm prompt template not found at $PROMPT_TEMPLATE" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Build applied research block (if mode=applied)
# ---------------------------------------------------------------------------
APPLIED_BLOCK=""
if [[ "$MODE" == "applied" ]]; then
  if [[ -z "$CODEBASE_PATH" ]]; then
    echo "Error: applied mode requires --codebase <path>" >&2
    exit 1
  fi
  APPLIED_TEMPLATE="$PLUGIN_ROOT/templates/applied-research-block.md"
  if [[ -f "$APPLIED_TEMPLATE" ]]; then
    APPLIED_BLOCK=$(sed \
      -e "s|{{CODEBASE_PATH}}|$CODEBASE_PATH|g" \
      -e "s|{{OUTPUT_DIR}}|$OUTPUT_DIR|g" \
      -e "s|{{PLUGIN_ROOT}}|$PLUGIN_ROOT|g" \
      -e "s|{{LANGUAGE}}|$LANGUAGE|g" \
      "$APPLIED_TEMPLATE")
  else
    echo "Warning: Applied research template not found at $APPLIED_TEMPLATE" >&2
    echo "   Continuing in innovation mode." >&2
    MODE="innovation"
    CODEBASE_PATH=""
  fi
fi

# ---------------------------------------------------------------------------
# Replace placeholders in main template
# ---------------------------------------------------------------------------
# First pass: replace simple placeholders with sed
ALGO_PROMPT=$(sed \
  -e "s|{{TOPIC}}|$TOPIC|g" \
  -e "s|{{OUTPUT_DIR}}|$OUTPUT_DIR|g" \
  -e "s|{{LANGUAGE}}|$LANGUAGE|g" \
  -e "s|{{COMPLETION_PROMISE}}|$COMPLETION_PROMISE|g" \
  -e "s|{{PLUGIN_ROOT}}|$PLUGIN_ROOT|g" \
  -e "s|{{CODEBASE_PATH}}|$CODEBASE_PATH|g" \
  -e "s|{{MODE}}|$MODE|g" \
  "$PROMPT_TEMPLATE")

# Second pass: replace multi-line blocks (sed can't handle these)
ALGO_PROMPT=$(python3 -c "
import sys
prompt = sys.stdin.read()
applied = '''$APPLIED_BLOCK'''
prompt = prompt.replace('{{APPLIED_RESEARCH_BLOCK}}', applied)
print(prompt)
" <<< "$ALGO_PROMPT")

# ---------------------------------------------------------------------------
# Create output directory structure
# ---------------------------------------------------------------------------
mkdir -p "$OUTPUT_DIR/algorithms/known"
mkdir -p "$OUTPUT_DIR/algorithms/invented"
mkdir -p "$OUTPUT_DIR/algorithms/tests"
mkdir -p "$OUTPUT_DIR/benchmarks/generators"
mkdir -p "$OUTPUT_DIR/benchmarks/results"
mkdir -p "$OUTPUT_DIR/analysis/curve_fits"
mkdir -p "$OUTPUT_DIR/state/meetings"
mkdir -p "$OUTPUT_DIR/figures"

# ---------------------------------------------------------------------------
# Initialize SQLite database
# ---------------------------------------------------------------------------
if [[ ! -f "$OUTPUT_DIR/algo.db" ]]; then
  python3 "$PLUGIN_ROOT/scripts/algo_database.py" init --db-path "$OUTPUT_DIR/algo.db" > /dev/null
fi

# ---------------------------------------------------------------------------
# Create state file
# ---------------------------------------------------------------------------
mkdir -p .claude

cat > .claude/algo-loop.local.md <<EOF
---
active: true
topic: "$TOPIC"
current_phase: 1
phase_name: "explore"
phase_iteration: 1
global_iteration: 1
max_global_iterations: $MAX_ITERATIONS
completion_promise: "$COMPLETION_PROMISE"
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
output_dir: "$OUTPUT_DIR"
mode: "$MODE"
language: "$LANGUAGE"
codebase_path: "$CODEBASE_PATH"
innovation_cycles: 0
max_innovation_cycles: $MAX_INNOVATION_CYCLES
algorithms_found: 0
algorithms_invented: 0
algorithms_implemented: 0
benchmarks_run: 0
---

$ALGO_PROMPT
EOF

# ---------------------------------------------------------------------------
# Output setup message
# ---------------------------------------------------------------------------
MODE_LABEL=""
case "$MODE" in
  standard)   MODE_LABEL="Standard (survey known algorithms)" ;;
  innovation) MODE_LABEL="Innovation (survey + invent novel approaches)" ;;
  applied)    MODE_LABEL="Applied (codebase-aware algorithmic optimization)" ;;
esac

CODEBASE_LINE=""
if [[ -n "$CODEBASE_PATH" ]]; then
  CODEBASE_LINE="Codebase: $CODEBASE_PATH"
fi

PHASE2_NOTE=""
INNOVATION_LINE=""
if [[ "$MODE" == "innovation" || "$MODE" == "applied" ]]; then
  PHASE2_NOTE=" + invent novel approaches"
  INNOVATION_LINE="Max innovation cycles: $MAX_INNOVATION_CYCLES"
fi

PHASE1_NOTE=""
if [[ "$MODE" == "applied" ]]; then
  PHASE1_NOTE=" + codebase analysis"
fi

cat <<EOF
Algorithmic Research Loop activated!

Mode: $MODE_LABEL
Topic: $TOPIC
Language: $LANGUAGE
${CODEBASE_LINE:+$CODEBASE_LINE
}Output: $OUTPUT_DIR/
Max iterations: $MAX_ITERATIONS
${INNOVATION_LINE:+$INNOVATION_LINE
}Completion promise: $COMPLETION_PROMISE

Pipeline phases:
  1. Explore     -- Survey known algorithms and papers${PHASE1_NOTE}
  2. Ideate      -- Design novel algorithmic approaches${PHASE2_NOTE}
  3. Implement   -- Code algorithms with tests (TDD)
  4. Benchmark   -- Measure performance against baselines
  5. Validate    -- Verify correctness and edge cases
  6. Analyze     -- Fit complexity curves, compare asymptotics
  7. Report      -- Produce final research report with figures

State: .claude/algo-loop.local.md
Monitor: grep 'current_phase\|global_iteration\|algorithms_' .claude/algo-loop.local.md

EOF

echo "==============================================================="
echo "CRITICAL -- Completion Promise"
echo "==============================================================="
echo ""
echo "To complete the research, output this EXACT text:"
echo "  <promise>$COMPLETION_PROMISE</promise>"
echo ""
echo "ONLY output this when the algorithm research is GENUINELY complete."
echo "Do NOT output false promises to exit the loop."
echo "==============================================================="
echo ""
echo "Starting Phase 1: Explore..."
echo ""
echo "$ALGO_PROMPT"
