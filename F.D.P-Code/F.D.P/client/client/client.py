import threading
import socket
import tkinter as tk  # Tkinter
from PIL import ImageTk, Image  # Pillow
import cv2
import pickle, struct, imutils
import PIL.Image, PIL.ImageTk
import os
import pytesseract
import winsound as sd
import time

from datetime import datetime

from Detection_Models import *

#host_ip='127.0.0.1'
host_ip = '192.168.0.9'
port = 9001

client_chat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_chat.connect((host_ip, port))

name = '학번_이름'

chatting_board = None
book_state = 1

def beepsound(): # 비프음 재생q
    fr = 2000    # range : 37 ~ 32767
    du = 1000     # 1000 ms == 1second
    sd.Beep(fr, du) # winsound.Beep(frequency, duration)

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

class tkCamera(tk.Frame):

    def __init__(self, window, video_source=0):
        super().__init__(window)

        self.window = window

        # self.window.title(window_title)
        self.video_source = video_source
        self.vid = MyVideoCapture(self.video_source)

        self.canvas = tk.Canvas(window, width=self.vid.width, height=self.vid.height)
        #self.canvas.pack()
        self.canvas.place(x=30, y=30)

        # After it is called once, the update method will be automatically called every delay milliseconds

        self.delay = 15
        self.update_widget()

    def update_widget(self):
        self.flag = 0
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        if ret:
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            check_stuName = 0  # 이름 일치 여부
            check_stuNum = 0  # 학번 일치 여부

            stuName = '이름'  # 정답 이름
            stuNum = '학번'  # 정답 학번

            admission = 0  # 학생증 인증 여부

            text = pytesseract.image_to_string(frame, lang='kor')  # img 에서 text 인식
            text = text.replace(" ", "")  # 띄어쓰기 제거
            cv2.rectangle(frame, (round(640 * 0.1), round(480 * 0.1)), (round(640 * 0.9), round(480 * 0.9)),
                          (255, 0, 0), 4)
            if (stuName in text): check_stuName = 1  # 이름 인식
            if (stuNum in text): check_stuNum = 1  # 학번 인식
            if (check_stuName == 1 and check_stuNum == 1):  # 이름, 학번 모두 인식 완료
                cv2.rectangle(frame, (round(640 * 0.1), round(480 * 0.1)), (round(640 * 0.9), round(480 * 0.9)),
                          (0, 255, 0), 4)  # 초록 테두리
                imwrite('StudentIDCard/' + stuNum + '_' + stuName + '.jpg', frame)  # 신분증 이미지 저장
                beepsound()  # 비프음
                cv2.waitKey(2000)
                self.flag=1

            self.image = PIL.Image.fromarray(frame)
            self.photo = PIL.ImageTk.PhotoImage(image=self.image)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        if self.flag==0:
            self.window.after(self.delay, self.update_widget)
        else:
            # self.vid.release()
            cv2.destroyAllWindows()

class App:

    def __init__(self, window, window_title, video_source1=0):
        self.window = window

        self.window.title(window_title)

        # open video source (by default this will try to open the computer webcam)
        self.vid1 = tkCamera(window, video_source1)
        self.vid1.pack()
        # Create a canvas that can fit the above video source size
        #self.window.mainloop()


class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)
        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.width = 640
        self.height = 480

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                frame = cv2.resize(frame, (640, 480))
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
win = tk.Tk()  # 인스턴스 생성

#win.title("대기실 GUI")  # 제목 표시줄 추가
win.geometry("700x600")
win.option_add("*Font", "Arial 20 bold italic")
App(win, "대기실 GUI", 0)

# room 라벨
lab1 = tk.Label(win)
lab1.config(text="ROOM NO.")
lab1.place(x=70, y=540)
# lab1.pack()
# room 입력창
ent1 = tk.Entry(win)
ent1.place(x=240, y=540)

def enter_room():
    ent1_get=ent1.get()
    print(ent1_get)

class Test_start():
    def __init__(self):
        self.btn1 = tk.Button(win,text="입장",command=win.destroy)

        self.btn1.config(width=6)
        self.btn1.place(x=565, y=525)
    def nextpage(self):
        self.btn1.config(text="입장!")

test_start = Test_start()

win.mainloop()  # GUI 시작

# ---------------------------------------------------------------------------------------------------------------------

client_chat.send(f'{name}'.encode('utf-8'))  # 이름 서버에 보냄

