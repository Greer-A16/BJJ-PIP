from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

positions_bp = Blueprint("positions_bp", __name__)

positions = globals.db.positions

@positions_bp.route("/api/v1.0/positions", methods=["GET"])
@jwt_required
@admin_required
def admin_get_all_positions():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = page_size * (page_num - 1)

    data_to_return = []
    for position in positions.find().skip(page_start).limit(page_size):
        position["_id"] = str(position["_id"])
        data_to_return.append(position)
    return make_response(jsonify(data_to_return), 200)

@positions_bp.route("/api/v1.0/positions/me", methods=["GET"])
@jwt_required
def get_user_positions():
    data_to_return = []
    for position in list(positions.find({"user_id": g.user_id})):
        position["_id"] = str(position["_id"])
        data_to_return.append(position)
    if data_to_return is not None:
        return make_response(jsonify(data_to_return), 200)
    else:
        return make_response(jsonify({"error": "Invalid Position ID"}), 404)

@positions_bp.route("/api/v1.0/positions/<string:id>", methods=["GET"])
@jwt_required
def show_one_position(id):
    if g.admin:
        position = positions.find_one({"_id": ObjectId(id)})
    else:
        position = positions.find_one({'_id': ObjectId(id), "user_id": g.user_id})
    if position is not None:
        position["_id"] = str(position["_id"])
        return make_response(jsonify(position), 200)
    else:
        return make_response(jsonify({"error": "Position Not Found"}), 404)

@positions_bp.route("/api/v1.0/positions", methods=["POST"])
@jwt_required
def create_position():
    user_id = g.user_id

    required_fields = ["name", "attire", "description", "position_type"]

    if all(field in request.form for field in required_fields):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        new_position = {
            "user_id": user_id,
            "name": request.form["name"],
            "description": request.form["description"],
            "attire": request.form["attire"],
            "position_type": request.form["position_type"],
            "created_at": now,
            "updated_at": now,
        }

        result= positions.insert_one(new_position)
        new_position_link = ("http://localhost:5001/api/v1.0/positions/"+ str(result.inserted_id))
        return make_response(jsonify({"url": new_position_link}), 201)
    else:
        return make_response(jsonify({"error": "Missing form data"}), 400)

@positions_bp.route("/api/v1.0/positions/<string:id>", methods=["PUT"])
@jwt_required
def edit_position(id):
    user_id = g.user_id

    required_fields = ["duration_minutes", "attire", "session_date", "session_type"]

    exists = positions.find_one({"_id": ObjectId(id)})
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

        updated_position = {
            "user_id": user_id,
            "name": request.form["name"],
            "description": request.form["description"],
            "attire": request.form["attire"],
            "position_type": request.form["position_type"],
            "updated_at": now,
        }

        query = {"_id": ObjectId(id), "user_id": g.user_id}
        result= positions.update_one(
            query,
            {"$set": updated_position}
        )

        if result.matched_count == 0:
            return make_response(jsonify({"error": "Training Session not found"}), 404)

        updated_position_link = ("http://localhost:5001/api/v1.0/positions/" + id)
        return make_response(jsonify({"message": "Training Session Updated", "url": updated_position_link}))
        
@positions_bp.route("/api/v1.0/positions/<string:id>", methods=["DELETE"])
@jwt_required
def delete_position(id):
    user_id = g.get("user_id")
    if not user_id:
        return make_response(jsonify({"error": "Token has no user id, please log in again"}), 401)
    existing = positions.find_one({"_id": ObjectId(id)})
    if existing is None:
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)
 
    if existing.get("user_id") != user_id:
        return make_response(jsonify({"error": "You can only delete your own training sessions"}), 403)

    result = positions.delete_one({"_id": ObjectId(id), "user_id": user_id})
    if result.deleted_count == 1:
        return make_response("", 204)
    else:
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)