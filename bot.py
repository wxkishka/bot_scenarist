from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
import logging
from datetime import datetime
import sqlite3
from config import (TOKEN, GENRES, CHARACTERS, SETTING, LOG_PATH, END_STORY,
                    SYSTEM_CONTENT, MAX_TOKENS_IN_SESSION,)
from gpt import ask_gpt, count_tokens, count_tokens_in_dialog
from database import (create_db, create_table, insert_data_into_db,
                      current_session, select_role_content, user_exists,
                      is_limit_users, is_limit_sessions, session_counter,
                      tokens_in_session, whole_story_db)

bot = TeleBot(TOKEN)
# Создаю базу даных.
create_db()
# Создаю в БД таблицу для хранения данных пользователя.
create_table()
# Создаю словарь для хранения данных пользователя для его сценария.
user_data = dict()

# Указываю параметры логирования.
logging.basicConfig(
    level=logging.INFO,
    filename=LOG_PATH,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding='UTF-8',
    filemode='w'
)


def create_keyboard(buttons_list, button=''):
    """Функция для создания кнопок бота."""
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list, button)
    return keyboard


@bot.message_handler(commands=['all_tokens'])
def all_tokens_counter(message):
    """Функция показывает количество израсходованных токенов в сессии."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    try:
        all_tokens = tokens_in_session(user_id)
        bot.send_message(chat_id, f'Вы израсходовали {all_tokens} в сессии.')
    except Exception as e:
        bot.send_message(chat_id, f'При получении количества токенов' 
                         f'произошла ошибка {e}')
        

@bot.message_handler(commands=['whole_story'])
def whole_story(message):
    """Функция выводит для чтения историю целиком."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    try:
        story = whole_story_db(user_id)
        bot.send_message(chat_id, story)
    except Exception as e:
        bot.send_message(chat_id, f'При получении истории произошла ошибка {e}.')


@bot.message_handler(commands=['end'])
def end_task(message):
    """Функция-обработчик команды 'end'."""
    buttons = ['/new_story', '/whole_story', '/all_tokens', '/debug']
    if not user_exists:
        bot.send_message(message.chat.id, 'Ты еще не начал ни одного сценария \n'
                         'нажми конопку "begin" и начни свой сценарий.')
        return
    story_handler(message, mode='end')
    bot.send_message(message.chat.id, 'Написание сценария завершено.',
                     reply_markup=create_keyboard(buttons))


