from __future__ import annotations
import asyncio
from contextlib import suppress
import ctypes
from time import perf_counter
from threading import Timer, current_thread
from typing import Any, Callable, Tuple


__all__ = ["get_elapsed_time_s", "TimeoutAfter"]


def get_elapsed_time_s(func: Callable, *args, **kwargs) -> Tuple[float, Any]:
    """Function timer helper

    Args:
        func (Callable): function to time

    Returns:
        Tuple[float: Any]: A tuple of the elapsed time and the function result
    """
    start = perf_counter()
    result = func(*args, **kwargs)
    stop = perf_counter()
    elapsed = stop - start
    return (elapsed, result)


class RecurringTask:
    def __init__(self, func: Callable, interval: float, **kwargs) -> None:
        """Recurring Asyncio Task

        Includes the ability to stop the task.

        Args:
            func (Callable): Callback function
            interval (float): Interval in seconds
        """
        self._func = func
        self._kwargs = kwargs
        self._interval = interval
        self._task: asyncio.Task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the task"""
        self._task.cancel()

    async def _run(self):
        with suppress(asyncio.CancelledError):
            while True:
                await asyncio.sleep(self._interval)
                self._func(**self._kwargs)


class TimeoutAfter:
    def __init__(self, timeout: float = 10):
        """Context manager to manage a timeout after a given time (Thread based).

        Args:
            timeout (float, optional): Timeout in seconds. Defaults to 10.
        Raises:
            TimeoutError: After the specified timeout is exceeded.
        """
        self._exception = TimeoutError
        self._caller_thread = current_thread()
        self._timer = Timer(timeout, self.raise_caller)
        self._timer.daemon = True
        self._timer.start()

    def __enter__(self):
        try:
            yield
        finally:
            self._timer.cancel()
        return self

    def __exit__(self, *_):
        self._timer.cancel()

    def raise_caller(self):
        ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self._caller_thread.ident), ctypes.py_object(self._exception)  # type: ignore
        )
        if ret == 0:
            raise ValueError("Invalid thread ID")
        elif ret > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self._caller_thread.ident, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
