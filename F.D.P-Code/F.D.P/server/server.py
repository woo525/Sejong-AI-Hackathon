import threading
import socket
import struct, pickle
import cv2
from tkinter import *
import tkinter as tk 
from PIL import Image
from PIL import ImageTk
import grading

host_ip = '192.168.0.9'
port = 9001

server_chat = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # 채팅 (text)
server_video1 = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # 전면 (video)
server_video2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # 후면 (video)

server_chat.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_video1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_video2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_chat.bind((host_ip,port))
server_video1.bind((host_ip,port-2))
server_video2.bind((host_ip,port-4))

server_chat.listen(3) # 3명까지
server_video1.listen(3) # 3명까지
server_video2.listen(3) # 3명까지

print(f'chat server 시작 : {host_ip}:{port}')
print(f'video server1 시작 : {host_ip}:{port-2}')
print(f'video server2 시작 : {host_ip}:{port-4}')

users = [] # user client server list (chat)
names = [] # user name list

hand_state = []
cheat_state = []
submit_state = []

# gui
console_log = None # 콘솔로그
hand_state_num = None
cheat_state_num = None
submit_state_num = None
book_state= True

f1 = None 
f2 = None
f3 = None
f4 = None

adr1 = ''
adr2 = ''

# ----------------   multi chat    ------------------- #
def write_log(msg):
    if console_log != None:
        console_log.insert(END,msg+'\n')

def write_log_warn(msg):
    if console_log != None:
        console_log.tag_config("warn", foreground="red")
        console_log.insert(END,msg+'\n', "warn")

def write_log_hands(msg):
    if console_log != None:
        console_log.tag_config("hands", foreground="blue")
        console_log.insert(END,msg+'\n', "hands")

def write_log_grade(msg):
    if console_log != None:
        console_log.tag_config("grade", foreground="green")
        console_log.insert(END,msg+'\n', "grade")

def changeText(label,msg):
    global cheat_state_num
    global submit_state_num
    global hand_state_num

    if label!=None:
        if (label=='cheat'):
            cheat_state_num.configure(text = msg)
        elif (label=='hand'):
            hand_state_num.configure(text = msg)
        elif (label=='submit'):
            submit_state_num.configure(text = msg)

def go_send(name,msg):
    try:
        if name=='all' or name=='모두': # 모두에게 보내고싶다면
            for i in range(0,len(users)): # user 다긁어와서 
                try: 
                    users[i].send(msg.encode('utf-8')) # 보냄
                except: continue
        else:
            index = names.index(name) # 특정 인원한테 보내기
            users[index].send(msg.encode('utf-8')) # 해당 client에게 보냄
    except:
        pass

def chat_server(server):
    global users
    global names
    global hand_state
    global cheat_state
    global submit_state

    def chat_recv(client,name): # 사용자가 보내는 메시지 받는 함수
        try:
            while client: # 클라이언트랑 연결되어있으면 True
                if client:
                    recv = client.recv(1024) # 받아

                    # counter
                    msg = recv.decode('utf-8')
                    if msg.find('(cheat)')!=-1:
                        msg = msg.split('(cheat)')[1]
                        write_log_warn(f'경고 : {name} 님에게 "{msg}" 말소리가 감지되었습니다.')
                        if name not in cheat_state:
                            cheat_state.append(name)
                            changeText('cheat',str(len(cheat_state)))
                    elif msg.find('(cheating)')!=-1:
                        msg = msg.split('(cheating)')[1]
                        write_log_warn(f'경고 : {msg}')
                        if name not in cheat_state:
                            cheat_state.append(name)
                            changeText('cheat',str(len(cheat_state)))
                    elif msg.find('(hand)')!=-1:
                        msg = msg.split('(hand)')[1]
                        write_log_hands(f'손들기 : {name} 님이 교수님을 호출합니다.')
                        if name not in hand_state:
                            hand_state.append(name)
                            changeText('hand',str(len(hand_state)))
                    elif msg.find('(submit)')!=-1:
                        msg = msg.split('(submit)')[1]
                        write_log_grade(f'제출 : {name} 님이 시험지를 제출하였습니다.')  
                        if name not in submit_state:
                            submit_state.append(name)  
                            changeText('submit',str(len(submit_state)))
                    else:
                        if (msg=='exit'): # 사용자가 exit라고 보냈으면
                            users.remove(client) # 리스트에서 지움
                            names.remove(name)
                            msg = f'전설의 {name} 님이 퇴장했다!'
                            write_log(msg)
                            client.close() # 클라이언트 연결 종료
                            break

                        msg = f'{name} : ' +recv.decode('utf-8') # 사용자 이름과 사용자가 보낸 text                    
                        write_log(msg)
                    
                else: # except
                    client.close()
        except:
            pass
        
        #msg = f'전설의 {name} 님이 퇴장했다!' # except
        #print(msg)
        client.close()

    def chat_server(): # chat_server main
        
        try:
            while True:
                client,addr = server.accept() # accept된 사용자를 받을 때까지 대기
                users.append(client) # client가 연결했으면 users 리스트에 client 연결 서버 추가

                if client: # client에서 이름 받아
                    recv = client.recv(1024)
                    name = recv.decode('utf-8')
                    names.append(name) # 이름 리스트에 추가
                    write_log(f'야생의 {name}{addr} 님이 등장했다!')
                    
                th = threading.Thread(target=chat_recv ,args=(client,name)) # msg recv(해당 클라이언트가 보내는 메시지를 받는) 스레드 생성해서 계속 돌아가게함
                th.start()
        except:
            pass

    c1 = threading.Thread(target=chat_server) # 사용자들이랑 서버랑 연결, 사용자들에게 메시지 받는
    c1.start()
    c1.join()

