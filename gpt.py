import requests
from transformers import AutoTokenizer
from config import (SYSTEM_CONTENT, MAX_TOKENS, GPT_URL,
                    HEADERS, ASSISTANT_CONTENT, MODEL_NAME)


class GPT:
    def __init__(self):
        self.system_content = SYSTEM_CONTENT
        self.URL = GPT_URL
        self.HEADERS = HEADERS
        self.MAX_TOKENS = MAX_TOKENS
        self.assistant_content = ASSISTANT_CONTENT

    @staticmethod
    def count_tokens(prompt):
        """Функция определяет количество токенов в промпте."""
        try:
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            return len(tokenizer.encode(prompt))
        except Exception as e:
            print(f'Ошибка при подсчете токенов: {str(e)}')
            return 0

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
        # if "error" in full_response or 'choices' not in full_response:
        #     self.clear_history()
        #     return False, f'Ошибка: {full_response}'
        # result = full_response['choices'][0]['message']['content']
        try:
            result = full_response['choices'][0]['message']['content']
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
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_request},
                {"role": "assistant", "content": assistant_content}
            ],
            "temperature": 1.2,
            "max_tokens": self.MAX_TOKENS,
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
