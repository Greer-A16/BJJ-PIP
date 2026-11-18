from flask import Blueprint, request, make_response, jsonify, g
from decorators import jwt_required, admin_required
import bcrypt
import jwt
import globals
from bson import ObjectId
from datetime import datetime, timezone, timedelta

technique_sequences_bp = Blueprint("technique_sequences_bp", __name__)

technique_sequences = globals.db.technique_sequences
