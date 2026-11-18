from flask import Blueprint, request, make_response, jsonify
from decorators import jwt_required
import bcrypt
import jwt
import globals
from datetime import datetime, timezone, timedelta

auth_bp = Blueprint("auth_bp", __name__)

users = globals.db.users
blacklist = globals.db.blacklist

@auth_bp.route('/api/v1.0/login', methods=['GET'])
def login():
    auth = request.authorization
    if auth:
        user = users.find_one( { 'username': auth.username})
        if user is not None:
            if bcrypt.checkpw(bytes(auth.password, 'UTF-8'), user["password_hash"]):
                token = jwt.encode( {
                    'user': auth.username,
                    'user_id': str(user["_id"]),
                    'admin': user['admin'],
                    'exp': datetime.now(timezone.utc) + timedelta(minutes=30)},
                    globals.secret_key,
                    algorithm="HS256")
                return make_response(jsonify({'token': token}), 200)
            else:
                return make_response(jsonify({'message': 'Bad Password'}), 401)
        else:
            return make_response(jsonify({'message': "Bad Username"}), 401)
    return make_response(jsonify({'message': "Authentication Required"}, 401))

@auth_bp.route('/api/v1.0/logout', methods=["GET"])
@jwt_required
def logout():
    token = request.headers['x-access-token']
    blacklist.insert_one({"token":token})
    return make_response(jsonify({"message": "Logout Successful"}), 200)
            
        