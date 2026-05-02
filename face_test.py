# import cv2
# import mediapipe as mp
# import math
# import winsound

# import pyttsx3

# engine = pyttsx3.init()
# voice_triggered = False

# # ---------- MEDIAPIPE SETUP ----------
# mp_face = mp.solutions.face_mesh
# mp_draw = mp.solutions.drawing_utils

# face_mesh = mp_face.FaceMesh(
#     static_image_mode=False,
#     max_num_faces=1,
#     refine_landmarks=True,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5
# )

# # ---------- LANDMARK INDEX ----------
# LEFT_EYE = [33,160,158,133,153,144]
# RIGHT_EYE = [362,385,387,263,373,380]

# UPPER_LIP = 13
# LOWER_LIP = 14

# NOSE = 1
# CHIN = 152

# # ---------- VARIABLES ----------
# calibrated_ear = None
# ear_sum = 0
# calibration_frames = 0
# CALIBRATION_TOTAL = 60

# closed_frames = 0
# blink_counter = 0
# yawn_counter = 0

# # ---------- FUNCTIONS ----------
# def dist(p1,p2):
#     return math.hypot(p1[0]-p2[0],p1[1]-p2[1])

# def eye_aspect_ratio(eye):
#     A = dist(eye[1],eye[5])
#     B = dist(eye[2],eye[4])
#     C = dist(eye[0],eye[3])
#     return (A+B)/(2*C)

# # ---------- CAMERA ----------
# cap = cv2.VideoCapture(0)

# while True:

#     ret,frame = cap.read()
#     if not ret:
#         break

#     frame = cv2.flip(frame,1)
#     frame = cv2.resize(frame,(640,480))

#     h,w,_ = frame.shape

#     rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
#     results = face_mesh.process(rgb)

#     fatigue_score = 0

#     if results.multi_face_landmarks:

#         for face_landmarks in results.multi_face_landmarks:

#             # -------- DRAW FACE MESH --------
#             mp_draw.draw_landmarks(
#                 frame,
#                 face_landmarks,
#                 mp_face.FACEMESH_TESSELATION,
#                 mp_draw.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1),
#                 mp_draw.DrawingSpec(color=(0,0,255), thickness=1)
#             )

#             landmarks = face_landmarks.landmark

#             left_eye=[]
#             right_eye=[]

#             # -------- LEFT EYE --------
#             for i in LEFT_EYE:
#                 x = int(landmarks[i].x * w)
#                 y = int(landmarks[i].y * h)
#                 left_eye.append((x,y))
#                 cv2.circle(frame,(x,y),2,(0,255,0),-1)

#             # -------- RIGHT EYE --------
#             for i in RIGHT_EYE:
#                 x = int(landmarks[i].x * w)
#                 y = int(landmarks[i].y * h)
#                 right_eye.append((x,y))
#                 cv2.circle(frame,(x,y),2,(0,255,0),-1)

#             # -------- EAR --------
#             leftEAR = eye_aspect_ratio(left_eye)
#             rightEAR = eye_aspect_ratio(right_eye)
#             ear = (leftEAR + rightEAR) / 2

#             cv2.putText(frame,f"EAR: {ear:.2f}",
#                         (20,40),
#                         cv2.FONT_HERSHEY_SIMPLEX,
#                         0.8,(0,255,0),2)

#             # -------- CALIBRATION --------
#             if calibrated_ear is None:

#                 ear_sum += ear
#                 calibration_frames += 1

#                 cv2.putText(frame,
#                 "Calibrating... Keep eyes open",
#                 (20,80),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 0.7,(255,255,0),2)

#                 if calibration_frames >= CALIBRATION_TOTAL:
#                     calibrated_ear = ear_sum/calibration_frames

#                 cv2.imshow("Driver Monitor",frame)
#                 continue

#             EAR_THRESHOLD = calibrated_ear * 0.65

#             # -------- EYES CLOSED --------
#             if ear < EAR_THRESHOLD:
#                 closed_frames += 1
#             else:
#                 if closed_frames > 2:
#                     blink_counter += 1
#                 closed_frames = 0

#             if closed_frames > 12:
#                 fatigue_score += 2
#                 cv2.putText(frame,"EYES CLOSED",
#                             (20,120),
#                             cv2.FONT_HERSHEY_SIMPLEX,
#                             0.8,(0,0,255),2)

#             # -------- YAWNING --------
#             upper = (int(landmarks[UPPER_LIP].x*w),
#                      int(landmarks[UPPER_LIP].y*h))

#             lower = (int(landmarks[LOWER_LIP].x*w),
#                      int(landmarks[LOWER_LIP].y*h))

#             mouth_dist = dist(upper,lower)

#             if mouth_dist > 28:
#                 yawn_counter += 1
#             else:
#                 yawn_counter = 0

