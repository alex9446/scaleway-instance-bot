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
