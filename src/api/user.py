import datetime
from flask import Blueprint, render_template
from flask import request, jsonify
from src.api.response_utils import send_response
from src.bl.action_result import ActionResult, ResultCode
from src.bl.auth import get_login_res
from src.common_utils import mask_email
from src.db.sql.user import User
from src import db
from src.utils import get_uid
from logger_util import get_logger

log = get_logger(__name__)
user_blueprint = Blueprint("user_blueprint", __name__)


@user_blueprint.route("/api/user/sign_up", methods=['POST'])
def sign_up():
    req_id: str = get_uid()
    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name')
        password = data.get('password')
        if not email:
            res: ActionResult = ActionResult(ResultCode.InvalidDataOrArgument, message="Email is required.",
                                             req_id=req_id, http_res_status=204)
            return send_response(res)
        # Check if user already exists
        existing_user = User.get_by_email(email)
        if existing_user:
            res: ActionResult = ActionResult(ResultCode.UserAlreadyPresent, message="User with this email already "
                                             "exists.", req_id=req_id, http_res_status=409)
            return send_response(res)
        # Create new user
        user = User(email=email, name=name, password=password)
        db.session.add(user)
        db.session.commit()
        res: ActionResult = ActionResult(code=ResultCode.Ok, data=get_login_res(user), message="User registered "
                                         "successfully.", req_id=req_id, http_res_status=200)
        return send_response(res)
    except Exception as ex:
        log.exception(f"Request failed. Reason: Exception: {ex}, request_id: {req_id}.")
        return jsonify({"success": False, "message": "Internal server error.", "request_id": req_id}), 500


@user_blueprint.route("/api/user/login", methods=['POST'])
def login():
    req_id: str = get_uid()
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        if not email:
            res: ActionResult = ActionResult(ResultCode.InvalidDataOrArgument, message="Email is required.",
                                             req_id=req_id, http_res_status=204)
            return send_response(res)
        # Check if user already exists
        user: User = User.get_by_email(email)
        if not user:
            res: ActionResult = ActionResult(ResultCode.UserNotFound, message=f"User Not behavioral with "
                                             f"email: {email} ", req_id=req_id, http_res_status=404)
            return send_response(res)

        if not user.is_password_matched(password):
            res: ActionResult = ActionResult(ResultCode.AuthenticationError, message=f"Incorrect email or password",
                                             req_id=req_id, http_res_status=404)
            return send_response(res)
        user_last_login = user.last_login.isoformat() if user.last_login else ""
        user.last_login = datetime.datetime.now()
        db.session.commit()
        log.info(f"User successfully logged in: {mask_email(email)}, req id: {req_id}")
        res: ActionResult = ActionResult(code=ResultCode.Ok, data=get_login_res(user,
                                         last_login_iso_date=user_last_login), message="User registered successfully.",
                                         req_id=req_id, http_res_status=200)
        return send_response(res)
    except Exception as ex:
        log.exception(f"Request failed. Reason: Exception: {ex}, request_id: {req_id}.")
        return jsonify({"success": False, "message": "Internal server error.", "request_id": req_id}), 500


@user_blueprint.route("/signup", methods=["GET"])
def front_end_signup():
    return render_template("signup.html")


@user_blueprint.route("/login", methods=["GET"])
def front_end_login():
    return render_template("login.html")


@user_blueprint.route("/", methods=["GET"])
def front_end_home():
    return render_template("home.html")
