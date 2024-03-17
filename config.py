import os.path
from gpt import get_token
# TOKEN = '6787855008:AAFNpFZ-Y1DD_x1mV0UYoPqH0AVwTW9iacQ'
TOKEN = '5924781016:AAFe6DmVlFmhFGWE18Y-wSfFN6gcHzrh3Zk'
DB_NAME = 'db.sqlite'
LOG_PATH = 'log_file.txt'

TOKEN = '5924781016:AAFe6DmVlFmhFGWE18Y-wSfFN6gcHzrh3Zk'
GPT_URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
FOLDER_ID = 'b1gr1l4ru3gbjel7ihgi'
MODEL_URI = f'gpt://{FOLDER_ID}/yandexgpt-lite'
IAM_TOKEN = get_token()
HEADERS = {"Authorization": f"Bearer {IAM_TOKEN}",
           "Content-Type": "application/json"}
MAX_TOKENS = 100
MAX_LETTERS = 100
MAX_PROJECT_TOKENS = 15000  # Максимальное количество токенов на проект.
MAX_USERS = 5  # Максимальное количество пользователей.
MAX_USER_TOKENS = 300  # Максимальное количество токенов на пользователя.
MAX_TOKENS_IN_SESSION = 100 # Максимальное количество токенов на сессию.
MAX_SESSIONS = 3  # Максимальное количество сессий.

# Раздел настоек для историй.
GENRES = ['ужастик', 'триллер', 'комедия']
CHARACTERS = ['максимус', 'клоун', 'пони', 'белоснежка']
SETTING = ['кино', 'игра', 'мультфильм']
SYSTEM_CONTENT = ("Ты пишешь историю вместе с человеком. "
    "Историю вы пишете по очереди. Начинает человек, а ты продолжаешь. "
    "Если это уместно, ты можешь добавлять в историю диалог между персонажами. "
    "Диалоги пиши с новой строки и отделяй тире. "
    "Не пиши никакого пояснительного текста в начале, а просто логично продолжай историю.")
ASSISTANT_CONTENT = ''
CONTINUE_STORY = 'Продолжи сюжет в 1-3 предложения и оставь интригу. Не пиши никакой пояснительный текст от себя'
END_STORY = 'Напиши завершение истории c неожиданной развязкой. Не пиши никакой пояснительный текст от себя'

# Раздел настроек для получения и обновления IAM_TOKEN
METADATA_URL = '158.160.140.71/computeMetadata/v1/instance/service-accounts/default/token'
METADATA_HEADERS = {'Metadata-Flavor': "Google"}
TOKEN_PATH = 'iam_token.json'
