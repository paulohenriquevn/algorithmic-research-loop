#!/usr/bin/env python3
"""
SQLite database for the Algorithmic Research Loop plugin.

Stores algorithms (known + invented), implementations, benchmarks,
complexity analysis, invention log, quality scores, and agent messages.

Usage:
    python3 algo_database.py init --db-path algo.db
    python3 algo_database.py add-algorithm --db-path algo.db --algo-json '{...}'
    python3 algo_database.py add-implementation --db-path algo.db --algo-id ID --impl-json '{...}'
    python3 algo_database.py add-benchmark --db-path algo.db --benchmark-json '{...}'
    python3 algo_database.py add-benchmark-result --db-path algo.db --result-json '{...}'
    python3 algo_database.py add-complexity --db-path algo.db --complexity-json '{...}'
    python3 algo_database.py add-invention --db-path algo.db --invention-json '{...}'
    python3 algo_database.py add-quality-score --db-path algo.db --phase N --score 0.85 --details '{...}'
    python3 algo_database.py add-message --db-path algo.db --from-agent NAME --phase N --content "..."
    python3 algo_database.py query-algorithms --db-path algo.db [--category known|invented] [--status proposed]
    python3 algo_database.py query-results --db-path algo.db [--algo-id ID] [--benchmark-id ID]
    python3 algo_database.py stats --db-path algo.db
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS algorithms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,                 -- "known" | "invented"
    origin TEXT,                            -- "literature" | "recombination" | "mutation" | "analogy" | "inversion" | "hybrid" | "simplification" | "novel"
    parent_ids TEXT,                        -- JSON array of algorithm IDs (for invented)
    description TEXT NOT NULL,
    domain TEXT,                            -- "sorting", "retrieval", "inference", etc.
    components TEXT,                        -- JSON: {"data_structure": "heap", "paradigm": "divide_conquer", "heuristic": "..."}
    pseudocode TEXT,
    theoretical_time TEXT,                  -- "O(n)", "O(n log n)", "O(n^2)"
    theoretical_space TEXT,                 -- "O(1)", "O(n)"
    source_url TEXT,                        -- Paper/repo URL (for known)
    invention_rationale TEXT,               -- Why it was invented (for invented)
    status TEXT NOT NULL DEFAULT 'proposed', -- "proposed" | "implemented" | "tested" | "benchmarked" | "validated" | "discarded"
    discard_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS implementations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    algorithm_id TEXT NOT NULL REFERENCES algorithms(id),
    version INTEGER NOT NULL DEFAULT 1,
    language TEXT NOT NULL DEFAULT 'python',
    file_path TEXT NOT NULL,
    test_file_path TEXT,
    tests_passed INTEGER DEFAULT 0,
    tests_total INTEGER DEFAULT 0,
    lines_of_code INTEGER,
    status TEXT NOT NULL DEFAULT 'draft',    -- "draft" | "tests_pass" | "tests_fail" | "ready"
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(algorithm_id, version)
);

CREATE TABLE IF NOT EXISTS benchmarks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    input_generator TEXT,                    -- Code/path for input generation
    input_sizes TEXT NOT NULL,               -- JSON array: [100, 1000, 10000, 100000]
    metrics TEXT NOT NULL,                   -- JSON array: ["time_ms", "memory_mb", "correctness"]
    warmup_runs INTEGER DEFAULT 3,
    measured_runs INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS benchmark_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benchmark_id TEXT NOT NULL REFERENCES benchmarks(id),
    algorithm_id TEXT NOT NULL REFERENCES algorithms(id),
    implementation_id INTEGER REFERENCES implementations(id),
    input_size INTEGER NOT NULL,
    metric TEXT NOT NULL,                    -- "time_ms", "memory_mb", "correctness"
    value REAL NOT NULL,
    std_dev REAL,
    min_value REAL,
    max_value REAL,
    runs INTEGER,
    environment TEXT,                        -- JSON: {"cpu": "...", "ram": "...", "python": "3.12"}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS complexity_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    algorithm_id TEXT NOT NULL REFERENCES algorithms(id),
    analysis_type TEXT NOT NULL,             -- "theoretical" | "empirical"
    metric TEXT NOT NULL,                    -- "time" | "space"
    complexity_class TEXT NOT NULL,          -- "O(n)", "O(n log n)", "O(n^2)"
    empirical_fit TEXT,                      -- "y = 2.3n + 15" (curve fitting result)
    r_squared REAL,                          -- Goodness of fit
    data_points TEXT,                        -- JSON: [[input_size, measured_value], ...]
    discrepancy TEXT,                        -- Description of theoretical vs empirical divergence
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invention_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle INTEGER NOT NULL DEFAULT 1,       -- Innovation cycle (1-3)
    algorithm_id TEXT REFERENCES algorithms(id),
    strategy TEXT NOT NULL,                 -- "recombination" | "mutation" | "analogy" | "inversion" | "hybrid" | "simplification"
    hypothesis TEXT NOT NULL,               -- "Combining X with Y should improve Z because..."
    outcome TEXT,                           -- "success" | "partial" | "failure"
    result_summary TEXT,
    insight TEXT,                           -- Lesson learned
    feeds_next TEXT,                        -- JSON: suggestions for next cycle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quality_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase INTEGER NOT NULL,
    phase_name TEXT NOT NULL,
    iteration INTEGER NOT NULL,
    score REAL NOT NULL,
    passed INTEGER NOT NULL,
    threshold REAL NOT NULL,
    dimensions TEXT,                         -- JSON object {dimension: score}
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent TEXT NOT NULL,
    to_agent TEXT,                           -- NULL = broadcast
    phase INTEGER NOT NULL,
    iteration INTEGER NOT NULL,
    message_type TEXT NOT NULL,              -- 'finding', 'instruction', 'feedback', 'question', 'decision', 'meeting_minutes'
    content TEXT NOT NULL,
    metadata TEXT,                           -- JSON for structured data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_algorithms_category ON algorithms(category);
CREATE INDEX IF NOT EXISTS idx_algorithms_status ON algorithms(status);
CREATE INDEX IF NOT EXISTS idx_algorithms_domain ON algorithms(domain);
CREATE INDEX IF NOT EXISTS idx_implementations_algo ON implementations(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_implementations_status ON implementations(status);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_algo ON benchmark_results(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_benchmark ON benchmark_results(benchmark_id);
CREATE INDEX IF NOT EXISTS idx_complexity_algo ON complexity_analysis(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_invention_cycle ON invention_log(cycle);
CREATE INDEX IF NOT EXISTS idx_invention_outcome ON invention_log(outcome);
CREATE INDEX IF NOT EXISTS idx_quality_phase ON quality_scores(phase);
CREATE INDEX IF NOT EXISTS idx_messages_phase ON agent_messages(phase);
CREATE INDEX IF NOT EXISTS idx_messages_type ON agent_messages(message_type);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    """Create a database connection with WAL mode for concurrent reads."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    """Initialize the database schema."""
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
        (SCHEMA_VERSION,),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Algorithms
# ---------------------------------------------------------------------------
def add_algorithm(db_path: str, algo: dict) -> dict:
    """Add an algorithm to the database."""
    conn = get_connection(db_path)
    algo_id = algo.get("id", "")

    existing = conn.execute("SELECT id FROM algorithms WHERE id = ?", (algo_id,)).fetchone()
    if existing:
        conn.close()
        return {"status": "duplicate", "existing_id": algo_id}

    conn.execute(
        """INSERT INTO algorithms (id, name, category, origin, parent_ids, description,
           domain, components, pseudocode, theoretical_time, theoretical_space,
           source_url, invention_rationale, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            algo_id,
            algo.get("name", ""),
            algo.get("category", "known"),
            algo.get("origin"),
            json.dumps(algo.get("parent_ids", [])),
            algo.get("description", ""),
            algo.get("domain"),
            json.dumps(algo.get("components", {})),
            algo.get("pseudocode"),
            algo.get("theoretical_time"),
            algo.get("theoretical_space"),
            algo.get("source_url"),
            algo.get("invention_rationale"),
            algo.get("status", "proposed"),
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "added", "id": algo_id}