#             if yawn_counter > 8:
#                 fatigue_score += 1
#                 cv2.putText(frame,"YAWNING",
#                             (20,160),
#                             cv2.FONT_HERSHEY_SIMPLEX,
#                             0.8,(0,165,255),2)

#             # -------- HEAD TILT --------
#             nose = (int(landmarks[NOSE].x*w),
#                     int(landmarks[NOSE].y*h))

#             chin = (int(landmarks[CHIN].x*w),
#                     int(landmarks[CHIN].y*h))

#             tilt = abs(nose[0]-chin[0])

#             if tilt > 40:
#                 fatigue_score += 1
#                 cv2.putText(frame,"HEAD TILT",
#                             (20,200),
#                             cv2.FONT_HERSHEY_SIMPLEX,
#                             0.8,(255,0,0),2)

#             # -------- FACIAL FATIGUE --------
#             if mouth_dist > 24 and ear < calibrated_ear*0.8:

#                 fatigue_score += 1

#                 cv2.putText(frame,"FACIAL FATIGUE",
#                             (20,240),
#                             cv2.FONT_HERSHEY_SIMPLEX,
#                             0.8,(255,255,0),2)

#             # -------- SCORE --------
#             cv2.putText(frame,
#             f"Fatigue Score: {fatigue_score}",
#             (20,300),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             0.9,(255,255,255),2)

#             # -------- FINAL ALERT --------
#             if fatigue_score >= 3:

#                 cv2.putText(frame,
#                 "DRIVER DROWSY!",
#                 (180,420),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 1.3,(0,0,255),3)

#                 winsound.Beep(2000,800)
#                 if not voice_triggered:
#                     engine.say("Driver please take a break")
#                     engine.runAndWait()
#                     voice_triggered=True

#             else:
#                 voice_triggered = False
    

#     cv2.imshow("Driver Monitoring System",frame)

#     if cv2.waitKey(1) & 0xFF == 27:
#         break

# cap.release()
# cv2.destroyAllWindows()






import cv2
import mediapipe as mp
import math
import winsound
import threading
import time

import pyttsx3

# ---------- TTS SETUP ----------
last_alert_time = 0
ALERT_COOLDOWN = 8  # seconds between voice alerts

def speak_async(text):
    """Run TTS in background thread so video doesn't freeze"""
    def _speak():
        e = pyttsx3.init()
        e.say(text)
        e.runAndWait()
    threading.Thread(target=_speak, daemon=True).start()

# ---------- MEDIAPIPE SETUP ----------
mp_face = mp.solutions.face_mesh
mp_draw = mp.solutions.drawing_utils

