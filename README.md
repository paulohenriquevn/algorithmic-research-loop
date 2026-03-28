# Algorithmic Research Loop

Autonomous algorithmic R&D laboratory for Claude Code. Give it a computational problem, and it explores known solutions, invents new approaches through creative recombination and mutation, implements everything with TDD, benchmarks against real data, validates complexity analysis, and produces a ranked innovation report with working code.

Combines four ideas:
- **[Ralph Wiggum](https://ghuntley.com/ralph/)** — self-referential AI loop via stop hook
- **[Autoresearch](https://github.com/karpathy/autoresearch)** (Karpathy) — autonomous experimentation: write code, execute, evaluate, keep/discard
- **Creative invention** — 6 strategies: recombination, mutation, analogy, inversion, hybridization, radical simplification
- **Formal validation** — theoretical Big-O analysis + empirical curve fitting + discrepancy detection

## Installation

### Step 1: Add the marketplace

```
/plugin marketplace add paulohenriquevn/algorithmic-research-loop
```

### Step 2: Install the plugin

```
/plugin install algorithmic-research-loop@algorithmic-research-loop
```

### Step 3: Reload plugins

```
/reload-plugins
```

## Quick Start

```bash
# Innovation mode (default) — explore + invent + benchmark + analyze
/algo-loop "Find k-th smallest element in unsorted array"

# Standard mode — benchmark known algorithms only
/algo-loop "Sorting algorithms for nearly-sorted data" --mode standard

# Applied mode — optimize for a specific codebase
/algo-loop "Reduce inference latency to <50ms" --mode applied --codebase ~/projects/my-llm

# Custom settings
/algo-loop "New retrieval technique that beats BM25+dense hybrid" --max-iterations 80 --language python
```

## How It Works

```
/algo-loop "Problem"
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 1: Explore        (max 3 iter)                        │
│  Find known algorithms, decompose components, bridge domains │
├──────────────────────────────────────────────────────────────┤
│  Phase 2: Ideate         (max 3 iter)                        │
│  Creative invention: recombine, mutate, analogize, invert    │
├──────────────────────────────────────────────────────────────┤
│  Phase 3: Implement      (max 5 iter)                        │
│  TDD implementation with standardized protocol interface     │
├──────────────────────────────────────────────────────────────┤
│  Phase 4: Benchmark      (max 4 iter)                        │
│  Design + execute benchmarks, statistical rigor              │
├──────────────────────────────────────────────────────────────┤
│  Phase 5: Validate       (max 3 iter)                        │
│  Big-O formal analysis + empirical curve fitting             │
├──────────────────────────────────────────────────────────────┤
│  Phase 6: Analyze        (max 3 iter)                        │
│  Root-cause forensics, gap detection, loop-back decision     │
├──────────────────────────────────────────────────────────────┤
│  Phase 7: Report         (max 2 iter)                        │
│  Final ranking, Pareto charts, invention log, deliverables   │
└──────────────────────────────────────────────────────────────┘
     │                           ▲
     │    ┌──────────────────────┘
     │    │ Loop-back (max 3 cycles)
     │    │ When Phase 6 finds promising
     │    │ unexplored directions
     ▼    │
  algo-output/
  ├── algorithms/          ← Working implementations (known + invented)
  ├── benchmarks/          ← Benchmark suite + results
  ├── analysis/            ← Complexity reports + curve fits
  ├── invention_log.md     ← Every idea tried, what worked, why
  ├── final_report.md      ← Ranked analysis with recommendations
  └── algo.db              ← All data in structured DB
```

Each iteration, the stop hook intercepts Claude's exit and re-injects the research prompt. Phases advance via completion markers or timeout. Quality gates repeat failed phases (Autoresearch keep/discard). The Analyze phase can loop back to Ideate for up to 3 innovation cycles.

## Three Modes

### 1. Innovation Mode (default)

```bash
/algo-loop "Reduce LLM inference latency to <50ms on edge devices"
```

Full pipeline with creative invention. The agent:
- Explores known techniques (quantization, pruning, speculative decoding...)
- Invents hybrids ("structural pruning + adaptive speculative decoding?")
- Implements each approach with TDD
- Benchmarks on real hardware
- Analyzes why things work or fail
- Loops back with new ideas based on insights

### 2. Standard Mode

```bash
/algo-loop "Sorting algorithms for nearly-sorted data" --mode standard
```

Skips Phase 2 (Ideate). Explores, implements, and benchmarks known algorithms only. Useful for systematic comparison without invention.

### 3. Applied Mode

```bash
/algo-loop "Optimize search performance" --mode applied --codebase ~/projects/my-app
```

Adds codebase analysis to Phase 1 and integration recommendations to Phase 7. Maps algorithmic solutions to your specific codebase.

## Commands

### `/algo-loop TOPIC [OPTIONS]`

| Option | Default | Description |
|--------|---------|-------------|
| `--mode MODE` | `innovation` | Operation mode: `standard`, `innovation`, or `applied` |
| `--codebase PATH` | *(off)* | Enable applied mode — analyze this project |
| `--max-iterations N` | `60` | Max global iterations before auto-stop |
| `--output-dir PATH` | `./algo-output` | Where output files go |
| `--language LANG` | `python` | Implementation language: `python`, `rust`, `go`, `typescript` |
| `--max-innovation-cycles N` | `3` | Max loop-back cycles from Analyze to Ideate |
| `--completion-promise TEXT` | `"ALGORITHM RESEARCH COMPLETE"` | Promise text to signal completion |

### `/algo-status`

View current state: phase, iteration, algorithm counts, benchmark results.

### `/algo-cancel`

Cancel an active loop. Output files are preserved.

### `/algo-help`

Explain the system and available commands.

## Output Structure

```
algo-output/
├── algo.db                          # SQLite DB (source of truth)
├── algorithms/
│   ├── known/                       # Known algorithm implementations
│   │   ├── quickselect.py
│   │   └── median_of_medians.py
│   ├── invented/                    # Novel inventions
│   │   ├── hybrid_adaptive_select.py
│   │   └── ...
│   └── tests/                       # All algorithm tests
│       ├── test_quickselect.py
│       └── test_hybrid_adaptive_select.py
├── benchmarks/
│   ├── suite.py                     # Benchmark runner
│   ├── generators/                  # Input generators
│   └── results/
│       ├── benchmark_raw.json       # Raw measurements
│       ├── benchmark_summary.json   # Statistical summary
│       └── benchmark_report.md      # Human-readable report
├── analysis/
│   ├── complexity_report.md         # Theoretical + empirical analysis
│   ├── curve_fits/                  # Curve fitting SVG charts
│   ├── forensic_report.md           # Root-cause analysis
│   └── gap_report.md                # Unexplored directions
├── state/
│   ├── exploration.md               # State of the art findings
│   ├── ideas.md                     # Generated ideas with status
│   └── meetings/                    # Chief scientist meeting minutes
├── figures/
│   ├── ranking_pareto.svg           # Pareto front visualization
│   ├── complexity_comparison.svg    # Big-O comparison chart
│   └── benchmark_heatmap.svg        # Performance heatmap
├── invention_log.md                 # Complete invention journal
└── final_report.md                  # Final ranked report
```

## 16 Specialized Agents

| Agent | Phase | Role |
|-------|-------|------|
| chief-scientist | All | Orchestrates group meetings, strategic decisions |
| quality-evaluator | All | Quality gates (keep/discard pattern) |
| literature-scout | 1 | Searches for known algorithms and papers |
| technique-analyst | 1 | Decomposes algorithms into reusable components |
| domain-bridge | 1 | Finds analogous techniques from different domains |
| idea-generator | 2 | 6 creative strategies for invention |
| mutation-engine | 2 | Systematic mutations of existing algorithms |
| algorithm-architect | 3 | Designs protocol interface and specs |
| implementation-coder | 3 | TDD implementation (RED-GREEN-REFACTOR) |
| test-engineer | 3 | Property-based tests, edge cases, fuzzing |
| benchmark-designer | 4 | Designs benchmark suite with statistical rigor |
| benchmark-runner | 4 | Executes benchmarks, collects metrics |
| complexity-analyst | 5 | Big-O analysis + empirical curve fitting |
| forensic-analyst | 6 | Root-cause analysis: why things work or fail |
| gap-detector | 6 | Identifies unexplored combinations and directions |
| report-writer | 7 | Final ranked report with Pareto analysis |

## Quality Gates & Hard Blocks

**Quality gates** (threshold 0.7): Phases 2-6 require quality evaluation before advancing. Failed phases repeat with evaluator feedback (Autoresearch keep/discard).

**Hard blocks** prevent advancement without evidence:

| Transition | Requirement |
|------------|-------------|
| Phase 1 → 2 | Algorithms decomposed into components |
| Phase 2 → 3 | At least one invention proposed |
| Phase 3 → 4 | Implementations with passing tests |
| Phase 4 → 5 | Benchmark results in database |
| Phase 5 → 6 | Complexity analysis completed |
| Phase 6 → 7 | Invention log populated with outcomes |

## Database

SQLite database (`algo.db`) with 9 tables:

- **algorithms** — Known + invented algorithms with decomposition and invention metadata
- **implementations** — Versioned code with test status
- **benchmarks** — Experiment definitions (inputs, metrics, runs)
- **benchmark_results** — Individual measurements with statistical detail
- **complexity_analysis** — Theoretical Big-O + empirical curve fits
- **invention_log** — Creative journal: hypothesis, outcome, insight, feeds next cycle
- **quality_scores** — Quality gate scores per phase
- **agent_messages** — Inter-agent communication

## License

MIT
