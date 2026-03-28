#!/usr/bin/env python3
"""Unit tests for algo_database.py."""

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from algo_database import (
    add_agent_message,
    add_algorithm,
    add_benchmark,
    add_benchmark_result,
    add_complexity,
    add_implementation,
    add_invention,
    add_quality_score,
    get_quality_history,
    get_stats,
    init_db,
    query_algorithms,
    query_benchmark_results,
    query_complexity,
    query_implementations,
    query_inventions,
    query_messages,
    results_matrix,
    update_algorithm,
    update_implementation,
    update_invention,
)

SAMPLE_ALGORITHM = {
    "id": "algo-mergesort",
    "name": "Merge Sort",
    "category": "known",
    "origin": "literature",
    "parent_ids": [],
    "description": "Divide-and-conquer sorting algorithm with O(n log n) worst case.",
    "domain": "sorting",
    "components": {"data_structure": "array", "paradigm": "divide_conquer"},
    "pseudocode": "split, sort halves, merge",
    "theoretical_time": "O(n log n)",
    "theoretical_space": "O(n)",
    "source_url": "https://en.wikipedia.org/wiki/Merge_sort",
    "invention_rationale": None,
    "status": "proposed",
}

SAMPLE_ALGORITHM_2 = {
    "id": "algo-quicksort",
    "name": "Quick Sort",
    "category": "known",
    "origin": "literature",
    "description": "Partition-based sorting with average O(n log n).",
    "domain": "sorting",
    "components": {"data_structure": "array", "paradigm": "divide_conquer", "heuristic": "pivot_selection"},
    "theoretical_time": "O(n log n)",
    "theoretical_space": "O(log n)",
    "status": "proposed",
}

SAMPLE_INVENTED = {
    "id": "algo-hybrid-sort-v1",
    "name": "Hybrid Adaptive Sort v1",
    "category": "invented",
    "origin": "recombination",
    "parent_ids": ["algo-mergesort", "algo-quicksort"],
    "description": "Combines merge sort stability with quicksort partitioning on nearly-sorted data.",
    "domain": "sorting",
    "components": {"data_structure": "array", "paradigm": "hybrid"},
    "theoretical_time": "O(n log n)",
    "theoretical_space": "O(n)",
    "invention_rationale": "Exploit nearly-sorted runs by detecting presortedness.",
    "status": "proposed",
}

SAMPLE_BENCHMARK = {
    "id": "bench-sort-random",
    "name": "Random Array Sorting Benchmark",
    "description": "Benchmark sorting algorithms on uniformly random integer arrays.",
    "input_generator": "random.randint(0, 10**6) for each element",
    "input_sizes": [100, 1000, 10000, 100000],
    "metrics": ["time_ms", "memory_mb", "correctness"],
    "warmup_runs": 3,
    "measured_runs": 10,
}


