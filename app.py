from gevent import monkey
monkey.patch_all()
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
import os
import cv2
import numpy as np
import base64
import time

from model import analyze_frame, analyze_image_file, analyze_video_file, frame_to_base64
from database import save_session, get_all_sessions, get_stats

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"]      = os.getenv("SECRET_KEY", "drowsiness123")
app.config["UPLOAD_FOLDER"]   = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

os.makedirs("uploads", exist_ok=True)

# Calibration store (per socket session)
calibration_store = {}

# ================================================================
# ROUTES
# ================================================================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats")
def stats():
    """Dashboard stats"""
    try:
        data = get_stats()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history")
def history():
    """Past sessions"""
    try:
        sessions = get_all_sessions()
        return jsonify(sessions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================================================
# IMAGE UPLOAD ROUTE
# ================================================================

@app.route("/api/analyze/image", methods=["POST"])
def analyze_image():
    if "file" not in request.files:
        return jsonify({"error": "File nahi mili"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "File select nahi ki"}), 400

    # Save file
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # Analyze
    result = analyze_image_file(filepath)

    if "error" in result:
        return jsonify(result), 400

    # Annotated frame base64 mein
    annotated = frame_to_base64(result["frame"])

    # MongoDB mein save
    try:
        save_session({
            "test_type"    : "image",
            "result"       : result["result"],
            "fatigue_score": result["fatigue_score"],
            "signals"      : result["signals"],
            "duration_secs": 0,
        })
    except:
        pass

    # Cleanup
    os.remove(filepath)

    return jsonify({
        "result"       : result["result"],
        "fatigue_score": result["fatigue_score"],
        "ear"          : result["ear"],
        "signals"      : result["signals"],
        "annotated"    : annotated,
    })

# ================================================================
# VIDEO UPLOAD ROUTE
# ================================================================

@app.route("/api/analyze/video", methods=["POST"])
def analyze_video():
    if "file" not in request.files:
        return jsonify({"error": "File nahi mili"}), 400

    file = request.files["file"]
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    result = analyze_video_file(filepath)

    if "error" in result:
        return jsonify(result), 400

    annotated = frame_to_base64(result.get("frame"))

    try:
        save_session({
            "test_type"    : "video",
            "result"       : result["result"],
            "fatigue_score": result["fatigue_score"],
            "signals"      : result["signals"],
            "duration_secs": result["total_frames"],
        })
    except:
        pass

    os.remove(filepath)

    return jsonify({
        "result"        : result["result"],
        "fatigue_score" : result["fatigue_score"],
        "drowsy_percent": result["drowsy_percent"],
        "total_frames"  : result["total_frames"],
        "drowsy_frames" : result["drowsy_frames"],
        "annotated"     : annotated,
    })

# ================================================================
# LIVE CAMERA — WEBSOCKET
# ================================================================

@socketio.on("connect")
def on_connect():
    print(f"Client connected: {request.sid}")
    calibration_store[request.sid] = {
        "ear_sum"   : 0,
        "frames"    : 0,
        "calibrated": None,
        "total"     : 40,
    }

@socketio.on("disconnect")
def on_disconnect():
    print(f"Client disconnected: {request.sid}")
    calibration_store.pop(request.sid, None)

@socketio.on("frame")
def handle_frame(data):
    """
    Browser se base64 frame aata hai →
    Analyze karo → Result wapas bhejo
    """
    try:
        sid = request.sid

        # Base64 → OpenCV frame
        img_data = base64.b64decode(data["frame"].split(",")[1])
        np_arr   = np.frombuffer(img_data, np.uint8)
        frame    = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return

        frame = cv2.resize(frame, (640, 480))

        cal = calibration_store.get(sid, {})

        # Calibration phase
        if cal.get("calibrated") is None:
            from model import eye_aspect_ratio, LEFT_EYE, RIGHT_EYE, face_mesh
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = face_mesh.process(rgb)

            if res.multi_face_landmarks:
                lm = res.multi_face_landmarks[0].landmark
                left_eye  = [(int(lm[i].x*w), int(lm[i].y*h)) for i in LEFT_EYE]
                right_eye = [(int(lm[i].x*w), int(lm[i].y*h)) for i in RIGHT_EYE]
                ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2
                cal["ear_sum"] += ear
                cal["frames"]  += 1

            progress = int((cal["frames"] / cal["total"]) * 100)

            if cal["frames"] >= cal["total"]:
                cal["calibrated"] = cal["ear_sum"] / cal["frames"]
                emit("calibration_done", {"ear": round(cal["calibrated"], 3)})
            else:
                emit("calibrating", {"progress": progress})
            return

        # Detection phase — annotated frame skip karo for speed
        result = analyze_frame(frame, cal["calibrated"])

        # Sirf result data bhejo — no heavy base64 image
        emit("result", {
            "result"       : result["result"],
            "fatigue_score": result["fatigue_score"],
            "ear"          : result["ear"],
            "signals"      : result["signals"],
            "annotated"    : None,
        })

        # Drowsy ho toh MongoDB mein save karo
        if result["result"] == "DROWSY":
            try:
                save_session({
                    "test_type"    : "live",
                    "result"       : "DROWSY",
                    "fatigue_score": result["fatigue_score"],
                    "signals"      : result["signals"],
                    "duration_secs": 0,
                })
            except:
                pass

    except Exception as e:
        print(f"Frame error: {e}")

# ================================================================
# RUN
# ================================================================

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)