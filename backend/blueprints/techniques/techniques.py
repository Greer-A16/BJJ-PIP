## ======================================================= ##
## TECHNIQUES BLUEPRINT FILE
## ======================================================= ##
## This file is used to hold all of the API calls that are
## associated with the techniques. 
##
## This file houses the following endpoints:
## -----------------------------------------
## Admin Get All Techniques
## Get User Techniques
## Show One Technique
## Create Technique
## Edit Technique
## Delete Technique
## Descriptive Technique

from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

techniques_bp = Blueprint("techniques_bp", __name__)

## Techniques DB collection
techniques = globals.db.techniques

## Positions DB collection
positions = globals.db.positions

## Admin endpoint to access all user techniques
@techniques_bp.route("/api/v1.0/techniques", methods=["GET"])
## User must be logged in to us as an admin status is required
@jwt_required
## User must habe admin access to use
@admin_required
def admin_get_all_techniques():
   
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
    for technique in techniques.find().skip(page_start).limit(page_size):

        ## COnvert the technique ID to a string
        technique["_id"] = str(technique["_id"])

        ## Add the techniques to the array to be returned
        data_to_return.append(technique)

    ## Return all of the techniques
    return make_response(jsonify(data_to_return), 200)

## User endpoint to get all of the techniques created by the requesting user
@techniques_bp.route("/api/v1.0/techniques/me", methods=["GET"])
## User must be logged in to use as this endpoint uses a users id from the login token
@jwt_required
def get_user_techniques():

    ## Array of techniques to return
    data_to_return = []

    ## For each of the techniques that have the requesting users ID
    for technique in list(techniques.find({"user_id": g.user_id})):

        ## Converting the technique ID to a string
        technique["_id"] = str(technique["_id"])

        ## Add the technique to the array to be returned
        data_to_return.append(technique)

    ## If there are techniques found
    if data_to_return is not None:

        ## Return all the techniques found
        return make_response(jsonify(data_to_return), 200)

    ## If there are no techniques found
    else:

        ## Return an error message that there are no techniques found
        return make_response(jsonify({"error": "Invalid technique ID"}), 404)

## User endpoint to get a single technique based on its technique ID
@techniques_bp.route("/api/v1.0/techniques/<string:id>", methods=["GET"])
## User must be logged in to use as this endpoint uses a users id from the login token
@jwt_required
def show_one_technique(id):

    ## If the user is an admin
    if g.admin:

        ## Find the position by its ID while checking that the requesting user is the creating user
        technique = techniques.find_one({"_id": ObjectId(id)})

    ## If the user does not have admin access
    else:

        ## Find the technique by its ID while checking that the requesting user is the creating user 
        technique = techniques.find_one({'_id': ObjectId(id), "user_id": g.user_id})

    ## If the technique is found
    if technique is not None:

        ## Convert the technique ID to a string
        technique["_id"] = str(technique["_id"])

        ## Return the technique in a JSON format
        return make_response(jsonify(technique), 200)

    ## If the technique is not found
    else:

        ## Return an error message that the technique was not found
        return make_response(jsonify({"error": "Technique Not Found"}), 404)

## User endpoint to create a new technique
@techniques_bp.route("/api/v1.0/techniques", methods=["POST"])
## User must be logged in to assign ownership to a technique
@jwt_required
def create_technique():

    ## Fetching User ID from token
    user_id = g.user_id

    ## Technique form fields that must be filled in when creating a technique
    required_fields = ["name", "attire", "description", "technique_type"]

    ## If all fields in the form are present
    if all(field in request.form for field in required_fields):

        ## Getting the current time
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        ## The data of the position to be created
        new_technique = {

            ## The user ID fetched from the token
            "user_id": user_id,

            ## Technique name input from the form
            "name": request.form["name"],

            ## Starting position ID of the technique
            "starting_position": request.form["starting_position"],

            ## Ending position ID of the technique
            "ending_position": request.form["ending_position"],

            ## Description of the technique
            "description": request.form["description"],

            ## Technique attire ( Gi, No-Gi, Mixed )
            "attire": request.form["attire"],

            ## Technique type input from the form
            "technique_type": request.form["technique_type"],

            ## Current time when the technique was created
            "created_at": now,

            ## Current time when technique was last updated
            "updated_at": now,
        }

        ## New technique
        result= techniques.insert_one(new_technique)

        ## Link to new technique with new ID
        new_technique_link = ("http://localhost:5001/api/v1.0/techniques/"+ str(result.inserted_id))

        ## Return a link to the new technique in a JSON format as a URL
        return make_response(jsonify({"url": new_technique_link}), 201)

    ## If not all of the fields in the form are present
    else:

        ## Return an error that there is data missing from the form
        return make_response(jsonify({"error": "Missing form data"}), 400)