class TestInitDB(unittest.TestCase):
    def test_init_creates_tables(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        init_db(db_path)

        conn = sqlite3.connect(db_path)
        tables = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()

        self.assertIn("algorithms", tables)
        self.assertIn("implementations", tables)
        self.assertIn("benchmarks", tables)
        self.assertIn("benchmark_results", tables)
        self.assertIn("complexity_analysis", tables)
        self.assertIn("invention_log", tables)
        self.assertIn("quality_scores", tables)
        self.assertIn("agent_messages", tables)
        self.assertIn("schema_version", tables)

    def test_init_sets_schema_version(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        init_db(db_path)

        conn = sqlite3.connect(db_path)
        version = conn.execute("SELECT version FROM schema_version").fetchone()[0]
        conn.close()

        self.assertEqual(version, 1)

    def test_init_is_idempotent(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        init_db(db_path)
        init_db(db_path)

        conn = sqlite3.connect(db_path)
        tables = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()

        self.assertIn("algorithms", tables)


class TestAddAlgorithm(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)

    def test_add_known_algorithm(self):
        result = add_algorithm(self.db_path, SAMPLE_ALGORITHM)

        self.assertEqual(result["status"], "added")
        self.assertEqual(result["id"], "algo-mergesort")

    def test_add_algorithm_checks_all_fields(self):
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)

        algos = query_algorithms(self.db_path)
        self.assertEqual(len(algos), 1)
        algo = algos[0]
        self.assertEqual(algo["name"], "Merge Sort")
        self.assertEqual(algo["category"], "known")
        self.assertEqual(algo["origin"], "literature")
        self.assertEqual(algo["domain"], "sorting")
        self.assertEqual(algo["theoretical_time"], "O(n log n)")
        self.assertEqual(algo["theoretical_space"], "O(n)")
        self.assertIsInstance(algo["components"], dict)
        self.assertEqual(algo["components"]["paradigm"], "divide_conquer")
        self.assertIsInstance(algo["parent_ids"], list)

    def test_add_duplicate_detection(self):
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        result = add_algorithm(self.db_path, SAMPLE_ALGORITHM)

        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(result["existing_id"], "algo-mergesort")

    def test_add_two_different_algorithms(self):
        r1 = add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        r2 = add_algorithm(self.db_path, SAMPLE_ALGORITHM_2)

        self.assertEqual(r1["status"], "added")
        self.assertEqual(r2["status"], "added")

    def test_add_invented_algorithm(self):
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM_2)
        result = add_algorithm(self.db_path, SAMPLE_INVENTED)

        self.assertEqual(result["status"], "added")
        algos = query_algorithms(self.db_path, category="invented")
        self.assertEqual(len(algos), 1)
        self.assertEqual(algos[0]["parent_ids"], ["algo-mergesort", "algo-quicksort"])


class TestUpdateAlgorithm(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)

    def test_update_status(self):
        result = update_algorithm(self.db_path, "algo-mergesort", {
            "status": "implemented",
        })

        self.assertEqual(result["status"], "updated")
        algos = query_algorithms(self.db_path, status="implemented")
        self.assertEqual(len(algos), 1)
        self.assertEqual(algos[0]["status"], "implemented")

    def test_update_components(self):
        new_components = {"data_structure": "linked_list", "paradigm": "divide_conquer"}
        result = update_algorithm(self.db_path, "algo-mergesort", {
            "components": new_components,
        })

        self.assertEqual(result["status"], "updated")
        algos = query_algorithms(self.db_path)
        self.assertEqual(algos[0]["components"]["data_structure"], "linked_list")

    def test_update_invalid_field(self):
        result = update_algorithm(self.db_path, "algo-mergesort", {
            "nonexistent_field": "value",
        })

        self.assertEqual(result["status"], "error")

    def test_update_multiple_fields(self):
        result = update_algorithm(self.db_path, "algo-mergesort", {
            "status": "tested",
            "description": "Updated description",
            "theoretical_time": "O(n)",
        })

        self.assertEqual(result["status"], "updated")
        algos = query_algorithms(self.db_path, status="tested")
        self.assertEqual(len(algos), 1)
        self.assertEqual(algos[0]["description"], "Updated description")


class TestQueryAlgorithms(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM_2)
        add_algorithm(self.db_path, SAMPLE_INVENTED)

    def test_query_all(self):
        algos = query_algorithms(self.db_path)
        self.assertEqual(len(algos), 3)

    def test_query_by_category_known(self):
        algos = query_algorithms(self.db_path, category="known")
        self.assertEqual(len(algos), 2)

    def test_query_by_category_invented(self):
        algos = query_algorithms(self.db_path, category="invented")
        self.assertEqual(len(algos), 1)
        self.assertEqual(algos[0]["id"], "algo-hybrid-sort-v1")

    def test_query_by_status(self):
        update_algorithm(self.db_path, "algo-mergesort", {"status": "implemented"})
        algos = query_algorithms(self.db_path, status="implemented")
        self.assertEqual(len(algos), 1)
        self.assertEqual(algos[0]["id"], "algo-mergesort")

    def test_query_by_domain(self):
        algos = query_algorithms(self.db_path, domain="sorting")
        self.assertEqual(len(algos), 3)

        algos = query_algorithms(self.db_path, domain="graph")
        self.assertEqual(len(algos), 0)

    def test_query_returns_parsed_json_fields(self):
        algos = query_algorithms(self.db_path, category="known")
        self.assertIsInstance(algos[0]["components"], dict)
        self.assertIsInstance(algos[0]["parent_ids"], list)


class TestAddImplementation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)

    def test_add_implementation(self):
        result = add_implementation(self.db_path, "algo-mergesort", {
            "version": 1,
            "language": "python",
            "file_path": "algorithms/known/mergesort.py",
            "test_file_path": "algorithms/tests/test_mergesort.py",
            "tests_passed": 5,
            "tests_total": 5,
            "lines_of_code": 42,
            "status": "tests_pass",
        })

        self.assertEqual(result["status"], "added")
        self.assertIn("id", result)
        self.assertEqual(result["algorithm_id"], "algo-mergesort")

    def test_add_implementation_default_values(self):
        result = add_implementation(self.db_path, "algo-mergesort", {
            "file_path": "algorithms/known/mergesort.py",
        })

        self.assertEqual(result["status"], "added")
        impls = query_implementations(self.db_path, algo_id="algo-mergesort")
        self.assertEqual(len(impls), 1)
        self.assertEqual(impls[0]["language"], "python")
        self.assertEqual(impls[0]["status"], "draft")
        self.assertEqual(impls[0]["version"], 1)


