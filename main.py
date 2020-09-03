import os
import logging

import requests
import telegram


telegram_token = os.getenv("TELEGRAM_TOKEN")
chat_id = 105427506


class LogsToTelegramHandler(logging.Handler):
    """Обработчик логов, который шлет их в телеграм канал."""
    def __init__(self):
        super().__init__()
        log_bot = telegram.Bot(token=telegram_token)

    def emit(self, record):
        log_entry = self.format(record)
        bot.send_message(
          chat_id=chat_id, text=log_entry,
          parse_mode=telegram.ParseMode.HTML,
          disable_web_page_preview=True
        )

logger = logging.getLogger("devman_notifications_bot")
logger.setLevel(logging.INFO)
logger.addHandler(LogsToTelegramHandler())


bot = telegram.Bot(token=telegram_token)

devman_token = os.getenv("DEVMAN_TOKEN")
headers = {
  "Authorization": f"Token {devman_token}"
}

check_list_url = 'https://dvmn.org/api/long_polling/'
payload = {}

logger.info('Devman notifications bot started.')

while True:
    try:
      response = requests.get(check_list_url, headers=headers, params=payload, timeout=100)
      response.raise_for_status()
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
      continue

    response_dict = response.json()
    status = response_dict.get('status')
    if status == 'found':
      for attempt in response_dict.get('new_attempts', []):
        is_negative = attempt.get('is_negative')
        result = "К сожалению в работе нашлись ошибки"
        if is_negative is False:
          result = "Преподавателю все понравилось, можно приступать к следующему уроку!"

        lesson_title = attempt.get('lesson_title')

        lesson_url = attempt.get('lesson_url')
        lesson_url = f'https://dvmn.org{lesson_url}'
        
        msg = f'У вас проверили работу <a href="{lesson_url}">{lesson_title}</a>\n\n{result}'

        bot.send_message(
          chat_id=chat_id, text=msg,
          parse_mode=telegram.ParseMode.HTML,
          disable_web_page_preview=True
        )

    elif status == 'timeout':
      payload['timestamp'] = response_dict.get('timestamp_to_request')
