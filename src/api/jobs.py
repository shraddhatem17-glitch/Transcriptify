import datetime
from flask import Blueprint, render_template
from flask import request, jsonify

import settings
from src.api.decorators import login_required
from src.api.response_utils import send_response
from src.bl.action_result import ActionResult, ResultCode
from src.bl.auth import get_login_res, AuthPayload
from src.common_utils import mask_email, get_job_file_name
from src.db.sql.user import User
from src import db, Job, JobType, JobStatus
from src.nlp import query_transcription
from src.utils import get_uid
from logger_util import get_logger
from flask import request, jsonify
from werkzeug.utils import secure_filename
import os


log = get_logger(__name__)
job_blueprint = Blueprint("job_blueprint", __name__)


@job_blueprint.route('/api/job/add_job', methods=['POST'])
@login_required
def add_job(auth_payload: AuthPayload):
    try:
        title = request.form.get('title')
        job_type = request.form.get('job_type')
        file = request.files.get('file')

        # Validate required fields
        if not title:
            res: ActionResult = ActionResult(ResultCode.InvalidDataOrArgument, message="Please add title",
                                             req_id=auth_payload.get_req_id(), http_res_status=400)
            return send_response(res)

        if job_type not in [jt.name for jt in JobType]:
            res: ActionResult = ActionResult(ResultCode.InvalidDataOrArgument, message="Invalid Job type.",
                                             req_id=auth_payload.get_req_id(), http_res_status=400)
            return send_response(res)

        if not file:
            res: ActionResult = ActionResult(ResultCode.FileNotFound, message="Please attach file.",
                                             req_id=auth_payload.get_req_id(), http_res_status=400)
            return send_response(res)

        # Validate file type
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        if '.' not in filename or file_ext not in settings.SUPPORTED_MEDIA_TYPE:
            error = f"Invalid file type, required file extension should be one of: {settings.SUPPORTED_MEDIA_TYPE} " \
                    f"give extension is: {file_ext}"
            log.error(error)
            res: ActionResult = ActionResult(ResultCode.InvalidDataOrArgument, message=error,
                                             req_id=auth_payload.get_req_id(), http_res_status=400)
            return send_response(res)

        # Save file
        file_name = get_job_file_name(auth_payload.user_id, file_ext)
        file_path = os.path.join(os.getcwd(), settings.UPLOAD_FOLDER, file_name)
        os.makedirs(os.path.join(os.getcwd(), settings.UPLOAD_FOLDER), exist_ok=True)
        file.save(file_path)

        # Save to DB
        job = Job(title=title, file_name=file_name, job_type=job_type, media_url=file_path,
                  user_id=auth_payload.user_id)
        db.session.add(job)
        db.session.commit()
        res: ActionResult = ActionResult(code=ResultCode.Ok, message=f"File uploaded and job created job_id: {job.id}",
                                         req_id=auth_payload.get_req_id(), http_res_status=200)
        return send_response(res)
    except Exception as ex:
        log.exception(f"Request failed. Reason: Exception: {ex}, request_id: {auth_payload.get_req_id()}.")
        return jsonify({"success": False, "message": "Internal server error.",
                        "request_id": auth_payload.get_req_id()}), 500