class TestUpdateImplementation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        result = add_implementation(self.db_path, "algo-mergesort", {
            "file_path": "algorithms/known/mergesort.py",
            "status": "draft",
        })
        self.impl_id = result["id"]

    def test_update_test_results(self):
        result = update_implementation(self.db_path, self.impl_id, {
            "tests_passed": 8,
            "tests_total": 10,
            "status": "tests_fail",
        })

        self.assertEqual(result["status"], "updated")
        impls = query_implementations(self.db_path, algo_id="algo-mergesort")
        self.assertEqual(impls[0]["tests_passed"], 8)
        self.assertEqual(impls[0]["tests_total"], 10)
        self.assertEqual(impls[0]["status"], "tests_fail")

    def test_update_status_to_pass(self):
        result = update_implementation(self.db_path, self.impl_id, {
            "status": "tests_pass",
            "tests_passed": 10,
            "tests_total": 10,
        })

        self.assertEqual(result["status"], "updated")

    def test_update_invalid_field(self):
        result = update_implementation(self.db_path, self.impl_id, {
            "nonexistent_field": "value",
        })

        self.assertEqual(result["status"], "error")


class TestQueryImplementations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM_2)
        add_implementation(self.db_path, "algo-mergesort", {
            "file_path": "mergesort.py", "status": "tests_pass",
        })
        add_implementation(self.db_path, "algo-quicksort", {
            "file_path": "quicksort.py", "status": "draft",
        })

    def test_query_all(self):
        impls = query_implementations(self.db_path)
        self.assertEqual(len(impls), 2)

    def test_query_by_algo_id(self):
        impls = query_implementations(self.db_path, algo_id="algo-mergesort")
        self.assertEqual(len(impls), 1)
        self.assertEqual(impls[0]["algorithm_id"], "algo-mergesort")

    def test_query_by_status(self):
        impls = query_implementations(self.db_path, status="tests_pass")
        self.assertEqual(len(impls), 1)
        self.assertEqual(impls[0]["algorithm_id"], "algo-mergesort")

    def test_query_includes_algorithm_name(self):
        impls = query_implementations(self.db_path, algo_id="algo-mergesort")
        self.assertEqual(impls[0]["algorithm_name"], "Merge Sort")


class TestAddBenchmark(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)

    def test_add_benchmark(self):
        result = add_benchmark(self.db_path, SAMPLE_BENCHMARK)

        self.assertEqual(result["status"], "added")
        self.assertEqual(result["id"], "bench-sort-random")

    def test_add_duplicate_benchmark(self):
        add_benchmark(self.db_path, SAMPLE_BENCHMARK)
        result = add_benchmark(self.db_path, SAMPLE_BENCHMARK)

        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(result["existing_id"], "bench-sort-random")


