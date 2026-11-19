## ======================================================= ##
## TRAINING SESSION TECHNIQUES BLUEPRINT FILE
## ======================================================= ##
## This file is used to hold all of the API calls that are
## associated with the linking of training sessions and 
## techniques. 
##
## This file houses the following endpoints:
## -----------------------------------------
## Create Training Session Technique Link
## Get All Techniques From One Session

from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

training_session_techniques_bp = Blueprint("training_session_techniques_bp", __name__)

## Training Session Techniques DB collection
training_session_techniques = globals.db.training_session_techniques

## Techniques DB collection
techniques = globals.db.techniques

## Training Session DB collection
training_sessions = globals.db.training_sessions

## User endpoint to create a link between training sessions and techniques
@training_session_techniques_bp.route("/api/v1.0/training_session/<string:training_id>/technique/<string:technique_id>", methods=["post"])
## User login required to create link
@jwt_required
def create_training_session_technique_link(training_id, technique_id):

    user_id = g.user_id

    ## Search for session from session id
    session = training_sessions.find_one({

        ## Training ID from endpoint
        "_id": ObjectId(training_id),

        ## User ID from token
        "user_id": user_id
    })

    ## If session is not found
    if session is None:

        ## Return error that training session was not found
        return make_response(jsonify({"error": "Training Session Not Found"}, 404))

    ## Search for technique from technique ID
    technique = techniques.find_one({

        ## Technique ID from endpoint
        "_id": ObjectId(technique_id),

        ## User ID from token
        "user_id": user_id
    })

    ## If technique is not found
    if technique is None:

        ## Return error that technique was not found
        return make_response(jsonify({"error": "technique Not Found"}, 404))

    ## New link with user training session and technique ID's
    new_link = {
        "user_id": user_id,
        "training_session_id": ObjectId(training_id),
        "technique_id": ObjectId(technique_id),
    }

    ## Inserting new link into collection
    result = training_session_techniques.insert_one(new_link)

    ## Link to new link
    new_technique_link = ("http://localhost:5001/api/v1.0/techniques/"+ str(result.inserted_id))

    ## Response in a JSON format as a URL
    return make_response(jsonify({"url": new_technique_link}), 201)

## User endpoint to get all of the techniques from a single training session
@training_session_techniques_bp.route("/api/v1.0/training_sessions/<string:id>/techniques")
## User must be logged in
@jwt_required
def get_all_techniques_from_one_session(id):

    ## Searching for training session by ID
    session = training_sessions.find_one({

        ## Training Session ID
        "_id": ObjectId(id),

        ## User ID
        "user_id": g.user_id
    })

    ## If training session is not found
    if session is None:

        ## Response with error that training session was not found
        return make_response(jsonify({"error": "Training Session Not Found"}, 404))

    ## Searching for training session links by training session ID
    links = training_session_techniques.find({

        ## Training Session ID
       "training_session_id" : ObjectId(id),

       ## User ID
       "user_id": g.user_id
    })

    ## Data to return array
    data_to_return = []

    ## For all of the links to techniques found
    for link in links:

        ## Search for the technique linked to the training session
        technique = techniques.find_one({

            ## technique ID from link
            "_id": link["technique_id"],

            ## User ID
            "user_id": g.user_id
        })

        ## If technique was found
        if technique:

            ## Convert Technique ID to string
            technique["_id"] = str(technique["_id"])

            ## Add technique to array
            data_to_return.append(technique)

    ## Return all the found techniques
    return make_response(jsonify(data_to_return), 200)