## User endpoint to edit an existing technique
@techniques_bp.route("/api/v1.0/techniques/<string:id>", methods=["PUT"])
## User must be logged in to edit an owned technique
@jwt_required
def edit_technique(id):
    
    ## Fetching User ID from token
    user_id = g.user_id

    ## Technique form fields that must be filled in when editing a technique
    required_fields = ["name", "attire", "description", "technique_type"]

    ## Checking the DB collection to make sure the technique already exists
    exists = techniques.find_one({"_id": ObjectId(id)})

    ## If the technique does not exist
    if exists is None:

        ## Return an error message that the technique does not exist
        return make_response(jsonify({"error": "Invalid technique ID"}), 404)

    ## If the technique exists but the user ID does not match the ID of the logged in user
    if exists.get("user_id") != user_id:

        ## Return an error message that the user cannot edit a technique that they do now own
        return make_response(jsonify({"error": "You can only edit your own techniques"}), 403)

    ## If all the fields in the form are present
    if all(field in request.form for field in required_fields):

        ## Getting the curen time
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        ## The data of the technique to be edited
        updated_technique = {

            ## The user ID fetched from the token
            "user_id": user_id,

            ## Technique name input from the form
            "name": request.form["name"],

            ## Starting position ID of the technique
            "starting_position": request.form["starting_position"],

            ## Ending position ID of the technique
            "ending_position": request.form["ending_position"],

            ## Description of the technique
            "description": request.form["description"],

            ## Technique attire ( Gi, No-Gi, Mixed )
            "attire": request.form["attire"],

            ## Technique type input from the form
            "technique_type": request.form["technique_type"],

            ## Current time when the technique was updated
            "updated_at": now,
        }

        ## PUT query containing the technique and the user ID
        query = {"_id": ObjectId(id), "user_id": g.user_id}

        ## Updated technique
        result= techniques.update_one(

            ## PUT query
            query,

            ## The updated data
            {"$set": updated_technique}
        )

        # If the technique did not updated
        if result.matched_count == 0:

            ## Return an error that says the position was not found
            return make_response(jsonify({"error": "technique not found"}), 404)

        ## Link to get the updated position
        updated_technique_link = ("http://localhost:5001/api/v1.0/techniques/" + id)

        ## Return a link to the updated position in a JSON format as a URL
        return make_response(jsonify({"message": "technique Updated", "url": updated_technique_link}))

## User endpoint to delete an existing technique
@techniques_bp.route("/api/v1.0/techniques/<string:id>", methods=["DELETE"])
## User must be logged in to delete an owned technique 
@jwt_required
def delete_technique(id):

    ## Fetching the User ID from toknen
    user_id = g.get("user_id")

    ## Checking the DB collection to make sure the technique already exists
    existing = techniques.find_one({"_id": ObjectId(id)})

    ## If the technique does not exist
    if existing is None:

        ## Return an error that the technique ID was not found
        return make_response(jsonify({"error": "Invalid Technique ID"}), 404)

    ## If the technique exists but user ID does not match the ID of the logged in user
    if existing.get("user_id") != user_id:

        ## Return an error message that the user cannot edit a technique that they do not own
        return make_response(jsonify({"error": "You can only delete your own Techniques"}), 403)

    ## Delete the technique from the DB collection
    result = techniques.delete_one({"_id": ObjectId(id), "user_id": user_id})

    ## If the technique was successfully deleted
    if result.deleted_count == 1:

        ## Return success
        return make_response("", 204)
    
    ## If the technique was not deleted
    else:

        ## Return an error that the technique ID is invalud
        return make_response(jsonify({"error": "Invalid Technique ID"}), 404)

## User endpoint to provide a single technique with the positions 
@techniques_bp.route("/api/v1.0/technique_description/<string:id>", methods=["GET"])
## User must be logged in to access techniques
@jwt_required
def descriptive_technique(id):

    ## If the user is an admin
    if g.admin:

        ## Find the technique by its ID without needing to be the creating user 
        technique = techniques.find_one({"_id": ObjectId(id)})

    ## If the user does not have admin access
    else:

        ## Find the technique by its ID while checking that the requesting user is the creating user
        technique = techniques.find_one({'_id': ObjectId(id), "user_id": g.user_id})

    ## If the technique is found 
    if technique is not None:

        ## Convert the technique ID to a string
        technique["_id"] = str(technique["_id"])

        ## assigning the starting position ID to a variable
        starting_position = technique["starting_position"]

        ## assigning the ending position ID to a variable
        ending_position = technique["ending_position"]

        ## Finding the starting position by its ID
        starting = positions.find_one({'_id': ObjectId(starting_position), "user_id": g.user_id})

        ## Finding the ending position by its ID
        ending = positions.find_one({'_id': ObjectId(ending_position), "user_id": g.user_id})

        ## If the starting position is found
        if starting:

            ## Convert the position ID to a string
            starting["_id"] = str(starting["_id"])

        ## If the ending position is found
        if ending:

            ## Convert the position ID to a string
            ending["_id"] = str(ending["_id"])

        ## Response with the technique name, starting position name,ending position name, and technique details
        response = {"Technique Name: ": technique["name"], "Starting Position: ": starting["name"], "Ending Position: ": ending["name"],  "Details: ": technique["description"]}

        ## Return the response
        return make_response(jsonify(response), 200)
    
    ## If thetechnique is not found
    else:
        
        ## Return an error message that the technique ID was not found.
        return make_response(jsonify({"error": "technique Not Found"}), 404)
