import socket
import sys
import time

HOST = "localhost"
PORT = int(sys.argv[1])
file = sys.argv[2]

with open(file, "r") as f:
    cmds = f.readlines()
    

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    i = 0
    while i < len(cmds):
        msg = cmds[i].rstrip('\n')
        s.send(msg.encode())
        data = s.recv(1024)
        print(data.decode().rstrip('\n'))
        i += 1
    time.sleep(0.5)