#!/usr/bin/env python3
import time
import asyncio
import aiomqtt
import json
import re

# ===================== CONFIG (AJUSTA ESTO) =====================
# de preferencia mayor a 5s para que inicien otros servicios primero
time.sleep(7)

PREFIX = "oan/control/2m/guiador/motores/"   # <-- AJUSTA a tu Telescopio
BROKER_HOST = "192.168.0.237"                 # <-- AJUSTA a tu broker MQTT
BROKER_PORT = 1883

TCP_HOST = "127.0.0.1"
TCP_PORT = 9055
# ================================================================


# ===================== TCP hacia driver =====================
async def manda(data: str) -> str:
    try:
        reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
        writer.write(data.encode())
        await writer.drain()
        data_rec = await reader.read(1024)
        response = data_rec.decode()
        writer.close()
        await writer.wait_closed()
        return response
    except Exception as e:
        print(f"[TCP] Error en manda: {e}")
        return "ERROR"


def pela_msg_egj(data: str) -> str:
    try:
        res = re.sub("OK$", "", data)
        res = res.replace('[', '').replace(']', '').replace("'", '')
        return res
    except Exception as e:
        print(f"[PARSE] Error en pela_msg_egj: {e}")
        return ""


async def pide_estado() -> dict:
    try:
        res = pela_msg_egj(await manda("EGJ\n"))
        return json.loads(res)
    except json.decoder.JSONDecodeError as error:
        print("[ESTADO] JSONDecodeError:", error)
        return {"ERROR": True}
    except Exception as e:
        print(f"[ESTADO] Error en pide_estado: {e}")
        return {"ERROR": True}


# ===================== MQTT helpers =====================
async def publica_estado(cliente, datos: dict) -> None:
    # Si el estado viene malo, no publiques
    if not isinstance(datos, dict) or 'ERROR' in datos:
        return
    try:
        await cliente.publish(PREFIX + "status", json.dumps(datos))
    except (aiomqtt.MqttError, OSError) as e:
        # IMPORTANTE: propaga para que com_con_guiador rompa y espere client nuevo
        print(f"[MQTT] publish status falló: {e}")
        raise
    except Exception as e:
        # Otros errores no necesariamente implican desconexión
        print(f"[MQTT] publish status falló (otro): {e}")


def msg_a_json(msg: bytes) -> dict:
    try:
        return json.loads(msg.decode())
    except json.decoder.JSONDecodeError as error:
        print("[JSON] Error en el json:", error)
        return {}
    except Exception as e:
        print(f"[JSON] Error en msg_a_json: {e}")
        return {}


# ===================== Procesadores de mensajes =====================
async def procesa_msg_mueve(cliente, msg: bytes):
    await asyncio.sleep(0.1)
    data = msg_a_json(msg)
    res = ""
    for nom in ('AR', 'DEC', 'FOCO', 'ZOOM'):
        if nom in data:
            res += " %s= %f" % (nom, data[nom])
    if len(res) <= 1:
        return
    await manda(res)


async def procesa_msg_mueve_relativo(cliente, msg: bytes):
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


async def procesa_msg_inicia_ejes(cliente, msg: bytes):
    await asyncio.sleep(0.1)
    data = msg_a_json(msg)
    res = ""
    for nom in ('AR', 'DEC', 'FOCO', 'ZOOM'):
        if nom in data:
            res += " BUSCA_CENTRO_%s" % (nom)
    if len(res) <= 1:
        return
    await manda(res)


async def procesa_msg_pide_estado(cliente, msg: bytes):
    dat = await pide_estado()
    await publica_estado(cliente, dat)


async def procesa_msg_cambia_params(cliente, msg: bytes):
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


async def procesa_msg_def_coords(cliente, msg: bytes):
    await asyncio.sleep(0.1)
    data = msg_a_json(msg)
    res = ""
    for nom in ('AR', 'DEC', 'FOCO', 'ZOOM'):
        if nom in data:
            res += "DEF_CERO_%s " % (nom)
    if len(res) <= 1:
        return
    await manda(res)


# ===================== MQTT listener con reconexión =====================
async def listen(client_queue: asyncio.Queue):
    topic_y_manejadores = (
        (PREFIX + "mueve", procesa_msg_mueve),
        (PREFIX + "mueve_relativo", procesa_msg_mueve_relativo),
        (PREFIX + "dame_estado", procesa_msg_pide_estado),
        (PREFIX + "inicializa_ejes", procesa_msg_inicia_ejes),
        (PREFIX + "define_coordenadas", procesa_msg_def_coords),
        (PREFIX + "cambia_params", procesa_msg_cambia_params),
    )
    topics, manejadores = zip(*topic_y_manejadores)

    backoff = 1.0
    backoff_max = 30.0

    while True:
        try:
            print(f"[MQTT] Conectando a {BROKER_HOST}:{BROKER_PORT} ...")
            async with aiomqtt.Client(BROKER_HOST, port=BROKER_PORT, keepalive=20) as client:
                print("[MQTT] Conectado.")
                backoff = 1.0

                # Suscripción (primero dejamos listo el client)
                for t in topics:
                    await client.subscribe(t)
                print("[MQTT] Suscrito a tópicos.")

                # Ahora sí: publica el cliente “vigente” (solo el más reciente)
                while not client_queue.empty():
                    try:
                        client_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                await client_queue.put(client)

                async with client.messages() as messages:
                    async for message in messages:
                        for ind, t in enumerate(topics):
                            if message.topic.matches(t):
                                try:
                                    await manejadores[ind](client, message.payload)
                                except Exception as e:
                                    # Aísla fallas por handler (robusto 24/7)
                                    print(
                                        f"[MQTT] Error en handler de {t}: {e}")
                                break

        except (aiomqtt.MqttError, OSError) as e:
            print(
                f"[MQTT] Desconectado / no disponible: {e}. Reintento en {backoff:.1f}s")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2.0, backoff_max)
        except Exception as e:
            print(
                f"[MQTT] Error inesperado en listen(): {e}. Reintento en {backoff:.1f}s")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2.0, backoff_max)


# ===================== Loop de estado periódico =====================
async def com_con_guiador(client_queue: asyncio.Queue):
    print("[GUIADOR] Inicia com_con_guiador (publica estado periódico)")

    while True:
        # Espera cliente conectado (o reconectado)
        client = await client_queue.get()
        print("[GUIADOR] Cliente MQTT activo recibido.")
        i = 0

        while True:
            try:
                await asyncio.sleep(0.1)
                i += 1
                if i > 10:
                    i = 0
                    data = await pide_estado()
                    await publica_estado(client, data)

            except (aiomqtt.MqttError, OSError) as e:
                # Si cayó MQTT (o publish lanzó "not connected"), sal y espera al nuevo client
                print(
                    f"[GUIADOR] MQTT cayó mientras publicaba: {e}. Esperando reconexión...")
                break
            except Exception as e:
                print(f"[GUIADOR] Error en ciclo com_con_guiador: {e}")


# ===================== MAIN =====================
async def corredor():
    client_queue = asyncio.Queue(maxsize=1)
    await asyncio.gather(
        listen(client_queue),
        com_con_guiador(client_queue),
    )


if __name__ == "__main__":
    try:
        asyncio.run(corredor())
    except Exception as e:
        print(f"[MAIN] Error fatal: {e}")
