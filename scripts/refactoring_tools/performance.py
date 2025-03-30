"""Performance analysis tools for the refactoring system."""

import cProfile
import io
import logging
import pstats
import sys
import tracemalloc
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .context import RefactoringContext

logger = logging.getLogger(__name__)


@dataclass
class ProfileStats:
    """Statistics from profiling a function."""

    total_time: float
    calls: int
    time_per_call: float
    cumulative_time: float
    callers: List[str]
    callees: List[str]


@dataclass
class MemoryStats:
    """Statistics from memory tracking."""

    current_size: int
    peak_size: int
    traceback: List[str]
    allocations: List[Tuple[int, List[str]]]  # (size, traceback)


class ProfileCollector:
    """Collect performance metrics using cProfile."""

    def __init__(self, context: RefactoringContext):
        self.context = context
        self._profiler = cProfile.Profile()
        self._stats: Optional[pstats.Stats] = None

    def start_profiling(self) -> None:
        """Start collecting profile data."""
        self._profiler.enable()

    def stop_profiling(self) -> None:
        """Stop collecting profile data."""
        self._profiler.disable()
        self._stats = pstats.Stats(self._profiler)
        self._stats.strip_dirs()
        self._stats.sort_stats("cumulative")

    def get_stats(self, top_n: int = 10) -> List[ProfileStats]:
        """Get profiling statistics.

        Args:
            top_n: Number of top functions to return

        Returns:
            List of profile statistics for top functions
        """
        if not self._stats:
            return []

        try:
            # Capture stats output using StringIO
            stream = io.StringIO()
            original_stdout = sys.stdout
            sys.stdout = stream

            try:
                self._stats.print_stats()
                self._stats.print_callers()
                self._stats.print_callees()
            finally:
                sys.stdout = original_stdout

            # Parse the output
            output = stream.getvalue()
            lines = output.split("\n")

            # Extract function stats
            stats = []
            in_stats = False
            current_func = None

            for line in lines:
                if line.strip().startswith("ncalls"):
                    in_stats = True
                    continue

                if in_stats and line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        calls = int(parts[0].split("/")[0])
                        total_time = float(parts[1])
                        time_per_call = float(parts[2])
                        cumulative_time = float(parts[3])
                        func_name = parts[5]

                        stats.append(
                            ProfileStats(
                                total_time=total_time,
                                calls=calls,
                                time_per_call=time_per_call,
                                cumulative_time=cumulative_time,
                                callers=self._get_callers(func_name, lines),
                                callees=self._get_callees(func_name, lines),
                            )
                        )

                        if len(stats) >= top_n:
                            break

            return stats
        except Exception as e:
            self.context.logger.error(f"Failed to get profile stats: {e}")
            return []

    def _get_callers(self, func_name: str, lines: List[str]) -> List[str]:
        """Extract callers of a function from stats output."""
        callers = []
        in_callers = False

        for line in lines:
            if line.strip().startswith("Called by:"):
                in_callers = True
                continue

            if in_callers and line.strip():
                if "->" in line:  # New function section
                    break
                parts = line.strip().split()
                if len(parts) >= 2:
                    callers.append(parts[-1])

        return callers

    def _get_callees(self, func_name: str, lines: List[str]) -> List[str]:
        """Extract functions called by a function from stats output."""
        callees = []
        in_callees = False

        for line in lines:
            if line.strip().startswith("Calls:"):
                in_callees = True
                continue

            if in_callees and line.strip():
                if "->" in line:  # New function section
                    break
                parts = line.strip().split()
                if len(parts) >= 2:
                    callees.append(parts[-1])

        return callees


class MemoryTracker:
    """Track memory usage of functions."""

    def __init__(self, context: RefactoringContext):
        self.context = context
        self._tracking = False

    def start_tracking(self) -> None:
        """Start tracking memory allocations."""
        tracemalloc.start()
        self._tracking = True

    def stop_tracking(self) -> None:
        """Stop tracking memory allocations."""
        if self._tracking:
            tracemalloc.stop()
            self._tracking = False

    def get_snapshot(self) -> MemoryStats:
        """Get current memory usage statistics.

        Returns:
            Memory statistics including current usage and peak
        """
        if not self._tracking:
            return MemoryStats(0, 0, [], [])

        try:
            snapshot = tracemalloc.take_snapshot()
            stats = snapshot.statistics("lineno")

            current = tracemalloc.get_traced_memory()
            peak = tracemalloc.get_tracemalloc_memory()

            # Get top allocations
            allocations = []
            for stat in stats[:10]:  # Top 10 allocations
                size = stat.size
                trace = [f"{frame.filename}:{frame.lineno}" for frame in stat.traceback]
                allocations.append((size, trace))

            # Get current traceback
            frames = traceback.extract_stack()
            traceback_lines = [f"{frame.filename}:{frame.lineno}" for frame in frames]

            return MemoryStats(
                current_size=current[0],
                peak_size=peak,
                traceback=traceback_lines,
                allocations=allocations,
            )
        except Exception as e:
            self.context.logger.error(f"Failed to get memory stats: {e}")
            return MemoryStats(0, 0, [], [])
