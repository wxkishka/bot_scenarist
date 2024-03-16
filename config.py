# TOKEN = '6787855008:AAFNpFZ-Y1DD_x1mV0UYoPqH0AVwTW9iacQ'
TOKEN = '5924781016:AAFe6DmVlFmhFGWE18Y-wSfFN6gcHzrh3Zk'
GPT_URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
FOLDER_ID = 'b1gr1l4ru3gbjel7ihgi'
MODEL_URI = f'gpt://{FOLDER_ID}/yandexgpt-lite'
IAM_TOKEN = ''
HEADERS = {"Authorization": f"Bearer {IAM_TOKEN}",
           "Content-Type": "application/json"}
MAX_TOKENS = 100
MAX_LETTERS = 100
MAX_PROJECT_TOKENS = 15000  # Максимальное количество токенов на проект.
MAX_USERS = 5  # Максимальное количество пользователей.
MAX_USER_TOKENS = 300  # Максимальное количество токенов на пользователя.
MAX_TOKENS_IN_SESSION = 100 # Максимальное количество токенов на сессию.
MAX_SESSIONS = 3  # Максимальное количество сессий.

GENRES = ['ужастик', 'триллер', 'комедия']
CHARACTERS = ['максимус', 'клоун', 'пони', 'белоснежка']
SETTING = ['кино', 'игра', 'мультфильм']
SYSTEM_CONTENT = 'Ты бот, который пишет сценарии.'
ASSISTANT_CONTENT = ''
MODEL_NAME = "mistralai_mistral-7b-instruct-v0.1"
DB_NAME = 'db.sqlite'

LOG_PATH = 'log_file.txt'

METADATA_URL = '158.160.140.71/computeMetadata/v1/instance/service-accounts/default/token'
METADATA_HEADERS = {'Metadata-Flavor': "Google"}
TOKEN_PATH = 'iam_token.txt'