face_mesh = mp_face.FaceMesh(
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

# ---------- CALIBRATION VARIABLES ----------
calibrated_ear     = None
ear_sum            = 0
calibration_frames = 0
CALIBRATION_TOTAL  = 60

# ---------- DETECTION VARIABLES ----------
closed_frames = 0
yawn_counter  = 0
blink_counter = 0

# ---------- BLINK RATE TRACKING (Option A) ----------
# Normal blink rate  = 15-20 blinks/min
# Drowsy blink rate  = less than 8 blinks/min
# Agar 60 second window mein 8 se kam blinks = drowsiness signal
blink_window        = []   # har blink ka timestamp store hoga
BLINK_WINDOW_SECS   = 60   # 1 minute sliding window
LOW_BLINK_THRESHOLD = 8    # 8/min se kam = drowsy
blink_rate_per_min  = -1   # -1 = abhi enough data nahi
low_blink_frames    = 0    # lagatar kitne frames se low rate hai
LOW_BLINK_LIMIT     = 90   # ~3 seconds lagatar low rate ho tab fatigue add karo

# ---------- FPS TRACKING ----------
fps_start       = time.time()
fps_frame_count = 0
fps_display     = 0

# ---------- FUNCTIONS ----------
def dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def eye_aspect_ratio(eye):
    A = dist(eye[1], eye[5])
    B = dist(eye[2], eye[4])
    C = dist(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def get_head_pose(landmarks, w, h):
    """
    Head Pose Detection.
    
    PITCH → forward nod   : Z-axis depth (forehead vs chin)
    YAW   → left/right    : Nose X vs eye midpoint X (stable, no Z noise)
    ROLL  → side tilt     : Eye line angle
    """
    nose     = landmarks[1]
    chin     = landmarks[152]
    left_eye = landmarks[33]
    right_eye= landmarks[263]
    forehead = landmarks[10]

    # PITCH — forward/backward nod (Y-axis based, stable)
    # Seedha dekhne pe nose ~55% neeche forehead se hoti hai
    # Nod karne pe nose aur neeche jaati hai → ratio badhta hai
    nose_y      = nose.y * h
    forehead_y  = forehead.y * h
    chin_y      = chin.y * h
    face_h      = abs(chin_y - forehead_y)
    if face_h > 0:
        nose_rel = (nose_y - forehead_y) / face_h
        pitch    = (nose_rel - 0.55) * 100   # 0=normal, +ve=nodding down
    else:
        pitch = 0

    # YAW — left/right turn
    # Nose X ka eye midpoint X se kitna offset hai
    # Normalized by face width (eye distance) taaki distance se independent rahe
    nose_x    = nose.x * w
    le_x      = left_eye.x * w
    re_x      = right_eye.x * w
    eye_mid_x = (le_x + re_x) / 2
    eye_dist  = abs(re_x - le_x)  # face width as reference

    if eye_dist > 0:
        # offset ratio: 0 = center, +ve = turned right, -ve = turned left
        yaw_ratio = (nose_x - eye_mid_x) / eye_dist
        # Scale to degrees-like value (0.3 ratio ~ 30 deg turn)
        yaw = yaw_ratio * 100
    else:
        yaw = 0

    # ROLL — side tilt using eye line angle
    le_y = left_eye.y * h
    re_y = right_eye.y * h
    roll = math.degrees(math.atan2(re_y - le_y, re_x - le_x))

    return pitch, yaw, roll

# ---------- CAMERA ----------
cap = cv2.VideoCapture(0)

while True:

    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (640, 480))
    h, w, _ = frame.shape

    # FPS calculation
    fps_frame_count += 1
    if time.time() - fps_start >= 1.0:
        fps_display     = fps_frame_count
        fps_frame_count = 0
        fps_start       = time.time()

    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    fatigue_score = 0
    now_t         = time.time()

    # Always show FPS
    cv2.putText(frame, f"FPS: {fps_display}",
                (560, 20), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (180, 180, 180), 1)

    if results.multi_face_landmarks:

        for face_landmarks in results.multi_face_landmarks:

            # -------- FACE MESH --------
            mp_draw.draw_landmarks(
                frame, face_landmarks,
                mp_face.FACEMESH_TESSELATION,
                mp_draw.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1),
                mp_draw.DrawingSpec(color=(0, 0, 255), thickness=1)
            )

            landmarks = face_landmarks.landmark

            left_eye  = []
            right_eye = []

            for i in LEFT_EYE:
                x = int(landmarks[i].x * w)
                y = int(landmarks[i].y * h)
                left_eye.append((x, y))
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

            for i in RIGHT_EYE:
                x = int(landmarks[i].x * w)
                y = int(landmarks[i].y * h)
                right_eye.append((x, y))
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

            # -------- EAR --------
            ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2

            cv2.putText(frame, f"EAR: {ear:.2f}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)

            # -------- CALIBRATION --------
            if calibrated_ear is None:
                ear_sum += ear
                calibration_frames += 1

                cv2.putText(frame, "Calibrating... Keep eyes open",
                            (20, 80), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (255, 255, 0), 2)

                progress = int((calibration_frames / CALIBRATION_TOTAL) * 200)
                cv2.rectangle(frame, (20, 100), (220, 115), (50, 50, 50), -1)
                cv2.rectangle(frame, (20, 100), (20 + progress, 115), (0, 255, 255), -1)

                if calibration_frames >= CALIBRATION_TOTAL:
                    calibrated_ear = ear_sum / calibration_frames

                cv2.imshow("Driver Monitoring System", frame)
                continue

            EAR_THRESHOLD = calibrated_ear * 0.65

            # ================================================================
            # -------- EYES CLOSED DETECTION --------
            # ================================================================
            if ear < EAR_THRESHOLD:
                closed_frames += 1
            else:
                if closed_frames > 2:
                    # Ek complete blink hua — timestamp blink_window mein daalo
                    blink_counter += 1
                    blink_window.append(now_t)
                closed_frames = 0

            if closed_frames > 12:
                fatigue_score += 2
                cv2.putText(frame, "EYES CLOSED",
                            (20, 120), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 0, 255), 2)

            # ================================================================
            # -------- BLINK RATE ANALYSIS --------
            # Sliding 60-second window mein count karo
            # < 8 blinks/min = drowsiness detected
            # ================================================================

            # 60 sec se purane blinks window se hatao
            blink_window = [t for t in blink_window if now_t - t <= BLINK_WINDOW_SECS]

            # Rate calculate karo — minimum 10 sec data chahiye reliable hone ke liye
            if blink_window:
                window_duration = now_t - blink_window[0]
                if window_duration >= 10:
                    blink_rate_per_min = int((len(blink_window) / window_duration) * 60)
                else:
                    blink_rate_per_min = -1
            else:
                blink_rate_per_min = -1

            # Low blink rate frames counter
            if blink_rate_per_min != -1 and blink_rate_per_min < LOW_BLINK_THRESHOLD:
                low_blink_frames += 1
            else:
                low_blink_frames = max(0, low_blink_frames - 1)

            # 3 seconds lagatar low rate ho toh fatigue add karo
            if low_blink_frames > LOW_BLINK_LIMIT:
                fatigue_score += 1
                cv2.putText(frame, f"LOW BLINK RATE! ({blink_rate_per_min}/min)",
                            (20, 145), cv2.FONT_HERSHEY_SIMPLEX,
                            0.65, (0, 100, 255), 2)

            # Blink rate display — color se status pata chale
            if blink_rate_per_min == -1:
                blink_color = (160, 160, 160)
                blink_text  = "Blink Rate: Calculating..."
            elif blink_rate_per_min < LOW_BLINK_THRESHOLD:
                blink_color = (0, 100, 255)
                blink_text  = f"Blink Rate: {blink_rate_per_min}/min  [LOW!]"
            else:
                blink_color = (0, 220, 0)
                blink_text  = f"Blink Rate: {blink_rate_per_min}/min"

            cv2.putText(frame, blink_text,
                        (20, 360), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, blink_color, 2)

            # ================================================================
            # -------- YAWNING --------
            # ================================================================
            nose_pt = (int(landmarks[NOSE].x * w), int(landmarks[NOSE].y * h))
            chin_pt = (int(landmarks[CHIN].x * w), int(landmarks[CHIN].y * h))
            upper   = (int(landmarks[UPPER_LIP].x * w), int(landmarks[UPPER_LIP].y * h))
            lower   = (int(landmarks[LOWER_LIP].x * w), int(landmarks[LOWER_LIP].y * h))

            face_height = dist(nose_pt, chin_pt)
            mouth_dist  = dist(upper, lower)
            mouth_ratio = mouth_dist / face_height if face_height > 0 else 0

            if mouth_ratio > 0.30:
                yawn_counter += 1
            else:
                yawn_counter = 0

            if yawn_counter > 8:
                fatigue_score += 1
                cv2.putText(frame, "YAWNING",
                            (20, 170), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 165, 255), 2)

            # ================================================================
            # -------- HEAD POSE (3D pitch / yaw / roll) --------
            # ================================================================
            pitch, yaw, roll = get_head_pose(landmarks, w, h)

            # Live values for demo/tuning
            cv2.putText(frame, f"P:{pitch:.0f} Y:{yaw:.0f} R:{roll:.0f}",
                        (20, 210), cv2.FONT_HERSHEY_SIMPLEX,
                        0.55, (200, 200, 200), 1)

            if pitch > 10:   # +10 = sir kaafi aage jhuka hai
                fatigue_score += 1
                cv2.putText(frame, "HEAD DOWN (Nodding!)",
                            (20, 230), cv2.FONT_HERSHEY_SIMPLEX,
                            0.75, (0, 60, 255), 2)
            elif abs(roll) > 12:
                fatigue_score += 1
                cv2.putText(frame, f"HEAD SIDE TILT ({roll:.0f}deg)",
                            (20, 230), cv2.FONT_HERSHEY_SIMPLEX,
                            0.75, (255, 80, 0), 2)
            elif abs(yaw) > 25:
                fatigue_score += 1
                cv2.putText(frame, "LOOKING AWAY",
                            (20, 230), cv2.FONT_HERSHEY_SIMPLEX,
                            0.75, (0, 255, 255), 2)

            # ================================================================
            # -------- FACIAL FATIGUE --------
            # ================================================================
            if mouth_ratio > 0.25 and ear < calibrated_ear * 0.8:
                fatigue_score += 1
                cv2.putText(frame, "FACIAL FATIGUE",
                            (20, 255), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (255, 255, 0), 2)

            # ================================================================
            # -------- SCORE & STATS --------
            # ================================================================
            cv2.putText(frame,
                        f"Fatigue Score: {fatigue_score}  |  Total Blinks: {blink_counter}",
                        (20, 310), cv2.FONT_HERSHEY_SIMPLEX,
                        0.65, (255, 255, 255), 2)

            # ================================================================
            # -------- FINAL DROWSY ALERT --------
            # ================================================================
            if fatigue_score >= 3:
                cv2.putText(frame, "DRIVER DROWSY!",
                            (160, 440), cv2.FONT_HERSHEY_SIMPLEX,
                            1.3, (0, 0, 255), 3)

                if now_t - last_alert_time > ALERT_COOLDOWN:
                    winsound.Beep(2000, 800)
                    speak_async("Driver please take a break")
                    last_alert_time = now_t

    else:
        # Face camera mein nahi dikh raha
        cv2.putText(frame, "No Face Detected",
                    (220, 240), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0, 165, 255), 2)

    cv2.imshow("Driver Monitoring System", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
