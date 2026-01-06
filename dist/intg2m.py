
import asyncio
import socket
from queue import Queue


def manda( data ):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect(('192.168.0.11', 9055))
    request = data 
    if request:
        server.send(request.encode('utf8'))
        response = server.recv(1024).decode('utf8')
        print(response)
        server.close()
    return response

def procesa( datain, writer ):
    ret = manda(datain)
    return ret




async def handle_echo(reader, writer):
    """ Mantiene el socket abierto """
    while True:
        data = await reader.read(1024)
        if not data :
            break
        data_dec = data.decode()
        print(f"Llego:{data_dec}")
        res = procesa( data_dec, writer )
        writer.write( (res+"\n").encode() )
        await writer.drain()
    print("Termino conexion")
    writer.close()



    
async def guiad2m_socket_server(port):
    HOST = 'localhost'
    port = 9055
    server = await asyncio.start_server(handle_echo, HOST, port)
    async with server:
        await server.serve_forever()




async def corredor():
    await asyncio.gather (  guiad2m_socket_server(9055) )

if __name__ == '__main__' :
    asyncio.run( corredor()  )

