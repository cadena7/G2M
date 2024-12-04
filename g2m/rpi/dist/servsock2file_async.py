"""
Prog intermediario entre el servidor del guiador 2m y la interfaz de usuario 
del guiador2m (version GTK 1.2 ui_motores )
La interfaz abre el socket y lo mantiene abierto todo el tiempo de ahi la necesidad
de este intermediario.
"""
import asyncio
import socket
from queue import Queue


estadoGlobal = {
    "BUSCA_CENTRO_AR": False,
    "BUSCA_CENTRO_DEC": False,
    "BUSCA_CENTRO_FOCO": False,
    "BUSCA_CENTRO_ZOOM": False,
    "ERROR_CENTRO_AR": False,
    "ERROR_CENTRO_DEC": False,
    "ERROR_CENTRO_FOCO": False,
    "ERROR_CENTRO_ZOOM": False
    }

def manda_a_sock_arch( data , arch= "/dev/shm/com/servobb/socket"):
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.connect(arch)
    request = data
    if request:
        server.send(request.encode('utf8'))
        response = server.recv(1024).decode('utf8')
        print(response)
        server.close()
    return response

def manda( data ):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect(('localhost', 9055))
    request = data 
    if request:
        server.send(request.encode('utf8'))
        response = server.recv(1024).decode('utf8')
        print(response)
        server.close()
    return response

def procesa( datain, writer ):
    ## ret = manda_a_sock_arch(datain)
    ret = manda( datain )
    return ret


def checa_estado_inicios():
    return not estadoGlobal["BUSCA_CENTRO_AR"] and \
        not estadoGlobal["BUSCA_CENTRO_DEC"] and \
        not estadoGlobal["BUSCA_CENTRO_ZOOM"] and \
        not estadoGlobal["BUSCA_CENTRO_FOCO"]



async def checa_centrado(reader, writer ):

    while True:

        print("Espera un seg")
        await asyncio.sleep(1)

        #data = await reader.read(1024)
        res = procesa( "EG?" , writer)
        writer.write( (res+"\n").encode() )
        await writer.drain()
        print("<<flush>>")


        if checa_estado_inicios() :
            print("Ya acabo buscar centros")
            break

        if estadoGlobal["BUSCA_CENTRO_AR"] :
            if res.find("INICIANDO_AR") != -1 :
                pass
            else:
                estadoGlobal["BUSCA_CENTRO_AR"] = False

        if estadoGlobal["BUSCA_CENTRO_DEC"] :
            if res.find("INICIANDO_DEC") != -1 :
                pass
                #writer.write(b"BUSCANDO DEC\n")
            else:
                estadoGlobal["BUSCA_CENTRO_DEC"] = False

        if estadoGlobal["BUSCA_CENTRO_FOCO"] :
            if res.find("INICIANDO_FOCO") != -1 :
                pass
            else:
                estadoGlobal["BUSCA_CENTRO_FOCO"] = False


        if estadoGlobal["BUSCA_CENTRO_ZOOM"] :
            if res.find("INICIANDO_ZOOM") != -1 :
                pass
            else:
                estadoGlobal["BUSCA_CENTRO_ZOOM"] = False


                


async def handle_echo(reader, writer):
    """ Mantiene el socket abierto """
    print("Inicia serv")
    while True:
        data = await reader.read(1024)
        if not data :
            break
        data_dec = data.decode()
        if data_dec.find("BUSCA_CENTRO_AR" ) != -1 :
            estadoGlobal["BUSCA_CENTRO_AR"] = True
        if data_dec.find("BUSCA_CENTRO_DEC" ) != -1 :
            estadoGlobal["BUSCA_CENTRO_DEC"] = True
        if data_dec.find("BUSCA_CENTRO_FOCO" ) != -1 :
            estadoGlobal["BUSCA_CENTRO_FOCO"] = True
        if data_dec.find("BUSCA_CENTRO_ZOOM" ) != -1 :
            estadoGlobal["BUSCA_CENTRO_ZOOM"] = True

        print(f"Llego:{data_dec}")
        res = procesa( data_dec , writer )
        writer.write( (res+"\n").encode() )
        await writer.drain()

        if not checa_estado_inicios() :
            await checa_centrado(reader,writer)


    print("Termino conexion")
    writer.close()





async def guiad2m_socket_server(port_sock):
    HOST = ''
    port = port_sock
    server = await asyncio.start_server(handle_echo, HOST, port)
    async with server:
        await server.serve_forever()




async def corredor():
    await asyncio.gather (  guiad2m_socket_server(9056) )

if __name__ == '__main__' :
    print("Prog serv")
    asyncio.run( corredor()  )
