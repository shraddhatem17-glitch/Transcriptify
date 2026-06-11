import os
import time
from flask import make_response, jsonify, send_file, Response
import settings
from logger_util import get_logger
from src.common_utils import convert_elapsed_time_to_hh_mm_ss_ms
import typing as t
from src.bl.action_result import ActionResult

log = get_logger(__name__)


def send_response(res: ActionResult = None, code=200, data: object = None, req_id: str = None,
                  auth_payload=None):
    try:
        msg: str = ""
        req_time_taken = time.time() - auth_payload.req_st if auth_payload else ""
        if req_time_taken:
            req_time_taken = convert_elapsed_time_to_hh_mm_ss_ms(req_time_taken)
        if res:
            if res.http_res_status:
                code = res.http_res_status
            res_dic = res.to_dic()
            msg = res.message
            if data is None:
                data = res.data
            if not req_id:
                req_id = res.req_id
        else:
            res_dic = ActionResult.get_ok_dic()

        if data is not None:
            res_dic['data'] = data
        if auth_payload:
            res_dic['response_id'] = auth_payload.r_id
            if not req_id:
                req_id = auth_payload.get_req_id()
        elif req_id:
            res_dic['response_id'] = req_id
        if req_id:
            if code == 200:
                log.info(f"Request Pass. Message {msg}, {req_id}, time taken: {req_time_taken}")
            elif code == 500:
                log.warn(f"Request Failed with exception. {req_id}, time taken: {req_time_taken}")
        return make_response(jsonify(res_dic)), code
    except Exception as ex:
        log.exception(ex)


def get_content_type(file_name: str):
    try:
        file_ext: str = file_name.split('.')[-1].lower()
        if file_ext == 'mp4':
            return "video/mp4"

        if file_ext == 'mp3':
            return "audio/mpeg"

        if file_ext == 'pdf':
            return "application/pdf"

        if file_ext == 'jpeg':
            return "image/jpeg"

        if file_ext == 'png':
            return "image/png"

        if file_ext == 'docx':
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    except Exception as ex:
        log.exception(ex)
        return ""


def send_file_response(file_path_or_data: t.Union[str, t.BinaryIO, os.PathLike],
                       mimetype: str, max_age=settings.MEDIA_CACHE_SEC, req_id: str = '', auth_payload=None):
    if auth_payload:
        req_id = auth_payload.get_req_id()
        req_id += f' {auth_payload.get_processing_log()}'
    log.info(f"Request Pass. {req_id}")
    res: Response = send_file(file_path_or_data, mimetype=mimetype, max_age=max_age)
    res.headers.add('Access-Control-Allow-Origin', '*')
    return res