class TestAddBenchmarkResult(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        add_benchmark(self.db_path, SAMPLE_BENCHMARK)

    def test_add_benchmark_result(self):
        result = add_benchmark_result(self.db_path, {
            "benchmark_id": "bench-sort-random",
            "algorithm_id": "algo-mergesort",
            "input_size": 10000,
            "metric": "time_ms",
            "value": 12.5,
            "std_dev": 0.8,
            "min_value": 11.2,
            "max_value": 14.1,
            "runs": 10,
            "environment": {"cpu": "x86_64", "python": "3.12"},
        })

        self.assertEqual(result["status"], "added")
        self.assertIn("id", result)

    def test_add_multiple_results(self):
        for size in [100, 1000, 10000]:
            add_benchmark_result(self.db_path, {
                "benchmark_id": "bench-sort-random",
                "algorithm_id": "algo-mergesort",
                "input_size": size,
                "metric": "time_ms",
                "value": size * 0.001,
            })

        results = query_benchmark_results(self.db_path, algo_id="algo-mergesort")
        self.assertEqual(len(results), 3)


class TestQueryBenchmarkResults(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM_2)
        add_benchmark(self.db_path, SAMPLE_BENCHMARK)
        add_benchmark(self.db_path, {
            "id": "bench-sort-sorted",
            "name": "Sorted Array Benchmark",
            "description": "Benchmark on already sorted arrays.",
            "input_sizes": [1000, 10000],
            "metrics": ["time_ms"],
        })

        add_benchmark_result(self.db_path, {
            "benchmark_id": "bench-sort-random",
            "algorithm_id": "algo-mergesort",
            "input_size": 1000, "metric": "time_ms", "value": 1.2,
        })
        add_benchmark_result(self.db_path, {
            "benchmark_id": "bench-sort-random",
            "algorithm_id": "algo-quicksort",
            "input_size": 1000, "metric": "time_ms", "value": 0.9,
        })
        add_benchmark_result(self.db_path, {
            "benchmark_id": "bench-sort-random",
            "algorithm_id": "algo-mergesort",
            "input_size": 1000, "metric": "memory_mb", "value": 8.0,
        })
        add_benchmark_result(self.db_path, {
            "benchmark_id": "bench-sort-sorted",
            "algorithm_id": "algo-mergesort",
            "input_size": 1000, "metric": "time_ms", "value": 0.5,
        })

    def test_query_by_algo_id(self):
        results = query_benchmark_results(self.db_path, algo_id="algo-mergesort")
        self.assertEqual(len(results), 3)

    def test_query_by_benchmark_id(self):
        results = query_benchmark_results(self.db_path, benchmark_id="bench-sort-random")
        self.assertEqual(len(results), 3)

    def test_query_by_metric(self):
        results = query_benchmark_results(self.db_path, metric="memory_mb")
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0]["value"], 8.0)

    def test_query_combined_filters(self):
        results = query_benchmark_results(
            self.db_path, algo_id="algo-mergesort", metric="time_ms",
        )
        self.assertEqual(len(results), 2)


class TestResultsMatrix(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM_2)
        add_benchmark(self.db_path, SAMPLE_BENCHMARK)

        for algo_id, value in [("algo-mergesort", 1.2), ("algo-quicksort", 0.9)]:
            add_benchmark_result(self.db_path, {
                "benchmark_id": "bench-sort-random",
                "algorithm_id": algo_id,
                "input_size": 1000, "metric": "time_ms", "value": value,
            })
            add_benchmark_result(self.db_path, {
                "benchmark_id": "bench-sort-random",
                "algorithm_id": algo_id,
                "input_size": 10000, "metric": "time_ms", "value": value * 10,
            })

    def test_results_matrix_structure(self):
        matrix = results_matrix(self.db_path)

        self.assertEqual(matrix["status"], "ok")
        self.assertEqual(matrix["total_entries"], 4)
        self.assertIn("time_ms@1000", matrix["matrix"])
        self.assertIn("time_ms@10000", matrix["matrix"])

    def test_results_matrix_entries_per_key(self):
        matrix = results_matrix(self.db_path)

        self.assertEqual(len(matrix["matrix"]["time_ms@1000"]), 2)

    def test_results_matrix_filter_by_metric(self):
        add_benchmark_result(self.db_path, {
            "benchmark_id": "bench-sort-random",
            "algorithm_id": "algo-mergesort",
            "input_size": 1000, "metric": "memory_mb", "value": 5.0,
        })

        matrix = results_matrix(self.db_path, metric="time_ms")
        self.assertIn("time_ms", matrix["metrics"])
        # memory_mb should not appear in the matrix keys
        for key in matrix["matrix"]:
            self.assertTrue(key.startswith("time_ms"))

    def test_results_matrix_empty(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            empty_db = f.name
        init_db(empty_db)

        matrix = results_matrix(empty_db)
        self.assertEqual(matrix["total_entries"], 0)
        self.assertEqual(matrix["matrix"], {})


class TestAddComplexity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)

    def test_add_theoretical_complexity(self):
        result = add_complexity(self.db_path, {
            "algorithm_id": "algo-mergesort",
            "analysis_type": "theoretical",
            "metric": "time",
            "complexity_class": "O(n log n)",
            "notes": "Proven optimal for comparison-based sorting.",
        })

        self.assertEqual(result["status"], "added")
        self.assertIn("id", result)

    def test_add_empirical_complexity(self):
        result = add_complexity(self.db_path, {
            "algorithm_id": "algo-mergesort",
            "analysis_type": "empirical",
            "metric": "time",
            "complexity_class": "O(n log n)",
            "empirical_fit": "y = 0.0012 * n * log2(n) + 0.5",
            "r_squared": 0.998,
            "data_points": [[100, 0.1], [1000, 1.2], [10000, 13.5]],
            "discrepancy": "None significant",
        })

        self.assertEqual(result["status"], "added")