# ---------------- client -> host ----------------- #
def send_host(msg):  # 사용자에게 해당 학생 경고문 날리는 함수 (stt과 영상 모델에서 사용)
    try:
        client_chat.send(msg.encode('utf-8'))
    except:
        pass

def hand():  # 손들기 버튼
    send_host('(hand)')


def submit():  # 제출 버튼
    send_host('(submit)')


def file_send(name):
    client_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_file.connect((host_ip, port - 6))  # 채팅 주고받는 서버 포트랑 연결

    client_file.send(name.encode('utf-8'))
    data_transferred = 0
    id = name.split('_')[0]

    filename = f'/Users/2kyung19/Desktop/client/test/{id}.jpg'

    with open(filename, 'rb') as f:
        try:
            data = f.read(1024)
            while data:
                data_transferred += client_file.send(data)
                data = f.read(1024)
        except:
            pass

    print('채점 완료')
    client_file.close()


# ---------------- multi chat  ------------------- #
send_check = True  # 원래는 False값이어야 할() 듯


def go_send():  # gui 상에서 보내기 버튼 누르면 send가 True가 됨
    global send_check

    send_check = True

def write_log(msg):
    global chatting_board

    if chatting_board != None:
        chatting_board.insert("end",  '\n' + msg + '\n')


def chat_thread():
    def chat_recv(server, name):  # 관리자로부터 메시지 받는
        global book_state
        try:
            while client_chat:  # 서버랑 연결 되어있으면 True
                recv = server.recv(1024)  # 메시지 받음
                try:
                    msg = recv.decode('utf-8')
                    if msg.find('[채점]') != -1:
                        file_send(name)
                        continue
                    elif msg.find('[openbook]')!= -1:
                        book_state=1
                        continue
                    elif msg.find('[closebook]')!=-1:
                        book_state=0
                        continue

                    write_log('교수님 : ' + msg)
                except:
                    pass
        except:
            pass

    def chat_client():  # chat main
        global send_check

        c1 = threading.Thread(target=chat_recv, args=(client_chat, name))  # 서버로부터 메시지 받는 함수 계속 돌림
        c1.start()

        try:
            while client_chat:  # 서버랑 연결되어있으면
                send = input('')

                if not send or send_check == False:
                    # send_check=False # input값에 아무것도 없으면
                    continue

                try:
                    client_chat.send(send.encode('utf-8'))  # 메시지를 관리자에게 보내
                    # send_check=False # 보내고 나면 check False 처리
                except:
                    pass

                if (send == 'exit'):  # exit
                    print('종료합니다')
                    break
        except:
            pass

        client_chat.close()
        c1.join()

    chat_client()
    client_chat.close()

    # t1 = threading.Thread(target=func2)
    # t1.start()
    # t1.join()


# ---------------- push client video  ------------------- #


cam1 = cv2.VideoCapture(0)  # 캠
def push_video1():  # 전면캠
    client_video1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_video1.connect((host_ip, port - 2))  # 전면캠 받는 서버랑 연결
    print(f'video1 server 연결 : {host_ip}:{port - 2}')

    #cam1 = cv2.VideoCapture(0)  # 캠

    def video_send():
        if client_video1:  # 서버랑 연결 중이면 True
            while (cam1.isOpened()):
                try:
                    ret, frame = cam1.read()
                    # [model] ------------------------------------------------------------------------------------------
                    frame, correct_f = Front_Detection(frame)
                    if correct_f == 0:
                        client_chat.send('[부정행위 의심] : 수험자가 일치하지 않습니다.'.encode('utf-8'))
                        write_log('[부정행위 의심] : 수험자가 일치하지 않습니다.')
                    # --------------------------------------------------------------------------------------------------
                    frame = imutils.resize(frame, width=380)  # frame size 알맞게 변경 가능
                    a = pickle.dumps(frame)
                    message = struct.pack("Q", len(a)) + a
                    client_video1.sendall(message)  # 서버에 push

                    #cv2.imshow('client_1', frame)

                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        client_video1.close()  # 서버랑 연결 종료
                except:
                    break
        client_video1.close()  # 서버랑 연결 종료

    vt1 = threading.Thread(target=video_send)  # push video
    vt1.start()
    vt1.join()

