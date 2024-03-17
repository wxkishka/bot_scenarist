import os.path
import time
import json
import logging
import requests
import sqlite3
from config import CONTINUE_STORY, END_STORY
from bot import user_data
from database import user_exists, current_session
from config import (SYSTEM_CONTENT, MAX_TOKENS, GPT_URL,
                    HEADERS, ASSISTANT_CONTENT, FOLDER_ID,
                    IAM_TOKEN, MAX_TOKENS_IN_SESSION,
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


    def is_tokens_limit(user_id, chat_id, bot):
        """Функция получает идентификатор пользователя, чата и самого бота,
           чтобы иметь возможность отправлять сообщения"""
        # Если такого пользователя нет в таблице, ничего делать не будем
        if not user_exists(user_id):
            return

            # Берём из таблицы идентификатор сессии
        session_id = current_session(user_id)
        # Получаем из таблицы размер текущей сессии в токенах
        tokens_of_session = get_size_of_session(user_id, session_id)

        # В зависимости от полученного числа выводим сообщение
        if tokens_of_session >= MAX_TOKENS_IN_SESSION:
            bot.send_message(
                chat_id,
                f'Вы израсходовали все токены в этой сессии. Вы можете начать новую, введя help_with')

        elif tokens_of_session + 50 >= MAX_TOKENS_IN_SESSION:  # Если осталось меньше 50 токенов
            bot.send_message(
                chat_id,
                f'Вы приближаетесь к лимиту в {MAX_TOKENS_IN_SESSION} токенов в этой сессии. '
                f'Ваш запрос содержит суммарно {tokens_of_session} токенов.')

        elif tokens_of_session / 2 >= MAX_TOKENS_IN_SESSION:  # Если осталось меньше половины
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


def create_prompt(user_id, user_data):
    """ Функция создает промт для начала истории, используя выбор пользователя (жанр, герой и т.п.)
        Принимает два параметра: user_data (словарь данных от пользователей)
        и user_id (id конкретного пользователя)
    """
    # Начальный текст для нашей истории - вводная часть
    prompt = SYSTEM_CONTENT
    # Добавляем в начало истории инфу о жанре и главном герое, которых выбрал пользователь
    prompt += (f"\nНапиши начало истории в стиле {user_data[user_id]['genre']} "
              f"с главным героем {user_data[user_id]['character']}. "
              f"Вот начальный сеттинг: \n{user_data[user_id]['setting']}. \n"
              "Начало должно быть коротким, 1-3 предложения.\n")

    # Если пользователь указал что-то еще в "дополнительной информации", добавляем это тоже
    if user_data[user_id]['additional_info']:
        prompt += (f"Также пользователь попросил учесть "
                   f"следующую дополнительную информацию: {user_data[user_id]['additional_info']} ")

    # Добавляем к prompt напоминание не давать пользователю лишних подсказок
    prompt += 'Не пиши никакие подсказки пользователю, что делать дальше. Он сам знает'

    # Возвращаем сформированный текст истории
    return prompt


def ask_gpt(collection, mode='continue'):
    """Функция выполняет запрос к YandexGPT"""
    # Замени <iam-токен> и <folder_id> на реальные значения для доступа к API
    token = IAM_TOKEN  # IAM-токен для аутентификации
    folder_id = FOLDER_ID # ID папки в облаке

    # URL для запроса к YandexGPT
    url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    # Заголовки запроса, включая токен авторизации
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Данные для запроса, включая URI-модели, настройки и сообщения
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",  # Адрес модели GPT
        "completionOptions": {  # Опции генерации текста
            "stream": False,  # Отключение потоковой передачи
            "temperature": 0.6,  # Температура для вариативности ответов
            "maxTokens": 200  # Максимальное количество токенов в ответе
        },
        "messages": []  # Список сообщений для истории
    }

    # Добавление сообщений из collection в данные запроса
    for row in collection:
        content = row['content']

        # Добавление инструкций в зависимости от режима работы
        if mode == 'continue' and row['role'] == 'user':
            content += '\n' + CONTINUE_STORY
        elif mode == 'end' and row['role'] == 'user':
            content += '\n' + END_STORY

        # Формирование сообщения для отправки
        data["messages"].append({
            "role": row["role"],  # Роль отправителя (пользователь или система)
            "text": content  # Текст сообщения
        })

    # Отправка запроса и обработка ответа
    try:
        response = requests.post(url, headers=headers, json=data)  # Отправка запроса
        if response.status_code != 200:
            result = f"Status code {response.status_code}."  # Обработка ошибки статуса
            return result
        # Получение и возврат результата из ответа
        result = response.json()['result']['alternatives'][0]['message']['text']
    except Exception as e:
        # Обработка исключения при запросе
        result = "Произошла непредвиденная ошибка. Подробности см. в журнале."

    return result  # Возвращаем результат