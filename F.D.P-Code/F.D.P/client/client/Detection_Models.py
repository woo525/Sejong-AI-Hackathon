import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime
import mediapipe as mp
import pytesseract
import winsound as sd
import logging
import pyttsx3
# ----------------------------------------------------------------------------------------------------------------------
# [face detection] -----------------------------------------------------------------------------------------------------
stuName = '김우혁'
stuNum = '17011882'

path = 'StudentNames'
images = []
studentNames = []
myList = os.listdir(path)

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    studentNames.append(os.path.splitext(cl)[0])
print('Student Names: ', studentNames)

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

def markAttendance(name):
    with open('Attendance.csv', 'r+') as f:
        myDataList = f.readlines()
        nameList = []
        for line in myDataList:
            entry = line.split(',')
            nameList.append(entry[0])
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'\n{name},{dtString}')

encodeListKnown = findEncodings(images)
print('Encoding Complete!')

correct_face = 1 # 일치하는 것으로 시작!
# ----------------------------------------------------------------------------------------------------------------------
# [object detection] ---------------------------------------------------------------------------------------------------
classNames = []
classFile = 'coco.names' # 91 labels
with open(classFile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

# make object detection model
configPath = 'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'
weightsPath = 'frozen_inference_graph.pb'

net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0/ 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

toDetectIds = [77, 84] # cell phone, book
# ----------------------------------------------------------------------------------------------------------------------
# [hand detection] -----------------------------------------------------------------------------------------------------
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
# ----------------------------------------------------------------------------------------------------------------------
# [TTS]
def TTS(message):
    engine = pyttsx3.init()  # 보이스엔진 초기화
    voices = engine.getProperty('voices')
    volume = engine.getProperty('volume')
    rate = engine.getProperty('rate')
    print('rate = ',rate)
    engine.setProperty('rate', 200)
    engine.say(message)
    engine.runAndWait()

# [한글 파일명으로 이미지 저장]
def imwrite(filename, img, params=None): # 한글 이름으로 파일 저장하기 위함
    try:
        ext = os.path.splitext(filename)[1]
        result, n = cv2.imencode(ext, img, params)

        if result:
            with open(filename, mode='w+b') as f:
                n.tofile(f)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False
# ----------------------------------------------------------------------------------------------------------------------
# [Front Camera Detection Model] ---------------------------------------------------------------------------------------
def Front_Detection(img):

    global correct_face # 함수 안에서 변수 사용할 떄 전역변수임을 명시 !!

    # face recognition
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)  # default -> tolerance=0.6
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)  # distance 반환
        # print(matches)
        # print(faceDis)

        matchIndex = np.argmin(faceDis)  # distance 작을수록 유사도 높음 -> argmin 사용
        # print(matchIndex)

        if matches[matchIndex]:
            name = studentNames[matchIndex].upper()
            if name != 'WOOHYEOK':
                correct_face = 0
            else:
                correct_face = 1

            # print(name)  # 인식된 수험자
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 1)  # 마지막 요소는 두께
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (255, 0, 0), cv2.FILLED)
            cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 1)

            # markAttendance(name)  # .csv 파일에 이름/시각 기입

    return img ,correct_face
# ----------------------------------------------------------------------------------------------------------------------
# [Back Camera Detection Model] ----------------------------------------------------------------------------------------
def Back_Detection(img, book_flag):
    with mp_hands.Hands(min_detection_confidence=0.6, min_tracking_confidence=0.5) as hands:

        # hand detector
        hand_num = 0

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # BGR 2 RGB
        img = cv2.flip(img, 1)  # Flip on horizontal
        img.flags.writeable = False  # Set flag
        results = hands.process(img)  # Detections
        img.flags.writeable = True  # Set flag to true
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # RGB 2 BGR

        if results.multi_hand_landmarks:
            if len(results.multi_hand_landmarks) == 2:
                hand_num = 2
            else:
                hand_num = 1
        else:
            hand_num = 0

        if results.multi_hand_landmarks:
            for num, hand in enumerate(results.multi_hand_landmarks):
                mp_drawing.draw_landmarks(img, hand, mp_hands.HAND_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                                          mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2),
                                          )

        # object detector -> book, cell phone detect
        book_num = 0  # 감지된 책의 개수
        cell_phone_num = 0  # 감지된 휴대폰 개수
        classIds, confs, bbox = net.detect(img, confThreshold=0.6)  # score 60% 이상만 탐지

        if len(classIds) != 0:
            for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):

                if book_flag == 1: # open book 일 경우, 책에 박스 생성 X
                    if classId == 84: continue

                if classId in toDetectIds:

                    if classId == 84: book_num = book_num + 1
                    if classId == 77: cell_phone_num = cell_phone_num + 1

                    cv2.rectangle(img, box, color=(255, 0, 0), thickness=1)
                    cv2.putText(img, classNames[classId - 1].upper(), (box[0] + 10, box[1] + 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 0, 0), 1)

    return img, hand_num, book_num, cell_phone_num



