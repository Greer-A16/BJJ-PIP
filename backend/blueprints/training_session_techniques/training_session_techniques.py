from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

training_session_techniques_bp = Blueprint("training_session_techniques_bp", __name__)

training_session_techniques = globals.db.training_session_techniques
techniques = globals.db.techniques
training_sessions = globals.db.training_sessions

@training_session_techniques_bp.route("/api/v1.0/training_session/<string:training_id>/technique/<string:technique_id>", methods=["post"])
@jwt_required
def create_training_session_technique_link(training_id, technique_id):

    session = training_sessions.find_one({
        "_id": ObjectId(training_id),
        "user_id": g.user_id
    })

    if session is None:
        return make_response(
            jsonify({"error": "Training Session Not Found"}, 404)
        )
    
    technique = techniques.find_one({
        "_id": ObjectId(technique_id),
        "user_id": g.user_id
    })

    if technique is None:
        return make_response(
            jsonify({"error": "technique Not Found"}, 404)
        )
    
    new_link = {
        "user_id": g.user_id,
        "training_session_id": ObjectId(training_id),
        "technique_id": ObjectId(technique_id),
    }

    result = training_session_techniques.insert_one(new_link)
    new_technique_link = ("http://localhost:5001/api/v1.0/techniques/"+ str(result.inserted_id))
    return make_response(jsonify({"url": new_technique_link}), 201)

@training_session_techniques_bp.route("/api/v1.0/training_sessions/<string:id>/techniques")
@jwt_required
def get_all_techniques_from_one_session(id):

    session = training_sessions.find_one({
        "_id": ObjectId(id),
        "user_id": g.user_id
    })

    if session is None:
        return make_response(
            jsonify({"error": "Training Session Not Found"}, 404)
        )

    links = training_session_techniques.find({
       "training_session_id" : ObjectId(id),
       "user_id": g.user_id
    })

    data_to_return = []
    for link in links:
        technique = techniques.find_one({
            "_id": link["technique_id"],
            "user_id": g.user_id
        })

        if technique:
            technique["_id"] = str(technique["_id"])
            data_to_return.append(technique)

    return make_response(jsonify(data_to_return), 200)

@training_session_techniques_bp.route("/api/v1.0/descriptive_technique/<string:id>", methods=["GET"])
@jwt_required
def descriptive_technique(id):