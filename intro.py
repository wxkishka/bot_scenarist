import requests

# Константы
SYSTEM_PROMPT = (
    "Ты пишешь историю вместе с человеком. "
    "Историю вы пишете по очереди. Начинает человек, а ты продолжаешь. "
    "Если это уместно, ты можешь добавлять в историю диалог между персонажами. "
    "Диалоги пиши с новой строки и отделяй тире. "
    "Не пиши никакого пояснительного текста в начале, а просто логично продолжай историю."
)
CONTINUE_STORY = 'Продолжи сюжет в 1-3 предложения и оставь интригу. Не пиши никакой пояснительный текст от себя'
END_STORY = 'Напиши завершение истории c неожиданной развязкой. Не пиши никакой пояснительный текст от себя'

# Данные пользователей
user_data = {
    '10439284': {
        'genre': "фэнтези",
        'character': "храбрый рыцарь",
        'setting': "пещера с драконом",
        'additional_info': "в поисках потерянного артефакта."
    },
    '4920572': {
        'genre': "научная фантастика",
        'character': "космический пират",
        'setting': "орбитальная станция",
        'additional_info': "на миссии по спасению родной планеты."
    },
}

# Функция создает промт для начала истории, используя выбор пользователя (жанр, герой и т.п.)
# Принимает два параметра: user_data (словарь данных от пользователей) 
# и user_id (id конкретного пользователя)
def create_prompt(user_data, user_id):
    # Начальный текст для нашей истории - это типа вводная часть
    prompt = SYSTEM_PROMPT

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

# Функция для запроса к YandexGPT
def ask_gpt(collection, mode='continue'):
    """Запрос к YandexGPT"""
    token = '<iam-токен>'
    folder_id = '<folder_id>'

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": 200},
        "messages": []
    }

    for row in collection:
        content = row['content']
        if mode == 'continue' and row['role'] == 'user':
            content += '\n' + CONTINUE_STORY
        elif mode == 'end' and row['role'] == 'user':
            content += '\n' + END_STORY
        data["messages"].append({"role": row["role"], "text": content})

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            return f"Status code {response.status_code}."
        return response.json()['result']['alternatives'][0]['message']['text']
    except Exception as e:
        return "Произошла непредвиденная ошибка."

# Основной блок исполнения
if __name__ == '__main__':
    user_id = '10439284'  # Устанавливаем ID пользователя.
    prompt = create_prompt(user_data, user_id)  # Создаем начальный промт.
    print(f"Начальный промт:\n{prompt}\n")  # Выводим промт на экран.

    collection = [{'role': 'user', 'content': prompt}]  # Начинаем собирать данные для запроса.

    # Первый запрос для продолжения истории.
    response = ask_gpt(collection, mode='continue')
    print(f"Первое продолжение истории от YandexGPT:\n{response}\n")
    collection.append({'role': 'assistant', 'content': response})  # Добавляем ответ в collection.

    # Второй запрос для дальнейшего продолжения истории.
    response = ask_gpt(collection, mode='continue')
    print(f"Второе продолжение истории от YandexGPT:\n{response}\n")
    collection.append({'role': 'assistant', 'content': response})  # Снова добавляем ответ в collection.

    # Третий запрос для завершения истории.
    response = ask_gpt(collection, mode='end')
    print(f"Завершение истории от YandexGPT:\n{response}\n")
    collection.append({'role': 'assistant', 'content': response})  # Добавляем финальный ответ в collection.
