import json
from logger_util import get_logger

log = get_logger(__name__)


def get_config_dict() -> dict:
    template_config: dict = json.load(open('config.json'))
    env_config: dict = json.load(open('config_env.json'))
    for k in template_config.keys():
        try:
            a = env_config[k]
        except KeyError:
            log.error(f'********** CONFIG MISMATCH **********\n {k} not found in config_env.json')
            raise Exception(f'********** CONFIG MISMATCH **********\n {k} not found in config_env.json')
    for k in env_config.keys():
        try:
            a = template_config[k]
        except KeyError:
            log.error(f'********** CONFIG MISMATCH **********\n {k} not found in config.json')
            raise Exception(f'********** CONFIG MISMATCH **********\n {k} not found in config.json')
    return env_config


config = get_config_dict()

APP_NAME = config['APP_NAME']
SECRET_KEY = config['SECRET_KEY']
FLASK_SERVER_PORT = config['FLASK_SERVER_PORT']
UPLOAD_FOLDER = config['UPLOAD_FOLDER']
DB_BASE_URL = config['DB_BASE_URL']
DB_NAME = config['DB_NAME']
ENV = config['ENV']
SYS_SECRET_KEY = config['SYS_SECRET_KEY']
VIDEO_MEDIA_TYPE: [str] = ["mp4"]
AUDIO_MEDIA_TYPE: [str] = ["mp3"]
DEEPGRAM_TOKEN: str = config['DEEPGRAM_TOKEN']
GEMINI_API_KEY: str = config['GEMINI_API_KEY']
MEDIA_CACHE_SEC: int = 3600
SUPPORTED_MEDIA_TYPE = VIDEO_MEDIA_TYPE + AUDIO_MEDIA_TYPE
# OPENAI_API_KEY: str = config['OPENAI_API_KEY']
# GEMINI_API_KEY: str = config['GEMINI_API_KEY']
# MONGO_URL = config['MONGO_URL']
# MONGO_DB_NAME = config['MONGO_DB_NAME']
# MONGO_PORT: int = 27017

log.info(f'{ENV} Setting loaded.')
