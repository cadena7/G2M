#!/usr/bin/python
import socket
import threading
import socketserver
import sys,os
import time
from subprocess import *
import shlex


import instruccionesguiador as itd

# Esperar 4 segundos antes de ejecutar el resto del programa
time.sleep(4)




def maneja_conexion(dat):
    sal = itd.interpreta(dat)
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
        if ( r ):self.request.send( (s+"OK\n").encode() )
        else: self.request.send(b'ERR CMD\n')





class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


import signal


def Exit_gracefully(signal, frame):
    #... log exiting information ...
    #... close any open files ...
    print( "Saliendo graciosamente" )
    sys.exit(0)



if __name__ == "__main__":
    HOST, PORT = "", 9055
    signal.signal(signal.SIGINT, Exit_gracefully)

    itd.inicia()
    hebra1 = threading.Thread(target=itd.hebra_busca_ceros)
    hebra1.start()
    # Create the server, binding to localhost on port 9999

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    #server_thread.setDaemon(True)
    server_thread.daemon=True
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
