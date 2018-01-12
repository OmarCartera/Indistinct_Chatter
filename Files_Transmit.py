#--------------------//SERVER//-----------------------#
import socket
from thread import *
import os


def RetrFile(name, sock):
    while True:
        filename = raw_input('Enter path of filename to send: ')
        
        if os.path.isfile(filename):
            sock.send(filename + '`' + str(os.path.getsize(filename)))
            userResponse = sock.recv(2048)
            if userResponse[:2] == 'OK':
                with open(filename, 'rb') as f:
                    bytesToSend = f.read(2048)
                    sock.send(bytesToSend)
                    while bytesToSend != "":
                        bytesToSend = f.read(2048)
                        sock.send(bytesToSend)
        else:
            print("ERR ")


host = ''
port = 5000

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host,port))
s.listen(5)

print "Server Started."
while True:
    c, addr = s.accept()
    print "client connedted ip:<" + str(addr) + ">"
    start_new_thread(RetrFile, ("RetrThread", c))
     
s.close()