from flask import Blueprint, request, make_response, jsonify
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from datetime import datetime, timezone, timedelta

training_sessions_bp = Blueprint("training_sessions_bp", __name__)

training_sessions = globals.db.training_sessions


@training_sessions_bp.route("/api/v1.0/training_sessions", methods=["GET"])
@jwt_required
@admin_required
def admin_get_all_training_sessions():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = page_size * (page_num - 1)

    data_to_return = []
    for training_session in training_sessions.find() \
            .skip(page_start).limit(page_size):
        data_to_return.append(training_session)
    return make_response(jsonify(data_to_return), 200)

@training_sessions_bp.route("/api/v1.0/training_sessions/<string:id>", methods=["GET"])
@jwt_required
def get_user_training_session(id):
    training_session_list = list(training_sessions.find({'user_id': id}))
    if training_session_list is not None:
        return make_response(jsonify(training_session_list), 200)
    else:
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)

