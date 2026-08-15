from os import getenv
from time import sleep

from requests import get, post
from requests.exceptions import ConnectionError

SECRET_HEADER = 'X-Telegram-Bot-Api-Secret-Token'
BOT_TOKEN = getenv('BOT_TOKEN')
SECRET_TOKEN = getenv('SECRET_TOKEN')
TIMEOUT = 30
LOCALHOST = 'http://localhost:8000/webhook'

if not (BOT_TOKEN and SECRET_TOKEN):
    required_variables = 'BOT_TOKEN, SECRET_TOKEN'
    raise RuntimeError(f'missing required variables: {required_variables}')


offset = 0

while True:
    print('get updates...')
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
    url += f'?offset={offset}&timeout={TIMEOUT}'

    try:
        data = get(url, timeout=TIMEOUT*2).json()
    except KeyboardInterrupt:
        break

    if data['ok'] and data['result']:
        print('new update')
        update = data['result'][0]

        try:
            headers = {SECRET_HEADER: SECRET_TOKEN}
            post(LOCALHOST, json=update, headers=headers)
            offset = update['update_id'] + 1
        except ConnectionError:
            print(f'{LOCALHOST} connection error!')
            sleep(5)
