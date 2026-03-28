#!/usr/bin/env python3
"""
Benchmarking utilities for the Algorithmic Research Loop plugin.

Provides statistically rigorous benchmarking with environment reporting,
outlier detection, and memory profiling. Uses only Python stdlib
(tracemalloc, time, platform, os, etc.).

Usage:
    python3 benchmark_utils.py env

Programmatic usage:
    from benchmark_utils import run_benchmark, memory_usage, detect_outliers

    result = run_benchmark(my_func, args=(data,), warmup=3, runs=10)
    mem = memory_usage(my_func, args=(data,))
    outliers = detect_outliers(result["raw_times"])
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
import tracemalloc
from typing import Optional


# ---------------------------------------------------------------------------
# Benchmarking
# ---------------------------------------------------------------------------

def run_benchmark(func: callable, args: tuple = (), kwargs: Optional[dict] = None,
                  warmup: int = 3, runs: int = 10) -> dict:
    """Run a function multiple times and collect timing statistics.

    Args:
        func: The callable to benchmark.
        args: Positional arguments to pass to func.
        kwargs: Keyword arguments to pass to func.
        warmup: Number of warmup iterations (not measured).
        runs: Number of measured iterations.

    Returns:
        Dict with mean, std_dev, min, max, median, raw_times (all in ms),
        plus warmup and runs counts.

    Raises:
        ValueError: If runs < 1 or warmup < 0.
    """
    if runs < 1:
        raise ValueError(f"runs must be >= 1, got {runs}")
    if warmup < 0:
        raise ValueError(f"warmup must be >= 0, got {warmup}")

    if kwargs is None:
        kwargs = {}

    # Warmup phase
    for _ in range(warmup):
        func(*args, **kwargs)

    # Measured phase
    raw_times_ms = []
    for _ in range(runs):
        start = time.perf_counter()
        func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        raw_times_ms.append(elapsed_ms)

    mean = sum(raw_times_ms) / len(raw_times_ms)
    # Use sample variance (Bessel's correction) for unbiased estimate with small samples
    divisor = len(raw_times_ms) - 1 if len(raw_times_ms) > 1 else 1
    variance = sum((t - mean) ** 2 for t in raw_times_ms) / divisor
    std_dev = variance ** 0.5
    sorted_times = sorted(raw_times_ms)
    n = len(sorted_times)
    if n % 2 == 1:
        median = sorted_times[n // 2]
    else:
        median = (sorted_times[n // 2 - 1] + sorted_times[n // 2]) / 2.0

    return {
        "mean_ms": round(mean, 4),
        "std_dev_ms": round(std_dev, 4),
        "min_ms": round(min(raw_times_ms), 4),
        "max_ms": round(max(raw_times_ms), 4),
        "median_ms": round(median, 4),
        "raw_times_ms": [round(t, 4) for t in raw_times_ms],
        "warmup": warmup,
        "runs": runs,
    }


# ---------------------------------------------------------------------------
# Outlier detection
# ---------------------------------------------------------------------------

def detect_outliers(times: list[float], threshold: float = 2.0) -> list[int]:
    """Detect outlier indices using z-score method.

    An observation is flagged as an outlier if its absolute z-score exceeds
    the given threshold (default: 2.0 standard deviations from the mean).

    Args:
        times: List of timing measurements.
        threshold: Z-score threshold for outlier classification.

    Returns:
        List of indices that are outliers.
    """
    if len(times) < 2:
        return []

    mean = sum(times) / len(times)
    # Use sample variance (Bessel's correction) for unbiased estimate
    divisor = len(times) - 1 if len(times) > 1 else 1
    variance = sum((t - mean) ** 2 for t in times) / divisor
    std_dev = variance ** 0.5

    if std_dev == 0.0:
        return []

    outliers = []
    for i, t in enumerate(times):
        z_score = abs(t - mean) / std_dev
        if z_score > threshold:
            outliers.append(i)

    return outliers


# ---------------------------------------------------------------------------
# Environment info
# ---------------------------------------------------------------------------

def get_environment() -> dict:
    """Collect environment information for benchmark reproducibility.

    Returns:
        Dict with cpu, cpu_count, ram_total_mb, python_version, os, os_version,
        architecture, and hostname.
    """
    ram_total_mb = _get_total_ram_mb()

    return {
        "cpu": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "ram_total_mb": ram_total_mb,
        "python_version": platform.python_version(),
        "os": platform.system(),
        "os_version": platform.release(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
    }


def _get_total_ram_mb() -> Optional[int]:
    """Read total RAM from /proc/meminfo (Linux) or fallback to None."""
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    # Line format: "MemTotal:       16384000 kB"
                    kb = int(line.split()[1])
                    return kb // 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_time(ms: float) -> str:
    """Convert milliseconds to a human-readable string.

    Examples:
        0.045   -> "0.05ms"
        1.234   -> "1.23ms"
        1500.0  -> "1.50s"
        95000.0 -> "1.58min"
    """
    if ms < 0:
        return f"-{format_time(-ms)}"

    if ms < 1000.0:
        return f"{ms:.2f}ms"
    elif ms < 60000.0:
        return f"{ms / 1000.0:.2f}s"
    else:
        return f"{ms / 60000.0:.2f}min"


# ---------------------------------------------------------------------------
# Memory profiling
# ---------------------------------------------------------------------------

def memory_usage(func: callable, args: tuple = (), kwargs: Optional[dict] = None) -> dict:
    """Measure peak memory usage of a function call using tracemalloc.

    Args:
        func: The callable to profile.
        args: Positional arguments to pass to func.
        kwargs: Keyword arguments to pass to func.

    Returns:
        Dict with peak_mb (peak memory allocated during the call) and
        current_mb (memory still allocated after the call).
    """
    if kwargs is None:
        kwargs = {}

    tracemalloc.start()
    try:
        func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    return {
        "peak_mb": round(peak / (1024 * 1024), 4),
        "current_mb": round(current / (1024 * 1024), 4),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmarking utilities for the Algorithmic Research Loop"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("env", help="Print environment info as JSON")

    args = parser.parse_args()

    if args.command == "env":
        env_info = get_environment()
        json.dump(env_info, sys.stdout, indent=2, ensure_ascii=False)
        print()


if __name__ == "__main__":
    main()
