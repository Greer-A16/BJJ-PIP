## ======================================================= ##
## AUTH BLUEPRINT FILE
## ======================================================= ##
## This file is used to hold all of the API calls that are
## associated with the user authorization. 
##
## This file houses the following endpoints:
## -----------------------------------------
## Login
## Logout
## Create New User

import uuid
from flask import Blueprint, request, make_response, jsonify
from decorators import jwt_required
import bcrypt
import jwt
import globals
from datetime import datetime, timezone, timedelta

## Blueprint
auth_bp = Blueprint("auth_bp", __name__)

## Db Collections
users = globals.db.users
blacklist = globals.db.blacklist

## Login User
@auth_bp.route('/api/v1.0/login', methods=['GET'])
def login():

    ## Flask authorization method
    auth = request.authorization
    if auth:

         ## Search users collection for username
        user = users.find_one( { 'username': auth.username})

        ## If username exists in the users collection
        if user is not None:
            
            ## If hashed password is the entered password
            if bcrypt.checkpw(bytes(auth.password, 'UTF-8'), user["password_hash"]):

                ## Encode the token with the following user information
                token = jwt.encode( {
                    ## Username
                    'user': auth.username,

                    ## User ID
                    'user_id': str(user["_id"]),

                    ## Admin permissions
                    'admin': user['admin'],

                    ## Expiry date ( 30 minutes )
                    'exp': datetime.now(timezone.utc) + timedelta(minutes=30)},

                    ## Secret key from globals file
                    globals.secret_key,

                    ## Algorithm used
                    algorithm="HS256")

                ## Return user token
                return make_response(jsonify({'token': token}), 200)

            ## If the hashed password is NOT the entered password
            else:
                return make_response(jsonify({'message': 'Bad Password'}), 401)
        
        ## If username does NOT exist in the users collection
        else:
            return make_response(jsonify({'message': "Bad Username"}), 401)
        
    return make_response(jsonify({'message': "Authentication Required"}, 401))

@auth_bp.route('/api/v1.0/logout', methods=["GET"])
@jwt_required
def logout():

    ## Fetching token from the request headers
    token = request.headers['x-access-token']

    ## Inserting fetched token into blacklist
    blacklist.insert_one({"token":token})

    return make_response(jsonify({"message": "Logout Successful"}), 200)

## Endpoint for an unregistered user to create an account
@auth_bp.route('/api/v1.0/create_account', methods=["POST"])
def create_account():

    ## Data required to create a new user account
    required_fields = ["email", "username", "password_hash", "first_name", "last_name", "dob", "belt_rank", "stripe_no"]

    ## If all fields in the form are present
    if all(field in request.form for field in required_fields):

        ## Getting the current time
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        ## Hashing the password from the form
        password_hash = bcrypt.hashpw(request.form["password_hash"].encode("utf-8"), bcrypt.gensalt())

        ## Check if email is already registered to an account
        existing_user = users.find_one({"email": request.form["email"]})

        ## If the email is already present
        if existing_user is not None:

            ## Return an error message that the email is already registered
            return make_response(jsonify({"error": "Email already registered to an account. Log in instead"}))

        ## The data of the new user
        new_user = {

            ## Generates a unique ID
            "_id": str(uuid.uuid4()),

            ## The user email
            "email": request.form["email"],

            ## The username
            "username": request.form["username"],

            ## The user password
            "password_hash": password_hash,

            ## The user admin status
            ## False by default until changed by an existing admin
            "admin": False,

            ## The user first name
            "first_name": request.form["first_name"],

            ## The user last name
            "last_name": request.form["last_name"],

            ## The user date of birth
            "dob": request.form["dob"],

            ## The user belt rank
            "belt_rank": request.form["belt_rank"],

            ## The user number of stripes
            "stripe_no": request.form["stripe_no"],

            ## The user local profile image path
            "profile_img_path": request.form.get("profile_img_path", "/assets/images/default_pfp.png"),

            ## Current time when the user account was created
            "created_at": now,
            
            ## Current time when the user account was updated
            "updated_at": now,
        }

        ## New user
        result= users.insert_one(new_user)

        ## Return the user id to the new created user
        return make_response(jsonify({"id": str(result.inserted_id)}), 201)
