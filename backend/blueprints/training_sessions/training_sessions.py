## ======================================================= ##
## TRAINING SESSION BLUEPRINT FILE
## ======================================================= ##
## This file is used to hold all of the API calls that are
## associated with the training Sessions. 
##
## This file houses the following endpoints:
## -----------------------------------------
## Admin Get All Training Sessions
## Get User Training Sessions
## Show One Training Session
## Create Training Session
## Edit Training Session
## Delete Training Session
## Descriptive Training Session

from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

training_sessions_bp = Blueprint("training_sessions_bp", __name__)

## Training Sessions DB collection
training_sessions = globals.db.training_sessions

## Admin endpoint to access all user training sessions
@training_sessions_bp.route("/api/v1.0/training_sessions", methods=["GET"])
## User must be logged in to us as an admin status is required
@jwt_required
## User must have admin access to use
@admin_required
def admin_get_all_training_sessions():
    ## Setting pagination initial page number to 1 and items per page to 10
    page_num, page_size = 1, 10

    ## Check for presence of page number in query string and retrieve value
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))

    ## Check for presence of page size in query string and retrieve value
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))

    ## Calculate elements to be shown
    page_start = page_size * (page_num - 1)

    ## Array of techniques to be returned
    data_to_return = []

    ## For each of the techniques within the page number and page size
    for training_session in training_sessions.find().skip(page_start).limit(page_size):

        ## Convert the Training Session ID to a string
        training_session["_id"] = str(training_session["_id"])

        ## Add the Training Session to the array to be returned
        data_to_return.append(training_session)

    ## Return all of the training sessions
    return make_response(jsonify(data_to_return), 200)

## User endpoint to get all of the training sessions created by the requesting user
@training_sessions_bp.route("/api/v1.0/training_sessions/me", methods=["GET"])
## User must be logged in to use as this endpoint uses a users id from the login token
@jwt_required
def get_user_training_sessions():

    ## Array of training sessions to return
    data_to_return = []

    ## For each of the training sessions that have the requesting users ID
    for training_session in list(training_sessions.find({"user_id": g.user_id})):

        ## Converting the training session ID to a string
        training_session["_id"] = str(training_session["_id"])

        ## Add the training session to the array to be returned
        data_to_return.append(training_session)

    ## If there are training sessions found
    if data_to_return is not None:
        ## Return all the training sessions found
        return make_response(jsonify(data_to_return), 200)

    ## If there are no training sessions found
    else:
        ## Return an error message that there are no training sessions found
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)

## User endpoint to get a single training session based on its training session ID
@training_sessions_bp.route("/api/v1.0/training_sessions/<string:id>", methods=["GET"])
## User must be logged in to use as this endpoint uses a users id from the login token
@jwt_required
def show_one_training_session(id):

    ## If the user is an admin
    if g.admin:

        ## Find the training session by its ID while checking that the requesting user is the creating user
        training_session = training_sessions.find_one({"_id": ObjectId(id)})

    ## If the user does not have admin access
    else:

        ## Find the training session by its ID while checking that the requesting user is the creating user 
        training_session = training_sessions.find_one({'_id': ObjectId(id), "user_id": g.user_id})

    ## If the training session is found
    if training_session is not None:

        ## Converting the training session ID to a string
        training_session["_id"] = str(training_session["_id"])

        ## Return the training session in a JSON format
        return make_response(jsonify(training_session), 200)

    ## If the training session is not found
    else:

        ## Return an error message that the training session was not found
        return make_response(jsonify({"error": "Training Session Not Found"}), 404)

## User endpoint to create a new training session
@training_sessions_bp.route("/api/v1.0/training_sessions", methods=["POST"])
## User must be logged in to assign ownership to a training session
@jwt_required
def create_training_session():

    ## Fetching User ID from token
    user_id = g.user_id

    ## training session form fields that must be filled in when creating a training session
    required_fields = ["duration_minutes", "attire", "session_date", "session_type"]

    ## If all fields in the form are present
    if all(field in request.form for field in required_fields):

        try:
            ## Ensure that the minutes is an int
            duration_minutes = int(request.form["duration_minutes"])
        except ValueError:
            return make_response(jsonify({"error": "duration_minutes must be a number"}), 400)

        ## Getting the current time
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        ## The data of the position to be created
        new_training_session = {

            ## The user ID fetched from the token
            "user_id": user_id,

            ## The ID of the class ession
            "class_session_id": request.form.get("class_session_id"),

            ## The ID of the gym
            "gym_id": request.form.get("gym_id"),

            ## The date of the session
            "session_date": request.form["session_date"],

            ## The type of session
            "session_type": request.form["session_type"],

            ## The time of the training session
            "duration_minutes": duration_minutes,

            ## The attire of the training session
            "attire": request.form["attire"],

            ## The notes of the training session
            "notes": request.form.get("notes"),

            ## When the training sesion was created
            "created_at": now,

            ## When the training session was last created
            "updated_at": now,
        }

        ## new training session
        result= training_sessions.insert_one(new_training_session)

        ## Link to new training session with new ID
        new_training_session_link = ("http://localhost:5001/api/v1.0/training_sessions/"+ str(result.inserted_id))

        ## Return a link to the new training session in a JSON format as a URL
        return make_response(jsonify({"url": new_training_session_link}), 201)

    ## If not all of the fields in the form are present
    else:

        ## Return an error that there is data missing from the form
        return make_response(jsonify({"error": "Missing form data"}), 400)

