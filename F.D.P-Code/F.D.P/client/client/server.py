import threading
import socket
import struct, pickle
import cv2

host_ip = '127.0.0.1'
port = 9001

# [추가된 코드]
submit_state = [0, 0] # 클라이언트 1,2 에게 받음
cheat_state = [0, 0] # 클라이언트 1,2 에게 받음
hand_state = [0, 0] # 클라이언트 1,2 에게 받음

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

# ----------------   multi chat    ------------------- #
send_check = True # 원래는 False값이어야 할 듯

def go_send(): # gui 상에서 보내기 버튼 누르면 send가 True가 됨
    global send_check

    send_check = True

def chat_server(server):
    def chat_recv(client,name): # 사용자가 보내는 메시지 받는 함수
        try:
            while client: # 클라이언트랑 연결되어있으면 True
                if client:
                    recv = client.recv(1024) # 받아
                    msg = f'{name} : ' +recv.decode('utf-8') # 사용자 이름과 사용자가 보낸 text
                    print(msg)

                    if (recv.decode('utf-8')=='exit'): # 사용자가 exit라고 보냈으면
                        users.remove(client) # 리스트에서 지움
                        names.remove(name)
                        msg = f'전설의 {name} 님이 퇴장했다!'
                        print(msg)
                        client.close() # 클라이언트 연결 종료
                        break
                else: # except
                    client.close()
        except:
            pass
        
        msg = f'전설의 {name} 님이 퇴장했다!' # except
        print(msg)
        client.close()

    def chat_send(): # 사용자에게 메시지 보내는 함수
        global send_check

        try:
            while True:
                send = input() # name : text 규격으로
                
                if not send or send_check == False:
                    # send_check=False # input값에 아무것도 없으면
                    continue

                try: # 관리자가 작성한 메시지 분할작업 ( --- : text )
                    name = send.split(' : ')[0]
                    msg = f'server : ' + send.split(' : ')[1] # 사용자에게 server : text 이런 규격으로 보냄
                except:
                    print('학생이름 : text 규격에 맞추세요')
                    continue

                if name=='all': # 모두에게 보내고싶다면
                    for i in range(0,len(users)): # user 다긁어와서 
                        try: 
                            users[i].send(msg.encode('utf-8')) # 보냄
                        except: continue
                    continue

                try:
                    index = names.index(name) # 김아무개 : --- 라고했으면 김아무개의 client 연결서버를 users 리스트에서 찾음
                    users[index].send(msg.encode('utf-8')) # 해당 client에게 보냄
                except:
                    print(f'해당 {name} 학생은 존재하지 않습니다.')
        except:
            pass

    def chat_server(): # chat_server main
        try:
            while True:
                client,addr = server.accept() # accept된 사용자를 받을 때까지 대기
                users.append(client) # client가 연결했으면 users 리스트에 client 연결 서버 추가

                if client: # client에서 이름 받아
                    recv = client.recv(1024)
                    name = recv.decode('utf-8')
                    names.append(name) # 이름 리스트에 추가
                    print(f'야생의 {name}{addr} 님이 등장했다!')
                
                th = threading.Thread(target=chat_recv ,args=(client,name)) # msg recv(해당 클라이언트가 보내는 메시지를 받는) 스레드 생성해서 계속 돌아가게함
                th.start()
        except:
            pass

    c1 = threading.Thread(target=chat_server) # 사용자들이랑 서버랑 연결, 사용자들에게 메시지 받는
    c2 = threading.Thread(target=chat_send) # 사용자들에게 메시지 보내는

    c1.start()
    c2.start()

    c1.join()
    c2.join()

# ---------------- get user video  ------------------- #
def video_server(server):
	def video_recv(addr,client):
		try:
			print(f'success client connected : {addr}')

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
					
					cv2.imshow(f"FROM {addr}",frame)
					
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
    v1 = threading.Thread(target=video_server, args=(server_video1,)) # 전면캠 받을 수 있도록
    v2 = threading.Thread(target=video_server, args=(server_video2,)) # 후면캠 받을 수 있도록

    v1.start()
    v2.start()

    v1.join()
    v2.join()

# ---------------- main  ------------------- #
def main():
    t1 = threading.Thread(target=chat_server, args=(server_chat, )) # chatting server
    t2 = threading.Thread(target=video_thread) # video server

    t1.start()
    t2.start()

    t1.join()
    t2.join()

main()

server_chat.close()
server_video1.close()
server_video2.close()