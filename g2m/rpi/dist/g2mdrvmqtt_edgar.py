import time
import asyncio
import aiomqtt
import json
import re

# Esperar 4 segundos antes de ejecutar el resto del programa
time.sleep(4)

PREFIX = "oan/control/2m/guiador/motores/"


async def manda(data):
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', 9055)
        writer.write(data.encode())
        await writer.drain()
        data_rec = await reader.read(1024)
        response = data_rec.decode()
        writer.close()
        await writer.wait_closed()
        return response
    except Exception as e:
        print(f"Error en manda: {e}")
        return "ERROR"


def pela_msg_egj(data):
    try:
        res = re.sub("OK$", "", data)
        res = res.replace('[', '').replace(']', '').replace("'", '')
        return res
    except Exception as e:
        print(f"Error en pela_msg_egj: {e}")
        return ""


async def publica_estado(cliente, datos):
    try:
        if 'ERROR' in datos:
            await asyncio.sleep(0.1)
            return
        res = json.dumps(datos)
        await cliente.publish(PREFIX + "status", res)
    except Exception as e:
        print(f"Error en publica_estado: {e}")


async def pide_estado():
    try:
        res = pela_msg_egj(await manda("EGJ\n"))
        data = json.loads(res)
    except json.decoder.JSONDecodeError as error:
        data = {"ERROR": True}
        print("ERROR en el estado,", error)
    except Exception as e:
        data = {"ERROR": True}
        print(f"Error en pide_estado: {e}")
    print("Llego", data)
    return data


async def com_con_guiador(cola):
    i = 0
    print("Inicia com con guiador")
    try:
        client = await cola.get()
        while True:
            await asyncio.sleep(0.1)
            i += 1
            if i > 10:
                i = 0
                try:
                    data = await pide_estado()
                    await publica_estado(client, data)
                except Exception as e:
                    print(f"Error en ciclo com_con_guiador: {e}")
    except Exception as e:
        print(f"Error en com_con_guiador: {e}")


def msg_a_json(msg):
    try:
        data = json.loads(msg.decode())
    except json.decoder.JSONDecodeError as error:
        data = {}
        print("Error en el json,", error)
    except Exception as e:
        data = {}
        print(f"Error en msg_a_json: {e}")
    return data


async def procesa_msg_mueve(cliente, msg):
    try:
        await asyncio.sleep(0.1)
        data = msg_a_json(msg)
        print("Procesa msg mover", data)
        res = ""
        for nom in ('AR', 'DEC', 'FOCO', 'ZOOM'):
            if nom in data:
                res += " %s= %f" % (nom, data[nom])
        if len(res) <= 1:
            return
        await manda(res)
    except Exception as e:
        print(f"Error en procesa_msg_mueve: {e}")


async def procesa_msg_mueve_relativo(cliente, msg):
    try:
        await asyncio.sleep(0.1)
        data = msg_a_json(msg)
        res = ""
        cmds = ('AR+', 'DEC+', 'FOC+', 'Z+')
        for ind, nom in enumerate(('AR', 'DEC', 'FOCO', 'ZOOM')):
            if nom in data:
                res += " PON_INC_%s= %.2f  %s " % (nom, data[nom], cmds[ind])
        if len(res) <= 1:
            return
        await pide_estado()
        await manda(res)
    except Exception as e:
        print(f"Error en procesa_msg_mueve_relativo: {e}")


async def procesa_msg_inicia_ejes(cliente, msg):
    try:
        await asyncio.sleep(0.1)
        data = msg_a_json(msg)
        res = ""
        for nom in ('AR', 'DEC', 'FOCO', 'ZOOM'):
            if nom in data:
                res += " BUSCA_CENTRO_%s" % (nom)
        if len(res) <= 1:
            return
        await manda(res)
    except Exception as e:
        print(f"Error en procesa_msg_inicia_ejes: {e}")


async def procesa_msg_pide_estado(cliente, msg):
    try:
        dat = await pide_estado()
        await publica_estado(cliente, dat)
    except Exception as e:
        print(f"Error en procesa_msg_pide_estado: {e}")


async def procesa_msg_cambia_params(cliente, msg):
    try:
        await asyncio.sleep(0.1)
        data = msg_a_json(msg)
        res = ""
        if "ESC_PLACA" in data:
            res += " ESC_PLACA= %f " % (data['ESC_PLACA'])
        if "RESTABLECE_BANDERA_ERR" in data:
            res += " RESTABLECE_BANDERA_ERR "
        if "CANCELA" in data:
            cuales = data["CANCELA"]
            for item in ("AR", "DEC", "FOCO", "ZOOM"):
                if item in cuales:
                    res += " CANCELA_INICIO_" + item
        if len(res) <= 1:
            return
        await manda(res)
    except Exception as e:
        print(f"Error en procesa_msg_cambia_params: {e}")


async def procesa_msg_def_coords(cliente, msg):
    try:
        await asyncio.sleep(0.1)
        data = msg_a_json(msg)
        res = ""
        for nom in ('AR', 'DEC', 'FOCO', 'ZOOM'):
            if nom in data:
                res += "DEF_CERO_%s " % (nom)
        if len(res) <= 1:
            return
        await manda(res)
    except Exception as e:
        print(f"Error en procesa_msg_def_coords: {e}")


async def listen(cola):
    try:
        topic_y_manejadores = (
            (PREFIX + "mueve", procesa_msg_mueve),
            (PREFIX + "mueve_relativo", procesa_msg_mueve_relativo),
            (PREFIX + "dame_estado", procesa_msg_pide_estado),
            (PREFIX + "inicializa_ejes", procesa_msg_inicia_ejes),
            (PREFIX + "define_coordenadas", procesa_msg_def_coords),
            (PREFIX + "cambia_params", procesa_msg_cambia_params)
        )

        async with aiomqtt.Client("192.168.0.1") as client:
            await cola.put(client)
            async with client.messages() as messages:
                topics, manejadores = zip(*topic_y_manejadores)
                for topic in topics:
                    await client.subscribe(topic)

                async for message in messages:
                    print(message.topic)
                    print(message.payload.decode())
                    for ind, topic in enumerate(topics):
                        if message.topic.matches(topic):
                            try:
                                await manejadores[ind](client, message.payload)
                            except Exception as e:
                                print(f"Error en handler de {topic}: {e}")
    except Exception as e:
        print(f"Error en listen: {e}")


async def main(cola):
    try:
        loop = asyncio.get_event_loop()
        task = loop.create_task(listen(cola))
        print("Magic!")
        await task
    except Exception as e:
        print(f"Error en main: {e}")


async def corredor():
    cola = asyncio.Queue()
    try:
        await asyncio.gather(main(cola), com_con_guiador(cola))
    except Exception as e:
        print(f"Error en corredor: {e}")

if __name__ == "__main__":
    try:    
        # Ejecutar el programa principal
        asyncio.run(corredor())

    except Exception as e:
        print(f"Error en ejecución principal: {e}")
