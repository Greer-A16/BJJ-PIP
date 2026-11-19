## ======================================================= ##
## POSITIONS BLUEPRINT FILE
## ======================================================= ##
## This file is used to hold all of the API calls that are
## associated with the positions. 
##
## This file houses the following endpoints:
## -----------------------------------------
## Admin Get All Positions
## Get User Positions
## Show One Position
## Create Position
## Edit Position
## Delete Position

from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

positions_bp = Blueprint("positions_bp", __name__)

## Positions DB collection
positions = globals.db.positions

## Admin endpoint to access all user positions. 
@positions_bp.route("/api/v1.0/positions", methods=["GET"])
## User must be logged in to use as admin status is required
@jwt_required
## User must have admin access to use
@admin_required
def admin_get_all_positions():

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

    ## Array of positions to be returned
    data_to_return = []

    ## For each of the positions within the page number and page size
    for position in positions.find().skip(page_start).limit(page_size):

        ## Convert the position ID to a string
        position["_id"] = str(position["_id"])

        ## Add the position to the array to be returned
        data_to_return.append(position)

    ## Return all of the positions
    return make_response(jsonify(data_to_return), 200)

## User endpoint to get all of the positions created by the requesting user
@positions_bp.route("/api/v1.0/positions/me", methods=["GET"])
## User must be logged in to use as this endpoint uses a users id from the login token
@jwt_required
def get_user_positions():

    ## Array of positions to return
    data_to_return = []

    ## For each of the positions that have the requesting users ID
    for position in list(positions.find({"user_id": g.user_id})):

        ## Convert the position ID to a string
        position["_id"] = str(position["_id"])

        ## Add the positions to the array to be returned
        data_to_return.append(position)

    ## If there are positions found
    if data_to_return is not None:

        ## Return all of the found positions
        return make_response(jsonify(data_to_return), 200)

    ## If there are no positions found
    else:

        ## Return an error message that there are no positions found
        return make_response(jsonify({"error": "No Positions Found"}), 404)


## User endpoint to get a single position based on its position ID
@positions_bp.route("/api/v1.0/positions/<string:id>", methods=["GET"])
## User must be logged in to use as this endpoint uses a users id from the login token
@jwt_required
def show_one_position(id):

    ## If the user is an admin
    if g.admin:

        ## Find the position by its ID without needing to be the creating user
        position = positions.find_one({"_id": ObjectId(id)})

    ## If the user does not have admin access
    else:

        ## Find the position by its ID while checking that the requesting user is the creating user
        position = positions.find_one({'_id': ObjectId(id), "user_id": g.user_id})

    ## If the position is found
    if position is not None:

        ## Convert the position ID to a string
        position["_id"] = str(position["_id"])

        ## Return the position in a json format
        return make_response(jsonify(position), 200)

    ## If the position is not found
    else:

        ## Return an error message that the position was not found
        return make_response(jsonify({"error": "Position Not Found"}), 404)

## User endpoint to create a new position
@positions_bp.route("/api/v1.0/positions", methods=["POST"])
## User must be logged in to assign ownership to a position
@jwt_required
def create_position():

    ## Fetching User ID from token
    user_id = g.user_id

    ## Position form fields that must be filled in when creating a technique
    required_fields = ["name", "attire", "description", "position_type"]

    ## If all the fields in the form are present
    if all(field in request.form for field in required_fields):

        ## Getting the current time
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        ## The data of the position to be created
        new_position = {

            ## The user ID fetched from the token
            "user_id": user_id,

            ## Position name input from the form
            "name": request.form["name"],

            ## Position description input from the form
            "description": request.form["description"],

            ## Position attire ( Gi, No-Gi, Mixed ) input from the form
            "attire": request.form["attire"],

            ## Position type input from the form
            "position_type": request.form["position_type"],

            ## Current time when position was created
            "created_at": now,

            ## Current time when position was last updated
            "updated_at": now,
        }

        ## New position
        result= positions.insert_one(new_position)

        ## Link to new position with new ID
        new_position_link = ("http://localhost:5001/api/v1.0/positions/"+ str(result.inserted_id))

        ## Return a link to the new position in a JSON format as a URL
        return make_response(jsonify({"url": new_position_link}), 201)

    ## If not all of the fields in the form are present
    else:

        ## Return an error that there is data missing from the form
        return make_response(jsonify({"error": "Missing form data"}), 400)


## User endpoint to edit an existing position
@positions_bp.route("/api/v1.0/positions/<string:id>", methods=["PUT"])
## User must be logged in to edit an owned position
@jwt_required
def edit_position(id):

    ## Fetching User ID from token
    user_id = g.user_id

    ## Position form fields that must be filled in when editing a position
    required_fields = ["name", "attire", "description", "position_type"]

    ## Checking the DB collection to make sure the position already exists
    exists = positions.find_one({"_id": ObjectId(id)})

    ## If the position does not exist
    if exists is None:

        ## Return an error message that the position does not exist
        return make_response(jsonify({"error": "Invalid Position ID"}), 404)

    ## If the position exists but the user ID does not match the ID of the logged in user
    if exists.get("user_id") != user_id:

        ## Return an error message that the user can not edit a position that they do not own
        return make_response(jsonify({"error": "You can only edit your own Positions"}), 403)

    ## If all the fields in the form are present
    if all(field in request.form for field in required_fields):

        ## Getting the current time
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        ## The data of the position to be edited
        updated_position = {

            ## The user ID fetched from the token
            "user_id": user_id,

            ## Position name input from the form
            "name": request.form["name"],

            ## Position description input from the form
            "description": request.form["description"],

            ## Position attire ( Gi, No-Gi, Mixed ) input from the form
            "attire": request.form["attire"],

            ## Position type input from the form
            "position_type": request.form["position_type"],

            ## Current time when position was updated
            "updated_at": now,
        }

        ## PUT query containing the position and user ID
        query = {"_id": ObjectId(id), "user_id": g.user_id}

        ## updated position
        result= positions.update_one(

            ## PUT query
            query,

            ## The updated data
            {"$set": updated_position}
        )

        ## If the position did not update
        if result.matched_count == 0:

            ## Return an error that the position was not found
            return make_response(jsonify({"error": "Position not found"}), 404)

        ## Link to get the updated position
        updated_position_link = ("http://localhost:5001/api/v1.0/positions/" + id)

        ## Return a link to the updated position in a JSON format as a URL
        return make_response(jsonify({"message": "Position Updated", "url": updated_position_link}))


## User endpoint to delete an existing position
@positions_bp.route("/api/v1.0/positions/<string:id>", methods=["DELETE"])
## User must be logged in to delete an owned position
@jwt_required
def delete_position(id):

    ## Fetching User ID from token
    user_id = g.user_id

    ## Checking the DB collection to make sure the position already exists
    existing = positions.find_one({"_id": ObjectId(id)})

    ## If the position does not exist
    if existing is None:

        ## Return an error that the position ID was not found
        return make_response(jsonify({"error": "Invalid Position ID"}), 404)

    ## If the position exists but the user ID does not match the ID of the logged in user
    if existing.get("user_id") != user_id:

        ## Return an error message that the user can not edit a position that they do not own
        return make_response(jsonify({"error": "You can only delete your own Positions"}), 403)

    ## Delete the position from the DB collection
    result = positions.delete_one({"_id": ObjectId(id), "user_id": user_id})

    ## If the position was successfully deleted
    if result.deleted_count == 1:

        ## Return success
        return make_response("", 204)

    ## If the position was not deleted
    else:

        ## Return an error that the position ID is invalid
        return make_response(jsonify({"error": "Invalid Position ID"}), 404)