## ======================================================= ##
## TECHNIQUE SEQUENCES BLUEPRINT FILE
## ======================================================= ##
## This file is used to hold all of the API calls that are
## associated with the technique sequences. 
##
## This file houses the following endpoints:
## -----------------------------------------
## Get User Sequences
## Show One Sequence and Steps
## Create Sequence

from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

technique_sequences_bp = Blueprint("technique_sequences_bp", __name__)

## Sequences DB collection
sequences = globals.db.technique_sequences
## Sequence Steps DB collection
sequence_steps = globals.db.sequence_steps

## User endpoint to get all of the sequences created by the requesting user 
## Does not include the sequence steps
@technique_sequences_bp.route("/api/v1.0/sequences/me", methods=["GET"])
## User must be logged in to use as as this endpoint uses a users ID from the login token
@jwt_required
def get_user_sequences():

    ## Array of sequences to return
    data_to_return = []

    ## For each of the sequences that have the requesting users ID
    for sequence in list(sequences.find({"user_id": g.user_id})):

        ## Convert the sequence ID to a string
        sequence["_id"] = str(sequence["_id"])

        ## Add the sequences to the array to be returned
        data_to_return.append(sequence)

    ## If there are sequences found
    if data_to_return is not None:

        ## Return all of the found sequences
        return make_response(jsonify(data_to_return), 200)

    ## If there are no sequences found
    else:

        ## Return an error message that there are no sequences found
        return make_response(jsonify({"error": "No Sequences Found"}), 404)


## User endpoint to get a sequence and all of its steps
@technique_sequences_bp.route("/api/v1.0/sequences/<string:id>", methods=["GET"])
@jwt_required
def get_one_sequence_and_steps(id):

    ## Assign the sequence ID to a variable
    sequence_id = ObjectId(id)

    ## If the user is an admin
    if g.admin:

        ## Find the sequence by its ID without needing to be the creating user
        sequence = sequences.find_one({"_id": sequence_id})

    ## If the user does not have admin access
    else:

        ## Find the sequence by its ID while checking that the requesting user is the creating user
        sequence = sequences.find_one({'_id': sequence_id, "user_id": g.user_id})

    ## If the sequence does not exist
    if sequence is None:

        ## Return an error message that the sequence ID is invalid
        return make_response(jsonify({"error": "Invalid Sequence ID"}), 404)
    
    ## Array of the sequence steps
    sequence_steps_to_return = []

    ## Checking the sequence steps DB collection for sequence steps
    steps = sequence_steps.find({

        ## The sequence ID to search the sequence steps DB for
        "sequence_id": sequence_id,

        ## The user ID to search the sequence steps DB for
        "user_id": sequence["user_id"]

        ## Sorting the sequence steps from lowest to highest step number
    }).sort("step_no", 1)

    ## For each of the sequence steps found
    for step in steps:

        ## Convert the sequence step ID to a string
        step["_id"] = str(step["_id"])

        ## Convert the sequence ID to a string
        step["sequence_id"] = str(step["sequence_id"])

        ## Convert the technique ID to a string
        step["technique_id"] = str(step["technique_id"])

        ## Add the step to the array
        sequence_steps_to_return.append(step)

    ## Convert the sequence ID to a string
    sequence["_id"] = str(sequence["_id"])

    ## Creating the response
    response = {

        ## The sequence fetched
        "sequence": sequence,

        ## All of the found sequence steps
        "steps": sequence_steps_to_return
    }

    ## Return the sequence and all of the steps in a JSON format
    return make_response(jsonify(response), 200)

## User endpoint to create a new sequence
@technique_sequences_bp.route("/api/v1.0/sequences", methods=["POST"])
## User must be logged in to get the user ID from the login token
@jwt_required
def create_sequence():

    ## Fetching User ID from token
    user_id = g.user_id

    ## Sequence form field that must be filled in when creating a sequence
    required_fields = ["name"]

    ## If the field in the form request is present
    if all(field in request.form for field in required_fields):

        ## Getting the current time
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        ## The data of the sequence to be created
        new_sequence = {

            ## The user ID fetched from the token
            "user_id": user_id,

            ## Sequence name input from the frorm
            "name": request.form["name"],

            ## Current time when the sequence was created
            "created_at": now,

            ## Current time when sequence was updated
            "updated_at": now,
        }

        ## New Sequence
        result= sequences.insert_one(new_sequence)

        ## Link to the new sequence with the new ID
        new_sequence_link = ("http://localhost:5001/api/v1.0/sequences/"+ str(result.inserted_id))

        ## Return a link to the new sequence in a JSON format as a URL
        return make_response(jsonify({"url": new_sequence_link}), 201)

    ## If not all of the fields in the form are preset
    else:

        ## Return an error that there is data missing from the form
        return make_response(jsonify({"error": "Missing form data"}), 400)
