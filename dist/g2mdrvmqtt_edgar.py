#!/usr/bin/env python3
import time
import asyncio
import aiomqtt
import json
import os
import re

# ===================== CONFIG (AJUSTA ESTO) =====================
# de preferencia mayor a 5s para que inicien otros servicios primero
RETARDO_INICIO_S = 7

PREFIX = "oan/control/2m/guiador/motores/"    # <-- AJUSTA a tu Telescopio
BROKER_HOST = "192.168.0.237"                 # <-- AJUSTA a tu broker MQTT
BROKER_PORT = 1883

TCP_HOST = "127.0.0.1"
TCP_PORT = 9055

DEF_LIMITES_CONF_ARCH = "/home/guiador/config/limites-motores-guiador-2m.json"
DEF_CERO_OFFSETS_ARCH = "/home/guiador/config/offsets-cero-mecanicos-2m.json"
POSICION_VALIDA_TIMEOUT_S = 5.0
MARGEN_LIMITE_AR_DEC = 10.0
MARGEN_LIMITE_FOCO = 3.0
EJES_GUIADOR = ("AR", "DEC", "FOCO")

LIMITES_CONFIG_DEFAULT = {
    "version": "g2m-defaults",
    "AR": {
        "unidad": "arcsec",
        "switch_min": -1911.02,
        "switch_max": 1744.23,
        "margen": MARGEN_LIMITE_AR_DEC,
    },
    "DEC": {
        "unidad": "arcsec",
        "switch_min": -2482.26,
        "switch_max": 1116.11,
        "margen": MARGEN_LIMITE_AR_DEC,
    },
    "FOCO": {
        "unidad": "mm",
        "switch_min": -49.39,
        "switch_max": 76.31,
        "margen": MARGEN_LIMITE_FOCO,
    },
}
# ================================================================


def _normaliza_config_limites(data):
    config = {"version": str(data.get("version", "sin-version"))}
    for eje in EJES_GUIADOR:
        eje_data = data[eje]
        switch_min = float(eje_data["switch_min"])
        switch_max = float(eje_data["switch_max"])
        margen = float(eje_data["margen"])
        if switch_min >= switch_max:
            raise ValueError(f"switch_min >= switch_max en {eje}")
        if margen < 0:
            raise ValueError(f"margen negativo en {eje}")
        if switch_min + margen >= switch_max - margen:
            raise ValueError(f"margen deja rango vacio en {eje}")
        config[eje] = {
            "unidad": str(eje_data["unidad"]),
            "switch_min": switch_min,
            "switch_max": switch_max,
            "margen": margen,
        }
    return config


def carga_config_limites(archivo=None):
    if archivo is None:
        archivo = DEF_LIMITES_CONF_ARCH
    try:
        with open(archivo, "r", encoding="ascii") as arch:
            return _normaliza_config_limites(json.load(arch))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"[LIMITES] Config limites invalida; usando defaults: {exc}")
        return _normaliza_config_limites(LIMITES_CONFIG_DEFAULT)


def limites_desde_config(config):
    return {
        eje: (
            config[eje]["switch_min"] + config[eje]["margen"],
            config[eje]["switch_max"] - config[eje]["margen"],
        )
        for eje in EJES_GUIADOR
    }


def switches_desde_config(config):
    return {
        eje: (config[eje]["switch_min"], config[eje]["switch_max"])
        for eje in EJES_GUIADOR
    }


def configura_limites(archivo=None):
    global LIMITES_CONFIG
    global LIMITES_SWITCHES_MECANICOS_ABS
    global LIMITES_MECANICOS_ABS
    global LIMITES_CONF_VERSION
    LIMITES_CONFIG = carga_config_limites(archivo)
    LIMITES_SWITCHES_MECANICOS_ABS = switches_desde_config(LIMITES_CONFIG)
    LIMITES_MECANICOS_ABS = limites_desde_config(LIMITES_CONFIG)
    LIMITES_CONF_VERSION = LIMITES_CONFIG.get("version", "sin-version")


def config_autoritaria_payload():
    return {
        "LIMITES_CONF_VERSION": LIMITES_CONF_VERSION,
        "LIMITES_CONFIG": LIMITES_CONFIG,
        "LIMITES_SWITCHES_MECANICOS_ABS": LIMITES_SWITCHES_MECANICOS_ABS,
        "LIMITES_MECANICOS_ABS": LIMITES_MECANICOS_ABS,
        "OFFSETS_CERO": {
            eje: float(OFFSETS_CERO.get(eje, 0.0)) for eje in EJES_GUIADOR
        },
    }


def marca_config_sucia():
    global CONFIG_DIRTY
    CONFIG_DIRTY = True