class TestQueryComplexity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM_2)

        add_complexity(self.db_path, {
            "algorithm_id": "algo-mergesort",
            "analysis_type": "theoretical",
            "metric": "time",
            "complexity_class": "O(n log n)",
        })
        add_complexity(self.db_path, {
            "algorithm_id": "algo-mergesort",
            "analysis_type": "empirical",
            "metric": "time",
            "complexity_class": "O(n log n)",
            "r_squared": 0.998,
        })
        add_complexity(self.db_path, {
            "algorithm_id": "algo-quicksort",
            "analysis_type": "theoretical",
            "metric": "time",
            "complexity_class": "O(n log n)",
        })

    def test_query_by_algo_id(self):
        results = query_complexity(self.db_path, algo_id="algo-mergesort")
        self.assertEqual(len(results), 2)

    def test_query_by_type(self):
        results = query_complexity(self.db_path, analysis_type="theoretical")
        self.assertEqual(len(results), 2)

    def test_query_by_algo_and_type(self):
        results = query_complexity(
            self.db_path, algo_id="algo-mergesort", analysis_type="empirical",
        )
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0]["r_squared"], 0.998)


class TestAddInvention(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)

    def test_add_invention(self):
        result = add_invention(self.db_path, {
            "cycle": 1,
            "algorithm_id": "algo-mergesort",
            "strategy": "mutation",
            "hypothesis": "Replacing merge step with in-place merge reduces space to O(1).",
            "outcome": None,
        })

        self.assertEqual(result["status"], "added")
        self.assertIn("id", result)

    def test_add_invention_with_all_fields(self):
        result = add_invention(self.db_path, {
            "cycle": 2,
            "algorithm_id": "algo-mergesort",
            "strategy": "recombination",
            "hypothesis": "Combine merge sort with insertion sort for small subarrays.",
            "outcome": "success",
            "result_summary": "15% faster on arrays < 50 elements.",
            "insight": "Hybrid approaches work well for small inputs.",
            "feeds_next": ["Try with different cutoff thresholds"],
        })

        self.assertEqual(result["status"], "added")


class TestUpdateInvention(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        result = add_invention(self.db_path, {
            "cycle": 1,
            "algorithm_id": "algo-mergesort",
            "strategy": "mutation",
            "hypothesis": "In-place merge to reduce space.",
        })
        self.inv_id = result["id"]

    def test_update_outcome(self):
        result = update_invention(self.db_path, self.inv_id, {
            "outcome": "partial",
            "result_summary": "Space reduced but time increased 20%.",
            "insight": "In-place merge adds overhead for cache misses.",
        })

        self.assertEqual(result["status"], "updated")
        invs = query_inventions(self.db_path, outcome="partial")
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0]["insight"], "In-place merge adds overhead for cache misses.")

    def test_update_feeds_next(self):
        result = update_invention(self.db_path, self.inv_id, {
            "feeds_next": ["Try block merge", "Investigate symmerge"],
        })

        self.assertEqual(result["status"], "updated")

    def test_update_invalid_field(self):
        result = update_invention(self.db_path, self.inv_id, {
            "nonexistent_field": "value",
        })

        self.assertEqual(result["status"], "error")


