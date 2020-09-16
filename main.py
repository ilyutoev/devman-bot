import os
import logging
import time

import requests
import telegram


class LogsToTelegramHandler(logging.Handler):
    """Обработчик логов, который шлет их в телеграм канал."""
    def __init__(self, telegram_token, chat_id):
        super().__init__()
        self.chat_id = chat_id
        log_bot = telegram.Bot(token=telegram_token)

    def emit(self, record):
        log_entry = self.format(record)
        bot.send_message(
          chat_id=self.chat_id, text=log_entry,
          disable_web_page_preview=True
        )

logger = logging.getLogger("devman_notifications_bot")
logger.setLevel(logging.INFO)


def main():
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    devman_token = os.getenv("DEVMAN_TOKEN")

    logger.addHandler(LogsToTelegramHandler(telegram_token, chat_id))

    bot = telegram.Bot(token=telegram_token)

    headers = {
    "Authorization": f"Token {devman_token}"
    }

    check_list_url = 'https://dvmn.org/api/long_polling/'
    payload = {}

    logger.info('Devman notifications bot started.')

    connect_attempts = 0

    while True:
        try:
            try:
                response = requests.get(check_list_url, headers=headers, params=payload, timeout=100)
                response.raise_for_status()
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                logger.error('Ошибка получения данных с dvmn.org.')
                logger.exception(e)
                connect_attempts += 1
                if connect_attempts > 5:
                    time.sleep(60)
                    connect_attempts = 0

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

                payload['timestamp'] = response_dict.get('last_attempt_timestamp')

            elif status == 'timeout':
                payload['timestamp'] = response_dict.get('timestamp_to_request')

        except Exception as e:
            logger.error('Бот упал')
            logger.exception(e)


if __name__ == '__main__':
    main()