def carga_offsets_cero(archivo=None):
    if archivo is None:
        archivo = DEF_CERO_OFFSETS_ARCH
    offsets = {eje: 0.0 for eje in EJES_GUIADOR}
    try:
        with open(archivo, "r", encoding="ascii") as arch:
            data = json.load(arch)
        for eje in EJES_GUIADOR:
            offsets[eje] = float(data.get(eje, 0.0))
    except FileNotFoundError:
        print("[LIMITES] No hay archivo de offsets; usando offsets cero")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"[LIMITES] Offsets invalidos; usando ceros: {exc}")
    return offsets


def guarda_offsets_cero(archivo=None):
    if archivo is None:
        archivo = DEF_CERO_OFFSETS_ARCH
    try:
        directorio = os.path.dirname(archivo)
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        with open(archivo, "w", encoding="ascii") as arch:
            json.dump(OFFSETS_CERO, arch, indent=2, sort_keys=True)
        return True
    except OSError as exc:
        registra_aviso([f"no se pudieron guardar offsets: {exc}"])
        return False


def usuario_a_mecanico(eje, valor):
    return float(valor) + OFFSETS_CERO.get(eje, 0.0)


def mecanico_a_usuario(eje, valor):
    return float(valor) - OFFSETS_CERO.get(eje, 0.0)


def limita_valor_mecanico(eje, valor):
    limites = LIMITES_MECANICOS_ABS.get(eje)
    if limites is None:
        return float(valor), False
    vmin, vmax = limites
    valor_float = float(valor)
    valor_limitado = min(max(valor_float, vmin), vmax)
    return valor_limitado, valor_limitado != valor_float


def registra_aviso(avisos):
    global LIMITE_ACTIVO
    global ULTIMO_AVISO
    LIMITE_ACTIVO = bool(avisos)
    ULTIMO_AVISO = " | ".join(avisos)
    if ULTIMO_AVISO:
        print(f"[LIMITES] {ULTIMO_AVISO}")


def actualiza_estado_cache(datos, ahora=None):
    if ahora is None:
        ahora = time.time()
    if not isinstance(datos, dict) or datos.get("ERROR"):
        return False
    actualizado = False
    for eje in EJES_GUIADOR:
        if eje not in datos:
            continue
        try:
            ULTIMO_ESTADO[eje] = float(datos[eje])
        except (TypeError, ValueError):
            continue
        POS_VALIDAS[eje] = True
        T_ULTIMA_POSICION[eje] = ahora
        actualizado = True
    aplica_reset_offset_si_corresponde(datos)
    return actualizado


def posicion_reciente(eje, ahora=None):
    if ahora is None:
        ahora = time.time()
    if not POS_VALIDAS.get(eje, False):
        return False
    return ahora - T_ULTIMA_POSICION.get(eje, 0.0) <= POSICION_VALIDA_TIMEOUT_S


def limita_mueve_absoluto(data):
    seguro = dict(data)
    avisos = []
    for eje in EJES_GUIADOR:
        if eje not in data:
            continue
        try:
            solicitado = float(data[eje])
        except (TypeError, ValueError):
            seguro.pop(eje, None)
            avisos.append(f"{eje}: valor absoluto invalido")
            continue
        solicitado_mecanico = usuario_a_mecanico(eje, solicitado)
        mecanico_limitado, cambio = limita_valor_mecanico(eje, solicitado_mecanico)
        aplicado = mecanico_a_usuario(eje, mecanico_limitado)
        seguro[eje] = aplicado
        if cambio:
            avisos.append(f"{eje}: solicitado {solicitado:.2f}, aplicado {aplicado:.2f}")
    registra_aviso(avisos)
    return seguro


def limita_mueve_relativo(data, ahora=None):
    seguro = dict(data)
    avisos = []
    for eje in EJES_GUIADOR:
        if eje not in data:
            continue
        if not posicion_reciente(eje, ahora=ahora):
            seguro.pop(eje, None)
            avisos.append(f"{eje}: sin posicion reciente")
            continue
        try:
            solicitado = float(data[eje])
            actual = float(ULTIMO_ESTADO[eje])
        except (KeyError, TypeError, ValueError):
            seguro.pop(eje, None)
            avisos.append(f"{eje}: posicion invalida")
            continue
        destino = actual + solicitado
        destino_mecanico = usuario_a_mecanico(eje, destino)
        mecanico_limitado, cambio = limita_valor_mecanico(eje, destino_mecanico)
        destino_limitado = mecanico_a_usuario(eje, mecanico_limitado)
        aplicado = destino_limitado - actual
        if abs(aplicado) < 1e-9:
            seguro.pop(eje, None)
        else:
            seguro[eje] = aplicado
        if cambio:
            avisos.append(f"{eje}: solicitado {solicitado:.2f}, aplicado {aplicado:.2f}")
    registra_aviso(avisos)
    return seguro