def update_algorithm(db_path: str, algo_id: str, updates: dict) -> dict:
    """Update specific fields of an algorithm."""
    conn = get_connection(db_path)
    allowed_fields = {
        "status", "discard_reason", "theoretical_time", "theoretical_space",
        "pseudocode", "components", "invention_rationale", "description",
    }
    set_clauses = []
    values = []
    for field, value in updates.items():
        if field in allowed_fields:
            set_clauses.append(f"{field} = ?")
            if field == "components":
                values.append(json.dumps(value) if isinstance(value, dict) else value)
            else:
                values.append(value)

    if not set_clauses:
        conn.close()
        return {"status": "error", "message": "no valid fields to update"}

    values.append(algo_id)
    conn.execute(
        f"UPDATE algorithms SET {', '.join(set_clauses)} WHERE id = ?", values
    )
    conn.commit()
    conn.close()
    return {"status": "updated", "id": algo_id}


def query_algorithms(db_path: str, category: str | None = None,
                     status: str | None = None,
                     domain: str | None = None) -> list[dict]:
    """Query algorithms with optional filters."""
    conn = get_connection(db_path)
    query = "SELECT * FROM algorithms WHERE 1=1"
    params: list = []

    if category:
        query += " AND category = ?"
        params.append(category)
    if status:
        query += " AND status = ?"
        params.append(status)
    if domain:
        query += " AND domain = ?"
        params.append(domain)

    query += " ORDER BY category, name"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_algo(row) for row in rows]


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------
def add_implementation(db_path: str, algo_id: str, impl: dict) -> dict:
    """Add an implementation for an algorithm."""
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO implementations
           (algorithm_id, version, language, file_path, test_file_path,
            tests_passed, tests_total, lines_of_code, status, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            algo_id,
            impl.get("version", 1),
            impl.get("language", "python"),
            impl.get("file_path", ""),
            impl.get("test_file_path"),
            impl.get("tests_passed", 0),
            impl.get("tests_total", 0),
            impl.get("lines_of_code"),
            impl.get("status", "draft"),
            impl.get("notes"),
        ),
    )
    conn.commit()
    impl_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"status": "added", "id": impl_id, "algorithm_id": algo_id}


