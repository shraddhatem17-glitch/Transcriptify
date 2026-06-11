from functools import wraps
from flask import request
from sqlalchemy.exc import OperationalError
from logger_util import get_logger
from src.api.response_utils import send_response
from src.bl.action_result import ActionResult, ResultCode
from src.bl.auth import AuthPayload

log = get_logger(__name__)


HEADER_AUTH_KEY: str = "AuthToken"
URL_AUTH_KEY: str = 't'


def validate_auth_token(token, f, *args, **kwargs):
    try:
        auth_payload = AuthPayload.decode_auth_token(token)
        return validate_auth_payload(auth_payload, f, *args, **kwargs)
    except Exception as ex:
        log.exception(ex)
        res = ActionResult(ResultCode.InvalidDataOrArgument, "Invalid auth token.")
        log.info(f"Request failed. Reason: {res.message}")
        return send_response(res, 401)


def login_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if HEADER_AUTH_KEY in request.headers:
            token = request.headers[HEADER_AUTH_KEY]
        elif URL_AUTH_KEY in request.args.keys():
            token = request.args.get(URL_AUTH_KEY)

        if token:
            return validate_auth_token(token, f, *args, **kwargs)
        else:
            res = ActionResult(ResultCode.AuthenticationError, "Invalid auth token.")
            log.info(f"Request failed. Reason: {res.message}")
            return send_response(res, 401)
    return decorator


def validate_auth_payload(auth_payload: AuthPayload, f, *args, **kwargs):
    try:
        if auth_payload is None:
            res = ActionResult(ResultCode.InvalidDataOrArgument, "Invalid auth token.")
            log.info(f"Request failed. Reason: {res.message} url: {request.url}")
            return send_response(res, 401)

        auth_payload.url = request.path
        auth_payload.http_method = str(request.method)
        log.info(f"Request received. method: {request.method} {auth_payload.get_req_id()}")

        attempt = 0
        while attempt < 5:
            try:
                attempt += 1
                if not auth_payload.is_url_accessible(request.url):
                    res = ActionResult(ResultCode.URLNotAccessible, "Url is not accessible. Please login again")
                    log.info(f"Request failed. Reason: {res.message} . req_id: {auth_payload.get_req_id()}")
                    return send_response(res, 403)
                else:
                    return f(auth_payload, *args, **kwargs)
            except OperationalError:
                log.info(f"Due to my sql connection error login {attempt} fail. {OperationalError}")
                AuthPayload.solve_operation_error()
            except Exception as ex:
                log.exception(ex)
                res = ActionResult(ResultCode.InvalidDataOrArgument, "Invalid auth token.")
                log.info(f"Request failed. Reason: {res.message}")
                return send_response(res, 401)

        res = ActionResult(ResultCode.InvalidDataOrArgument, "Invalid auth token.")
        log.info(f"Request failed. Reason: {res.message}")
        return send_response(res, 401)
    except Exception as ex:
        log.exception(ex)
        res = ActionResult(ResultCode.InvalidDataOrArgument, "Invalid auth token.")
        log.info(f"Request failed. Reason: {res.message}")
        return send_response(res, 401)
