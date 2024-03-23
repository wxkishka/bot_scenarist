# import os.path
import time
import json
import logging
import requests
import sqlite3
from config import (GPT_URL, FOLDER_ID,MAX_TOKENS_IN_SESSION, LOG_PATH,
                    TOKEN_PATH, METADATA_URL, METADATA_HEADERS,
                    CONTINUE_STORY, END_STORY, MODEL_URI)

# Указываю параметры логирования.
logging.basicConfig(
    level=logging.INFO,
    filename=LOG_PATH,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding='UTF-8',
    filemode='w'
)

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


def create_token():
    """Функция для создания нового токена."""
    # token_dir = os.path.dirname(TOKEN_PATH)
    # if not os.path.exists(token_dir):
    #     os.makedirs(token_dir)

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
        logging.error(f'Ошибка при получении токена: {e}')


IAM_TOKEN = get_token()

def count_tokens(text):
    """Функция подсчитывает количество токенов в сообщении."""
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
       "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
       "maxTokens": MAX_TOKENS_IN_SESSION,
       "text": text
    }
    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize",
            json=data,
            headers=headers
        ).json()['tokens']
    ) 


def count_tokens_in_dialog(collection: sqlite3.Row):
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
    for row in collection:
        data["messages"].append(
            {
                "role": row['role'],
                "text": row['content']
            }
        )

    return len(
        requests.post(
            'https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion',
            json=data,
            headers=headers
        ).json()['tokens']
    )


def is_limit_in_session(collection):
    """Функция проверяет превышение лимита токенов в сессии."""
    tokens = count_tokens_in_dialog(collection)
    return tokens < MAX_TOKENS_IN_SESSION


def ask_gpt(collection, mode='continue'):
    """Функция выполняет запрос к YandexGPT"""
    url = GPT_URL
    headers = {"Authorization": f"Bearer {IAM_TOKEN}",
               "Content-Type": "application/json"}
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": MAX_TOKENS_IN_SESSION
        },
        "messages": []
    }
    # Добавляю данные из collection в json запрос.
    for row in collection:
        content = row['content']
        if mode == 'continue' and row['role'] == 'user':
            content += '\n' + CONTINUE_STORY
        elif mode == 'end' and row['role'] == 'user':
            content += '\n' + END_STORY

        data["messages"].append({
            "role": row["role"],
            "text": content
        })
    # Отправляю запрос и обрабатываю возможные ошибки.
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            result = f"Status code {response.status_code}."  # Обработка ошибки статуса
            return result
        result = response.json()['result']['alternatives'][0]['message']['text']
    except Exception as e:
        result = f"Непредвиденная ошибка: {e}."

    return result
