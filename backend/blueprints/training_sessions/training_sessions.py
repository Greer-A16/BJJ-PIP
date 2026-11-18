from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
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
    for training_session in training_sessions.find().skip(page_start).limit(page_size):
        training_session["_id"] = str(training_session["_id"])
        data_to_return.append(training_session)
    return make_response(jsonify(data_to_return), 200)

@training_sessions_bp.route("/api/v1.0/training_sessions/me", methods=["GET"])
@jwt_required
def get_user_training_session():
    data_to_return = []
    for training_session in list(training_sessions.find({"user_id": g.user_id})):
        training_session["_id"] = str(training_session["_id"])
        data_to_return.append(training_session)
    if data_to_return is not None:
        return make_response(jsonify(data_to_return), 200)
    else:
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)

@training_sessions_bp.route("/api/v1.0/training_sessions/<string:id>", methods=["GET"])
@jwt_required
def show_one_training_session(id):
    if g.admin:
        training_session = training_sessions.find_one({"_id": ObjectId(id)})
    else:
        training_session = training_sessions.find_one({'_id': ObjectId(id), "user_id": g.user_id})
    if training_session is not None:
        training_session["_id"] = str(training_session["_id"])
        return make_response(jsonify(training_session), 200)
    else:
        return make_response(jsonify({"error": "Training Session Not Found"}), 404)


@training_sessions_bp.route("/api/v1.0/training_sessions", methods=["POST"])
@jwt_required
def create_training_session():
    user_id = g.user_id

    required_fields = ["duration_minutes", "attire", "session_date", "session_type"]

    if all(field in request.form for field in required_fields):
        try:
            duration_minutes = int(request.form["duration_minutes"])
        except ValueError:
            return make_response(jsonify({"error": "duration_minutes must be a number"}), 400)

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        new_training_session = {
            "user_id": user_id,
            "class_session_id": request.form.get("class_session_id"),
            "gym_id": request.form.get("gym_id"),
            "session_date": request.form["session_date"],
            "session_type": request.form["session_type"],
            "duration_minutes": duration_minutes,
            "attire": request.form["attire"],
            "notes": request.form.get("notes"),
            "created_at": now,
            "updated_at": now,
        }

        result= training_sessions.insert_one(new_training_session)
        new_training_session_link = ("http://localhost:5001/api/v1.0/training_sessions/"+ str(result.inserted_id))
        return make_response(jsonify({"url": new_training_session_link}), 201)
    else:
        return make_response(jsonify({"error": "Missing form data"}), 400)


@training_sessions_bp.route("/api/v1.0/training_sessions/<string:id>", methods=["PUT"])
@jwt_required
def edit_training_session(id):
    user_id = g.user_id

    required_fields = ["duration_minutes", "attire", "session_date", "session_type"]

    exists = training_sessions.find_one({"_id": ObjectId(id)})
    if exists is None:
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)

    if exists.get("user_id") != user_id:
        return make_response(jsonify({"error": "You can only edit your own training sessions"}), 403)

    if all(field in request.form for field in required_fields):
        try:
            duration_minutes = int(request.form["duration_minutes"])
        except ValueError:
            return make_response(jsonify({"error": "duration_minutes must be a number"}), 400)

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        updated_training_session = {
            "user_id": user_id,
            "class_session_id": request.form.get("class_session_id"),
            "gym_id": request.form.get("gym_id"),
            "session_date": request.form["session_date"],
            "session_type": request.form["session_type"],
            "duration_minutes": duration_minutes,
            "attire": request.form["attire"],
            "notes": request.form.get("notes"),
            # "created_at": now,
            "updated_at": now,
        }

        query = {"_id": ObjectId(id), "user_id": g.user_id}
        result= training_sessions.update_one(
            query,
            {"$set": updated_training_session}
        )

        if result.matched_count == 0:
            return make_response(jsonify({"error": "Training Session not found"}), 404)

        updated_training_session_link = ("http://localhost:5001/api/v1.0/training_sessions/" + id)
        return make_response(jsonify({"message": "Training Session Updated", "url": updated_training_session_link}))
        
@training_sessions_bp.route("/api/v1.0/training_sessions/<string:id>", methods=["DELETE"])
@jwt_required
def delete_training_session(id):
    user_id = g.get("user_id")
    if not user_id:
        return make_response(jsonify({"error": "Token has no user id, please log in again"}), 401)
    existing = training_sessions.find_one({"_id": ObjectId(id)})
    if existing is None:
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)
 
    if existing.get("user_id") != user_id:
        return make_response(jsonify({"error": "You can only delete your own training sessions"}), 403)

    result = training_sessions.delete_one({"_id": ObjectId(id), "user_id": user_id})
    if result.deleted_count == 1:
        return make_response("", 204)
    else:
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)