@job_blueprint.route('/api/job/get_all_jobs', methods=['GET'])
@login_required
def get_all_jobs(auth_payload: AuthPayload):
    try:
        data = []
        jobs: [Job] = Job.get_jobs_by_user_id(auth_payload.user_id)
        j: Job
        for j in jobs:
            data.append({"title": j.title, "id": j.id, "filename": j.file_name, "created_on": j.created_on, "job_type":
                         j.job_type, "status": j.status})
        res: ActionResult = ActionResult(data=data, code=ResultCode.Ok, req_id=auth_payload.get_req_id(),
                                         http_res_status=200)
        return send_response(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@job_blueprint.route('/api/job/<int:job_id>/get_job_transcription', methods=['GET'])
@login_required
def get_job_transcription(auth_payload: AuthPayload, job_id: int):
    try:
        job: Job = Job.get_job_by_id(job_id)
        if not job:
            error = f"Job not available with job id: {job_id}."
            log.error(error)
            res: ActionResult = ActionResult(ResultCode.InvalidDataOrArgument, message=error,
                                             req_id=auth_payload.get_req_id(), http_res_status=404)
            return send_response(res)
        if job.user_id != auth_payload.user_id:
            error = f"This Job dose not belongs to you, job id: {job_id}."
            log.error(error)
            res: ActionResult = ActionResult(ResultCode.AuthorizationError, message=error,
                                             req_id=auth_payload.get_req_id(), http_res_status=403)
            return send_response(res)
        if job.status != JobStatus.Completed.value:
            error = f"Job status for job id: {job_id} is not {JobStatus.Completed.value} current status: {job.status}."
            log.error(error)
            res: ActionResult = ActionResult(ResultCode.CurrentlyUnableToProcess, message=error,
                                             req_id=auth_payload.get_req_id(), http_res_status=409)
            return send_response(res)
        filename = job.file_name.split(".")[0] + ".txt"
        file_path = os.path.join("static", filename)
        if not os.path.exists:
            error = f"File not available with file id: {file_path}."
            log.error(error)
            res: ActionResult = ActionResult(ResultCode.InvalidDataOrArgument, message=error,
                                             req_id=auth_payload.get_req_id(), http_res_status=404)
            return send_response(res)
        with open(file_path, "r", encoding="utf-8") as f:
            transcription = f.read()
        data = {"transcription": transcription}
        res: ActionResult = ActionResult(data=data, code=ResultCode.Ok, req_id=auth_payload.get_req_id(),
                                         http_res_status=200)
        return send_response(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@job_blueprint.route('/api/job/<int:job_id>/get_job_summary', methods=['GET'])
@login_required
def get_job_summary(auth_payload: AuthPayload, job_id: int):
    try:
        job: Job = Job.get_job_by_id(job_id)
        if not job:
            error = f"Job not available with job id: {job_id}."
            log.error(error)
            res: ActionResult = ActionResult(ResultCode.InvalidDataOrArgument, message=error,
                                             req_id=auth_payload.get_req_id(), http_res_status=404)
            return send_response(res)
        if job.user_id != auth_payload.user_id:
            error = f"This Job dose not belongs to you, job id: {job_id}."
            log.error(error)
            res: ActionResult = ActionResult(ResultCode.AuthorizationError, message=error,
                                             req_id=auth_payload.get_req_id(), http_res_status=403)
            return send_response(res)
        if job.status != JobStatus.Completed.value:
            error = f"Job status for job id: {job_id} is not {JobStatus.Completed.value} current status: {job.status}."
            log.error(error)
            res: ActionResult = ActionResult(ResultCode.CurrentlyUnableToProcess, message=error,
                                             req_id=auth_payload.get_req_id(), http_res_status=409)
            return send_response(res)
        filename = job.file_name.split(".")[0] + ".txt"
        file_path = os.path.join("static", filename)
        if not os.path.exists:
            error = f"File not available with file id: {file_path}."
            log.error(error)
            res: ActionResult = ActionResult(ResultCode.InvalidDataOrArgument, message=error,
                                             req_id=auth_payload.get_req_id(), http_res_status=404)
            return send_response(res)
        with open(file_path, "r", encoding="utf-8") as f:
            transcription = f.read()
        summary = query_transcription(transcription=transcription, req_id=auth_payload.get_req_id())
        data = {"summary": summary}
        res: ActionResult = ActionResult(data=data, code=ResultCode.Ok, req_id=auth_payload.get_req_id(),
                                         http_res_status=200)
        return send_response(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@job_blueprint.route("/add_job", methods=["GET"])
def front_end_add_job():
    return render_template("add_job.html")


@job_blueprint.route("/get_all_jobs", methods=["GET"])
def front_end_get_all_jobs():
    return render_template("listing_jobs.html")


@job_blueprint.route("/job/<int:job_id>/analysis", methods=["GET"])
def front_end_get_job_analysis(job_id: int):
    return render_template("job_analysis.html", job_id=job_id)

