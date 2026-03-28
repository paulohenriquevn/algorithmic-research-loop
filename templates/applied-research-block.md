
## Applied Research Mode — Codebase-Aware Pipeline

**This research loop is operating in APPLIED RESEARCH mode.**

You are not conducting general algorithmic exploration. You are solving a **specific performance or algorithmic problem** within an existing codebase. Every phase is modified to connect findings to the target system.

**Codebase path:** `{{CODEBASE_PATH}}`
**Codebase analysis:** `{{OUTPUT_DIR}}/state/codebase_analysis.md`

---

### Phase 1 Modification: Codebase-First Exploration

**BEFORE searching for algorithms**, analyze the codebase at `{{CODEBASE_PATH}}`:

1. Read all relevant source files, architecture documents, and existing benchmarks
2. Produce a structured analysis at `{{OUTPUT_DIR}}/state/codebase_analysis.md`:
   ```markdown
   # Codebase Analysis

   ## Architecture Overview
   [High-level description of the system]

   ## Current Algorithms in Use
   | Component | Current Algorithm | Complexity | Performance | Bottleneck? |
   |-----------|------------------|------------|-------------|-------------|
   | ... | ... | ... | ... | yes/no |

   ## Identified Bottlenecks
   [Where is time/space being wasted? What are the hot paths?]

   ## Performance Profile
   [Current latencies, throughput, memory usage — measured if available]

   ## Constraints
   [Hard constraints: max latency, memory limits, API contracts, backward compatibility]

   ## Optimization Targets
   [Specific components where algorithmic improvement would have the highest impact]
   ```

3. Derive search queries from the analysis — search for algorithms that solve the SPECIFIC bottlenecks identified, not generic problem descriptions

Example: If the codebase has a `search_index.py` using brute-force nearest neighbor with 500ms latency and a target of <50ms, search for "approximate nearest neighbor sublinear" — not just "search algorithms."

---

### Phase 2 Modification: Targeted Invention

When ideating, constrain inventions to the codebase's real constraints:
- Respect memory limits, API contracts, and backward compatibility requirements
- Consider integration complexity as a first-class concern
- Prioritize inventions that can be incrementally adopted (drop-in replacements)

Each invention must include:
```markdown
### Integration Assessment
- **Drop-in replacement:** [yes/no — does it match the existing interface?]
- **Migration effort:** [low/medium/high]
- **Risk:** [what could break during integration?]
- **Rollback strategy:** [how to revert if the new algorithm causes issues]
```

---

### Phase 3 Modification: Interface-Compatible Implementation

Implementations must match the existing codebase's interfaces:
- Extract the ACTUAL interface from the codebase (function signatures, input/output types)
- Implement algorithms as drop-in replacements where possible
- Write integration tests that use real data shapes from the codebase

---

### Phase 4 Modification: Realistic Benchmarks

Benchmark inputs must include data representative of the actual codebase:
- Extract sample inputs from the target system (or generate realistic synthetic data matching its distribution)
- Include the CURRENT algorithm as a baseline in all benchmarks
- Measure the same metrics the codebase cares about (not just abstract time/space)

---

### Phase 7 Modification: Integration Recommendations

The final report MUST include an additional section:

```markdown
## Integration Recommendations

### Recommended Algorithm per Component
| Component | Current | Recommended | Expected Improvement | Migration Effort |
|-----------|---------|-------------|---------------------|-----------------|
| ... | ... | ... | ... | ... |

### Integration Plan
[Step-by-step plan for adopting the recommended algorithms]

### Risk Assessment
[What could go wrong and how to mitigate]

### Validation Criteria
[How to verify the new algorithms work correctly in the codebase]
```
