from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

techniques_bp = Blueprint("techniques_bp", __name__)

techniques = globals.db.techniques
positions = globals.db.positions

@techniques_bp.route("/api/v1.0/techniques", methods=["GET"])
@jwt_required
@admin_required
def admin_get_all_techniques():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = page_size * (page_num - 1)

    data_to_return = []
    for technique in techniques.find().skip(page_start).limit(page_size):
        technique["_id"] = str(technique["_id"])
        data_to_return.append(technique)
    return make_response(jsonify(data_to_return), 200)

@techniques_bp.route("/api/v1.0/techniques/me", methods=["GET"])
@jwt_required
def get_user_techniques():
    data_to_return = []
    for technique in list(techniques.find({"user_id": g.user_id})):
        technique["_id"] = str(technique["_id"])
        data_to_return.append(technique)
    if data_to_return is not None:
        return make_response(jsonify(data_to_return), 200)
    else:
        return make_response(jsonify({"error": "Invalid technique ID"}), 404)

@techniques_bp.route("/api/v1.0/techniques/<string:id>", methods=["GET"])
@jwt_required
def show_one_technique(id):
    if g.admin:
        technique = techniques.find_one({"_id": ObjectId(id)})
    else:
        technique = techniques.find_one({'_id': ObjectId(id), "user_id": g.user_id})
    if technique is not None:
        technique["_id"] = str(technique["_id"])
        return make_response(jsonify(technique), 200)
    else:
        return make_response(jsonify({"error": "technique Not Found"}), 404)

@techniques_bp.route("/api/v1.0/techniques", methods=["POST"])
@jwt_required
def create_technique():
    user_id = g.user_id

    required_fields = ["name", "attire", "description", "technique_type"]

    if all(field in request.form for field in required_fields):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        new_technique = {
            "user_id": user_id,
            "name": request.form["name"],
            "starting_position": request.form["starting_position"],
            "ending_position": request.form["ending_position"],
            "description": request.form["description"],
            "attire": request.form["attire"],
            "technique_type": request.form["technique_type"],
            "created_at": now,
            "updated_at": now,
        }

        result= techniques.insert_one(new_technique)
        new_technique_link = ("http://localhost:5001/api/v1.0/techniques/"+ str(result.inserted_id))
        return make_response(jsonify({"url": new_technique_link}), 201)
    else:
        return make_response(jsonify({"error": "Missing form data"}), 400)

@techniques_bp.route("/api/v1.0/techniques/<string:id>", methods=["PUT"])
@jwt_required
def edit_technique(id):
    user_id = g.user_id

    required_fields = ["name", "attire", "description", "technique_type"]

    exists = techniques.find_one({"_id": ObjectId(id)})
    if exists is None:
        return make_response(jsonify({"error": "Invalid technique ID"}), 404)

    if exists.get("user_id") != user_id:
        return make_response(jsonify({"error": "You can only edit your own techniques"}), 403)

    if all(field in request.form for field in required_fields):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        updated_technique = {
            "user_id": user_id,
            "name": request.form["name"],
            "starting_position": request.form["starting_position"],
            "ending_position": request.form["ending_position"],
            "description": request.form["description"],
            "attire": request.form["attire"],
            "technique_type": request.form["technique_type"],
            "updated_at": now,
        }

        query = {"_id": ObjectId(id), "user_id": g.user_id}
        result= techniques.update_one(
            query,
            {"$set": updated_technique}
        )

        if result.matched_count == 0:
            return make_response(jsonify({"error": "technique not found"}), 404)

        updated_technique_link = ("http://localhost:5001/api/v1.0/techniques/" + id)
        return make_response(jsonify({"message": "technique Updated", "url": updated_technique_link}))
        
@techniques_bp.route("/api/v1.0/techniques/<string:id>", methods=["DELETE"])
@jwt_required
def delete_technique(id):
    user_id = g.get("user_id")
    if not user_id:
        return make_response(jsonify({"error": "Token has no user id, please log in again"}), 401)
    existing = techniques.find_one({"_id": ObjectId(id)})
    if existing is None:
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)
 
    if existing.get("user_id") != user_id:
        return make_response(jsonify({"error": "You can only delete your own training sessions"}), 403)

    result = techniques.delete_one({"_id": ObjectId(id), "user_id": user_id})
    if result.deleted_count == 1:
        return make_response("", 204)
    else:
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)

 
@techniques_bp.route("/api/v1.0/technique_description/<string:id>", methods=["GET"])
@jwt_required
def descriptive_technique(id):

    data = []
    if g.admin:
        technique = techniques.find_one({"_id": ObjectId(id)})
    else:
        technique = techniques.find_one({'_id': ObjectId(id), "user_id": g.user_id})
    if technique is not None:
        technique["_id"] = str(technique["_id"])
        starting_position = technique["starting_position"]
        ending_position = technique["ending_position"]
        starting = positions.find_one({'_id': ObjectId(starting_position), "user_id": g.user_id})
        ending = positions.find_one({'_id': ObjectId(ending_position), "user_id": g.user_id})

        if starting:
            starting["_id"] = str(starting["_id"])
        if ending:
            ending["_id"] = str(ending["_id"])
        response = {"Technique Name: ": technique["name"], "Starting Position: ": starting["name"], "Ending Position: ": ending["name"],  "Details: ": technique["description"]}
        return make_response(jsonify(response), 200)
    else:
        return make_response(jsonify({"error": "technique Not Found"}), 404)
