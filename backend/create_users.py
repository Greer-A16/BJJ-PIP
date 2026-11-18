import random
from datetime import datetime, timezone
from pymongo import MongoClient
import bcrypt

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.BJJPIP
users = db.users

def make_object_id():
    return "".join(random.choice("0123456789abcdef") for _ in range(24))

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

# user_list = [
#     {
#         "email": "homer@springfield.net",
#         "password_hash": b"homer_s",
#         "username": "ashtongreer",
#         "first_name": "Ashton",
#         "last_name": "Greer",
#         "dob": "20/08/202",
#         "belt_rank": "Blue",
#         "stripe_no": 2,
#         "profile_img_path": "",
#         "admin": False,
#     },
# ]

# user_list = [
#     {
#         "email": "admin@bjjpip,com",
#         "password_hash": b"admin_login",
#         "username": "adminuser",
#         "first_name": "Admin",
#         "last_name": "User",
#         "dob": "20/08/2004",
#         "belt_rank": "Blue",
#         "stripe_no": 2,
#         "profile_img_path": "",
#         "admin": True,
#     },
# ]

user_list = [
    {
        "email": "user2@bjjpip,com",
        "password_hash": b"user2_login",
        "username": "user2",
        "first_name": "User",
        "last_name": "Two",
        "dob": "20/08/2004",
        "belt_rank": "Blue",
        "stripe_no": 2,
        "profile_img_path": "",
        "admin": False,
    },
]

for new_user in user_list:
    new_user["_id"] = make_object_id()
    new_user["password_hash"] = bcrypt.hashpw(
        new_user["password_hash"], bcrypt.gensalt())
    new_user["created_at"] = now
    new_user["updated_at"] = now
    users.insert_one(new_user)

print(f"Inserted {len(user_list)} user(s)")