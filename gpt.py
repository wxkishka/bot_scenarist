import os.path
import time
import json
import logging
import requests
import sqlite3
from config import (SYSTEM_CONTENT, MAX_TOKENS, GPT_URL,
                    HEADERS, ASSISTANT_CONTENT, FOLDER_ID,
                    MODEL_URI, IAM_TOKEN, MAX_TOKENS_IN_SESSION,
                    LOG_PATH, TOKEN_PATH, METADATA_URL, METADATA_HEADERS,)


# Указываю параметры логирования.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding='UTF-8',
    filename=LOG_PATH,
    filemode='w'
)

class GPT:
    def __init__(self):
        self.system_content = SYSTEM_CONTENT
        self.URL = GPT_URL
        self.HEADERS = HEADERS
        self.MAX_TOKENS = MAX_TOKENS
        self.MAX_TOKENS_IN_SESSION = MAX_TOKENS_IN_SESSION
        self.assistant_content = ASSISTANT_CONTENT

    @staticmethod
    def count_tokens_in_dialog(messages: sqlite3.Row):
        """ Функция определяет количество токенов в сессии,
            messages - все промты из указанной сессии. """
        headers = {
            'Authorization': f'Bearer {IAM_TOKEN}',
            'Content-Type': 'application/json'
        }
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
            "maxTokens": MAX_TOKENS_IN_SESSION,
            "messages": []
        }

        # Проходимся по всем сообщениям и добавляем их в список
        for row in messages:
            data["messages"].append(
                {
                    "role": row["role"],
                    "text": row["content"]
                }
            )

        return len(
            requests.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion",
                json=data,
                headers=headers
            ).json()["tokens"]
        )


    def process_resp(self, response):
        """Функция для проверки и обработки ответа сервера."""
        if response.status_code < 200 or response.status_code >= 300:
            self.clear_history()
            return f'Ошибка: {response.status_code}'
        # Проверяю json
        try:
            full_response = response.json()
        except KeyError:
            self.clear_history()
            return 'Ошибка получения JSON'

        # Проверяю ошибки в ответе сервера.
        try:
            result = full_response['result']['alternatives'][0]['message']['text']
        except KeyError:
            self.clear_history()
            return 'Ошибка: некорректная структура ответа модели.'
        # Если content пустой, решение завершено.
        if result == '':
            self.clear_history()
            return 'Решение завершено.'
        # Сохраняю сообщение в историю
        self.save_history(result)
        return self.assistant_content

    def make_prompt(self, system_content, user_request, assistant_content):
        """Создаю промпт."""
        json = {
            "modelUri": MODEL_URI,
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": self.MAX_TOKENS
            },
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_request},
                {"role": "assistant", "content": assistant_content}
            ]
        }
        return json

    def send_request(self, json):
        """Функция для отправки запроса на сервер нейросети."""
        resp = requests.post(url=self.URL, headers=self.HEADERS, json=json)
        return resp

    def save_history(self, content_response):
        """Функция для сохранени истории обращений."""
        self.assistant_content += content_response

    def save_history(self, content_response):
        """Функция для сохранени истории обращений."""
        if isinstance(content_response, str):
            self.assistant_content += content_response
        else:
            print("Предупреждение: content_response не является строкой")

    def clear_history(self):
        """Функция для очистки истории обращений."""
        self.assistant_content = ASSISTANT_CONTENT


    def is_tokens_limit(user_id, chat_id, bot):
        """Функция получает идентификатор пользователя, чата и самого бота,
           чтобы иметь возможность отправлять сообщения"""
        # Если такого пользователя нет в таблице, ничего делать не будем
        if not is_value_in_table(DB_TABLE_PROMPTS_NAME, 'user_id', user_id):
            return

            # Берём из таблицы идентификатор сессии
        session_id = get_user_session_id(user_id)
        # Получаем из таблицы размер текущей сессии в токенах
        tokens_of_session = get_size_of_session(user_id, session_id)

        # В зависимости от полученного числа выводим сообщение
        if tokens_of_session >= MAX_TOKENS_IN_SESSION:
            bot.send_message(
                chat_id,
                f'Вы израсходовали все токены в этой сессии. Вы можете начать новую, введя help_with')

        elif tokens_of_session + 50 >= MAX_TOKENS_IN_SESSION  # Если осталось меньше 50 токенов
            bot.send_message(
                chat_id,
                f'Вы приближаетесь к лимиту в {MAX_TOKENS_IN_SESSION} токенов в этой сессии. '
                f'Ваш запрос содержит суммарно {tokens_of_session} токенов.')

        elif tokens_of_session / 2 >= MAX_TOKENS_IN_SESSION  # Если осталось меньше половины
            bot.send_message(
                chat_id,
                f'Вы использовали больше половины токенов в этой сессии. '
                f'Ваш запрос содержит суммарно {tokens_of_session} токенов.'
            )


def create_token():
    """Функция для создания нового токена."""
    token_dir = os.path.dirname(TOKEN_PATH)
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)

    try:
        response = requests.get(METADATA_URL, headers=METADATA_HEADERS)
        if response.status_code == 200:
            token_data = response.json()
            # Рассчитываю время срока годности токена.
            token_data['expires_at'] = time.time() + token_data['expires_in']
            with open(TOKEN_PATH, 'w') as token_file:
                json.dump(token_data, token_file)
        else:
            logging.error((f'Не удалось обновить токен: {response.status_code}'))
    except Exception as e:
        logging.error('Ошибка при получении токена: {e}')


def get_token():
    """Функция возвращает IAM_Token."""
    try:
        with open(TOKEN_PATH, 'r') as file:
            token_data = json.load(file)
            expires_at = token_data['expires_at']
        if expires_at < time.time():
            create_token()
    except:
        create_token()
    with open(TOKEN_PATH, 'r') as file:
        token_data = json.load(file)
        token = token_data['access_token']
    return token

