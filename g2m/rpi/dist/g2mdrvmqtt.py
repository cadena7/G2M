import asyncio
#import asyncio_mqtt as aiomqtt
import  aiomqtt
import json
import re


PREFIX="oan/control/2m/guiador/motores/"


async def manda( data ):
    reader,writer = await asyncio.open_connection('127.0.0.1', 9055)
    writer.write( data.encode() )
    await writer.drain()
    data_rec = await reader.read(1024)
    response = data_rec.decode()
    writer.close()
    await writer.wait_closed()
    return response

def pela_msg_egj(data):
    #res = data.replace("OK","")
    res = re.sub( "OK$","", data)
    res = res.replace('[','')
    res = res.replace(']','')
    res = res.replace("'",'')
    return res

async def publica_estado(cliente , datos):
    if 'ERROR' in datos:
        await asyncio.sleep(0.01)
        return
    res = json.dumps( datos )
    await cliente.publish(PREFIX+"status", res)


async def pide_estado():
    res = pela_msg_egj( await manda("EGJ\n") )
    try:
        data = json.loads( res )
    except json.decoder.JSONDecodeError as error:
        data = {"ERROR": True}
        print("ERROR en el estado, ", error)
    print("Llego ", data)
    return data


async def com_con_guiador(cola):
    i=0
    print("inicia com con guiador")
    client = await cola.get()
    while True:
        await asyncio.sleep(0.1)
        i = i +1
        if i > 10 :
            i = 0
            data = await pide_estado()
            await publica_estado(client,data)


def msg_a_json( msg ):
    try:
        data = json.loads( msg.decode() )
    except json.decoder.JSONDecodeError as error:
        data = {}
        print("Error en el json, ", error)
    return data

async def procesa_msg_mueve( cliente, msg):
    await asyncio.sleep(.01)
    data = msg_a_json( msg )
    print("Procesa msg mover", data)
    res = ""
    for nom in ('AR', 'DEC','FOCO','ZOOM') :
        if nom in data :
            res += " %s= %f" % (nom, data[nom])
    if len(res) <= 1 :
        return
    await manda( res )

async def procesa_msg_mueve_relativo(cliente,  msg ):
    await asyncio.sleep(.01)
    data = msg_a_json( msg )
    res = ""
    cmds = ('AR+', 'DEC+', 'FOC+', 'Z+')
    for ind, nom in enumerate( ( 'AR', 'DEC','FOCO','ZOOM' )) :
        if nom in data :
            res += " PON_INC_%s= %.2f  %s " % (nom, data[nom], cmds[ind])
    if len(res) <= 1 :
        return
    await pide_estado()
    await manda( res )

        
async def procesa_msg_inicia_ejes(cliente, msg ):
    await asyncio.sleep(.01)
    data = msg_a_json( msg )
    res = ""
    for nom in ('AR', 'DEC','FOCO','ZOOM') :
        if nom in data :
            res += " BUSCA_CENTRO_%s" % (nom)
    if len(res) <= 1:
        return
    await manda( res )

async def procesa_msg_pide_estado(cliente, msg ):
    dat = await pide_estado()
    await publica_estado(cliente,dat)


async def procesa_msg_cambia_params(cliente, msg ):
    await asyncio.sleep(.01)
    data = msg_a_json( msg )
    res = ""
    if "ESC_PLACA" in data :
        res += " ESC_PLACA= %f " % (data['ESC_PLACA'])
    if "RESTABLECE_BANDERA_ERR" in data :
        res += " RESTABLECE_BANDERA_ERR "
    if "CANCELA" in data :
        cuales = data["CANCELA"]
        for item in ("AR", "DEC","FOCO","ZOOM"):
            if item in cuales :
                res += " CANCELA_INICIO_" + item
    if len(res) <= 1 :
        return
    await manda( res )


async def procesa_msg_def_coords( cliente, msg ):
    await asyncio.sleep(.01)
    data = msg_a_json( msg )
    res = ""
    for nom in ('AR', 'DEC', 'FOCO', 'ZOOM' ):
        if nom in data :
            res += "DEF_CERO_%s " % ( nom )
    if len(res) <= 1:
        return
    await manda( res )


async def listen(cola):
    topic_y_manejadores = (
        ( PREFIX+"mueve",procesa_msg_mueve ),
        ( PREFIX+"mueve_relativo",  procesa_msg_mueve_relativo ),
        ( PREFIX+"dame_estado", procesa_msg_pide_estado ),
        ( PREFIX+"inicializa_ejes",  procesa_msg_inicia_ejes ),
        ( PREFIX+"define_coordenadas",  procesa_msg_def_coords ),
        ( PREFIX+"cambia_params",  procesa_msg_cambia_params )
    )

    async with aiomqtt.Client("192.168.0.1") as client:
        await cola.put( client )
        async with client.messages() as messages:
            topics = []
            manejadores = []
            for item in topic_y_manejadores :
                await client.subscribe( item[0] )
                topics.append( item[0] )
                manejadores.append( item[1] )

            async for message in messages:
                print(message.topic)
                print(message.payload.decode())
                for ind, topic in enumerate(topics) :
                    if message.topic.matches( topic ) :
                        await manejadores[ind]( client, message.payload )



async def main(cola):
    # Wait for messages in (unawaited) asyncio task
    loop = asyncio.get_event_loop()
    task = loop.create_task(listen(cola))
    # This will still run!
    print("Magic!")
    # If you don't await the task here the program will simply finish.
    # However, if you're using an async web framework you usually don't have to await
    # the task, as the framework runs in an endless loop.
    await task


async def corredor():
    cola =  asyncio.Queue()
    await asyncio.gather (  main(cola), com_con_guiador(cola)  )

if __name__ == "__main__" :
    asyncio.run(corredor())