## User endpoint to edit an existing training session
@training_sessions_bp.route("/api/v1.0/training_sessions/<string:id>", methods=["PUT"])
## User must be logged in to edit an owned training session
@jwt_required
def edit_training_session(id):

    ## Fetching User ID from token
    user_id = g.user_id

    ## training session form fields that must be filled in when editing a training session
    required_fields = ["duration_minutes", "attire", "session_date", "session_type"]

    ## Checking the DB collection to make sure the training session already exists
    exists = training_sessions.find_one({"_id": ObjectId(id)})

    ## If the training session does not exist
    if exists is None:
        ## Return an error message that the training session does not exist
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)

    ## If the training session exists but the user ID does not match the ID of the logged in user
    if exists.get("user_id") != user_id:

        ## Return an error message that the user cannot edit a training session that they do now own
        return make_response(jsonify({"error": "You can only edit your own training sessions"}), 403)

    ## If all the fields in the form are present
    if all(field in request.form for field in required_fields):
        try:
            ## And the duration is in minutes
            duration_minutes = int(request.form["duration_minutes"])
        except ValueError:
            return make_response(jsonify({"error": "duration_minutes must be a number"}), 400)

        ## Getting the current time
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        ## The data of the training session to be updated with
        updated_training_session = {
            
            ## The user ID fetched from the token
            "user_id": user_id,

            ## The ID of the class ession
            "class_session_id": request.form.get("class_session_id"),

            ## The ID of the gym
            "gym_id": request.form.get("gym_id"),

            ## The date of the session
            "session_date": request.form["session_date"],

            ## The type of session
            "session_type": request.form["session_type"],

            ## The time of the training session
            "duration_minutes": duration_minutes,

            ## The attire of the training session
            "attire": request.form["attire"],

            ## The notes of the training session
            "notes": request.form.get("notes"),

            ## When the training session was last updated
            "updated_at": now,
        }

        ## PUT query containing the training session and the user ID
        query = {"_id": ObjectId(id), "user_id": g.user_id}

        ## Updated training session
        result= training_sessions.update_one(

            ## The PUT query
            query,

            ## The updated data
            {"$set": updated_training_session}
        )

        ## If the training session did not update
        if result.matched_count == 0:

            ## Return an error that says the training session was not found
            return make_response(jsonify({"error": "Training Session not found"}), 404)

        ## Link to get the updated position
        updated_training_session_link = ("http://localhost:5001/api/v1.0/training_sessions/" + id)

        ## Return a link to the updated position in a JSON format as a URL
        return make_response(jsonify({"message": "Training Session Updated", "url": updated_training_session_link}))

## User endpoint to delete an existing training session
@training_sessions_bp.route("/api/v1.0/training_sessions/<string:id>", methods=["DELETE"])
## User must be logged in to delete an owned technique
@jwt_required
def delete_training_session(id):

    ## Fetching the user ID from the token
    user_id = g.get("user_id")

    ## Checking the DB collection to make sure it already exists
    existing = training_sessions.find_one({"_id": ObjectId(id)})

    ## If the training session doesnt exist
    if existing is None:

        ## Return an error that the training session DI was not found
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)

    ## If the training session exists but user ID does not match the ID of the logged in user
    if existing.get("user_id") != user_id:

        ## Return an error message
        return make_response(jsonify({"error": "You can only delete your own training sessions"}), 403)

    ## Deleted training session
    result = training_sessions.delete_one({"_id": ObjectId(id), "user_id": user_id})

    ## If the training session was deleted
    if result.deleted_count == 1:

        ## Return success
        return make_response("", 204)

    ## If the training session was not deleted
    else:

        ## Return an error
        return make_response(jsonify({"error": "Invalid Training Session ID"}), 404)