class TestQueryInventions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM)

        add_invention(self.db_path, {
            "cycle": 1, "strategy": "mutation",
            "hypothesis": "Hypo 1", "outcome": "success",
        })
        add_invention(self.db_path, {
            "cycle": 1, "strategy": "recombination",
            "hypothesis": "Hypo 2", "outcome": "failure",
        })
        add_invention(self.db_path, {
            "cycle": 2, "strategy": "analogy",
            "hypothesis": "Hypo 3", "outcome": "success",
        })

    def test_query_by_cycle(self):
        invs = query_inventions(self.db_path, cycle=1)
        self.assertEqual(len(invs), 2)

    def test_query_by_outcome(self):
        invs = query_inventions(self.db_path, outcome="success")
        self.assertEqual(len(invs), 2)

    def test_query_by_strategy(self):
        invs = query_inventions(self.db_path, strategy="mutation")
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0]["hypothesis"], "Hypo 1")

    def test_query_all(self):
        invs = query_inventions(self.db_path)
        self.assertEqual(len(invs), 3)


class TestQualityScores(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)

    def test_add_passing_score(self):
        result = add_quality_score(
            self.db_path, phase=2, phase_name="ideate",
            iteration=1, score=0.85, threshold=0.7,
            dimensions={"novelty": 0.9, "feasibility": 0.8},
            feedback="Good ideation quality",
        )

        self.assertEqual(result["status"], "recorded")
        self.assertTrue(result["passed"])

    def test_add_failing_score(self):
        result = add_quality_score(
            self.db_path, phase=3, phase_name="implement",
            iteration=1, score=0.5, threshold=0.7,
            feedback="Tests failing",
        )

        self.assertFalse(result["passed"])

    def test_passed_calculation_at_threshold(self):
        result = add_quality_score(
            self.db_path, phase=2, phase_name="ideate",
            iteration=1, score=0.7, threshold=0.7,
        )

        self.assertTrue(result["passed"])

    def test_passed_calculation_below_threshold(self):
        result = add_quality_score(
            self.db_path, phase=2, phase_name="ideate",
            iteration=1, score=0.699, threshold=0.7,
        )

        self.assertFalse(result["passed"])

    def test_quality_history_by_phase(self):
        add_quality_score(self.db_path, 2, "ideate", 1, 0.5, 0.7)
        add_quality_score(self.db_path, 2, "ideate", 2, 0.8, 0.7)
        add_quality_score(self.db_path, 3, "implement", 1, 0.9, 0.7)

        history = get_quality_history(self.db_path, phase=2)
        self.assertEqual(len(history), 2)

    def test_quality_history_all(self):
        add_quality_score(self.db_path, 2, "ideate", 1, 0.5, 0.7)
        add_quality_score(self.db_path, 3, "implement", 1, 0.9, 0.7)

        all_history = get_quality_history(self.db_path)
        self.assertEqual(len(all_history), 2)


