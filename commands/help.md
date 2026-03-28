---
description: "Explain algorithmic research loop and available commands"
---

# Algorithmic Research Loop Help

Please explain the following to the user:

## What is the Algorithmic Research Loop?

A Claude Code plugin that runs an autonomous algorithmic research pipeline using the Ralph Wiggum loop technique. You give it a computational problem, and it iterates through 7 phases -- surveying known algorithms, inventing novel approaches, implementing them with TDD, benchmarking against baselines, validating correctness, analyzing complexity curves, and producing a complete research report.

**Inspired by:**
- **Ralph Wiggum** (Geoffrey Huntley) -- self-referential AI loop mechanism
- **Autoresearch** (Andrej Karpathy) -- autonomous AI experimentation pattern
- **Academic Research Loop** -- multi-agent academic research pipeline (adapted for algorithms)

## The 7 Phases

| Phase | Name | What happens | Max iterations |
|-------|------|-------------|---------------|
| 1 | Explore (survey) | Search for known algorithms, papers, implementations | 3 |
| 2 | Ideate (invent) | Design novel algorithmic approaches | 3 |
| 3 | Implement (code) | Implement algorithms with tests using TDD | 5 |
| 4 | Benchmark (measure) | Run benchmarks against baselines and known solutions | 3 |
| 5 | Validate (prove) | Verify correctness, edge cases, invariants | 2 |
| 6 | Analyze (complexity) | Fit complexity curves, compare asymptotic behavior | 2 |
| 7 | Report (write) | Produce final research report with figures and data | 2 |

## Research Modes

| Mode | Description |
|------|-------------|
| **standard** | Survey and catalog known algorithms for the problem |
| **innovation** | Survey known algorithms, then invent and benchmark novel approaches (default) |
| **applied** | Analyze a codebase, identify algorithmic bottlenecks, and propose optimized replacements backed by benchmarks |

## Available Commands

### /algo-loop TOPIC [OPTIONS]

Start an algorithmic research loop.

```
/algo-loop Sorting algorithms for nearly-sorted data
/algo-loop Graph shortest path with negative weights --language rust
/algo-loop String matching --mode standard --max-iterations 30
/algo-loop "Cache eviction policies" --codebase ~/projects/my-cache
/algo-loop Convex hull algorithms --language go --max-innovation-cycles 5
```

**Options:**
- `--mode <standard|innovation|applied>` -- Research mode (default: innovation)
- `--codebase <path>` -- Path to target project (implies mode=applied)
- `--language <python|rust|go|typescript>` -- Implementation language (default: python)
- `--max-iterations <n>` -- Max global iterations (default: 60)
- `--output-dir <path>` -- Output directory (default: ./algo-output)
- `--max-innovation-cycles <n>` -- Max invention cycles (default: 3)
- `--completion-promise <text>` -- Custom promise (default: "ALGORITHM RESEARCH COMPLETE")

### /algo-status

View current algorithmic research loop status: phase, iteration, algorithm counts, benchmark results, output files.

### /algo-cancel

Cancel an active algorithmic research loop. Output files are preserved.

## Output Structure

```
algo-output/
├── algo.db                    -- SQLite database (source of truth)
├── algorithms/
│   ├── known/                 -- Implementations of known algorithms
│   ├── invented/              -- Novel algorithm implementations
│   └── tests/                 -- Test suites for all algorithms
├── benchmarks/
│   ├── generators/            -- Input data generators
│   └── results/               -- Benchmark results and raw data
├── analysis/
│   └── curve_fits/            -- Complexity curve fitting data
├── state/
│   └── meetings/              -- Agent meeting minutes
└── figures/                   -- Generated figures and plots
```

## How It Works

1. The stop hook intercepts Claude's exit after each iteration
2. Claude reads the state file to know its current phase
3. Each iteration advances the research within the current phase
4. Phase completion markers (`<!-- PHASE_N_COMPLETE -->`) trigger phase transitions
5. Quality gates enforce evidence requirements before advancing (phases 2-6)
6. If a phase exceeds its iteration limit, it forces advancement to the next phase
7. The loop ends when Claude outputs `<promise>ALGORITHM RESEARCH COMPLETE</promise>`

## Key Differences from Academic Research Loop

- **Implementation-first**: algorithms are coded and tested, not just described
- **TDD discipline**: every algorithm has tests written before implementation
- **Benchmarking**: empirical performance comparison across implementations
- **Complexity analysis**: automatic curve fitting to verify Big-O claims
- **Innovation cycles**: structured invention of novel algorithmic approaches
- **Multi-language support**: implementations in Python, Rust, Go, or TypeScript

## Database

The plugin uses a SQLite database (`algo.db`) as the source of truth, managed via `algo_database.py`. It stores:
- Known and invented algorithms with metadata
- Implementation records linked to algorithms
- Benchmark results with statistical data
- Complexity analysis curve fits
- Agent coordination messages
