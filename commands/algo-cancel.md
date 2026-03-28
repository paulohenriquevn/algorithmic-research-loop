---
description: "Cancel active algorithmic research loop"
allowed-tools: ["Bash(test -f .claude/algo-loop.local.md:*)", "Bash(rm .claude/algo-loop.local.md)", "Read(.claude/algo-loop.local.md)"]
hide-from-slash-command-tool: "true"
---

# Cancel Algorithmic Research Loop

To cancel the algorithmic research loop:

1. Check if `.claude/algo-loop.local.md` exists using Bash: `test -f .claude/algo-loop.local.md && echo "EXISTS" || echo "NOT_FOUND"`

2. **If NOT_FOUND**: Say "No active algorithmic research loop found."

3. **If EXISTS**:
   - Read `.claude/algo-loop.local.md` to get current state (phase, iteration, topic, algorithm counts)
   - Remove the file using Bash: `rm .claude/algo-loop.local.md`
   - Report: "Cancelled algorithmic research loop for topic '[TOPIC]' (was at phase N/7: PHASE_NAME, global iteration M). Algorithms found: X, invented: Y, implemented: Z. Benchmarks run: B. Output preserved in OUTPUT_DIR."
