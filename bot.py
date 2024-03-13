from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
import logging
from config import TOKEN, MAX_LETTERS, SUBJECTS, ASSISTANT_CONTENT, LEVELS
from gpt import GPT
from database import (create_db, create_table, insert_data,
                      update_data, select_data, user_exists, delete_data)

bot = TeleBot(TOKEN)
gpt = GPT()
# Создаю базу даных.
create_db()
# Создаю в БД таблицу для хранения данных пользователя.
create_table()

# Указываю параметры логов.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding='UTF-8',
    filename='log_file.txt',
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
    buttons = ['help_with_'+subject for subject in SUBJECTS]
    bot.send_message(message.chat.id,
                     text=f'Привет, {user_name}! Я бот c ИИ, помогаю решать задачи!\n'
                          f'Нажми "help_with...", с желаемым предметом.\n'
                          f'Затем выбери уровень сложности ответа и задай вопрос. \n'
                          f'Если ответ не полный, нажми "continue".',
                     reply_markup=create_keyboard(buttons, 'continue'))
    bot.register_next_step_handler(message, subject_proc)


def subject_proc(message):
    user_id = message.from_user.id
    level_btn = [level for level in LEVELS]
    cmd_to_subject = {
        'help_with_math': 'математика',
        'help_with_biology': 'биология',
        'help_with_russian': 'русский язык'
    }
    current_subject = cmd_to_subject[message.text]
    insert_data(user_id, current_subject)
    bot.send_message(user_id, 'Выбери уровень сложности.',
                     reply_markup=create_keyboard(level_btn))
    bot.register_next_step_handler(message, levels_proc)


def levels_proc(message):
    user_id = message.from_user.id
    current_level = message.text
    update_data(user_id, 'level', current_level)
    bot.send_message(user_id, 'Теперь задай свой вопрос.')
    bot.register_next_step_handler(message, get_prompt)


@bot.message_handler(commands=['debug'])
def send_logs(message):
    """Функция-обработчик команды debug: отправляет лог-файл по запросу."""
    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


def continue_filter(message):
    """Функция-фильтр кнопки Продолжить."""
    button_text = 'continue'
    return message.text == button_text


@bot.message_handler(func=continue_filter)
def get_prompt(message):
    """Функция проверяет вопрос пользователя перед формированием промпта."""
    user_id = message.from_user.id
    current_subj = select_data(user_id, 'subject')[0]
    if message.content_type != 'text' or len(message.text) > MAX_LETTERS:
        bot.send_message(user_id, f'Сообщение должно быть текстом'
                                  f'или короче {MAX_LETTERS} символов.')
        bot.register_next_step_handler(message, get_prompt)
        return
    user_request = message.text
    if user_exists(user_id) and user_request != 'continue':
        system_content = f'Предмет-{current_subj}. Отвечай подробно на русском языке.'
        user_content = user_request
        update_data(user_id, 'task', user_content)
        assistant_content = ASSISTANT_CONTENT
        # update_data(user_id, 'answer', assistant_content)
    elif user_exists(user_id) and user_request == 'continue':
        print('Get prompt continue')
        system_content = f'Предмет-{current_subj}. Отвечай подробно на русском языке.'
        user_content = user_request
        assistant_content = select_data(user_id, 'answer')[0]
    # Формирую промпт, и отправляю в нейросеть.
    prompt = gpt.make_prompt(system_content, user_content, assistant_content)
    logging.info(f'Запрос пользователя к GPT: {prompt}.')
    resp = gpt.send_request(prompt)
    answer = gpt.process_resp(resp)
    # assistant_content = select_data(user_id, 'answer')[0] + answer
    assistant_content += answer
    update_data(user_id, 'answer', assistant_content)
    print(select_data(user_id, 'answer')[0])
    bot.send_message(user_id, answer,
                     reply_markup=create_keyboard(['continue', 'finish']))


def end_filter(message):
    """Функция-фильтр кнопки Завершить."""
    button_text = 'finish'
    return message.text == button_text


@bot.message_handler(content_types=['text'], func=end_filter)
def end_task(message):
    """Функция-обработчик команды 'finish'."""
    user_id = message.from_user.id
    bot.send_message(user_id, "Сеанс окончен.")
    delete_data(user_id)
    logging.info(f'Сеанс пользовалетя {message.from_user.first_name} завершён.')


# if __name__ == "__main__":
logging.info("Бот запущен")
bot.infinity_polling()
