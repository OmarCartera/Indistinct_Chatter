import socket

host=''
port=8080


s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host,port))
s.listen(1)
conn, addr = s.accept()

string = bytes('','UTF-8')


while True: 

    d = conn.recv(640*480)

    if not d:
        print ("break")
        break

    else:

        string += d

    pil_image = Image.fromstring("RGB",(352,288),string)
    #(352,288) is the return of cam.get_size()