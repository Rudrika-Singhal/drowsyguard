import cv2
import mediapipe as mp
import math

mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True
)

cap = cv2.VideoCapture(0)

LEFT_EYE  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def dist(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    if result.multi_face_landmarks:
        for face_landmarks in result.multi_face_landmarks:
            h, w, _ = frame.shape

            left = []
            right = []

            for idx in LEFT_EYE:
                lm = face_landmarks.landmark[idx]
                left.append((int(lm.x*w), int(lm.y*h)))

            for idx in RIGHT_EYE:
                lm = face_landmarks.landmark[idx]
                right.append((int(lm.x*w), int(lm.y*h)))

            # LEFT EAR
            left_ear = (
                dist(left[1], left[5]) + dist(left[2], left[4])
            ) / (2 * dist(left[0], left[3]))

            # RIGHT EAR
            right_ear = (
                dist(right[1], right[5]) + dist(right[2], right[4])
            ) / (2 * dist(right[0], right[3]))

            ear = (left_ear + right_ear) / 2

            # Display EAR
            cv2.putText(frame, f"EAR: {ear:.2f}",
                        (30, 40), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 255, 0), 2)

            # Blink detection
            if ear < 0.25:
                cv2.putText(frame, "EYES CLOSED",
                            (30, 80), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 0, 255), 2)

    cv2.imshow("Blink Detection", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()







# import cv2
# import mediapipe as mp
# import math
# import time

# # -------- INITIAL VALUES --------
# calibrated_ear = None
# ear_sum = 0
# calibration_frames = 0
# CALIBRATION_TOTAL_FRAMES = 90

# closed_frames = 0
# CLOSED_FRAMES_LIMIT = 20

# start_time = time.time()

# # -------- MEDIAPIPE SETUP --------
# mp_face = mp.solutions.face_mesh
# mp_draw = mp.solutions.drawing_utils

# face_mesh = mp_face.FaceMesh(
#     static_image_mode=False,
#     max_num_faces=1,
#     refine_landmarks=True,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5
# )

# # -------- LANDMARK INDEXES --------
# LEFT_EYE = [33,160,158,133,153,144]
# RIGHT_EYE = [362,385,387,263,373,380]
# MOUTH = [13,14,78,308]

# # -------- FUNCTIONS --------
# def dist(p1,p2):
#     return math.hypot(p1[0]-p2[0],p1[1]-p2[1])

# def eye_aspect_ratio(eye):
#     A = dist(eye[1],eye[5])
#     B = dist(eye[2],eye[4])
#     C = dist(eye[0],eye[3])
#     return (A+B)/(2*C)

# def mouth_ratio(mouth):
#     vertical = dist(mouth[0],mouth[1])
#     horizontal = dist(mouth[2],mouth[3])
#     return vertical/horizontal

# # -------- CAMERA --------
# cap = cv2.VideoCapture(0)

# while True:

#     ret, frame = cap.read()
#     if not ret:
#         break

#     frame = cv2.flip(frame,1)

#     h,w,_ = frame.shape

#     rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
#     results = face_mesh.process(rgb)

#     if results.multi_face_landmarks:

#         for face_landmarks in results.multi_face_landmarks:

#             landmarks = face_landmarks.landmark

#             left_eye=[]
#             right_eye=[]
#             mouth=[]

#             # ------- EYE LANDMARKS -------
#             for i in LEFT_EYE:
#                 x=int(landmarks[i].x*w)
#                 y=int(landmarks[i].y*h)
#                 left_eye.append((x,y))
#                 cv2.circle(frame,(x,y),2,(0,0,255),-1)

#             for i in RIGHT_EYE:
#                 x=int(landmarks[i].x*w)
#                 y=int(landmarks[i].y*h)
#                 right_eye.append((x,y))
#                 cv2.circle(frame,(x,y),2,(0,0,255),-1)

#             # ------- MOUTH LANDMARKS -------
#             for i in MOUTH:
#                 x=int(landmarks[i].x*w)
#                 y=int(landmarks[i].y*h)
#                 mouth.append((x,y))
#                 cv2.circle(frame,(x,y),2,(255,0,0),-1)

#             # -------- EAR --------
#             left_ear = eye_aspect_ratio(left_eye)
#             right_ear = eye_aspect_ratio(right_eye)

#             ear = (left_ear + right_ear) / 2

#             cv2.putText(frame,f"EAR: {ear:.2f}",
#                         (30,40),cv2.FONT_HERSHEY_SIMPLEX,
#                         1,(0,255,0),2)

#             # -------- CALIBRATION --------
#             if calibrated_ear is None:

#                 ear_sum += ear
#                 calibration_frames += 1

#                 cv2.putText(frame,"Calibrating... Keep eyes open",
#                             (30,80),cv2.FONT_HERSHEY_SIMPLEX,
#                             0.8,(255,255,0),2)

#                 if calibration_frames >= CALIBRATION_TOTAL_FRAMES:
#                     calibrated_ear = ear_sum / calibration_frames

#                 cv2.imshow("Driver Monitoring",frame)
#                 continue

#             EAR_THRESHOLD = calibrated_ear * 0.7

#             # -------- EYE CLOSURE --------
#             if ear < EAR_THRESHOLD:
#                 closed_frames += 1
#             else:
#                 closed_frames = 0

#             eye_score = 1 if closed_frames > CLOSED_FRAMES_LIMIT else 0

#             # -------- YAWNING --------
#             mar = mouth_ratio(mouth)

#             if mar > 0.6:
#                 cv2.putText(frame,"Yawning Detected",
#                             (30,120),cv2.FONT_HERSHEY_SIMPLEX,
#                             1,(255,0,0),2)
#                 yawn_score = 1
#             else:
#                 yawn_score = 0

#             # -------- DISTRACTION --------
#             nose = landmarks[1]

#             x = int(nose.x*w)

#             if x < w*0.3 or x > w*0.7:
#                 cv2.putText(frame,"Looking Away!",
#                             (30,160),cv2.FONT_HERSHEY_SIMPLEX,
#                             1,(0,255,255),2)
#                 distraction_score = 1
#             else:
#                 distraction_score = 0

#             # -------- FATIGUE SCORE --------
#             fatigue_score = eye_score*0.5 + yawn_score*0.3 + distraction_score*0.2

#             cv2.putText(frame,f"Fatigue Score: {fatigue_score:.2f}",
#                         (30,200),cv2.FONT_HERSHEY_SIMPLEX,
#                         0.8,(255,255,255),2)

#             # -------- DROWSINESS ALERT --------
#             if eye_score==1:
#                 cv2.putText(frame,"DROWSINESS ALERT!",
#                             (100,250),cv2.FONT_HERSHEY_SIMPLEX,
#                             1.5,(0,0,255),3)

#             # -------- BREAK RECOMMENDATION --------
#             drive_time = (time.time() - start_time)/60

#             if drive_time > 60 and fatigue_score > 0.6:

#                 cv2.putText(frame,"Take a Break!",
#                             (100,300),cv2.FONT_HERSHEY_SIMPLEX,
#                             1.2,(0,0,255),3)

#     cv2.imshow("Driver Monitoring",frame)

#     if cv2.waitKey(1) & 0xFF == 27:
#         break

# cap.release()
# cv2.destroyAllWindows()