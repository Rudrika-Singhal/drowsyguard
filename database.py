from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["drowsiness_db"]
sessions_collection = db["sessions"]

def save_session(data):
    """Ek detection session MongoDB mein save karo"""
    session = {
        "timestamp"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "test_type"    : data.get("test_type", "unknown"),
        "result"       : data.get("result", "UNKNOWN"),
        "fatigue_score": data.get("fatigue_score", 0),
        "signals"      : data.get("signals", {}),
        "duration_secs": data.get("duration_secs", 0),
    }
    result = sessions_collection.insert_one(session)
    session["_id"] = str(result.inserted_id)
    return session

def get_all_sessions():
    """Saari sessions fetch karo — latest pehle"""
    sessions = list(sessions_collection.find().sort("timestamp", -1).limit(20))
    for s in sessions:
        s["_id"] = str(s["_id"])
    return sessions

def get_stats():
    """Overall stats — total sessions, drowsy count, alert count"""
    total   = sessions_collection.count_documents({})
    drowsy  = sessions_collection.count_documents({"result": "DROWSY"})
    alert   = sessions_collection.count_documents({"result": "ALERT"})
    return {
        "total" : total,
        "drowsy": drowsy,
        "alert" : alert,
    }