# ---------------- get user video  ------------------- #
def convert_tkinter_1(frame,addr):
    global f1
    global f3
    if f1==None:
        return
    
    if adr1!=addr:
        label = f3
    else:
        label = f1

    img = Image.fromarray(frame)
    imgtk = ImageTk.PhotoImage(image=img)
    label.config(image=imgtk, width=600,height=400)
    label.image=imgtk

def convert_tkinter_2(frame,addr):
    global f2
    global f4
    if f2==None:
        return

    if adr2!=addr:
        label = f4
    else:
        label = f2
    img = Image.fromarray(frame)
    imgtk = ImageTk.PhotoImage(image=img)
    label.config(image=imgtk,width=600,height=400)
    label.image=imgtk

def save_adr1(addr):
    global adr1
    if adr1 == '':
        adr1 = addr

def save_adr2(addr):
    global adr2
    if adr2 == '':
        adr2 = addr

def video_server1(server):
	def video_recv(addr,client):
		try:
			save_adr1(addr)

			if client:
				data = b""
				payload_size = struct.calcsize("Q")

				while True:
					while len(data) < payload_size:
						packet = client.recv(4*1024) # 4K
						if not packet: break
						data+=packet
					packed_msg_size = data[:payload_size]
					data = data[payload_size:]
					msg_size = struct.unpack("Q",packed_msg_size)[0]
					
					while len(data) < msg_size:
						data += client.recv(4*1024)
					frame_data = data[:msg_size]
					data  = data[msg_size:]
					frame = pickle.loads(frame_data)
					convert_tkinter_1(frame,addr)
					#cv2.imshow(f"FROM {addr}",frame)
					
					key = cv2.waitKey(1) & 0xFF
					if key  == ord('q'):
						break
				client.close()
		except Exception as e:
			print(f"{addr} : 비디오 중지")
			pass
			
	while True: # main
		client,addr = server.accept() # client 연결 
        
		vt1 = threading.Thread(target=video_recv, args=(addr,client)) # 해당 클라이언트에게 video 받는 스레드 생성
		vt1.start()
		# print("total clients ",threading.activeCount() - 1)

def video_server2(server):
	def video_recv(addr,client):
		try:
			save_adr2(addr)

			if client:
				data = b""
				payload_size = struct.calcsize("Q")

				while True:
					while len(data) < payload_size:
						packet = client.recv(4*1024) # 4K
						if not packet: break
						data+=packet
					packed_msg_size = data[:payload_size]
					data = data[payload_size:]
					msg_size = struct.unpack("Q",packed_msg_size)[0]
					
					while len(data) < msg_size:
						data += client.recv(4*1024)
					frame_data = data[:msg_size]
					data  = data[msg_size:]
					frame = pickle.loads(frame_data)
					convert_tkinter_2(frame,addr)
					#cv2.imshow(f"FROM {addr}",frame)
					
					key = cv2.waitKey(1) & 0xFF
					if key  == ord('q'):
						break
				client.close()
		except Exception as e:
			print(f"{addr} : 비디오 중지")
			pass
			
	while True: # main
		client,addr = server.accept() # client 연결 

		vt1 = threading.Thread(target=video_recv, args=(addr,client)) # 해당 클라이언트에게 video 받는 스레드 생성
		vt1.start()
		# print("total clients ",threading.activeCount() - 1)

