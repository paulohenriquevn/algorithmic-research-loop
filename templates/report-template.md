# {{TITLE}}

## Abstract

[2-3 paragraph summary: problem addressed, methodology (explore/invent/implement/benchmark/validate), key findings, top-ranked algorithm, and main insight discovered through the creative process.]

---

## 1. Problem Statement

### 1.1 Formal Definition
[Precise input/output specification, constraints, objective function.]

### 1.2 Success Criteria
[What makes a solution good: time, space, approximation quality, simplicity, practical constants.]

### 1.3 Known Complexity Bounds
[Lower bounds, reductions, impossibility results. What is theoretically achievable?]

---

## 2. Methodology

### 2.1 Exploration Strategy
[How the search for known algorithms was conducted: sources searched, queries used, adjacent domains explored.]

### 2.2 Invention Strategy
[Which creative strategies were applied: recombination, mutation, analogy, inversion, hybridization, radical simplification. How many innovation cycles were executed.]

### 2.3 Implementation Protocol
[TDD approach, standard interface, language choice, testing methodology.]

### 2.4 Benchmarking Protocol
[Input sizes, scenarios (random/worst-case/realistic), warmup runs, measured runs, statistical methodology, outlier detection.]

### 2.5 Validation Protocol
[Theoretical derivation approach, empirical curve fitting method, discrepancy analysis criteria.]

---

## 3. Algorithm Catalog

### 3.1 Known Algorithms

| ID | Name | Category | Paradigm | Time (avg) | Time (worst) | Space | Source |
|----|------|----------|----------|-----------|-------------|-------|--------|
| ... | ... | known | ... | ... | ... | ... | [link] |

### 3.2 Invented Algorithms

| ID | Name | Strategy | Parents | Time (expected) | Space (expected) | Rationale |
|----|------|----------|---------|----------------|-----------------|-----------|
| ... | ... | recombination | algo_a + algo_b | ... | ... | ... |

### 3.3 Component Decomposition

| Algorithm | Data Structure | Paradigm | Heuristic | Key Insight |
|-----------|---------------|----------|-----------|-------------|
| ... | ... | ... | ... | ... |

---

## 4. Implementation Details

### 4.1 Protocol Interface
[Description of the standard interface all algorithms implement.]

### 4.2 Test Coverage
| Algorithm | Tests | Passed | Edge Cases Covered |
|-----------|-------|--------|-------------------|
| ... | N | N | [list] |

### 4.3 Implementation Notes
[Per-algorithm notes on implementation choices, optimizations, and tradeoffs.]

---

## 5. Benchmark Results

### 5.1 Random Input Scenario

| Algorithm | n=100 | n=1K | n=10K | n=100K | n=1M |
|-----------|-------|------|-------|--------|------|
| ... | X.XX ms | ... | ... | ... | ... |

### 5.2 Worst-Case Scenario

| Algorithm | n=100 | n=1K | n=10K | n=100K | n=1M |
|-----------|-------|------|-------|--------|------|
| ... | X.XX ms | ... | ... | ... | ... |

### 5.3 Realistic Input Scenario

| Algorithm | n=100 | n=1K | n=10K | n=100K | n=1M |
|-----------|-------|------|-------|--------|------|
| ... | X.XX ms | ... | ... | ... | ... |

### 5.4 Memory Usage

| Algorithm | n=100 | n=1K | n=10K | n=100K | n=1M |
|-----------|-------|------|-------|--------|------|
| ... | X.XX MB | ... | ... | ... | ... |

### 5.5 Statistical Summary
[Standard deviations, outlier analysis, confidence intervals for key comparisons.]

![Benchmark Heatmap](figures/benchmark_heatmap.svg)

---

## 6. Complexity Analysis

### 6.1 Theoretical Analysis

| Algorithm | Time (best) | Time (avg) | Time (worst) | Space | Derivation |
|-----------|------------|-----------|-------------|-------|------------|
| ... | ... | ... | ... | ... | [brief derivation or reference] |

### 6.2 Empirical Analysis

| Algorithm | Best Fit | Equation | R-squared | Data Points |
|-----------|----------|----------|-----------|-------------|
| ... | O(n log n) | y = 0.0023n*log(n) + 0.15 | 0.9987 | 5 |

### 6.3 Theory vs Practice

| Algorithm | Theoretical | Empirical | Match? | Discrepancy Explanation |
|-----------|------------|-----------|--------|------------------------|
| ... | O(n) | O(n) | Yes | Tight match, minor constant factor |
| ... | O(n log n) | O(n^1.2) | Partial | Cache effects at large n |

![Complexity Comparison](figures/complexity_comparison.svg)

---

## 7. Innovation Log

### 7.1 Cycle 1
[For each invention attempt: strategy, hypothesis, outcome, insight.]

| # | Strategy | Hypothesis | Outcome | Key Insight |
|---|----------|-----------|---------|-------------|
| 1 | Recombination | ... | success/partial/failure | ... |
| 2 | Mutation | ... | ... | ... |

### 7.2 Cycle 2 (if applicable)
[Ideas that emerged from Cycle 1 insights and gap analysis.]

### 7.3 Meta-Insights
[What did the creative process reveal about the problem space? Which strategies were most productive and why?]

---

## 8. Ranking & Pareto Analysis

### 8.1 Single-Objective Rankings

**By average-case time:**
1. Algorithm X — Y.YY ms at n=100K
2. Algorithm Z — Z.ZZ ms at n=100K
3. ...

**By worst-case time:**
1. ...

**By space efficiency:**
1. ...

### 8.2 Pareto Front

Algorithms on the Pareto front (not dominated on ALL dimensions):

| Algorithm | Time (avg) | Space | Correctness | Why Pareto-optimal |
|-----------|-----------|-------|-------------|-------------------|
| ... | ... | ... | ... | Best time with O(1) space |
| ... | ... | ... | ... | Best worst-case guarantee |

![Pareto Front](figures/ranking_pareto.svg)

### 8.3 Situational Recommendations

| Scenario | Recommended Algorithm | Reason |
|----------|----------------------|--------|
| Small inputs (n < 1000) | ... | Low overhead, simple |
| Large inputs, memory constrained | ... | O(1) space |
| Adversarial inputs possible | ... | Best worst-case |
| General purpose | ... | Best average-case tradeoff |

---

## 9. Recommendations

### 9.1 Primary Recommendation
[The overall best algorithm for the stated problem, with justification.]

### 9.2 When to Use Alternatives
[Specific conditions under which other algorithms are preferable.]

### 9.3 Open Questions
[What remains unanswered? What would further research explore?]

---

## Appendix

### A. Full Benchmark Data
[Complete tables with all measurements, standard deviations, min/max per configuration.]

### B. Environment
[CPU, RAM, OS, language version, dependencies.]

### C. Reproduction Instructions
```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python3 -m pytest algorithms/tests/ -v

# Run benchmarks
python3 benchmarks/run_benchmarks.py

# Generate figures
python3 figures/gen_*.py
```

### D. Database Schema
[Reference to algo.db schema and how to query it.]

### E. References
[Papers, textbooks, online resources cited throughout.]
