
import sys
import time
import threading
import socketserver
from  socket import *
import shlex


def manda( str1 , arch= "/dev/shm/com/servobb/socket"):
    """ """
    #arch = "/usr/local/instrumentacion/com/servobb/socket"
    try:
        s = socket(AF_UNIX, SOCK_STREAM)
        s.connect(arch)
    except IOError:
        print( "connect" )
        s.close()
        s = None

    if s is None:
        print( 'could not open socket' )
        return "Nada"

    ## s.settimeout(.1)
    s.send( str1.encode('utf-8'  ) )

    total_data=[]
    while True:
        data = s.recv(1024)
        if not data:
            break
        total_data.append(data)
        ##print "DATA",total_data
        td = b''.join(total_data)
        if b'Ok' in td:
            break
    total_data = b''.join(total_data)
    s.close()
    data1 = str( total_data , 'UTF-8')
    ## data1 = total_data.replace("=", " ")
    ##print "DATA1",data1
    return data1



def maneja_conexion(dat):
    sal = manda(dat)
    return True,sal




class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = str( self.request.recv(1024), 'UTF-8' )
        ## print "%s wrote:" % self.client_address[0]
        print( self.data )
        datal = shlex.split(self.data)
        data1 = ' '.join(datal)
        print( data1 )
        r,s = maneja_conexion( data1 )
        # just send back the same data, but upper-cased
        # self.request.send(self.data.upper())
        if  r :
            self.request.send( (s+"\n").encode() )
        else:
            self.request.send(b'ERR CMD\n')


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

import signal


def Exit_gracefully(signal, frame):
    #... log exiting information ...
    #... close any open files ...
    print( "Saliendo graciosamente" )
    sys.exit(0)

    
if __name__ == "__main__":
    HOST, PORT = "", 9095
    signal.signal(signal.SIGINT, Exit_gracefully)
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.setDaemon(True)
    server_thread.start()
    t=0
    refresca= 60*5*8

    while True:
        time.sleep( 0.55 )
        ## has_timeout()
        t = t+1
        if t > refresca :
            print( time.asctime(time.localtime()) )
            t = 0