def update_implementation(db_path: str, impl_id: int, updates: dict) -> dict:
    """Update implementation fields."""
    conn = get_connection(db_path)
    allowed_fields = {
        "status", "tests_passed", "tests_total", "lines_of_code", "notes",
        "file_path", "test_file_path",
    }
    set_clauses = []
    values = []
    for field, value in updates.items():
        if field in allowed_fields:
            set_clauses.append(f"{field} = ?")
            values.append(value)

    if not set_clauses:
        conn.close()
        return {"status": "error", "message": "no valid fields to update"}

    values.append(impl_id)
    conn.execute(
        f"UPDATE implementations SET {', '.join(set_clauses)} WHERE id = ?", values
    )
    conn.commit()
    conn.close()
    return {"status": "updated", "id": impl_id}


def query_implementations(db_path: str, algo_id: str | None = None,
                          status: str | None = None) -> list[dict]:
    """Query implementations with optional filters."""
    conn = get_connection(db_path)
    query = "SELECT i.*, a.name as algorithm_name FROM implementations i JOIN algorithms a ON i.algorithm_id = a.id WHERE 1=1"
    params: list = []
    if algo_id:
        query += " AND i.algorithm_id = ?"
        params.append(algo_id)
    if status:
        query += " AND i.status = ?"
        params.append(status)
    query += " ORDER BY i.algorithm_id, i.version"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------
