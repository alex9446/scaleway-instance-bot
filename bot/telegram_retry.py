from asyncio import sleep
from logging import getLogger
from typing import Awaitable, Callable, ParamSpec, TypeVar

from telegram.error import TimedOut

from .utils import ExceptionWrapper

MAX_ATTEMPTS = 5

logger = getLogger('uvicorn.error')

P = ParamSpec('P')
T = TypeVar('T')


async def telegram_retry(f: Callable[P, Awaitable[T]],
                         *args: P.args, **kwargs: P.kwargs) -> T:
    for attempt in range(MAX_ATTEMPTS):
        try:
            return await f(*args, **kwargs)
        except TimedOut as e:
            logger.warning('%s at attempt %s', ExceptionWrapper(e), attempt+1)
            await sleep(1)
            if attempt == MAX_ATTEMPTS - 1:
                raise
    assert False
