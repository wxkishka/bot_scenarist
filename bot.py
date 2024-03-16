from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
import logging
import datetime
from config import (TOKEN, SYSTEM_CONTENT, GENRES, ASSISTANT_CONTENT,
                    CHARACTERS, SETTING, LOG_PATH,)
from gpt import GPT
from database import (create_db, create_table, insert_data,
                      update_data, select_data, user_exists,
                      is_limit_users, is_limit_sessions, session_counter)

bot = TeleBot(TOKEN)
gpt = GPT()
# Создаю базу даных.
create_db()
# Создаю в БД таблицу для хранения данных пользователя.
create_table()
# Создаю словарь для хранения данных пользователя для его истории.
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
    user_data[user_id]['setting']= message.text
    bot.send_message(message.chat.id, 'Если хочешь начать, нажми Начать.',
                     reply_markup=create_keyboard('начать'))
    bot.register_next_step_handler(message, get_prompt)

@bot.message_handler(commands=['debug'])
def send_logs(message):
    """Функция-обработчик команды debug: отправляет лог-файл по запросу."""
    with open(LOG_PATH, "rb") as f:
        bot.send_document(message.chat.id, f)


def continue_filter(message):
    """Функция-фильтр кнопки Продолжить."""
    button_text = 'continue'
    return message.text == button_text


@bot.message_handler(func=continue_filter)
def get_prompt(message):
    """Функция проверяет вопрос пользователя перед формированием промпта."""
    user_id = message.from_user.id
    system_content = SYSTEM_CONTENT
    assistant_content = ASSISTANT_CONTENT
    user_content = (f'Напиши сценарий для {user_data[user_id]["setting"]}, '
                   f' в жанре {user_data[user_id]["genre"]}, '
                   f'в главной роли {user_data[user_id]["character"]}.')

    # Формирую промпт, и отправляю в нейросеть.
    prompt = gpt.make_prompt(system_content, user_content, assistant_content)
    logging.info(f'Запрос пользователя к GPT: {prompt}.')
    resp = gpt.send_request(prompt)
    answer = gpt.process_resp(resp)
    assistant_content += answer
    update_data(user_id, 'answer', assistant_content)
    print(select_data(user_id, 'answer')[0])
    bot.send_message(user_id, answer,
                     reply_markup=create_keyboard(['continue', 'finish']))


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