def add_benchmark(db_path: str, benchmark: dict) -> dict:
    """Add a benchmark definition."""
    conn = get_connection(db_path)
    bench_id = benchmark.get("id", "")

    existing = conn.execute("SELECT id FROM benchmarks WHERE id = ?", (bench_id,)).fetchone()
    if existing:
        conn.close()
        return {"status": "duplicate", "existing_id": bench_id}

    conn.execute(
        """INSERT INTO benchmarks (id, name, description, input_generator,
           input_sizes, metrics, warmup_runs, measured_runs)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            bench_id,
            benchmark.get("name", ""),
            benchmark.get("description", ""),
            benchmark.get("input_generator"),
            json.dumps(benchmark.get("input_sizes", [])),
            json.dumps(benchmark.get("metrics", [])),
            benchmark.get("warmup_runs", 3),
            benchmark.get("measured_runs", 10),
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "added", "id": bench_id}


def add_benchmark_result(db_path: str, result: dict) -> dict:
    """Add a benchmark result entry."""
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO benchmark_results
           (benchmark_id, algorithm_id, implementation_id, input_size,
            metric, value, std_dev, min_value, max_value, runs, environment)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            result.get("benchmark_id", ""),
            result.get("algorithm_id", ""),
            result.get("implementation_id"),
            result.get("input_size", 0),
            result.get("metric", ""),
            result.get("value", 0),
            result.get("std_dev"),
            result.get("min_value"),
            result.get("max_value"),
            result.get("runs"),
            json.dumps(result.get("environment", {})),
        ),
    )
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"status": "added", "id": rid}


def query_benchmark_results(db_path: str, algo_id: str | None = None,
                            benchmark_id: str | None = None,
                            metric: str | None = None) -> list[dict]:
    """Query benchmark results with optional filters."""
    conn = get_connection(db_path)
    query = """SELECT br.*, a.name as algorithm_name, b.name as benchmark_name
               FROM benchmark_results br
               JOIN algorithms a ON br.algorithm_id = a.id
               JOIN benchmarks b ON br.benchmark_id = b.id
               WHERE 1=1"""
    params: list = []
    if algo_id:
        query += " AND br.algorithm_id = ?"
        params.append(algo_id)
    if benchmark_id:
        query += " AND br.benchmark_id = ?"
        params.append(benchmark_id)
    if metric:
        query += " AND br.metric = ?"
        params.append(metric)
    query += " ORDER BY br.metric, br.input_size, br.value"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def results_matrix(db_path: str, benchmark_id: str | None = None,
                   metric: str | None = None) -> dict:
    """Build a cross-algorithm results matrix for comparison."""
    conn = get_connection(db_path)
    query = """SELECT br.*, a.name as algorithm_name, a.category
               FROM benchmark_results br
               JOIN algorithms a ON br.algorithm_id = a.id
               WHERE 1=1"""
    params: list = []
    if benchmark_id:
        query += " AND br.benchmark_id = ?"
        params.append(benchmark_id)
    if metric:
        query += " AND br.metric = ?"
        params.append(metric)
    query += " ORDER BY br.metric, br.input_size, br.value"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    matrix: dict[str, list[dict]] = {}
    for row in rows:
        d = dict(row)
        key = f"{d['metric']}@{d['input_size']}"
        if key not in matrix:
            matrix[key] = []
        matrix[key].append(d)

    return {
        "status": "ok",
        "metrics": list({r["metric"] for r in [dict(row) for row in rows]} if rows else set()),
        "total_entries": sum(len(v) for v in matrix.values()),
        "matrix": matrix,
    }


# ---------------------------------------------------------------------------
# Complexity Analysis
# ---------------------------------------------------------------------------
def add_complexity(db_path: str, analysis: dict) -> dict:
    """Add a complexity analysis entry."""
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO complexity_analysis
           (algorithm_id, analysis_type, metric, complexity_class,
            empirical_fit, r_squared, data_points, discrepancy, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            analysis.get("algorithm_id", ""),
            analysis.get("analysis_type", "theoretical"),
            analysis.get("metric", "time"),
            analysis.get("complexity_class", ""),
            analysis.get("empirical_fit"),
            analysis.get("r_squared"),
            json.dumps(analysis.get("data_points", [])),
            analysis.get("discrepancy"),
            analysis.get("notes"),
        ),
    )
    conn.commit()
    cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"status": "added", "id": cid}


def query_complexity(db_path: str, algo_id: str | None = None,
                     analysis_type: str | None = None) -> list[dict]:
    """Query complexity analysis entries."""
    conn = get_connection(db_path)
    query = """SELECT ca.*, a.name as algorithm_name
               FROM complexity_analysis ca
               JOIN algorithms a ON ca.algorithm_id = a.id
               WHERE 1=1"""
    params: list = []
    if algo_id:
        query += " AND ca.algorithm_id = ?"
        params.append(algo_id)
    if analysis_type:
        query += " AND ca.analysis_type = ?"
        params.append(analysis_type)
    query += " ORDER BY ca.algorithm_id, ca.analysis_type, ca.metric"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Invention Log
# ---------------------------------------------------------------------------
def add_invention(db_path: str, entry: dict) -> dict:
    """Add an invention log entry."""
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO invention_log
           (cycle, algorithm_id, strategy, hypothesis, outcome,
            result_summary, insight, feeds_next)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            entry.get("cycle", 1),
            entry.get("algorithm_id"),
            entry.get("strategy", ""),
            entry.get("hypothesis", ""),
            entry.get("outcome"),
            entry.get("result_summary"),
            entry.get("insight"),
            json.dumps(entry.get("feeds_next", [])),
        ),
    )
    conn.commit()
    iid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"status": "added", "id": iid}


def update_invention(db_path: str, inv_id: int, updates: dict) -> dict:
    """Update invention log entry (typically outcome/insight after testing)."""
    conn = get_connection(db_path)
    allowed_fields = {"outcome", "result_summary", "insight", "feeds_next"}
    set_clauses = []
    values = []
    for field, value in updates.items():
        if field in allowed_fields:
            set_clauses.append(f"{field} = ?")
            if field == "feeds_next" and isinstance(value, list):
                values.append(json.dumps(value))
            else:
                values.append(value)

    if not set_clauses:
        conn.close()
        return {"status": "error", "message": "no valid fields to update"}

    values.append(inv_id)
    conn.execute(
        f"UPDATE invention_log SET {', '.join(set_clauses)} WHERE id = ?", values
    )
    conn.commit()
    conn.close()
    return {"status": "updated", "id": inv_id}


def query_inventions(db_path: str, cycle: int | None = None,
                     outcome: str | None = None,
                     strategy: str | None = None) -> list[dict]:
    """Query invention log entries."""
    conn = get_connection(db_path)
    query = "SELECT * FROM invention_log WHERE 1=1"
    params: list = []
    if cycle is not None:
        query += " AND cycle = ?"
        params.append(cycle)
    if outcome:
        query += " AND outcome = ?"
        params.append(outcome)
    if strategy:
        query += " AND strategy = ?"
        params.append(strategy)
    query += " ORDER BY cycle, created_at"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Quality Scores
# ---------------------------------------------------------------------------
def add_quality_score(db_path: str, phase: int, phase_name: str,
                      iteration: int, score: float, threshold: float,
                      dimensions: dict | None = None,
                      feedback: str = "") -> dict:
    """Record a quality evaluation score for a phase."""
    passed = 1 if score >= threshold else 0
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO quality_scores
           (phase, phase_name, iteration, score, passed, threshold, dimensions, feedback)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (phase, phase_name, iteration, score, passed, threshold,
         json.dumps(dimensions or {}), feedback),
    )
    conn.commit()
    conn.close()
    return {"status": "recorded", "passed": bool(passed), "score": score}


def get_quality_history(db_path: str, phase: int | None = None) -> list[dict]:
    """Get quality score history."""
    conn = get_connection(db_path)
    query = "SELECT * FROM quality_scores"
    params: list = []
    if phase is not None:
        query += " WHERE phase = ?"
        params.append(phase)
    query += " ORDER BY created_at ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Agent Messages
# ---------------------------------------------------------------------------
def add_agent_message(db_path: str, from_agent: str, phase: int,
                      iteration: int, message_type: str, content: str,
                      to_agent: str | None = None,
                      metadata: dict | None = None) -> dict:
    """Record an inter-agent message."""
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO agent_messages
           (from_agent, to_agent, phase, iteration, message_type, content, metadata)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (from_agent, to_agent, phase, iteration, message_type, content,
         json.dumps(metadata or {})),
    )
    conn.commit()
    msg_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"status": "sent", "message_id": msg_id}


def query_messages(db_path: str, phase: int | None = None,
                   to_agent: str | None = None,
                   message_type: str | None = None) -> list[dict]:
    """Query agent messages."""
    conn = get_connection(db_path)
    query = "SELECT * FROM agent_messages WHERE 1=1"
    params: list = []
    if phase is not None:
        query += " AND phase = ?"
        params.append(phase)
    if to_agent:
        query += " AND (to_agent = ? OR to_agent IS NULL)"
        params.append(to_agent)
    if message_type:
        query += " AND message_type = ?"
        params.append(message_type)
    query += " ORDER BY created_at ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------
def get_stats(db_path: str) -> dict:
    """Get database statistics."""
    conn = get_connection(db_path)
    stats = {}

    stats["total_algorithms"] = conn.execute("SELECT COUNT(*) FROM algorithms").fetchone()[0]
    stats["algorithms_by_category"] = {}
    for row in conn.execute("SELECT category, COUNT(*) as cnt FROM algorithms GROUP BY category"):
        stats["algorithms_by_category"][row["category"]] = row["cnt"]
    stats["algorithms_by_status"] = {}
    for row in conn.execute("SELECT status, COUNT(*) as cnt FROM algorithms GROUP BY status"):
        stats["algorithms_by_status"][row["status"]] = row["cnt"]

    stats["total_implementations"] = conn.execute("SELECT COUNT(*) FROM implementations").fetchone()[0]
    stats["implementations_by_status"] = {}
    for row in conn.execute("SELECT status, COUNT(*) as cnt FROM implementations GROUP BY status"):
        stats["implementations_by_status"][row["status"]] = row["cnt"]

    stats["total_benchmarks"] = conn.execute("SELECT COUNT(*) FROM benchmarks").fetchone()[0]
    stats["total_benchmark_results"] = conn.execute("SELECT COUNT(*) FROM benchmark_results").fetchone()[0]
    stats["total_complexity_analyses"] = conn.execute("SELECT COUNT(*) FROM complexity_analysis").fetchone()[0]

    stats["total_inventions"] = conn.execute("SELECT COUNT(*) FROM invention_log").fetchone()[0]
    stats["inventions_by_outcome"] = {}
    for row in conn.execute("SELECT outcome, COUNT(*) as cnt FROM invention_log WHERE outcome IS NOT NULL GROUP BY outcome"):
        stats["inventions_by_outcome"][row["outcome"]] = row["cnt"]

    stats["total_quality_scores"] = conn.execute("SELECT COUNT(*) FROM quality_scores").fetchone()[0]
    stats["quality_summary"] = {}
    for row in conn.execute(
        "SELECT phase, phase_name, AVG(score) as avg_score, COUNT(*) as attempts, "
        "SUM(passed) as passes FROM quality_scores GROUP BY phase"
    ):
        stats["quality_summary"][row["phase"]] = {
            "phase_name": row["phase_name"],
            "avg_score": round(row["avg_score"], 3),
            "attempts": row["attempts"],
            "passes": row["passes"],
        }

    stats["total_agent_messages"] = conn.execute("SELECT COUNT(*) FROM agent_messages").fetchone()[0]

    conn.close()
    return stats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _row_to_algo(row: sqlite3.Row) -> dict:
    """Convert a database row to an algorithm dict."""
    d = dict(row)
    for json_field in ("parent_ids", "components"):
        if d.get(json_field):
            d[json_field] = json.loads(d[json_field])
    return d


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Algorithmic research database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    init_p = subparsers.add_parser("init", help="Initialize database")
    init_p.add_argument("--db-path", required=True)

    # add-algorithm
    aa = subparsers.add_parser("add-algorithm", help="Add an algorithm")
    aa.add_argument("--db-path", required=True)
    aa.add_argument("--algo-json", required=True)

    # update-algorithm
    ua = subparsers.add_parser("update-algorithm", help="Update algorithm fields")
    ua.add_argument("--db-path", required=True)
    ua.add_argument("--algo-id", required=True)
    ua.add_argument("--updates-json", required=True)

    # query-algorithms
    qa = subparsers.add_parser("query-algorithms", help="Query algorithms")
    qa.add_argument("--db-path", required=True)
    qa.add_argument("--category", default=None, choices=["known", "invented"])
    qa.add_argument("--status", default=None)
    qa.add_argument("--domain", default=None)

    # add-implementation
    ai = subparsers.add_parser("add-implementation", help="Add implementation")
    ai.add_argument("--db-path", required=True)
    ai.add_argument("--algo-id", required=True)
    ai.add_argument("--impl-json", required=True)

    # update-implementation
    ui = subparsers.add_parser("update-implementation", help="Update implementation")
    ui.add_argument("--db-path", required=True)
    ui.add_argument("--impl-id", type=int, required=True)
    ui.add_argument("--updates-json", required=True)

    # query-implementations
    qi = subparsers.add_parser("query-implementations", help="Query implementations")
    qi.add_argument("--db-path", required=True)
    qi.add_argument("--algo-id", default=None)
    qi.add_argument("--status", default=None)

    # add-benchmark
    ab = subparsers.add_parser("add-benchmark", help="Add benchmark definition")
    ab.add_argument("--db-path", required=True)
    ab.add_argument("--benchmark-json", required=True)

    # add-benchmark-result
    abr = subparsers.add_parser("add-benchmark-result", help="Add benchmark result")
    abr.add_argument("--db-path", required=True)
    abr.add_argument("--result-json", required=True)

    # query-results
    qr = subparsers.add_parser("query-results", help="Query benchmark results")
    qr.add_argument("--db-path", required=True)
    qr.add_argument("--algo-id", default=None)
    qr.add_argument("--benchmark-id", default=None)
    qr.add_argument("--metric", default=None)

    # results-matrix
    rm = subparsers.add_parser("results-matrix", help="Build cross-algorithm results matrix")
    rm.add_argument("--db-path", required=True)
    rm.add_argument("--benchmark-id", default=None)
    rm.add_argument("--metric", default=None)

    # add-complexity
    ac = subparsers.add_parser("add-complexity", help="Add complexity analysis")
    ac.add_argument("--db-path", required=True)
    ac.add_argument("--complexity-json", required=True)

    # query-complexity
    qc = subparsers.add_parser("query-complexity", help="Query complexity analysis")
    qc.add_argument("--db-path", required=True)
    qc.add_argument("--algo-id", default=None)
    qc.add_argument("--analysis-type", default=None, choices=["theoretical", "empirical"])

    # add-invention
    ainv = subparsers.add_parser("add-invention", help="Add invention log entry")
    ainv.add_argument("--db-path", required=True)
    ainv.add_argument("--invention-json", required=True)

    # update-invention
    uinv = subparsers.add_parser("update-invention", help="Update invention log entry")
    uinv.add_argument("--db-path", required=True)
    uinv.add_argument("--inv-id", type=int, required=True)
    uinv.add_argument("--updates-json", required=True)

    # query-inventions
    qinv = subparsers.add_parser("query-inventions", help="Query invention log")
    qinv.add_argument("--db-path", required=True)
    qinv.add_argument("--cycle", type=int, default=None)
    qinv.add_argument("--outcome", default=None, choices=["success", "partial", "failure"])
    qinv.add_argument("--strategy", default=None)

    # add-quality-score
    aqs = subparsers.add_parser("add-quality-score", help="Record quality score")
    aqs.add_argument("--db-path", required=True)
    aqs.add_argument("--phase", type=int, required=True)
    aqs.add_argument("--phase-name", required=True)
    aqs.add_argument("--iteration", type=int, required=True)
    aqs.add_argument("--score", type=float, required=True)
    aqs.add_argument("--threshold", type=float, default=0.7)
    aqs.add_argument("--dimensions-json", default="{}")
    aqs.add_argument("--feedback", default="")

    # quality-history
    qh = subparsers.add_parser("quality-history", help="Get quality scores")
    qh.add_argument("--db-path", required=True)
    qh.add_argument("--phase", type=int, default=None)

    # add-message
    am = subparsers.add_parser("add-message", help="Record agent message")
    am.add_argument("--db-path", required=True)
    am.add_argument("--from-agent", required=True)
    am.add_argument("--phase", type=int, required=True)
    am.add_argument("--iteration", type=int, required=True)
    am.add_argument("--message-type", required=True,
                    choices=["finding", "instruction", "feedback", "question",
                             "decision", "meeting_minutes"])
    am.add_argument("--content", required=True)
    am.add_argument("--to-agent", default=None)
    am.add_argument("--metadata-json", default="{}")

    # query-messages
    qm = subparsers.add_parser("query-messages", help="Query agent messages")
    qm.add_argument("--db-path", required=True)
    qm.add_argument("--phase", type=int, default=None)
    qm.add_argument("--to-agent", default=None)
    qm.add_argument("--message-type", default=None)

    # stats
    sp = subparsers.add_parser("stats", help="Database statistics")
    sp.add_argument("--db-path", required=True)

    args = parser.parse_args()

    if args.command == "init":
        init_db(args.db_path)
        json.dump({"status": "initialized", "path": args.db_path}, sys.stdout, indent=2)

    elif args.command == "add-algorithm":
        result = add_algorithm(args.db_path, json.loads(args.algo_json))
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "update-algorithm":
        result = update_algorithm(args.db_path, args.algo_id, json.loads(args.updates_json))
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "query-algorithms":
        results = query_algorithms(args.db_path, args.category, args.status, args.domain)
        json.dump(results, sys.stdout, indent=2)

    elif args.command == "add-implementation":
        result = add_implementation(args.db_path, args.algo_id, json.loads(args.impl_json))
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "update-implementation":
        result = update_implementation(args.db_path, args.impl_id, json.loads(args.updates_json))
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "query-implementations":
        results = query_implementations(args.db_path, args.algo_id, args.status)
        json.dump(results, sys.stdout, indent=2)

    elif args.command == "add-benchmark":
        result = add_benchmark(args.db_path, json.loads(args.benchmark_json))
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "add-benchmark-result":
        result = add_benchmark_result(args.db_path, json.loads(args.result_json))
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "query-results":
        results = query_benchmark_results(args.db_path, args.algo_id, args.benchmark_id, args.metric)
        json.dump(results, sys.stdout, indent=2)

    elif args.command == "results-matrix":
        matrix = results_matrix(args.db_path, args.benchmark_id, args.metric)
        json.dump(matrix, sys.stdout, indent=2)

    elif args.command == "add-complexity":
        result = add_complexity(args.db_path, json.loads(args.complexity_json))
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "query-complexity":
        results = query_complexity(args.db_path, args.algo_id, args.analysis_type)
        json.dump(results, sys.stdout, indent=2)

    elif args.command == "add-invention":
        result = add_invention(args.db_path, json.loads(args.invention_json))
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "update-invention":
        result = update_invention(args.db_path, args.inv_id, json.loads(args.updates_json))
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "query-inventions":
        results = query_inventions(args.db_path, args.cycle, args.outcome, args.strategy)
        json.dump(results, sys.stdout, indent=2)

    elif args.command == "add-quality-score":
        result = add_quality_score(
            args.db_path, args.phase, args.phase_name, args.iteration,
            args.score, args.threshold,
            json.loads(args.dimensions_json), args.feedback,
        )
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "quality-history":
        history = get_quality_history(args.db_path, args.phase)
        json.dump(history, sys.stdout, indent=2)

    elif args.command == "add-message":
        result = add_agent_message(
            args.db_path, args.from_agent, args.phase, args.iteration,
            args.message_type, args.content, args.to_agent,
            json.loads(args.metadata_json),
        )
        json.dump(result, sys.stdout, indent=2)

    elif args.command == "query-messages":
        messages = query_messages(args.db_path, args.phase, args.to_agent, args.message_type)
        json.dump(messages, sys.stdout, indent=2)

    elif args.command == "stats":
        stats = get_stats(args.db_path)
        json.dump(stats, sys.stdout, indent=2)

    print()


if __name__ == "__main__":
    main()
