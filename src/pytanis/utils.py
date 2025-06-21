"""Additional utilities"""

import functools
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

import pandas as pd
from structlog import get_logger

RT = TypeVar('RT')  # return type


def rm_keys(
    keys: Any | list[Any],
    dct: dict[Any, Any],
) -> dict[Any, Any]:
    """Return a copy with keys removed from dictionary"""
    if not isinstance(keys, list):
        keys = [keys]
    return {k: v for k, v in dct.items() if k not in keys}


def pretty_timedelta(seconds: int) -> str:
    """Converts timedelta in seconds to human-readable string

    Args:
        seconds: time delta in seconds

    Returns:
        timedelta as pretty string
    """
    sign = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return f'{sign}{days}d{hours}h{minutes}m{seconds}s'
    elif hours > 0:
        return f'{sign}{hours}h{minutes}m{seconds}s'
    elif minutes > 0:
        return f'{sign}{minutes}m{seconds}s'
    else:
        return f'{sign}{seconds}s'


def throttle(calls: int, seconds: int = 1) -> Callable[[Callable[..., RT]], Callable[..., RT]]:
    """Decorator for throttling a function to number of calls per seconds

    Args:
        calls: number of calls per interval
        seconds: number of seconds in interval

    Returns:
        wrapped function
    """
    if not isinstance(calls, int):
        msg = 'number of calls must be integer'
        raise ValueError(msg)
    if not isinstance(seconds, int):
        msg = 'number of seconds must be integer'
        raise ValueError(msg)

    def decorator(func: Callable[..., RT]) -> Callable[..., RT]:
        # keeps track of the last calls
        last_calls: list[float] = []
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> RT:
            nonlocal last_calls
            with lock:
                curr_time = time.time()
                # Remove old calls
                last_calls = [call for call in last_calls if call > curr_time - seconds]

                if len(last_calls) >= calls:
                    sleep_time = last_calls[0] + seconds - curr_time
                    logger = get_logger()
                    logger.debug('stalling call', func=func.__name__, secs=sleep_time)
                    time.sleep(sleep_time)

                resp = func(*args, **kwargs)
                last_calls.append(time.time())
                return resp

        return wrapper

    return decorator


def implode(df: pd.DataFrame, cols: str | list[str]) -> pd.DataFrame:
    """The inverse of Pandas' explode"""
    if not isinstance(cols, list):
        cols = [cols]
    orig_cols = df.columns
    grp_cols = [col for col in df.columns if col not in cols]
    df = df.groupby(grp_cols, group_keys=True, dropna=False).aggregate({col: lambda x: x.tolist() for col in cols})
    df.reset_index(inplace=True)
    df = df.loc[:, list(orig_cols)]
    return df
