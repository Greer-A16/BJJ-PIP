import random
from datetime import datetime, timezone
from pymongo import MongoClient

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.BJJPIP
training_sessions = db.training_sessions

def make_object_id():
    return "".join(random.choice("0123456789abcdef") for _ in range(24))

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

training_session_list = [
    {
        "user_id": "d86a1489c42bed6b5a8f03dd",
        "class_session_id": "",
        "gym_id": "",
        "session_date": "2026-11-17T18:30:00.000Z",
        "session_type": "Evening No-Gi",
        "duration_minutes": 90,
        "attire": "No-Gi",
        "notes": "Tough Session",
    },
]

for new_training_session in training_session_list:
    new_training_session["_id"] = make_object_id()
    new_training_session["created_at"] = now
    new_training_session["updated_at"] = now
    training_sessions.insert_one(new_training_session)

print(f"Inserted {len(training_session_list)} training session(s)")