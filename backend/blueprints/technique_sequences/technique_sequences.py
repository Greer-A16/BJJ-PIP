from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

technique_sequences_bp = Blueprint("technique_sequences_bp", __name__)

sequences = globals.db.technique_sequences
sequence_steps = globals.db.sequence_steps

@technique_sequences_bp.route("/api/v1.0/sequences/me", methods=["GET"])
@jwt_required
def get_user_sequences():
    data_to_return = []
    for sequence in list(sequences.find({"user_id": g.user_id})):
        sequence["_id"] = str(sequence["_id"])
        data_to_return.append(sequence)
    if data_to_return is not None:
        return make_response(jsonify(data_to_return), 200)
    else:
        return make_response(jsonify({"error": "Invalid sequence ID"}), 404)

@technique_sequences_bp.route("/api/v1.0/sequences/<string:id>", methods=["GET"])
@jwt_required
def get_one_sequence_and_steps(id):

    sequence_id = ObjectId(id)
    if g.admin:
        sequence = sequences.find_one({"_id": sequence_id})
    else:
        sequence = sequences.find_one({'_id': sequence_id, "user_id": g.user_id})


    if sequence is None:
        return make_response(jsonify({"error": "Invalid Sequence ID"}), 404)    
    ## sequence steps find all with sequence id
    sequence_steps_to_return = []
    steps = sequence_steps.find({
        "sequence_id": sequence_id,
        "user_id": sequence["user_id"]
    }).sort("step_no", 1)

    for step in steps:
        step["_id"] = str(step["_id"])
        step["sequence_id"] = str(step["sequence_id"])
        step["technique_id"] = str(step["technique_id"])
        ## print sequence

        sequence_steps_to_return.append(step)
    ## print all sequence steps
    sequence["_id"] = str(sequence["_id"])

    response = {
        "sequence": sequence,
        "steps": sequence_steps_to_return
    }

    return make_response(jsonify(response), 200)

@technique_sequences_bp.route("/api/v1.0/sequences", methods=["POST"])
@jwt_required
def create_sequence():
    user_id = g.user_id

    required_fields = ["name"]

    if all(field in request.form for field in required_fields):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        new_sequence = {
            "user_id": user_id,
            "name": request.form["name"],
            "created_at": now,
            "updated_at": now,
        }

        result= sequences.insert_one(new_sequence)
        new_sequence_link = ("http://localhost:5001/api/v1.0/sequences/"+ str(result.inserted_id))
        return make_response(jsonify({"url": new_sequence_link}), 201)
    else:
        return make_response(jsonify({"error": "Missing form data"}), 400)


@technique_sequences_bp.route("/api/v1.0/sequences/<string:id>/steps", methods=["POST"])
@jwt_required
def create_sequence_steps(id):
    user_id = g.user_id
    sequence_id =ObjectId(id)
    
    sequence = sequences.find_one({
        "_id": sequence_id,
        "user_id": user_id
    })

    if sequence is None:
        return make_response(jsonify({"error": "Sequence not Found"}, 404))

    if "technique_id" not in request.form:
        return make_response(jsonify({"error": "Missing Technique"}, 404))
    
    technique_id = request.form["technique_id"]

    existing_step_count = sequence_steps.count_documents({
        "sequence_id": sequence_id,
        "user_id": user_id
    })

    step_no = existing_step_count + 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    new_step = {
        "user_id": user_id,
        "sequence_id": sequence_id,
        "technique_id": ObjectId(technique_id),
        "step_no": step_no,
        "notes": request.form["notes"],
        "created_at": now,
        "updated_at": now,
    }

    result= sequence_steps.insert_one(new_step)
    ## not correct new steps link
    new_steps_link = ("http://localhost:5001/api/v1.0/sequence/"+ str(result.inserted_id))
    return make_response(jsonify({"url": new_steps_link}), 201)

