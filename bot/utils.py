from logging import getLogger
from pathlib import Path
from socket import create_connection

logger = getLogger('uvicorn.error')


def can_reach_telegram():
    try:
        with create_connection(('api.telegram.org', 443), timeout=5):
            return True
    except Exception:
        return False


def get_build_info():
    info_path = Path(__file__).resolve().parent.parent / 'build-info.txt'
    error_message = f'{info_path} file not found!'
    return info_path.read_text() if info_path.is_file() else error_message


class ExceptionWrapper:
    def __init__(self, exception: BaseException | None):
        self.e = exception

    def __str__(self):
        if self.e is None:
            return 'No exception'
        t = type(self.e)
        fullname = f'{t.__module__}.{t.__qualname__}'
        return f'{fullname}: {self.e}' if str(self.e) else fullname

    @property
    def parent(self):
        p = self.e and (self.e.__cause__ or self.e.__context__)
        return p and ExceptionWrapper(p)

    def as_chain(self):
        if p := self.parent:
            return f'{p.as_chain()} -> {self}'
        return str(self)