def video_thread(): # video_server main
    v1 = threading.Thread(target=video_server1, args=(server_video1,)) # 전면캠 받을 수 있도록
    v2 = threading.Thread(target=video_server2, args=(server_video2,)) # 후면캠 받을 수 있도록

    v1.start()
    v2.start()

    v1.join()
    v2.join()

# ---------------- file recv  ------------------- #
def file_recv(client):
    name = client.recv(1024)
    name = name.decode('utf-8')

    data = client.recv(1024)
    data_transferred = 0

    if not data:
        print(f'{name}님 미제출')
        client.close()
        return
    print(f'{name}님 파일 전송 중')

    id = name.split('_')[0]

    with open(f'./UserForms2/{id}.jpg', 'wb') as f: #현재dir에 filename으로 파일을 받는다
        try:
            while data: #데이터가 있을 때까지
                f.write(data) #1024바이트 쓴다
                data_transferred += len(data)
                data = client.recv(1024) #1024바이트를 받아 온다
        except Exception as ex:
            print(ex)
    print(f'{name}님 제출 완료')
    client.close()

def file(): # 채점 버튼
    server_file = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # 채팅 (text)
    server_file.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_file.bind((host_ip,port-6))
    server_file.listen(3) # 3명까지

    def file_th():
        for i in range(0,len(users)): # 모든 유저한테 chat server로 [채점] 이라고 보냄
            try: 
                users[i].send('[채점]'.encode('utf-8'))
            except: continue

        while True: # main
            client,addr = server_file.accept()
            ft1 = threading.Thread(target=file_recv, args=(client, ))
            ft1.start()
            ft1.join()
            break
    
    f1 =threading.Thread(target=file_th,)
    f1.start()
    f1.join()

    try:
        f2 = threading.Thread(target=grading.main)
        f2.start()
        f2.join()
    except:
        pass

