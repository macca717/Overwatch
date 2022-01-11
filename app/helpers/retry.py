from __future__ import annotations
import time
from typing import Any
from functools import wraps


def retry(
    exception_to_check,
    tries: int = 4,
    delay: int = 3,
    backoff: int = 2,
    logger: Any | None = None,
):
    """Retry calling the decorated function using an exponential backoff (Blocking).

    Args:
        exception_to_check (Exception): Exception to check
        tries (int, optional): number of times to try (not retry) before giving up. Defaults to 4.
        delay (int, optional): initial delay between retries in seconds. Defaults to 3.
        backoff (int, optional): backoff multiplier e.g. value of 2 will double the delay between each retry. Defaults to 2.
        logger (Logger, optional): logging.Logger instance. Defaults to None.
    """

    def deco_retry(func):
        @wraps(func)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exception_to_check as ex:
                    msg = f"{(str(ex))}, Retrying in {mdelay} seconds..."
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
