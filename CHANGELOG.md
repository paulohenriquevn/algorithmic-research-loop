# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial plugin structure with 7-phase pipeline (Explore, Ideate, Implement, Benchmark, Validate, Analyze, Report)
- 16 specialized agents for algorithmic research and invention
- SQLite database with 9 tables for algorithms, implementations, benchmarks, complexity analysis, and invention log
- Ralph Wiggum loop via stop hook with quality gates and hard blocks
- 3 operation modes: standard, innovation (default), and applied
- Loop-back mechanism from Analyze to Ideate (up to 3 innovation cycles)
- TDD-based implementation with standardized algorithm protocol
- Complexity analysis: theoretical Big-O + empirical curve fitting
- Benchmark suite with statistical rigor (warmup, multiple runs, std dev)
- Setup script with argument parsing and output directory initialization
- 4 slash commands: /algo-loop, /algo-status, /algo-cancel, /algo-help
- Enum validation for all domain values in database (category, status, origin, strategy, outcome, message_type)
- Range validation for quality scores (0-1), phase numbers (1-7), and r_squared (0-1)
- JSON parsing error handling with clear error messages in CLI
- Phase data flow documentation in algo-prompt.md (inputs/outputs per phase)
- Multi-language support instructions in agent definitions (Python, Rust, Go, TypeScript)
- Loop-back decision criteria with quantitative thresholds in chief-scientist agent
- Recovery protocol for failed quality gates in quality-evaluator agent
- Phase 5 scope clarification (correctness, complexity, stability, edge case validation)
- Test coverage: enum validation, range validation, JSON parsing errors, CLI error handling, Bessel correction, exception safety

### Changed
- Database functions use context managers (`with` statements) instead of manual `conn.close()` to prevent resource leaks
- Benchmark variance calculation uses Bessel's correction (n-1 divisor) for unbiased sample estimates
- Type hints use `from __future__ import annotations` + `Optional[T]` for Python 3.9+ compatibility
- Search functions (GitHub/ArXiv) now raise exceptions after exhausting retries instead of returning empty lists silently
- ArXiv year parsing handles malformed dates gracefully instead of crashing

### Fixed
- SQL injection vulnerability in stop-hook.sh: database path is now passed via sys.argv instead of string interpolation
- Silent error suppression in stop-hook.sh hard blocks: database errors are now detected and reported (returns -1 instead of 0)
- Temp file security in stop-hook.sh: uses `mktemp` instead of predictable PID-based filenames
- Quality gate enforcement: phases with quality gates now REQUIRE quality markers to advance (missing markers block advancement)
- Phase bounds validation: current_phase validated to be 1-7, prevents undefined behavior on corrupted state
- Response size limit (10MB) added to GitHub/ArXiv API calls to prevent memory exhaustion
