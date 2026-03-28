#!/usr/bin/env python3
"""Unit tests for benchmark_utils.py."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from benchmark_utils import (
    detect_outliers,
    format_time,
    get_environment,
    memory_usage,
    run_benchmark,
)


def _slow_func(data):
    """Dummy function that takes some time."""
    total = 0
    for x in data:
        total += x
    return total


def _always_42():
    """Dummy function that always returns 42."""
    return 42


def _allocating_func():
    """Dummy function that allocates memory."""
    return [0] * 100_000


class TestRunBenchmark(unittest.TestCase):
    def test_returns_correct_structure(self):
        # Arrange
        data = list(range(1000))

        # Act
        result = run_benchmark(_slow_func, args=(data,), runs=5, warmup=1)

        # Assert
        self.assertIn("mean_ms", result)
        self.assertIn("std_dev_ms", result)
        self.assertIn("min_ms", result)
        self.assertIn("max_ms", result)
        self.assertIn("runs", result)
        self.assertIn("raw_times_ms", result)
        self.assertEqual(result["runs"], 5)

    def test_mean_is_between_min_and_max(self):
        # Arrange
        data = list(range(100))

        # Act
        result = run_benchmark(_slow_func, args=(data,), runs=5, warmup=1)

        # Assert
        self.assertGreaterEqual(result["mean_ms"], result["min_ms"])
        self.assertLessEqual(result["mean_ms"], result["max_ms"])

    def test_std_dev_is_non_negative(self):
        # Arrange
        data = list(range(100))

        # Act
        result = run_benchmark(_slow_func, args=(data,), runs=5, warmup=1)

        # Assert
        self.assertGreaterEqual(result["std_dev_ms"], 0)

    def test_min_is_non_negative(self):
        # Arrange
        data = list(range(100))

        # Act
        result = run_benchmark(_slow_func, args=(data,), runs=3, warmup=1)

        # Assert
        self.assertGreaterEqual(result["min_ms"], 0)

    def test_warmup_runs_not_counted(self):
        # Arrange
        data = list(range(100))

        # Act
        result = run_benchmark(_slow_func, args=(data,), runs=3, warmup=5)

        # Assert — only measured runs should be counted
        self.assertEqual(result["runs"], 3)
        self.assertEqual(len(result["raw_times_ms"]), 3)

    def test_raw_times_length_matches_runs(self):
        # Arrange & Act
        result = run_benchmark(_always_42, runs=7, warmup=0)

        # Assert
        self.assertEqual(len(result["raw_times_ms"]), 7)

    def test_invalid_runs_raises(self):
        # Act & Assert
        with self.assertRaises(ValueError):
            run_benchmark(_always_42, runs=0)

    def test_invalid_warmup_raises(self):
        # Act & Assert
        with self.assertRaises(ValueError):
            run_benchmark(_always_42, runs=1, warmup=-1)

    def test_median_present(self):
        # Act
        result = run_benchmark(_always_42, runs=5, warmup=0)

        # Assert
        self.assertIn("median_ms", result)


class TestDetectOutliers(unittest.TestCase):
    def test_identifies_outliers(self):
        # Arrange — values with one clear outlier
        values = [10.0, 10.1, 9.9, 10.2, 9.8, 10.0, 50.0]

        # Act
        outlier_indices = detect_outliers(values)

        # Assert — index 6 (value 50.0) should be an outlier
        self.assertIn(6, outlier_indices)

    def test_no_outliers_in_uniform_data(self):
        # Arrange
        values = [10.0, 10.0, 10.0, 10.0, 10.0]

        # Act
        outlier_indices = detect_outliers(values)

        # Assert
        self.assertEqual(len(outlier_indices), 0)

    def test_returns_list_of_integers(self):
        # Arrange
        values = [1.0, 2.0, 3.0, 100.0]

        # Act
        outlier_indices = detect_outliers(values)

        # Assert
        self.assertIsInstance(outlier_indices, list)
        for idx in outlier_indices:
            self.assertIsInstance(idx, int)

    def test_empty_input(self):
        # Arrange
        values = []

        # Act
        outlier_indices = detect_outliers(values)

        # Assert
        self.assertEqual(len(outlier_indices), 0)

    def test_single_element(self):
        # Arrange
        values = [5.0]

        # Act
        outlier_indices = detect_outliers(values)

        # Assert
        self.assertEqual(len(outlier_indices), 0)

    def test_custom_threshold(self):
        # Arrange — values with a mild outlier
        values = [10.0, 10.1, 9.9, 10.2, 9.8, 12.0]

        # Act — strict threshold should flag more
        strict = detect_outliers(values, threshold=1.0)
        lenient = detect_outliers(values, threshold=3.0)

        # Assert — strict should detect at least as many as lenient
        self.assertGreaterEqual(len(strict), len(lenient))


class TestGetEnvironment(unittest.TestCase):
    def test_returns_required_fields(self):
        # Act
        env = get_environment()

        # Assert
        self.assertIn("cpu", env)
        self.assertIn("ram_total_mb", env)
        self.assertIn("python_version", env)
        self.assertIn("os", env)
        self.assertIn("cpu_count", env)

    def test_python_version_format(self):
        # Act
        env = get_environment()

        # Assert — should be something like "3.12.1"
        self.assertRegex(env["python_version"], r"^\d+\.\d+")

    def test_cpu_is_string(self):
        # Act
        env = get_environment()

        # Assert
        self.assertIsInstance(env["cpu"], str)

    def test_os_is_string(self):
        # Act
        env = get_environment()

        # Assert
        self.assertIsInstance(env["os"], str)

    def test_cpu_count_is_positive(self):
        # Act
        env = get_environment()

        # Assert
        self.assertIsNotNone(env["cpu_count"])
        self.assertGreater(env["cpu_count"], 0)


class TestFormatTime(unittest.TestCase):
    def test_formats_milliseconds(self):
        # Act
        result = format_time(1.23)

        # Assert — should show ms
        self.assertIn("ms", result)
        self.assertIn("1.23", result)

    def test_formats_seconds(self):
        # Act
        result = format_time(1500.0)

        # Assert — should convert to seconds
        self.assertIn("s", result)
        self.assertIn("1.50", result)

    def test_formats_minutes(self):
        # Act
        result = format_time(120000.0)

        # Assert — should convert to minutes
        self.assertIn("min", result)

    def test_formats_sub_millisecond(self):
        # Act
        result = format_time(0.045)

        # Assert — should still show as ms
        self.assertIn("ms", result)

    def test_formats_zero(self):
        # Act
        result = format_time(0.0)

        # Assert — should not raise, should return something meaningful
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_formats_negative(self):
        # Act
        result = format_time(-5.0)

        # Assert — should handle negative gracefully
        self.assertIsInstance(result, str)
        self.assertIn("-", result)


class TestMemoryUsage(unittest.TestCase):
    def test_returns_dict_with_peak_and_current(self):
        # Act
        mem = memory_usage(_allocating_func)

        # Assert
        self.assertIsInstance(mem, dict)
        self.assertIn("peak_mb", mem)
        self.assertIn("current_mb", mem)

    def test_peak_is_non_negative(self):
        # Act
        mem = memory_usage(_allocating_func)

        # Assert
        self.assertGreaterEqual(mem["peak_mb"], 0)

    def test_allocating_function_has_positive_peak(self):
        # Act
        mem = memory_usage(_allocating_func)

        # Assert — allocating 100k ints should use some memory
        self.assertGreater(mem["peak_mb"], 0)

    def test_accepts_args(self):
        # Arrange
        data = list(range(100))

        # Act
        mem = memory_usage(_slow_func, args=(data,))

        # Assert
        self.assertIn("peak_mb", mem)

    def test_accepts_kwargs(self):
        # Arrange
        def func_with_kwargs(x=0):
            return [0] * x

        # Act
        mem = memory_usage(func_with_kwargs, kwargs={"x": 1000})

        # Assert
        self.assertIn("peak_mb", mem)


if __name__ == "__main__":
    unittest.main()
