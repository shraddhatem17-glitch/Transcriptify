import settings
from datetime import datetime
import requests
from logger_util import get_logger


log = get_logger(__name__)
org_keys: dict = {}


class OrgKey(object):
    def __init__(self, org_id=None, key=None, expire_dt=None):
        self.org_id: int = org_id
        self.key: str = key
        self.expire_dt: datetime = expire_dt


def get_key_from_server(key_id):
    url: str = f"http://127.0.0.1:1978/encryptionUtil?env={settings.ENV}&corpId={key_id}&vapp={settings.APP_NAME}"
    response = requests.request('GET', url)
    if response.status_code == 200:
        return OrgKey(id, response.text)
    else:
        log.error(f"Couldn't fetch key for url: {url}")
        return None


def get_sys_key():
    try:
        return OrgKey(0, settings.SYS_SECRET_KEY)
    except Exception as ex:
        log.exception(ex)
        return None


sys_keys: OrgKey = get_sys_key()

#
# def get_org_key_from_server(org_id):
#     try:
#         org_id = str(org_id)
#         if settings.is_local_env():
#             file_path = f"{os.getcwd()}/{settings.UPLOAD_FOLDER}/keys.json"
#             f = open(file_path, "r")
#             all_org_keys: dict = json.loads(f.read())
#             f.close()
#             if org_id not in all_org_keys.keys():
#                 all_org_keys[org_id] = Fernet.generate_key().decode()
#                 f = open(file_path, "w")
#                 f.write(json.dumps(all_org_keys))
#                 f.close()
#             return OrgKey(org_id, all_org_keys[org_id])
#         else:
#             return get_key_from_server(org_id)
#     except Exception as ex:
#         log.exception(ex)
#         return None
#
#
# def get_org_key(org_id):
#     try:
#         global org_keys
#         if org_id not in org_keys.keys():
#             org_keys[org_id] = get_org_key_from_server(org_id)
#         return org_keys[org_id]
#     except Exception as ex:
#         log.exception(ex)
#         return None
#
#
# def load_all_keys():
#     from src.db_layer.sql_models.organization import Organizations
#     for org in Organizations.query.filter(Organizations.id > 0).all():
#         get_org_key(org.id)
#
#     sys_keys: OrgKey = get_sys_key()
