#!/bin/python
import signal
import os
import sys
import socket
import hashlib
import select
import time


HOST = 'localhost'
PORT = int(sys.argv[1])
#list that stores all the client sockets
SOCKET_LIST = []

#list that stores clients who logged in
logged_in = []

#lists of channels and usernames
channels = []
usernames = {}

#Use this variable for your loop
server_quit = False

#Do not modify or remove this handler
def quit_gracefully(signum, frame):
    global server_quit
    server_quit = True

#function that sends message to clients through socket
def broadcast(s, message): 
    try:
        s.send(message.encode())
    except:
        s.close()
        if s in SOCKET_LIST:
            SOCKET_LIST.remove(s)
        if s in logged_in:
            logged_in.remove(s)
        usernames.pop(s, None)

#function that handles login or register commands
def login_register(s, cmd):
    elements = cmd.split()

    #error case when number of arguments is incorrect
    if len(elements) != 3:
        return 0

    
    if elements[0] == "REGISTER":
        b_password = elements[2].encode()

        #checking if the user is already registered
        with open("passwords.csv") as f1:
            for line in f1.readlines():
                if line.split(",")[0] == elements[1]:
                    return 0
        
        #if the user is not registered, the username and hashed password is written to the database
        with open("passwords.csv", "a") as f:
            f.write("{},{}\n".format(elements[1], hashlib.sha256(b_password).hexdigest()))
            return elements[1]


    elif elements[0] == "LOGIN":
        b_password = elements[2].encode()
        hashed_password = hashlib.sha256(b_password).hexdigest()
        with open("passwords.csv") as f:
            data = f.readlines()

        for i in range(len(data)):
            entry = data[i].rstrip("\n").split(",")

            #if one of the hashed passwords matches the hashed version of the password in the command
            if entry[1] == hashed_password:

                #checking if the user is already logged in
                if s in logged_in:
                    return 0
        
                logged_in.append(s)
                return elements[1]

    return 0


def create(s, cmd):
    elements = cmd.split()

    #error case when number of arguments is incorrect
    if len(elements) != 2:
        return 0

    #checking if the channel already exists
    for i in range(len(channels)):
        if channels[i][0] == elements[1]:
            return 0
    channels.append([elements[1]])
    return 1
        
def join(s, cmd):
    elements = cmd.split()

    #error case when number of arguments is incorrect
    if len(elements) != 2:
        return 0

    #checking if the user already joined the channel and adding the user if not already
    for i in range(len(channels)):
        if channels[i][0] == elements[1]:
            if s in channels[i]:
                return 0
            else:
                channels[i].append(s)
                return 1
    return 0


def say(s, cmd):
    elements = cmd.split()
    for i in range(len(channels)):
        #making sure that the user is in the channel and the channel exists
        if channels[i][0] == elements[1] and s in channels[i]:
            #formulating a message using the username list
            msg = ' '.join(elements[2:])
            username = usernames[s]
            recv = "RECV {} {} {}\n".format(username, elements[1], msg)

            #broadcasting the message to every user in the channel
            for socket in channels[i][1:]:   
                broadcast(socket, recv)

            return

    #error case when the user is not in the channel or the channel doesn't exist
    broadcast(s, "User not in channel\n")
        


def run():
    #Do not modify or remove this function call
    signal.signal(signal.SIGINT, quit_gracefully)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        #setting up server
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        server.bind((HOST, PORT))
        server.listen()
        SOCKET_LIST.append(server)

        #loops while server is running
        while server_quit == False:

            readable, writable, exceptional = select.select(SOCKET_LIST, [], [], 2)
            
            #iterating through every readable socket
            for s in readable:

                #this indicates that a new client is connecting, they are then added to the list of client sockets
                if s == server:
                    connection, client_address = s.accept()
                    SOCKET_LIST.append(connection)

                else:
                    try:

                        data = s.recv(1024)

                        if data:
                            #if the data recevied is not VOID, it is decoded and the command is processed
                            entry = data.decode()
                            type = entry.split()[0]
                            
                            #channel command that broadcasts every single channel, channel can always be called no matter the login status
                            if type == "CHANNELS":
                                names = []
                                for i in range(len(channels)):
                                    names.append(channels[i][0])
                                broadcast(s, "RESULT CHANNELS {}\n".format(', '.join(sorted(names))))

                            #processing the valid commands for a user that's logged in
                            if s in logged_in:
                                if type == "CREATE":
                                    success = create(s, entry)
                                    broadcast(s, "RESULT {} {}\n".format(entry.rstrip('\n'), success))
                                    
                                elif type == "JOIN":
                                    success = join(s, entry)
                                    broadcast(s, "RESULT {} {}\n".format(entry.rstrip('\n'), success))
                                    
                                elif type == "SAY":
                                    say(s, entry)
                    
                                elif type == "LOGIN":
                                    broadcast(s, "RESULT LOGIN 0\n")
      
                            #processing the valid commands for a user that's not logged in
                            else:
                                if type == "LOGIN" or type == "REGISTER":

                                    username = login_register(s, entry)
                                    if username == 0:
                                        success = 0
                                        
                                    else:
                                        usernames[s] = username
                                        success = 1
                                    
                                    broadcast(s, "RESULT {} {}\n".format(type, success))

                                    
                            
                            
                        #if the data is VOID, the client socket is closed and it is removed from all lists
                        else:
                            s.close()
                            if s in SOCKET_LIST:
                                SOCKET_LIST.remove(s)
                            if s in logged_in:
                                logged_in.remove(s)
                            usernames.pop(s, None)

                    except:
                        continue

        exit()

if __name__ == '__main__':
    f = open("passwords.csv", "w")
    f.close()
    run()



