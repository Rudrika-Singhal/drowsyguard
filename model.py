import cv2
import math
import numpy as np
import base64
import time

# ---------- MEDIAPIPE SETUP ----------
from mediapipe.python.solutions.face_mesh import FaceMesh
from mediapipe.python.solutions.face_mesh_connections import FACEMESH_TESSELATION
from mediapipe.python.solutions.drawing_utils import draw_landmarks, DrawingSpec

face_mesh = FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ---------- LANDMARK INDEX ----------
LEFT_EYE  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
UPPER_LIP = 13
LOWER_LIP = 14
NOSE      = 1
CHIN      = 152

# ---------- FUNCTIONS ----------
def dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def eye_aspect_ratio(eye):
    A = dist(eye[1], eye[5])
    B = dist(eye[2], eye[4])
    C = dist(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def get_head_pose(landmarks, w, h):
    nose      = landmarks[1]
    chin      = landmarks[152]
    left_eye  = landmarks[33]
    right_eye = landmarks[263]
    forehead  = landmarks[10]

    # PITCH
    nose_y     = nose.y * h
    forehead_y = forehead.y * h
    chin_y     = chin.y * h
    face_h     = abs(chin_y - forehead_y)
    if face_h > 0:
        nose_rel = (nose_y - forehead_y) / face_h
        pitch    = (nose_rel - 0.55) * 100
    else:
        pitch = 0

    # YAW
    nose_x    = nose.x * w
    le_x      = left_eye.x * w
    re_x      = right_eye.x * w
    eye_mid_x = (le_x + re_x) / 2
    eye_dist  = abs(re_x - le_x)
    if eye_dist > 0:
        yaw = ((nose_x - eye_mid_x) / eye_dist) * 100
    else:
        yaw = 0

    # ROLL
    le_y = left_eye.y * h
    re_y = right_eye.y * h
    roll = math.degrees(math.atan2(re_y - le_y, re_x - le_x))

    return pitch, yaw, roll

def analyze_frame(frame, calibrated_ear=None):
    h, w, _ = frame.shape
    rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results  = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return {
            "face_detected": False,
            "ear"          : 0,
            "fatigue_score": 0,
            "result"       : "NO FACE",
            "signals"      : {},
            "frame"        : frame
        }

    landmarks = results.multi_face_landmarks[0].landmark

    left_eye  = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in LEFT_EYE]
    right_eye = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in RIGHT_EYE]

    ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2

    if calibrated_ear is None:
        # Smart auto-calibration:
        # Agar EAR > 0.25 → normal eyes → standard threshold use karo
        # Agar EAR < 0.25 → naturally small eyes → unki apni EAR use karo
        # Yeh Chinese/Assamese/small eye people ke liye fair hai
        if ear >= 0.25:
            calibrated_ear = 0.28   # normal eyes
        else:
            calibrated_ear = ear    # naturally small eyes — unki own EAR baseline

    # Threshold = 70% of their OWN open-eye EAR
    # Isse koi bhi unfairly alert nahi hoga
    EAR_THRESHOLD = calibrated_ear * 0.70

    nose_pt = (int(landmarks[NOSE].x * w), int(landmarks[NOSE].y * h))
    chin_pt = (int(landmarks[CHIN].x * w), int(landmarks[CHIN].y * h))
    upper   = (int(landmarks[UPPER_LIP].x * w), int(landmarks[UPPER_LIP].y * h))
    lower   = (int(landmarks[LOWER_LIP].x * w), int(landmarks[LOWER_LIP].y * h))

    face_height = dist(nose_pt, chin_pt)
    mouth_dist  = dist(upper, lower)
    mouth_ratio = mouth_dist / face_height if face_height > 0 else 0

    pitch, yaw, roll = get_head_pose(landmarks, w, h)

    eye_closed   = ear < EAR_THRESHOLD
    yawning      = mouth_ratio > 0.30
    head_nodding = pitch > 10
    head_tilted  = abs(roll) > 12
    looking_away = abs(yaw) > 25

    fatigue_score = 0
    if eye_closed:
        fatigue_score += 2
    if yawning:
        fatigue_score += 1
    if head_nodding:
        fatigue_score += 1
    if head_tilted:
        fatigue_score += 1
    if mouth_ratio > 0.25 and ear < calibrated_ear * 0.8:
        fatigue_score += 1

    result = "DROWSY" if fatigue_score >= 3 else "ALERT"

    # Draw on frame
    try:
        draw_landmarks(
            frame,
            results.multi_face_landmarks[0],
            FACEMESH_TESSELATION,
            DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1),
            DrawingSpec(color=(0, 0, 255), thickness=1)
        )
    except:
        pass

    color = (0, 0, 255) if result == "DROWSY" else (0, 255, 0)
    cv2.putText(frame, f"EAR: {ear:.2f}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Score: {fatigue_score}",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, result,
                (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

    if eye_closed:
        cv2.putText(frame, "EYES CLOSED", (10, 135),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
    if yawning:
        cv2.putText(frame, "YAWNING", (10, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 2)
    if head_nodding:
        cv2.putText(frame, "HEAD DOWN", (10, 185),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 60, 255), 2)

    return {
        "face_detected": True,
        "ear"          : round(ear, 3),
        "fatigue_score": fatigue_score,
        "result"       : result,
        "signals"      : {
            "eye_closed"  : eye_closed,
            "yawning"     : yawning,
            "head_nodding": head_nodding,
            "head_tilted" : head_tilted,
            "looking_away": looking_away,
        },
        "frame": frame
    }

def analyze_image_file(image_path, calibrated_ear=None):
    frame = cv2.imread(image_path)
    if frame is None:
        return {"error": "Image load nahi hui"}
    frame = cv2.resize(frame, (640, 480))
    return analyze_frame(frame, calibrated_ear)

def analyze_video_file(video_path, calibrated_ear=None):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "Video load nahi hui"}

    frame_results = []
    frame_count   = 0
    drowsy_frames = 0
    total_frames  = 0
    sample_frame  = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % 10 != 0:
            continue

        frame  = cv2.resize(frame, (640, 480))
        result = analyze_frame(frame.copy(), calibrated_ear)

        if result["face_detected"]:
            total_frames += 1
            if result["result"] == "DROWSY":
                drowsy_frames += 1
            if sample_frame is None or result["result"] == "DROWSY":
                sample_frame = result["frame"]
            frame_results.append({
                "frame_no"     : frame_count,
                "result"       : result["result"],
                "fatigue_score": result["fatigue_score"],
            })

    cap.release()

    if total_frames == 0:
        return {"error": "Video mein face detect nahi hua"}

    drowsy_percent = (drowsy_frames / total_frames) * 100
    overall_result = "DROWSY" if drowsy_percent > 30 else "ALERT"
    avg_fatigue    = sum(r["fatigue_score"] for r in frame_results) / len(frame_results)

    return {
        "face_detected" : True,
        "result"        : overall_result,
        "fatigue_score" : round(avg_fatigue, 1),
        "drowsy_percent": round(drowsy_percent, 1),
        "total_frames"  : total_frames,
        "drowsy_frames" : drowsy_frames,
        "frame_results" : frame_results[:20],
        "signals"       : {},
        "frame"         : sample_frame
    }

def frame_to_base64(frame):
    if frame is None:
        return None
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')