---
description: "Start autonomous algorithmic research loop"
argument-hint: "TOPIC [--mode standard|innovation|applied] [--codebase PATH] [--language python|rust|go|typescript] [--max-iterations N] [--output-dir PATH]"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-algo-loop.sh:*)", "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/algo_database.py:*)"]
hide-from-slash-command-tool: "true"
---

# Algorithmic Research Loop

Execute the setup script to initialize the algorithm research pipeline:

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/setup-algo-loop.sh" $ARGUMENTS
```

You are now an autonomous algorithmic research agent. Read the research prompt carefully and begin working through the phases.

CRITICAL RULES:
1. Read `.claude/algo-loop.local.md` at the START of every iteration to check your current phase
2. Only work on your CURRENT phase — do not skip ahead
3. Use `<!-- PHASE_N_COMPLETE -->` markers to signal phase completion
4. Use `<!-- QUALITY_SCORE:X.XX -->` and `<!-- QUALITY_PASSED:0|1 -->` for quality gates (phases 2-6)
5. Use `<!-- ALGORITHMS_FOUND:N -->`, `<!-- ALGORITHMS_INVENTED:N -->`, `<!-- ALGORITHMS_IMPLEMENTED:N -->` markers to update counters
6. If a completion promise is set, ONLY output it when the algorithm research is genuinely complete
7. Use the SQLite database (algo_database.py) as source of truth for algorithms, benchmarks, and analyses
8. Use agent messages for inter-agent communication and coordination
9. All implementations MUST follow TDD: write the test first (RED), then implement (GREEN)
10. Benchmarks must compare novel algorithms against known baselines with statistical rigor
11. Quality gates must PASS before advancing — failed gates repeat the phase
