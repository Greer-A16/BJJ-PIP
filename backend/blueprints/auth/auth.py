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
            
        