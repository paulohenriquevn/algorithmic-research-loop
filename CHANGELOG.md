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
