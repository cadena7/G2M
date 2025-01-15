#!/usr/bin/python
import socket
import threading
import socketserver
import sys
import os
import time
from subprocess import *
import shlex
import signal
import instruccionesguiador as itd

# Esperar 4 segundos antes de ejecutar el resto del programa
time.sleep(4)

def maneja_conexion(dat):
    try:
        sal = itd.interpreta(dat)
        return True, sal
    except Exception as e:
        print(f"Error al manejar la conexión: {e}")
        return False, "Error interno"

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            self.data = str(self.request.recv(1024), 'UTF-8')
            print(f"Datos recibidos: {self.data}")
            datal = shlex.split(self.data)
            data1 = ' '.join(datal)
            r, s = maneja_conexion(data1)
            if r:
                self.request.send((s + "OK\n").encode())
            else:
                self.request.send(b'ERR CMD\n')
        except Exception as e:
            print(f"Error en el manejo de la solicitud: {e}")
            self.request.send(b'ERR INTERNAL\n')

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

def Exit_gracefully(signal, frame):
    print("Saliendo graciosamente")
    os._exit(0)

if __name__ == "__main__":
    HOST, PORT = "", 9055
    signal.signal(signal.SIGINT, Exit_gracefully)
    signal.signal(signal.SIGTERM, Exit_gracefully)

    try:
        print("Iniciando instrucciones del guiador")
        itd.inicia()

        # Hebra para búsqueda de ceros
        hebra1 = threading.Thread(target=itd.hebra_busca_ceros, daemon=True)
        hebra1.start()

        # Crear el servidor
        server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
        ip, port = server.server_address
        print(f"Servidor iniciado en {ip}:{port}")

        # Hilo del servidor
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        refresca = 60 * 5 * 8
        t = 0

        while True:
            time.sleep(0.55)
            t += 1
            if t > refresca:
                print(f"Refrescando en {time.asctime(time.localtime())}")
                t = 0

    except Exception as e:
        print(f"Error fatal: {e}")
    finally:
        print("Deteniendo el servidor")
        server.shutdown()
        server.server_close()