class TestAgentMessages(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)

    def test_add_broadcast_message(self):
        result = add_agent_message(
            self.db_path, from_agent="explorer", phase=1, iteration=1,
            message_type="finding",
            content="Found 12 known sorting algorithms for nearly-sorted data.",
        )

        self.assertEqual(result["status"], "sent")
        self.assertIn("message_id", result)

    def test_add_directed_message(self):
        result = add_agent_message(
            self.db_path, from_agent="ideator", phase=2, iteration=1,
            message_type="decision",
            content="Proposing hybrid timsort-mergesort approach.",
            to_agent="implementer",
            metadata={"algorithm_id": "algo-hybrid-v1"},
        )

        self.assertEqual(result["status"], "sent")

    def test_query_messages_by_phase(self):
        add_agent_message(self.db_path, "a", 1, 1, "finding", "msg1")
        add_agent_message(self.db_path, "b", 2, 1, "finding", "msg2")
        add_agent_message(self.db_path, "c", 1, 2, "finding", "msg3")

        msgs = query_messages(self.db_path, phase=1)
        self.assertEqual(len(msgs), 2)

    def test_query_messages_by_type(self):
        add_agent_message(self.db_path, "a", 1, 1, "finding", "msg1")
        add_agent_message(self.db_path, "a", 1, 1, "instruction", "msg2")

        msgs = query_messages(self.db_path, message_type="instruction")
        self.assertEqual(len(msgs), 1)

    def test_query_messages_for_agent(self):
        add_agent_message(self.db_path, "a", 1, 1, "finding", "broadcast")
        add_agent_message(self.db_path, "a", 1, 1, "instruction", "for-b",
                          to_agent="b")
        add_agent_message(self.db_path, "a", 1, 1, "instruction", "for-c",
                          to_agent="c")

        msgs = query_messages(self.db_path, to_agent="b")
        self.assertEqual(len(msgs), 2)  # broadcast + directed to b


class TestStats(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        init_db(self.db_path)

        add_algorithm(self.db_path, SAMPLE_ALGORITHM)
        add_algorithm(self.db_path, SAMPLE_ALGORITHM_2)
        add_algorithm(self.db_path, SAMPLE_INVENTED)

        update_algorithm(self.db_path, "algo-mergesort", {"status": "implemented"})

        add_implementation(self.db_path, "algo-mergesort", {
            "file_path": "mergesort.py", "status": "tests_pass",
        })

        add_benchmark(self.db_path, SAMPLE_BENCHMARK)
        add_benchmark_result(self.db_path, {
            "benchmark_id": "bench-sort-random",
            "algorithm_id": "algo-mergesort",
            "input_size": 1000, "metric": "time_ms", "value": 1.2,
        })

        add_complexity(self.db_path, {
            "algorithm_id": "algo-mergesort",
            "analysis_type": "theoretical",
            "metric": "time",
            "complexity_class": "O(n log n)",
        })

        add_invention(self.db_path, {
            "cycle": 1, "strategy": "mutation",
            "hypothesis": "test", "outcome": "success",
        })

        add_quality_score(self.db_path, 2, "ideate", 1, 0.85, 0.7)
        add_agent_message(self.db_path, "explorer", 1, 1, "finding", "msg")

    def test_stats_total_algorithms(self):
        stats = get_stats(self.db_path)
        self.assertEqual(stats["total_algorithms"], 3)

    def test_stats_algorithms_by_category(self):
        stats = get_stats(self.db_path)
        self.assertEqual(stats["algorithms_by_category"]["known"], 2)
        self.assertEqual(stats["algorithms_by_category"]["invented"], 1)

    def test_stats_algorithms_by_status(self):
        stats = get_stats(self.db_path)
        self.assertEqual(stats["algorithms_by_status"]["implemented"], 1)
        self.assertEqual(stats["algorithms_by_status"]["proposed"], 2)

    def test_stats_implementations(self):
        stats = get_stats(self.db_path)
        self.assertEqual(stats["total_implementations"], 1)
        self.assertEqual(stats["implementations_by_status"]["tests_pass"], 1)

    def test_stats_benchmarks(self):
        stats = get_stats(self.db_path)
        self.assertEqual(stats["total_benchmarks"], 1)
        self.assertEqual(stats["total_benchmark_results"], 1)

    def test_stats_complexity(self):
        stats = get_stats(self.db_path)
        self.assertEqual(stats["total_complexity_analyses"], 1)

    def test_stats_inventions(self):
        stats = get_stats(self.db_path)
        self.assertEqual(stats["total_inventions"], 1)
        self.assertEqual(stats["inventions_by_outcome"]["success"], 1)

    def test_stats_quality_scores(self):
        stats = get_stats(self.db_path)
        self.assertEqual(stats["total_quality_scores"], 1)
        self.assertIn(2, stats["quality_summary"])

    def test_stats_agent_messages(self):
        stats = get_stats(self.db_path)
        self.assertEqual(stats["total_agent_messages"], 1)


if __name__ == "__main__":
    unittest.main()
