from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
import logging
from datetime import datetime
import sqlite3
from config import (TOKEN, GENRES,
                    CHARACTERS, SETTING, LOG_PATH, END_STORY)
from gpt import ask_gpt, create_prompt, count_tokens_in_dialog
from database import (create_db, create_table, insert_data_into_db,
                      current_session, select_role_content, user_exists,
                      is_limit_users, is_limit_sessions, session_counter)

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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding='UTF-8',
    filename=LOG_PATH,
    filemode='w'
)


def create_keyboard(buttons_list, button=''):
    """Функция для создания кнопок бота."""
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list, button)
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    """Функция-обработчик команды start"""
    user_name = message.from_user.first_name
    buttons = ['new_story', 'end']
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
    # session_id = session_counter(user_id)
    # insert_data(user_id, session_id, datetime.now())
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
    user_data[user_id]['setting'] = message.text
    bot.send_message(message.chat.id, 'Если хочешь начать, нажми "Начать".\n'
                                      'или напиши дополнительную информацию для нейросети.',
                     reply_markup=create_keyboard('начать'))
    bot.register_next_step_handler(message, additional_info_proc)


def additional_info_proc(message):
    """Функция-обработчик. Обрабатывает комманды 'начать' или записывает
        дополнительную информация для создания сценария."""
    user_id = message.from_user.id
    if message.text == 'начать':
        story_init(message)
    else:
        user_data[user_id]['add_info'] = message.text
        bot.send_message(message.chat.id, 'Дополнительная информация прнята.\n'
                                          'нажми "начать", и начнём писать сценарий!',
                         reply_markup=create_keyboard('начать'))


@bot.message_handler(commands=['debug'])
def send_logs(message):
    """Функция-обработчик команды debug: отправляет лог-файл по запросу."""
    with open(LOG_PATH, "rb") as f:
        bot.send_document(message.chat.id, f)


def story_init(message):
    """Функция-обработчик команды первого запроса создания сценария."""
    user_id = message.from_user.id

    if user_exists(user_id):
        session_id = session_counter(user_id)

    user_content = create_prompt(user_data, user_id)

    collection: sqlite3.Row = select_role_content(user_id, session_id)
    collection.append({'role': 'system', 'content': 'user_content'})
    tokens = count_tokens_in_dialog(collection)

    insert_data_into_db(user_id, datetime.now(), session_id, 'system',
                        user_content, tokens)

    gpt_answer = ask_gpt(collection)

    collection: sqlite3.Row = select_role_content(user_id, session_id)
    collection.append({'role': 'assistant', 'content': gpt_answer})
    insert_data_into_db(user_id, datetime.now(), session_id, 'assistant',
                        gpt_answer, tokens)
    bot.send_message(message.chat.id, gpt_answer,
                     reply_markup=create_keyboard('continue', 'end'))


@bot.message_handler(content_types=['text'])
def story_handler(message, mode='continue'):
    """Функция-обработчик написания сценария. Инициирует создание промпта.
       Вызывает функцию обращения к нейросети, отслеживает действия пользователя
       при написании сценария."""
    user_id = message.from_user.id
    session_id = current_session(user_id)
    user_content = message.text
    if mode == 'end':
        user_content = END_STORY

    collection: sqlite3.Row = select_role_content(user_id, session_id)
    collection.append({'role': 'user', 'content': user_content})

    tokens = count_tokens_in_dialog(collection)

    # if is_tokens_limit(message, tokens, bot):
    #     return

    insert_data_into_db(user_id, datetime.now(), session_id, 'user', user_content, tokens)

    # if is_tokens_limit(message,tokens, bot):
    #     return

    gpt_answer = ask_gpt(collection, mode)

    collection: sqlite3.Row = select_role_content(user_id, session_id)
    collection.append({'role': 'assistant', 'content': gpt_answer})
    tokens = count_tokens_in_dialog(collection)

    insert_data_into_db(user_id, datetime.now(), session_id, 'assistant',
                        gpt_answer, tokens)

    bot.send_message(message.chat.id, gpt_answer,
                     reply_markup=create_keyboard('continue', 'end'))


def end_filter(message):
    """Функция-фильтр кнопки Завершить."""
    button_text = 'end'
    return message.text == button_text


@bot.message_handler(content_types=['text'], func=end_filter)
def end_task(message):
    """Функция-обработчик команды 'end'."""
    user_id = message.from_user.id
    bot.send_message(user_id, "Сеанс окончен.")
    # delete_data(user_id)
    logging.info(f'Сеанс пользовалетя {message.from_user.first_name} завершён.')


# if __name__ == "__main__":
logging.info("Бот запущен")
bot.infinity_polling()