# ----------------   gui    ------------------- #
def gui():
    global console_log
    global hand_state_num
    global cheat_state_num
    global submit_state_num
    global f1
    global f2
    global f3
    global f4

    def Isopenbook(): # 오픈북 토글 누르면 벌어지는 일
        global book_state
        if book_state: 
            button_toggle.configure(image=button_notopenbook) #오픈북모드 OFF
            book_state = False
            go_send('all','[closebook]')
            
        else:  
            button_toggle.configure(image=button_openbook) #오픈북모드 ON
            book_state = True
            go_send('all','[openbook]')
            
    def Grading() : # 시험지 채점 버튼 누르면 벌어지는 일
        write_log_grade('--------채점 시작-------')
        write_log_grade('--------채점 중-------')
        th = threading.Thread(target=file)
        th.start()
        th.join()
        write_log_grade('--------채점 완료-------')

    def SendMessage(): # 채팅 전송 버튼 누르면 벌어지는 일
        Message = entry_chatting.get() # 입력창에 있는 메세지 얻어와서
        frame_chatting_board.insert(END, "\n" + clicked.get() + "에게 : " + Message + "\n") #위에 채팅보드에 띄우고
        entry_chatting.delete(0,END)
        
        go_send(clicked.get(), Message)

    # HOST GUI 설계
    window = tk.Tk() # 인스턴스 생성

    window.title("HOST GUI")
    window.geometry("1650x820+150+100") 
    window.resizable(False, False)

    # 학생 1
    label_client1_name = Label(window, bg="white", text="학번_이름", width=36, height=2, padx=12, relief="solid", font="Arial 16 bold")
    label_client1_name.place(x=30, y=30)
    frame_client1_front = Label(window, bg="white", width=70, height=23, relief="solid")
    frame_client1_front.place(x=30, y=80)
    frame_client1_rear = Label(window, bg="white", width=70, height=23, relief="solid")
    frame_client1_rear.place(x=30, y=430)
    f1 = frame_client1_front
    f2 = frame_client1_rear

    # 학생 2
    label_client2_name = Label(window, bg="white", text="학번_이름", width=36, height=2, padx=12, relief="solid", font="Arial 16 bold")
    label_client2_name.place(x=550, y=30)
    frame_client2_front = Label(window, bg="white", width=70, height=23, relief="solid")
    frame_client2_front.place(x=550, y=80)
    frame_client2_rear = Label(window, bg="white", width=70, height=23, relief="solid")
    frame_client2_rear.place(x=550, y=430)
    f3 = frame_client2_front
    f4 = frame_client2_rear

    # 현상황 반영 아이콘 영역
    label_icon = Label(window, width=38, height=9, relief="solid")
    label_icon.place(x=1080, y=30)

    pic_icon1 = PhotoImage(file='icons/free-icon-question-4185747.png')
    label_icon1 = Label(window, width=88, height=80, image=pic_icon1, relief="solid", bg="white")#sunken
    label_icon1.place(x=1080, y=30)
    label_icon1_count = Label(window, width=4, height=1, padx= 4, pady= 9, bg="white", relief="solid", text='0', font="Arial 25 bold")
    label_icon1_count.place(x=1080, y=111)
    hand_state_num=label_icon1_count

    pic_icon2 = PhotoImage(file='icons/free-icon-siren-995261.png')
    label_icon2 = Label(window, width=88, height=80, image=pic_icon2, relief="solid", bg="white")
    label_icon2.place(x=1170, y=30)
    label_icon2_count = Label(window, width=4, height=1, padx= 4, pady= 9, bg="white", relief="solid", text='0', font="Arial 25 bold")
    label_icon2_count.place(x=1170, y=111)
    cheat_state_num=label_icon2_count

    pic_icon3 = PhotoImage(file='icons/check.png')
    label_icon3 = Label(window, width=88, height=80, image=pic_icon3, relief="solid", bg="white")
    label_icon3.place(x=1260, y=30)
    label_icon3_count = Label(window, width=4, height=1, padx= 4, pady= 9, bg="white", relief="solid", text='0', font="Arial 25 bold")
    label_icon3_count.place(x=1260, y=111)
    submit_state_num=label_icon3_count

    # 오픈북 여부 토글 영역
    label_openbook = Label(window, bg="white", width=13, height=2, pady=3, relief="solid", text="Openbook Mode", font="Arial 13 bold")
    label_openbook.place(x=1360, y=30)
    button_openbook = PhotoImage(file='icons/switch-on-green.png')
    button_notopenbook = PhotoImage(file='icons/switch-off-red.png')
    button_toggle = tk.Button(window, image=button_openbook, width=130, height=80, relief="solid", bg="white", command=Isopenbook)
    button_toggle.place(x=1360, y=84)

    # 시험지 채점하기 버튼 영역
    button_grade = tk.Button(window, width=8, height=5, relief="solid", text="시험지\n채점", font="Arial 15 bold", bg="white", command=Grading) 
    button_grade.place(x=1506, y=30)

    # 채팅창 영역
    label_chatting = Label(window, width=75, height=39, relief="solid") #채팅창 전체
    label_chatting.place(x=1080, y=195)

    frame_chatting_board = tk.Text(window, bg="white", width=57, height=24, padx=3, pady=5, font="Arial 13 bold") #채팅 보드
    frame_chatting_board.place(x=1082,y=197)
    console_log = frame_chatting_board

    clicked = StringVar()
    clicked.set(" 받을 사람")
    student_list = ["모두", "-", "-"]
    optionmenu = OptionMenu(window, clicked, *student_list)
    optionmenu.config(width=14, height = 1, font="Arial 12 bold")
    optionmenu.place(x=1098, y=675)

    entry_chatting=tk.Entry(window,width=60) #입력창
    entry_chatting.place(x=1100,y=710, height=60)

    button_chatting=tk.Button(window, text="전송", font="Arial 15 bold", width=5, command=SendMessage) #전송 버튼 
    button_chatting.place(x=1530,y=709, height=60)

    window.mainloop() #GUI 시작
# ———————— main  ————————— #
def main():
    t1 = threading.Thread(target=gui)
    t2 = threading.Thread(target=chat_server, args=(server_chat, )) # chatting server
    t3 = threading.Thread(target=video_thread) # video server
    
    t1.start()
    t2.start()
    t3.start()
    

    t1.join()
    t2.join()
    t3.join()

main()

server_chat.close()
server_video1.close()
server_video2.close()