cam2 = cv2.VideoCapture(1)
def push_video2():  # 후면캠
    global book_state

    client_video2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_video2.connect((host_ip, port - 4))
    print(f'video2 server 연결 : {host_ip}:{port - 4}')

    #cam2 = cv2.VideoCapture(1)

    def video_send():
        global book_state
        if client_video2:
            # start = datetime.now()
            while (cam2.isOpened()):
                try:
                    ret, frame = cam2.read()
                    # [model] ------------------------------------------------------------------------------------------
                    frame, hand_f, book_f, cell_phone_f = Back_Detection(frame, book_state)

                    # now = datetime.now()
                    if hand_f < 2:  # 손 부정행위 의심
                        if now - start >= 5000:
                            client_chat.send('(cheating)양 손이 화면안에 위치하지 않습니다.'.encode('utf-8'))  # 이름 서버에 보냄
                            write_log('(cheating)양 손이 화면안에 위치하지 않습니다.')
                    else:
                        start = datetime.now()

                    if book_f > 0:  # 책 부정행위 의심
                        client_chat.send('(cheating)오픈북 시험이 아닙니다.'.encode('utf-8'))  # 이름 서버에 보냄
                        write_log('(cheating)오픈북 시험이 아닙니다.')
                    if cell_phone_f > 0:
                        client_chat.send('(cheating)휴대전화가 감지 되었습니다'.encode('utf-8'))  # 이름 서버에 보냄
                        write_log('(cheating)휴대전화가 갑지 되었습니다.')
                    # --------------------------------------------------------------------------------------------------
                    frame = imutils.resize(frame, width=380)
                    a = pickle.dumps(frame)
                    message = struct.pack('Q', len(a)) + a

                    client_video2.sendall(message)

                    #cv2.imshow('client_2', frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        client_video2.close()
                except:
                    break
        client_video2.close()

    vt1 = threading.Thread(target=video_send)  # push video
    vt1.start()

    vt1.join()


def video_thread():  # video main
    v1 = threading.Thread(target=push_video1)  # 전면캠 보내는
    v2 = threading.Thread(target=push_video2)  # 후면캠 보내는

    v1.start()
    v2.start()

    v1.join()
    v2.join()
class tkCamera2(tk.Frame):
    global book_state
    global video_type

    def __init__(self, window, video_source=0):
        super().__init__(window)

        self.window = window

        # self.window.title(window_title)
        self.video_source = video_source
        self.vid = MyVideoCapture2(self.video_source)

        self.canvas = tk.Canvas(window, width=self.vid.width, height=self.vid.height)
        self.canvas.place(x=30, y=30)
        #self.canvas.pack()

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 15
        self.update_widget()

    def update_widget(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        if ret:
            # [model] --------------------------------------------------------------------------------------------------
            if video_type == 0: frame, correct_f = Front_Detection(frame)
            else: frame, hand_f, book_f, cell_phone_f = Back_Detection(frame, book_state)
            # ----------------------------------------------------------------------------------------------------------
            self.image = PIL.Image.fromarray(frame)
            self.photo = PIL.ImageTk.PhotoImage(image=self.image)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update_widget)


class App2:

    def __init__(self, window, window_title, video_source1=0, video_source2=0):
        self.window = window

        self.window.title(window_title)

        # open video source (by default this will try to open the computer webcam)
        self.vid1 = tkCamera2(window, video_source1)
        self.vid1.pack()

video_type = 0

class MyVideoCapture2:
    global video_type

    def __init__(self, video_source=0):
        # Open the video source
        self.vid1 = cam1
        self.vid2 = cam2

        if not (self.vid1.isOpened() and self.vid2.isOpened()):
            raise ValueError("Unable to open video source")

        # Get video source width and height
        # self.width = self.vid1.get(cv2.CAP_PROP_FRAME_WIDTH)
        # self.height = self.vid1.get(cv2.CAP_PROP_FRAME_HEIGHT)
        #
        # self.width = self.vid2.get(cv2.CAP_PROP_FRAME_WIDTH)
        # self.height = self.vid2.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.width = 600
        self.height = 400

    def get_frame(self):
        # self.vid = cv2.VideoCapture(video_type)


        if self.vid1.isOpened() and self.vid2.isOpened():
            if video_type == 0: ret, frame = self.vid1.read()
            else: ret, frame = self.vid2.read()

            if ret:
                frame = cv2.resize(frame, (600, 400))
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

# ---------------- stt  ------------------- #
import speech_recognition as sr
import pyttsx3

def TTS(message):
    engine = pyttsx3.init()  # 보이스엔진 초기화
    voices = engine.getProperty('voices')
    volume = engine.getProperty('volume')
    rate = engine.getProperty('rate')
    # print('rate = ',rate)
    engine.setProperty('rate', 200)
    engine.say(message)
    engine.runAndWait()
    # time.sleep(5)
    # engine.endLoop()