def filtra_define_coordenadas(data, ahora=None):
    seguro = {}
    avisos = []
    cambio = False
    datos = dict(data)
    if isinstance(data.get("TODOS"), dict):
        datos.update(data["TODOS"])
    for eje in EJES_GUIADOR:
        if eje not in datos:
            continue
        if not posicion_reciente(eje, ahora=ahora):
            avisos.append(f"{eje}: define cero sin posicion reciente")
            continue
        try:
            valor = float(datos[eje])
        except (TypeError, ValueError):
            avisos.append(f"{eje}: valor de cero invalido")
            continue
        if valor != 0.0:
            avisos.append(f"{eje}: solo se permite definir cero")
            continue
        OFFSETS_CERO[eje] += float(ULTIMO_ESTADO[eje])
        seguro[eje] = 0
        cambio = True
    if cambio:
        guarda_offsets_cero()
        marca_config_sucia()
    registra_aviso(avisos)
    return seguro


def marca_reset_offset(ejes):
    if not isinstance(ejes, dict):
        return
    for eje in EJES_GUIADOR:
        if eje in ejes or "TODOS" in ejes:
            RESET_OFFSET_PENDIENTE[eje] = True


def aplica_reset_offset_si_corresponde(datos):
    mapa_ok = {
        "AR": "OK_CENTRO_AR",
        "DEC": "OK_CENTRO_DEC",
        "FOCO": "OK_CENTRO_FOCO",
    }
    cambio = False
    for eje, llave in mapa_ok.items():
        if RESET_OFFSET_PENDIENTE.get(eje, False) and llave in datos:
            OFFSETS_CERO[eje] = 0.0
            RESET_OFFSET_PENDIENTE[eje] = False
            cambio = True
    if cambio:
        guarda_offsets_cero()
        marca_config_sucia()
    return cambio


configura_limites()
OFFSETS_CERO = carga_offsets_cero()
ULTIMO_ESTADO = {}
POS_VALIDAS = {eje: False for eje in EJES_GUIADOR}
T_ULTIMA_POSICION = {eje: 0.0 for eje in EJES_GUIADOR}
RESET_OFFSET_PENDIENTE = {eje: False for eje in EJES_GUIADOR}
CONFIG_DIRTY = True
LIMITE_ACTIVO = False
ULTIMO_AVISO = ""


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
        datos = json.loads(res)
        actualiza_estado_cache(datos)
        return datos
    except json.decoder.JSONDecodeError as error:
        print("[ESTADO] JSONDecodeError:", error)
        return {"ERROR": True}
    except Exception as e:
        print(f"[ESTADO] Error en pide_estado: {e}")
        return {"ERROR": True}


# ===================== MQTT helpers =====================
async def publica_config(cliente) -> None:
    global CONFIG_DIRTY
    try:
        await cliente.publish(
            PREFIX + "config",
            json.dumps(config_autoritaria_payload()),
            retain=True,
        )
        CONFIG_DIRTY = False
    except (aiomqtt.MqttError, OSError) as e:
        print(f"[MQTT] publish config falló: {e}")
        raise
    except Exception as e:
        print(f"[MQTT] publish config falló (otro): {e}")


async def publica_estado(cliente, datos: dict) -> None:
    # Si el estado viene malo, no publiques
    if not isinstance(datos, dict) or 'ERROR' in datos:
        return
    try:
        datos_pub = dict(datos)
        datos_pub["LIMITE_ACTIVO"] = LIMITE_ACTIVO
        datos_pub["ULTIMO_AVISO"] = ULTIMO_AVISO
        datos_pub.update(config_autoritaria_payload())
        await cliente.publish(PREFIX + "status", json.dumps(datos_pub))
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
    data = limita_mueve_absoluto(msg_a_json(msg))
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
    await pide_estado()
    data = limita_mueve_relativo(data)
    res = ""
    cmds = ('AR+', 'DEC+', 'FOC+', 'Z+')
    for ind, nom in enumerate(('AR', 'DEC', 'FOCO', 'ZOOM')):
        if nom in data:
            res += " PON_INC_%s= %.2f  %s " % (nom, data[nom], cmds[ind])
    if len(res) <= 1:
        return
    await manda(res)


async def procesa_msg_inicia_ejes(cliente, msg: bytes):
    await asyncio.sleep(0.1)
    data = msg_a_json(msg)
    marca_reset_offset(data)
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
    data_original = msg_a_json(msg)
    await pide_estado()
    data = filtra_define_coordenadas(data_original)
    res = ""
    for nom in ('AR', 'DEC', 'FOCO'):
        if nom in data:
            res += "DEF_CERO_%s " % (nom)
    if 'ZOOM' in data_original:
        res += "DEF_CERO_ZOOM "
    if len(res) <= 1:
        return
    await manda(res)
    if data:
        await publica_config(cliente)


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
                await publica_config(client)

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
                    if CONFIG_DIRTY:
                        await publica_config(client)

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
    time.sleep(RETARDO_INICIO_S)
    try:
        asyncio.run(corredor())
    except Exception as e:
        print(f"[MAIN] Error fatal: {e}")
