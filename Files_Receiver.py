#----------------------//CLIENT//-------------------------------
import socket

def Main():
    host = '192.168.1.9'
    port = 3245

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    s.connect((host, port))


    while 1:
        print 'Waiting for a file'
        
        data = s.recv(2048)
        filename = data.partition('`')[0]
        filesize = int(data[data.index('`')+1:])

        message = raw_input("File exists, " + str(filesize) +"Bytes, download? (Y/N)? -> ")
        if message == 'y':
            s.send('OK')
            with open('new_' + filename, 'wb') as f:
                data = s.recv(2048)
                totalRecv = len(data)
                f.write(data)
                while totalRecv < filesize:
                    data = s.recv(2048)
                    totalRecv += len(data)
                    f.write(data)
                    print "{0:.2f}".format((totalRecv/float(filesize))*100)+ "% Done"
                print "Download Completed!"
            f.close()
            #else:
                #print "File Does Not Exist!"


    s.close()
    
if __name__ == '__main__':
    Main()





