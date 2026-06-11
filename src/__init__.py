from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os
from flask_sqlalchemy import SQLAlchemy
import settings
from logger_util import get_logger
from functools import wraps
from flask_migrate import Migrate


os.makedirs('temp', exist_ok=True)
log = get_logger(__name__)
app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'frontend_src'))


mysql_local_base = settings.DB_BASE_URL
database_name = settings.DB_NAME
authorization = None


def with_app_context(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with app.app_context():
            return func(*args, **kwargs)
    return wrapper


class BaseConfig:
    """Base configuration."""
    APP_NAME = settings.APP_NAME
    SECRET_KEY = settings.SECRET_KEY
    UPLOAD_FOLDER = settings.UPLOAD_FOLDER
    AUTH_TOKEN = authorization
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 13
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = mysql_local_base + database_name


CORS(app, resources={r"*": {"origins": "*", "supports_credentials": True}})

app.config.from_object(BaseConfig)
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
from .db import *
from src.api.user import user_blueprint
from src.api.jobs import job_blueprint
app.register_blueprint(user_blueprint)
app.register_blueprint(job_blueprint)
