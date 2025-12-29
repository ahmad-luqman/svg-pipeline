"""Executor abstraction for parallel processing."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")


class ExecutorType(Enum):
    """Available executor types."""

    SEQUENTIAL = "sequential"
    THREADPOOL = "threadpool"
    PROCESSPOOL = "processpool"


@dataclass
class TaskResult:
    """Result of a task execution."""

    success: bool
    result: Any | None = None
    error: Exception | None = None


class Executor(ABC):
    """Abstract base class for task executors."""

    @abstractmethod
    def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> Future[T] | T:
        """Submit a task for execution.

        Args:
            fn: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future or direct result depending on executor type
        """
        ...

    @abstractmethod
    def map(self, fn: Callable[..., T], *iterables: Any) -> list[T]:
        """Map a function over iterables.

        Args:
            fn: Function to apply
            *iterables: Iterables to map over

        Returns:
            List of results
        """
        ...

    @abstractmethod
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor.

        Args:
            wait: Whether to wait for pending tasks
        """
        ...

    def __enter__(self) -> "Executor":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown(wait=True)


class SequentialExecutor(Executor):
    """Executor that runs tasks sequentially (no parallelism).

    This is the default and simplest executor, useful for debugging
    and when parallelism overhead isn't worth it.
    """

    def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function immediately and return result."""
        return fn(*args, **kwargs)

    def map(self, fn: Callable[..., T], *iterables: Any) -> list[T]:
        """Map function sequentially over iterables."""
        return [fn(*args) for args in zip(*iterables)]

    def shutdown(self, wait: bool = True) -> None:
        """No-op for sequential executor."""
        pass


class ThreadPoolTaskExecutor(Executor):
    """Executor using a thread pool for concurrent I/O-bound tasks.

    Best for tasks that spend time waiting (file I/O, network).
    """

    def __init__(self, max_workers: int | None = None):
        """Initialize thread pool executor.

        Args:
            max_workers: Maximum number of threads (default: CPU count + 4)
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> Future[T]:
        """Submit task to thread pool."""
        return self._executor.submit(fn, *args, **kwargs)

    def map(self, fn: Callable[..., T], *iterables: Any) -> list[T]:
        """Map function concurrently over iterables."""
        return list(self._executor.map(fn, *iterables))

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown thread pool."""
        self._executor.shutdown(wait=wait)


class ProcessPoolTaskExecutor(Executor):
    """Executor using a process pool for CPU-bound tasks.

    Best for computationally intensive tasks that can benefit
    from multiple CPU cores.

    Note: Functions and arguments must be picklable.
    """

    def __init__(self, max_workers: int | None = None):
        """Initialize process pool executor.

        Args:
            max_workers: Maximum number of processes (default: CPU count)
        """
        self._executor = ProcessPoolExecutor(max_workers=max_workers)

    def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> Future[T]:
        """Submit task to process pool."""
        return self._executor.submit(fn, *args, **kwargs)

    def map(self, fn: Callable[..., T], *iterables: Any) -> list[T]:
        """Map function across processes."""
        return list(self._executor.map(fn, *iterables))

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown process pool."""
        self._executor.shutdown(wait=wait)


def create_executor(
    executor_type: ExecutorType | str = ExecutorType.SEQUENTIAL,
    max_workers: int | None = None,
) -> Executor:
    """Factory function to create an executor.

    Args:
        executor_type: Type of executor to create
        max_workers: Maximum workers for parallel executors

    Returns:
        Configured executor instance
    """
    if isinstance(executor_type, str):
        executor_type = ExecutorType(executor_type)

    match executor_type:
        case ExecutorType.SEQUENTIAL:
            return SequentialExecutor()
        case ExecutorType.THREADPOOL:
            return ThreadPoolTaskExecutor(max_workers=max_workers)
        case ExecutorType.PROCESSPOOL:
            return ProcessPoolTaskExecutor(max_workers=max_workers)
        case _:
            raise ValueError(f"Unknown executor type: {executor_type}")