@bot.message_handler(commands=['start'])
def start(message):
    """Функция-обработчик команды start"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    user_data[user_id] = {
        'genre': None,
        'character': None,
        'setting': None,
        'add_info': None
    }
    buttons = ['/new_story', '/end']
    bot.send_message(message.chat.id,
                     text=f'Привет, {user_name}! Я бот, который умеет писать сценарии!\n'
                          f'Напишем историю вместе. Напиши /new_story, и начнём.\n'
                          f'Когда история будет написана, нажми /end.',
                     reply_markup=create_keyboard(buttons))


@bot.message_handler(commands=['new_story'])
def new_story_proc(message):
    """Функция-обработчик команды начала написания истории."""
    if is_limit_users():
        bot.send_message(message.chat.id,
                         'Превышен предел количества пользователей!')
        return
    bot.send_message(message.chat.id, 'Выбери жанр для истории.',
                     reply_markup=create_keyboard(GENRES))
    bot.register_next_step_handler(message, genre_proc)


def genre_proc(message):
    """Функция принимает и записывает в словарь жанр истории."""
    user_id = message.from_user.id
    if is_limit_sessions(user_id):
        bot.send_message(message.chat.id, 'У Вас превышен лимит сессий.')
        return

    user_data[user_id]['genre'] = message.text
    bot.send_message(message.chat.id, 'Выбери пероснаж.',
                     reply_markup=create_keyboard(CHARACTERS))
    bot.register_next_step_handler(message, character_proc)


def character_proc(message):
    """Функция принимает и записывает в словарь  героя истории."""
    user_id = message.from_user.id
    user_data[user_id]['character'] = message.text
    bot.send_message(message.chat.id, 'Выбери вселенную.',
                     reply_markup=create_keyboard(SETTING))
    bot.register_next_step_handler(message, setting_proc)


def setting_proc(message):
    """Функция принимает и записывает вселенную истории."""
    user_id = message.from_user.id
    buttons = ['/begin']
    user_data[user_id]['setting'] = message.text
    bot.send_message(message.chat.id, 'Если хочешь начать, нажми "begin".\n'
                                      'или напиши дополнительную информацию для нейросети.',
                     reply_markup=create_keyboard(buttons))
    bot.register_next_step_handler(message, additional_info_proc)


@bot.message_handler(commands=['begin'])
def additional_info_proc(message):
    """Функция-обработчик. Обрабатывает комманды 'начать' или записывает
        дополнительную информация для создания сценария."""
    user_id = message.from_user.id
    buttons = ['/begin']
    if message.text == '/begin':
        story_init(message)
    else:
        user_data[user_id]['add_info'] = message.text
        bot.send_message(message.chat.id, 'Дополнительная информация прнята.\n'
                                          'нажми "начать", и начнём писать сценарий!',
                         reply_markup=create_keyboard(buttons))


@bot.message_handler(commands=['debug'])
def send_logs(message):
    """Функция-обработчик команды debug: отправляет лог-файл по запросу."""
    with open(LOG_PATH, "rb") as f:
        bot.send_document(message.chat.id, f)


def create_prompt(user_id):
    """ Функция создает промт для начала истории ."""
    prompt = ''
    # Заполняем промпт данными для сценария.
    prompt += (f"\nНапиши начало истории в стиле {user_data[user_id]['genre']} "
               f"с главным героем {user_data[user_id]['character']}. "
               f"Вот начальный сеттинг: \n{user_data[user_id]['setting']}. \n"
               "Начало должно быть коротким, 1-3 предложения.\n")

    # Добваляем дополнительную информацию в промпт.
    if user_data[user_id]['add_info']:
        prompt += (f"Также пользователь попросил учесть "
                   f"следующую дополнительную информацию: {user_data[user_id]['add_info']} ")
    return prompt


def story_init(message):
    """Функция-обработчик команды 'begin' - начало сценария."""
    user_id = message.from_user.id
    buttons = ['/end']
    butn_if_exceded = ['/start', '/end']
    if not user_exists(user_id):
        session_id = 1
    else:
        session_id = session_counter(user_id)

    tokens = count_tokens(SYSTEM_CONTENT)

    insert_data_into_db(
        user_id,
        datetime.now(),
        session_id,
        'system',
        SYSTEM_CONTENT,
        tokens
    )
    
    user_content = create_prompt(user_id)

    collection: sqlite3.Row = select_role_content(user_id, session_id)
    collection.append({'role': 'user', 'content': 'user_content'})
    tokens = count_tokens_in_dialog(collection)
    if tokens < MAX_TOKENS_IN_SESSION:
        insert_data_into_db(user_id, datetime.now(), session_id, 'user',
                            user_content, tokens)
    else:
        bot.send_message(message.chat.id, 'Вы превысили максимальное количество \n'
                         'токенов на сессию.',
                         reply_markup=create_keyboard(butn_if_exceded))
        return

    gpt_answer = ask_gpt(collection)

    collection: sqlite3.Row = select_role_content(user_id, session_id)
    collection.append({'role': 'assistant', 'content': gpt_answer})

    tokens = count_tokens_in_dialog(collection)
    
    insert_data_into_db(user_id, datetime.now(), session_id, 'assistant',
                        gpt_answer, tokens)
    bot.send_message(message.chat.id, gpt_answer,
                     reply_markup=create_keyboard(buttons))


@bot.message_handler(content_types=['text'])
def story_handler(message, mode='continue'):
    """Функция-обработчик написания сценария. Инициирует создание промпта.
       Вызывает функцию обращения к нейросети, отслеживает действия пользователя
       при написании сценария."""
    buttons = ['/end']
    user_id = message.from_user.id
    session_id = current_session(user_id)
    user_content = message.text
    if mode == 'end':
        user_content = END_STORY

    collection: sqlite3.Row = select_role_content(user_id, session_id)
    collection.append({'role': 'user', 'content': user_content})

    tokens = count_tokens_in_dialog(collection)

    if tokens < MAX_TOKENS_IN_SESSION:
        insert_data_into_db(user_id, datetime.now(), session_id, 'user',
                            user_content, tokens)
    else:
        bot.send_message(message.chat.id, 'Вы превысили максимальное количество'
                         ' токенов на сессию.')  # reply_markup=create_keyboard(buttons))
        return
    
    gpt_answer = ask_gpt(collection, mode)

    collection: sqlite3.Row = select_role_content(user_id, session_id)
    collection.append({'role': 'assistant', 'content': gpt_answer})
    tokens = count_tokens_in_dialog(collection)

    insert_data_into_db(user_id, datetime.now(), session_id, 'assistant',
                        gpt_answer, tokens)

    bot.send_message(message.chat.id, gpt_answer,
                     reply_markup=create_keyboard(buttons))


# if __name__ == "__main__":
logging.info("Бот запущен")
bot.infinity_polling()
