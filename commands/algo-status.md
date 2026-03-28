---
description: "View current algorithmic research loop status"
allowed-tools: ["Bash(test -f .claude/algo-loop.local.md:*)", "Read(.claude/algo-loop.local.md)", "Bash(ls:*)", "Bash(wc:*)", "Bash(cat:*)"]
hide-from-slash-command-tool: "true"
---

# Algorithmic Research Loop Status

Check and display the current algorithmic research loop status:

1. Check if `.claude/algo-loop.local.md` exists: `test -f .claude/algo-loop.local.md && echo "EXISTS" || echo "NOT_FOUND"`

2. **If NOT_FOUND**: Say "No active algorithmic research loop."

3. **If EXISTS**:
   - Read `.claude/algo-loop.local.md` to get all state fields
   - Check the output directory for generated files
   - Display a formatted status report:

```
Algorithmic Research Loop Status
================================
Topic:            [topic]
Mode:             [mode]
Language:         [language]
Phase:            [N]/7 -- [phase_name]
Phase iteration:  [phase_iteration]
Global iteration: [global_iteration]/[max_global_iterations]
Started:          [started_at]

Algorithms:
  Found:          [algorithms_found]
  Invented:       [algorithms_invented]
  Implemented:    [algorithms_implemented]

Benchmarks run:   [benchmarks_run]
Innovation cycles: [innovation_cycles]/[max_innovation_cycles]

Output directory: [output_dir]
  algorithms/known/      [N files]
  algorithms/invented/   [N files]
  algorithms/tests/      [N files]
  benchmarks/results/    [N files]
  analysis/curve_fits/   [N files]
  figures/               [N files]
  algo.db:               [exists/missing]

Quality gate history:
  [List QUALITY_SCORE and QUALITY_PASSED markers found in state file]
```
