import datetime
import time
import jwt
from cryptography.fernet import InvalidToken
import urllib.parse
import settings
from src import db
from src.db import User
from logger_util import get_logger
from src.encryption import encrypt_data_sys, decrypt_data_sys
from src.utils import get_uid

log = get_logger(__name__)


class AuthPayload(object):
    def __init__(self, user_id, url=None, scope: str = "", http_method: str = ""):
        self.r_id: str = get_uid()
        self.user_id: int = user_id
        self.user = None
        self.url = url
        self.http_method: str = http_method
        self.scope: str = scope
        self.req_st = time.time()

    def get_user(self):
        if self.user is None:
            self.user = User.query.get(self.user_id)
        return self.user

    def get_req_id(self):
        return f"Req_id: {self.r_id} User_id: {self.user_id} URL: ({self.http_method}){self.url}"

    def get_processing_log(self):
        return f'Processing Time: {round(time.time() - self.req_st, 3)}'

    def is_url_accessible(self, url: str):
        url = url.split("?")[0]
        if self.scope == "*" or '/isp_qual_api/auth/login' in url:
            return True
        if self.scope not in url:
            return False
        return True

    @staticmethod
    def get_auth_token(user_id, duration_days=1, minutes=0, scope_regex: str = "*"):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                # Use limit of 2 hour for token validation
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=duration_days, minutes=minutes),
                'iat': datetime.datetime.utcnow(),
                'uid': user_id,
                'scope': scope_regex
            }
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            if isinstance(token, str):
                return urllib.parse.quote(encrypt_data_sys(token))
            return urllib.parse.quote(encrypt_data_sys(token.decode("utf-8")))

        except Exception as ex:
            log.exception(ex)
            return ex

    @staticmethod
    def decode_auth_token(auth_token):
        """
        Validates the auth token
        :param auth_token:
        :return: integer|string
        """
        try:
            # Url Decoding.
            auth_token = urllib.parse.unquote(auth_token)
            auth_token = decrypt_data_sys(auth_token)
            payload = jwt.decode(auth_token, settings.SECRET_KEY, algorithms='HS256')
            return AuthPayload(payload['uid'], scope=payload['scope'])
        except jwt.ExpiredSignatureError:
            log.info('Signature expired. Please log in again.')
            return None
        except jwt.InvalidTokenError:
            log.info('Invalid token. Please log in again.')
            return None
        except InvalidToken:
            log.info('Could not decrypt the token. Please log in again.')
            return None
        except Exception as ex:
            log.exception(ex)
            return None

    @staticmethod
    def solve_operation_error():
        db.session.rollback()


def get_login_res(user: User, remember: bool = False, scope: str = "*", last_login_iso_date="",
                  auth_duration_min: int = 0):
    if not last_login_iso_date and user.last_login:
        last_login_iso_date = user.last_login.isoformat()

    auth_duration_day = 365 if remember else 1
    if auth_duration_min:
        auth_duration_day = 0
    return {
        'status': 'success',
        'message': 'Successfully logged in.',
        'user_id': user.id,
        'full_name': user.full_name,
        'user_email': user.get_email(),
        'auth_token': AuthPayload.get_auth_token(user.id, duration_days=auth_duration_day,
                                                 minutes=auth_duration_min, scope_regex=scope),
        'last_login': last_login_iso_date + "Z" if last_login_iso_date else ""}
