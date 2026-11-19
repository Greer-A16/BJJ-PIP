## ======================================================= ##
## TECHNIQUE SEQUENCE STEPS BLUEPRINT FILE
## ======================================================= ##
## This file is used to hold all of the API calls that are
## associated with the technique sequence steps. 
##
## This file houses the following endpoints:
## -----------------------------------------
## Show One Sequence Step
## Create Sequence Steps

from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

sequence_steps_bp = Blueprint("sequence_steps_bp", __name__)

## Sequences DB collection
sequences = globals.db.technique_sequences
## Sequence Steps DB collection
sequence_steps = globals.db.sequence_steps

## User endpoint to get a single step based on its step ID
@sequence_steps_bp.route("/api/v1.0/sequence_steps/<string:id>", methods=["GET"])
## User must be logged in to use as this endpoint uses a users id from the login token
@jwt_required
def show_one_sequence_step(id):

    ## If the user is an admin
    if g.admin:

        ## Find the step by its ID without needing to be the creating user
        step = sequence_steps.find_one({"_id": ObjectId(id)})

    ## If the user does not have admin access
    else:

        ## Find the step by its ID while checking that the requesting user is the creating user
        step = sequence_steps.find_one({'_id': ObjectId(id), "user_id": g.user_id})

    ## If the step is found
    if step is not None:

        ## Convert the step ID to a string
        step["_id"] = str(step["_id"])

        ## Convert the sequence ID to a string
        step["sequence_id"] = str(step["sequence_id"])

        ## Convert the technique ID to a string
        step["technique_id"] = str(step["technique_id"])

        ## Return the step in a json format
        return make_response(jsonify(step), 200)

    ## If the step is not found
    else:

        ## Return an error message that the step was not found
        return make_response(jsonify({"error": "Step Not Found"}), 404)

## User endpoint to create the individual steps for a sequence
@sequence_steps_bp.route("/api/v1.0/sequences/<string:id>/steps", methods=["POST"])
## User must be logged in to assign ownership to a sequence step
@jwt_required
def create_sequence_steps(id):

    ## Fetching User ID from token
    user_id = g.user_id

    ## Assigning sequence ID from endpoint to a variable
    sequence_id =ObjectId(id)

    ## Finding the sequence from the DB collection 
    sequence = sequences.find_one({

        ## ID of the sequence
        "_id": sequence_id,

        ## User ID from the token
        "user_id": user_id
    })

    ## If the sequence does not exist
    if sequence is None:

        ## Return an error message that the sequence does not exist
        return make_response(jsonify({"error": "Sequence not Found"}, 404))

    ## If the technique ID is not provided in the request form
    if "technique_id" not in request.form:

        ## Return an error message that the form is missing the technique ID
        return make_response(jsonify({"error": "Missing Technique ID"}, 404))

    ## Assigning the technique ID from the form to a variable
    technique_id = request.form["technique_id"]

    ## Searching the DB collection for how many steps are already assigned to the sequence
    existing_step_count = sequence_steps.count_documents({

        ## Searching the sequence ID
        "sequence_id": sequence_id,

        ## Searching the user ID
        "user_id": user_id
    })

    ## Assigning the step number as the next step of the sequence
    step_no = existing_step_count + 1

    ## Getting the current time
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    ## The data of the new ste[]
    new_step = {

        ## The user ID fetched from the token
        "user_id": user_id,

        ## The sequence ID fetched from the endpoint request
        "sequence_id": sequence_id,

        ## The technique ID input from the form
        "technique_id": ObjectId(technique_id),

        ## The number of the sequence step
        "step_no": step_no,

        ## Any notes input from the form
        "notes": request.form["notes"],

        ## Current time when the position was created
        "created_at": now,

        ## Current time when the position was updated
        "updated_at": now,
    }

    ## The new sequence step
    result= sequence_steps.insert_one(new_step)

    ## not correct new steps link
    new_steps_link = ("http://localhost:5001/api/v1.0/sequence_step/"+ str(result.inserted_id))
    return make_response(jsonify({"url": new_steps_link}), 201)
