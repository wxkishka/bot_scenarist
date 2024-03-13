from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
import logging
from config import TOKEN, MAX_LETTERS, SUBJECT, ASSISTANT_CONTENT
from gpt import GPT

bot = TeleBot(TOKEN)
gpt = GPT()

# Параметры логов.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding='UTF-8',
    filename='log_file.txt',
    filemode='w'
)

# Словарь для хранения запросов пользоватлей.
user_data = dict()


def create_keyboard(buttons_list):
    """Функция для создания кнопок бота."""
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


def continue_filter(message):
    """Функция-фильтр кнопки Продолжить."""
    button_text = 'Продолжить'
    return message.text == button_text


@bot.message_handler(commands=['start', 'help'])
def start(message):
    """Функция-обработчик команд start и help."""
    user_name = message.from_user.first_name
    if message.text == '/start':
        bot.send_message(message.chat.id,
                         text=f'Привет, {user_name}! Я бот c ИИ, помогаю решать задачи!\n'
                              f'Нажми solve_task, напиши свой вопрос.\n'
                              f'Если ответ не полный, напиши продолжи.',
                         reply_markup=create_keyboard(['/solve_task', '/help']))
    elif message.text == '/help':
        bot.send_message(message.from_user.id,
                         text='Чтобы начать задавать вопросы, нажми solve_task',
                         reply_markup=create_keyboard(['/solve_task']))


@bot.message_handler(commands=['debug'])
def send_logs(message):
    """Функция-обработчик команды debug: отправляет лог-файл по запросу."""
    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    """Функция-обработчик команды solve_task, принимает вопрос от пользоватля."""
    bot.send_message(message.chat.id, 'Задай свой вопрос.')
    bot.register_next_step_handler(message, get_prompt)


@bot.message_handler(func=continue_filter)
def get_prompt(message):
    """Функция проверяет вопрос пользователя перед формированием промпта."""
    user_id = message.from_user.id
    if message.content_type != 'text':
        bot.send_message(user_id, 'Сообщение должно быть текстом.')
        bot.register_next_step_handler(message, get_prompt)
        return
    else:
        user_request = message.text
    if len(user_request) > MAX_LETTERS:
        bot.send_message(user_id,
                         f'Ошибка: Сообщение должно быть короче {MAX_LETTERS} символов.')
        bot.register_next_step_handler(message, get_prompt)
        return
    if user_id not in user_data or user_data[user_id] == {}:
        user_data[user_id] = {
            'system_content': f'Предмет - {SUBJECT}. Отвечай подробно на русском языке.',
            'user_content': user_request,
            'assistant_content': ASSISTANT_CONTENT
        }
    # Формирую промпт, и отправляю в нейросеть.
    prompt = gpt.make_prompt(user_data[user_id]['user_content'])
    logging.info(f'Запрос пользователя к GPT: {prompt}.')
    resp = gpt.send_request(prompt)
    answer = gpt.process_resp(resp)

    if isinstance(answer, tuple):
        answer = answer[1]  # обработка кортежа.

    user_data[user_id]['assistant_content'] += answer
    bot.send_message(user_id, user_data[user_id]['assistant_content'],
                     reply_markup=create_keyboard(['Продолжить', 'Завершить']))


def end_filter(message):
    """Функция-фильтр кнопки Завершить."""
    button_text = 'Завершить'
    return message.text == button_text


@bot.message_handler(content_types=['text'], func=end_filter)
def end_task(message):
    """Функция-обработчик команды 'Завершить'."""
    user_id = message.from_user.id
    bot.send_message(user_id, "Сеанс окончен.")
    user_data[user_id] = {}
    logging.info(f'Сеанс пользовалетя {message.from_user.first_name} завершён.')


# if __name__ == "__main__":
logging.info("Бот запущен")
bot.infinity_polling()
