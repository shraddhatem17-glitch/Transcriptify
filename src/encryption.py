import hashlib
from src.encryption_util import sys_keys
from cryptography.fernet import Fernet
from logger_util import get_logger

log = get_logger(__name__)


def convert_to_bytes(data):
    return str(data).encode()


def convert_to_bytes_lower(data):
    return str(data).lower().encode()


def encrypt_data(key, data) -> str:
    f = Fernet(key)
    r = f.encrypt(convert_to_bytes(data)).decode()
    del f
    return r


def decrypt_data(key, enc_data) -> str:
    f = Fernet(key)
    r = f.decrypt(convert_to_bytes(enc_data)).decode()
    del f
    return r


# def encrypt_data_org(org_id: int, data) -> str:
#     if data:
#         return encrypt_data(get_org_key(org_id).key, data)
#     return data
#
#
# def decrypt_data_org(org_id: int, enc_data) -> str:
#     if enc_data:
#         return decrypt_data(get_org_key(org_id).key, enc_data)
#     return enc_data


def encrypt_data_sys(data) -> str:
    if data:
        return encrypt_data(sys_keys.key, data)
    return data


def decrypt_data_sys(enc_data) -> str:
    if enc_data:
        return decrypt_data(sys_keys.key, enc_data)
    return enc_data


def hash_data(data):
    return hashlib.sha3_256(convert_to_bytes_lower(data)).hexdigest()