def stt():
    while True:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            # print("Speak!")

            try:
                audio = r.listen(source, timeout=0, phrase_time_limit=2.5)
                text = r.recognize_google(audio, language="ko-KR")
                write_log("경고 : " + text)
                send_host(f"(cheat){text}")
                TTS('시험과 관계 없는 말소리는 부정행위로 오해 받을 수 있습니다.')
            except sr.UnknownValueError:
                # print("Google Speech Recognition could not understand audio ")
                continue

            except sr.RequestError as e:
                # print("Could not request results from Google Speech Recognition service")
                continue


# --------------- gui -----------------------

def gui():
    global chatting_board
    global video_type
    # 시험장 GUI 설계
    win = tk.Tk()  # 인스턴스 생성

    win.title("시험장 GUI")  # 제목 표시줄 추가
    win.geometry("850x800+200+80")
    win.option_add("*Font", "Arial 20 bold italic")

    frm = tk.Frame(win, bg="black", width=600, height=400)  # 프레임 너비, 높이 설정
    frm.place(x=30, y=30)

    def HandsUp():  # 손들기 버튼 누르면 벌어지는 일
        frame_chatting_board.tag_config("hand", foreground="blue")
        frame_chatting_board.insert(tk.CURRENT, "\n" + "교수님께 손들기 요청을 완료 하였습니다." + "\n", "hand")
        hand()
        # 서버에 보내기

    def TestPaper():  # 시험지 제출 버튼 누르면 벌어지는 일
        # 캡쳐해서 서버로 보내기 (하는 척만 하는건가?)
        submit()
        pass

    def SendMessage():  # 채팅 전송 버튼 누르면 벌어지는 일
        Message = ent1_2.get()  # 입력창에 있는 메세지 얻어와서
        frame_chatting_board.insert("end", "\n" + "교수님께 : " + Message + "\n")  # 위에 채팅보드에 띄우고
        send_host(Message)
        ent1_2.delete(0, "end")

    class Test_start():
        def __init__(self):
            self.btn1 = tk.Button(win, text="시험 시작", command=self.end)
            self.btn1.config(width=10)
            self.btn1.place(x=650, y=50)

        def end(self):
            self.btn1.config(text="시험 종료")

    test_start = Test_start()

    btn2 = tk.Button(win, command=HandsUp)
    btn2.config(text="손들기")
    btn2.config(width=10)
    btn2.place(x=650, y=150)



    class Display_conv():
        global video_type

        def __init__(self):
            self.btn3 = tk.Button(win, text="후면 전환", command=self.display_conv)
            self.btn3.config(width=10)
            self.btn3.place(x=650, y=250)
            self.flag = 0

        def display_conv(self):
            global video_type

            if self.flag == 0:
                self.flag = 1
                self.btn3.config(text="전면 전환")
                video_type = 1
            else:
                self.flag = 0
                self.btn3.config(text="후면 전환")
                video_type = 0

    display_conv = Display_conv()
    App2(win, "시험장 GUI", 1, 0)

    btn4 = tk.Button(win, command=TestPaper)
    btn4.config(text="시험지 제출")
    btn4.config(width=10)
    btn4.place(x=650, y=350)

    frm_2 = tk.Frame(win, bg="white", width=800, height=200)  # 프레임 너비, 높이 설정
    frm_2.place(x=30, y=450)
    ent1_2 = tk.Entry(win, width=45)
    ent1_2.place(x=50, y=592, height=50)

    # 채팅창
    frame_chatting_board = tk.Text(win, bg="white", width=88, height=13, padx=3, pady=5, font="Arial 13 bold")  # 채팅 보드
    frame_chatting_board.place(x=30, y=450)
    chatting_board = frame_chatting_board

    # 채팅 입력창
    ent1_2 = tk.Entry(win, width=78, font="Arial 13 bold")
    ent1_2.place(x=30, y=725, height=53)

    # 채팅 전송버튼
    btn5_2 = tk.Button(win)
    btn5_2.config(text="전송", width=5, command=SendMessage)
    btn5_2.place(x=735, y=723)

    win.mainloop()  # GUI 시작


def main():
    t1 = threading.Thread(target=chat_thread)  # 채팅
    t2 = threading.Thread(target=video_thread)  # 비디오
    t3 = threading.Thread(target=stt)  # client audio stt
    t4 = threading.Thread(target=gui)

    t4.start()
    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()


main()