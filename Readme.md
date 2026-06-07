# Guiador del telescopio de 2 m

Guía técnica, operativa y de mantenimiento del control de motores del guiador
del telescopio de 2 m. Este documento describe únicamente valores comprobados
en el código y los archivos de configuración de este repositorio.

> **PELIGRO - MOVIMIENTO FÍSICO:** los comandos marcados con esta advertencia
> pueden mover AR, DEC, FOCO o ZOOM. Antes de ejecutarlos, confirme que el
> mecanismo esté libre, que ninguna persona esté trabajando cerca, que los
> límites sean correctos y que exista una forma inmediata de detener el eje.
>
> Los sockets TCP directos `9055` y `9095` permiten evitar parte o toda la
> protección de límites de MQTT. Úselos sólo para mantenimiento controlado.
> Para detener una salida manual de una PocketBeagle envíe `DAX 0`.

## Contenido

- [Arquitectura](#arquitectura)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Mapa de red y puertos](#mapa-de-red-y-puertos)
- [Instalación y dependencias](#instalación-y-dependencias)
- [Arranque y parada](#arranque-y-parada)
- [MQTT](#mqtt)
- [Comandos TCP y sockets](#comandos-tcp-y-sockets)
- [Operación de ejes](#operación-de-ejes)
- [Procedimiento recomendado de entonación](#procedimiento-recomendado-de-entonación)
- [Límites mecánicos y ceros](#límites-mecánicos-y-ceros)
- [PocketBeagles](#pocketbeagles)
- [Operación SACA ESPEJO](#operación-saca-espejo)
- [Logger MQTT](#logger-mqtt)
- [Diagnóstico y recuperación](#diagnóstico-y-recuperación)
- [Despliegue y configuración](#despliegue-y-configuración)
- [Antes de publicar el repositorio](#antes-de-publicar-el-repositorio)
- [Archivos importantes](#archivos-importantes)
- [Discrepancias conocidas](#discrepancias-conocidas)

## Arquitectura

El control activo está dividido en cinco capas:

1. Las interfaces `gscui` y `motgui-2m.py` se ejecutan en la computadora de
   observación.
2. UI, GSC, consola y backend intercambian mensajes mediante el broker MQTT
   `192.168.0.237:1883`.
3. En la Raspberry Pi `192.168.0.205`, `g2mdrvmqtt_edgar.py` traduce MQTT al
   intérprete TCP local `127.0.0.1:9055`.
4. `servg2m_edgar_v2.py` e `instruccionesguiador.py` convierten unidades,
   administran los ejes y se comunican con cada PocketBeagle.
5. Cada PocketBeagle sirve comandos de servo por TCP `9095` y controla un eje.

```text
UI motores / GSC / consola
          |
          v
MQTT 192.168.0.237:1883
          |
          v
Raspberry Pi 192.168.0.205
g2mdrvmqtt_edgar.py
          |
          v
127.0.0.1:9055
servg2m_edgar_v2.py + instruccionesguiador.py
          |
          +--> ZOOM 192.168.7.2:9095
          +--> FOCO 192.168.8.2:9095
          +--> DEC  192.168.9.2:9095
          +--> AR   192.168.10.2:9095
```

La ruta MQTT es la recomendada para operación normal porque aplica límites
mecánicos a AR, DEC y FOCO. Los movimientos relativos sólo se aceptan cuando el
backend recibió una posición válida del eje durante los últimos `5 s`.

ZOOM existe en el backend, el intérprete y una PocketBeagle. Sin embargo,
`test_epl/uiepls/motoresui/src/motgui-2m.py` establece `enable_Zoom = False`,
por lo que la interfaz actual no lo muestra.

## Estructura del repositorio

| Ruta | Función |
|---|---|
| `g2m/` | Scripts de operación desde la computadora de observación y logger. |
| `g2m/fns_g2m.sh` | Funciones de shell para consultar y mandar comandos al puerto `9055`. |
| `g2m/G2M_Logger/` | Registro MQTT en SQLite, exportación y gráficas. |
| `rpi/` | Configuración, scripts y software desplegado en la Raspberry Pi. |
| `rpi/dist/` | Backend activo: servidor `9055`, puente MQTT, intérprete y configuración de servo. |
| `rpi/config/` | Límites mecánicos y offsets de cero versionados. |
| `rpi/supervisor/` | Configuración de Supervisor para la Raspberry Pi. |
| `pocketbb/` | Arranque, aplicación y archivos de las PocketBeagles. |
| `test_epl/epls/` | Servicios EPL de GSC y consola. |
| `test_epl/uiepls/` | Interfaces gráficas de GSC y motores. |

Los directorios `backup/`, archivos `*_orig`, notas antiguas y scripts con
valores de otros equipos no son configuración autoritativa del guiador de 2 m.

## Mapa de red y puertos

### Direcciones activas

| Equipo o servicio | Dirección | Puerto | Uso |
|---|---:|---:|---|
| Broker MQTT | `192.168.0.237` | `1883` | Mensajería UI, GSC, consola y motores. |
| Raspberry Pi de motores | `192.168.0.205` | `9055` | Intérprete TCP del guiador. |
| SSH Raspberry Pi | `192.168.0.205` | `22` | Mantenimiento; el puerto predeterminado se comprueba en `rpi/leeme.txt`. |
| Consola del telescopio | `192.168.0.208` | `4955` | Socket usado por `consolad`. |
| Supervisor en Raspberry Pi | `192.168.0.205` | `9001` | Interfaz HTTP/XML-RPC. |
| Supervisor local | `/var/run/supervisor.sock` | Unix socket | `supervisorctl`. |
| ZOOM | `192.168.7.2` | `9095` | Servo directo y estado. |
| FOCO | `192.168.8.2` | `9095` | Servo directo y estado. |
| DEC | `192.168.9.2` | `9095` | Servo directo y estado. |
| AR | `192.168.10.2` | `9095` | Servo directo y estado. |
| SSH de PocketBeagles | IP de cada eje | `2276` | Dropbear dentro del chroot. |

La Raspberry Pi tiene IP estática `192.168.0.205/24`, gateway
`192.168.0.254` y crea las direcciones `.1` de las subredes USB.

### Correspondencia USB y eje

`rpi/dist/scripts/config_ips_g2m.sh` identifica cada interfaz USB por serial:

| Eje | Serial USB | Subred | Raspberry Pi | PocketBeagle |
|---|---|---|---|---|
| ZOOM | `1736GPB20546` | `192.168.7.0` | `192.168.7.1` | `192.168.7.2` |
| AR | `1741GPB42035` | `192.168.10.0` | `192.168.10.1` | `192.168.10.2` |
| FOCO | `1741GPB42111` | `192.168.8.0` | `192.168.8.1` | `192.168.8.2` |
| DEC | `1741GPB20518` | `192.168.9.0` | `192.168.9.1` | `192.168.9.2` |

Si se sustituye una PocketBeagle, actualice su serial en ese archivo antes de
reiniciar la red USB.

## Instalación y dependencias

### Herramientas del sistema

El código y los scripts usan, como mínimo:

```bash
sudo apt install python3 python3-venv netcat-openbsd mosquitto-clients \
  supervisor dropbear openssh-client iproute2 net-tools
```

También se usan `ping`, `ssh`, `scp`, `udevadm`, `ifconfig`, `route`, `chroot`,
`mount`, `ps`, `pgrep` y `tee`.

### Dependencias Python

Las dependencias comprobadas en el proyecto incluyen:

```bash
python3 -m venv venv3
source venv3/bin/activate
pip install aiomqtt paho-mqtt pandas openpyxl matplotlib seaborn
```

- `aiomqtt`: puente MQTT activo de motores.
- `paho-mqtt`: interfaces EPL y logger.
- `pandas` y `openpyxl`: exportación del logger.
- `matplotlib` y `seaborn`: gráficas del logger.

Las interfaces requieren además sus dependencias gráficas instaladas en el
entorno de observación.

## Arranque y parada

### Operación habitual desde la computadora de observación

El lanzador principal de motores verifica por `ping` la Raspberry Pi, detiene
instancias anteriores de GSC/UI, inicia GSC y consola, y abre ambas interfaces:

```bash
cd g2m
./nuevo-guiador-motores.sh
```

El script espera rutas instaladas bajo `/home/observa/chava/`. Si se despliega
en otra cuenta, ajuste los archivos de configuración EPL/UI.

Inicio individual de servicios y UI:

```bash
cd test_epl/epls/scripts
./corre_serv_gsc_2m.sh

cd ../../uiepls/scripts
./ejec_gscui.sh
./ejec_mot_guiadorui-2m.sh
```

Parada individual:

```bash
cd test_epl/epls/scripts
./ejec_gsc_d.sh stop
./ejec_consola_d.sh stop

cd ../../../g2m
./kill-g2m-gscui.sh
```

Los logs de estos servicios se escriben en `/tmp/gscd.log` y
`/tmp/consolad.consolad.log`.

### Supervisor en la Raspberry Pi

Supervisor administra:

| Servicio | Programa |
|---|---|
| `servg2m` | `python /home/guiador/dist/servg2m_edgar_v2.py` |
| `mqtt` | `/home/guiador/dist/scripts/ejecutar_g2m_edgar.sh` |
| `reinicio_automatico` | `python3 reinicio_edgar.py` |

Comandos de mantenimiento:

```bash
sudo supervisorctl status
sudo supervisorctl start servg2m mqtt reinicio_automatico
sudo supervisorctl stop servg2m mqtt reinicio_automatico
sudo supervisorctl restart servg2m mqtt
sudo supervisorctl reread
sudo supervisorctl update
```

`reinicio_automatico` reinicia el servicio `mqtt` diariamente a las `17:00`.
Supervisor descarta stdout y stderr de los tres programas en `/dev/null`; el
log general disponible es `/var/log/supervisor/supervisord.log`.

### Arranque de red y PocketBeagles

La Raspberry Pi debe ejecutar `rpi/dist/scripts/config_ips_g2m.sh` para asociar
seriales USB con subredes. La instalación actual contempla su ejecución desde
los scripts de arranque/crontab.

En cada PocketBeagle, `pocketbb/aplica.sh` prepara el chroot `/app`, arranca
Dropbear en `2276` y ejecuta `pocketbb/app/aplica.sh`. Este último inicia el
servo mediante `corre_servo_bb.sh`.

### Logger

```bash
cd g2m/G2M_Logger
./start.sh
./stop.sh
```

## MQTT

### Prefijos activos

| Subsistema | Prefijo |
|---|---|
| Motores | `oan/control/2m/guiador/motores/` |
| GSC | `oan/control/2m/gsc/` |
| Consola | `oan/control/2m/consola/` |

El broker activo comprobado es `192.168.0.237:1883`.

### Tópicos activos de motores

| Sufijo | Dirección | Retained | Payload comprobado | Efecto |
|---|---|---|---|---|
| `mueve` | UI → backend | No | JSON con valores numéricos `AR`, `DEC`, `FOCO` o `ZOOM` | Posición absoluta. |
| `mueve_relativo` | UI → backend | No | JSON con incrementos numéricos por eje | Movimiento relativo si la posición tiene menos de `5 s`. |
| `dame_estado` | cliente → backend | No | El contenido no se interpreta | Solicita publicación inmediata de estado. |
| `inicializa_ejes` | UI → backend | No | JSON; la presencia de `AR`, `DEC`, `FOCO`, `ZOOM` o `TODOS` selecciona ejes | Inicia/busca referencia. |
| `define_coordenadas` | UI → backend | No | JSON con valor `0` por eje; acepta `TODOS` como objeto | Define cero de usuario y guarda offsets. |
| `cambia_params` | UI → backend | No | JSON con `ESC_PLACA`, `RESTABLECE_BANDERA_ERR` o `CANCELA` | Cambia parámetros o cancela búsquedas. |
| `status` | backend → clientes | No | JSON de posiciones, errores, límites, offsets y avisos | Estado periódico y solicitado. |
| `config` | backend → clientes | Sí | JSON de límites, switches, márgenes y offsets | Configuración autoritativa. |

Unidades de usuario verificadas: AR y DEC en `arcsec`, FOCO en `mm`, y ZOOM
según su conversión de `3600` cuentas por unidad angular configurada.

Consulta segura:

```bash
mosquitto_sub -h 192.168.0.237 -p 1883 \
  -t 'oan/control/2m/guiador/motores/status' -v

mosquitto_sub -h 192.168.0.237 -p 1883 \
  -t 'oan/control/2m/guiador/motores/config' -v

mosquitto_pub -h 192.168.0.237 -p 1883 \
  -t 'oan/control/2m/guiador/motores/dame_estado' -m '{}'
```

> **PELIGRO - MOVIMIENTO FÍSICO:** ejemplos de movimiento MQTT:

```bash
# Posición absoluta en unidades de usuario
mosquitto_pub -h 192.168.0.237 -p 1883 \
  -t 'oan/control/2m/guiador/motores/mueve' \
  -m '{"AR":0.0,"DEC":0.0,"FOCO":20.0}'

# Movimiento relativo; requiere estado reciente
mosquitto_pub -h 192.168.0.237 -p 1883 \
  -t 'oan/control/2m/guiador/motores/mueve_relativo' \
  -m '{"AR":1.0}'

# Buscar la referencia de DEC
mosquitto_pub -h 192.168.0.237 -p 1883 \
  -t 'oan/control/2m/guiador/motores/inicializa_ejes' \
  -m '{"DEC":1}'
```

> **PELIGRO OPERATIVO:** este ejemplo no necesariamente mueve el eje, pero
> redefine la posición actual como cero y cambia la referencia de movimientos
> posteriores:

```bash
mosquitto_pub -h 192.168.0.237 -p 1883 \
  -t 'oan/control/2m/guiador/motores/define_coordenadas' \
  -m '{"AR":0}'
```

El estado publicado incluye las posiciones `AR`, `DEC`, `FOCO`, `ZOOM`,
`ESC_PLACA`, banderas de comunicación/inicialización cuando aplican,
`LIMITE_ACTIVO`, `ULTIMO_AVISO` y la configuración autoritativa.

### GSC y consola

El GSC de 2 m consume:

- `oan/control/2m/gsc/params_gsc`
- `oan/control/2m/gsc/actualiza_coordenadas`
- `oan/control/2m/gsc/buscar`
- `oan/control/2m/consola/mueve`
- `oan/control/2m/consola/status`

Publica `oan/control/2m/gsc/lista_objetos` y
`oan/control/2m/gsc/status`.

El monitor de consola de 2 m consume los sufijos `mueve`, `mueve_cenit`,
`define_cenit`, `comando` y `posicion_servicio`, y publica `status`, bajo
`oan/control/2m/consola/`.

### Tópicos de compatibilidad UI sin manejador activo

La UI de motores publica `actualiza_coordenadas` y escucha `comando`, pero
`rpi/dist/g2mdrvmqtt_edgar.py` no consume el primero ni publica el segundo.
No deben considerarse parte funcional del backend activo.

## Comandos TCP y sockets

### Servidor principal del guiador: `192.168.0.205:9055`

Para cargar las funciones de operación:

```bash
source g2m/fns_g2m.sh
edog2m       # estado legible
edog2mj      # estado JSON, una clave por línea
ag2m EGJ     # comando crudo al intérprete
```

Funciones directas por eje:

```bash
ejear ESTADO
ejedec ESTADO
ejefoco ESTADO
ejezoom ESTADO
```

Estas funciones agregan `FCMD` automáticamente. No lo añada de nuevo.
En cambio, todo comando crudo `EJEAR`, `EJEDEC`, `EJEFOCO` o `EJEZOOM`
enviado mediante `ag2m` debe terminar explícitamente en `FCMD`.

Catálogo del intérprete:

| Comando | Uso |
|---|---|
| `EG?`, `EGJ`, `EG+` | Consultas de estado. |
| `AR=`, `DEC=`, `FOCO=`, `ZOOM=` | Posiciones absolutas en unidades de usuario. |
| `AR+`, `AR-`, `DEC+`, `DEC-`, `FOC+`, `FOC-`, `Z+`, `Z-` | Movimiento por incremento configurado. |
| `ARL+`, `ARL-`, `DECL+`, `DECL-`, `FOCL+`, `FOCL-`, `ZL+`, `ZL-` | Variantes largas de movimiento. |
| `PON_INC_AR=`, `PON_INC_DEC=`, `PON_INC_FOCO=`, `PON_INC_ZOOM=` | Define incrementos. |
| `BUSCA_CENTRO_*`, `CANCELA_INICIO_*`, `POS_CENTRO_*` | Referencia y centros. |
| `DEF_CERO_AR`, `DEF_CERO_DEC`, `DEF_CERO_FOCO`, `DEF_CERO_ZOOM` | Define cero de usuario. |
| `RESTABLECE_BANDERA_ERR` | Restablece banderas de error. |
| `EJEAR`, `EJEDEC`, `EJEFOCO`, `EJEZOOM` | Pasa comandos al servo del eje. |
| `VEL_NORMAL_AR`, `VEL_CENTRADO_AR`, `VEL_NORMAL_DEC`, `VEL_CENTRADO_DEC` | Cambia velocidades. |
| `ESC_PLACA=` | Cambia escala de placa. |
| `LEECFG` | Recarga `guiador2m.cfg`. |

> **PELIGRO - MOVIMIENTO FÍSICO:** ejemplos por el intérprete `9055`:

```bash
source g2m/fns_g2m.sh
ag2m 'AR= 0'
ag2m 'DEC= 0'
ag2m 'FOCO= 20'
ag2m 'PON_INC_AR= 1'
ag2m 'AR+'
```

### Socket directo de PocketBeagle: `<IP>:9095`

Consulta segura:

```bash
echo ESTADO | nc -w 1 192.168.10.2 9095
```

Los campos observables incluyen:

| Campo | Interpretación usada por el software |
|---|---|
| `X` | Cuenta actual del codificador. |
| `XD` | Cuenta deseada actual de trayectoria. |
| `XT` | Objetivo de trayectoria. |
| `CTX` | Campo de conteo/estado expuesto por el servo. |
| `UX` | Salida de control. |
| `BIX` | Bits de inicio/índice. |
| `PIX` | Posición de inicio/índice. |
| `SW` | Estado de switches. |

> **PELIGRO - MOVIMIENTO FÍSICO:** `X=`, `CONTROL_PIDX`, búsquedas de inicio y
> `DAX` actúan directamente sobre el servo y evitan las protecciones MQTT.

```bash
# Mover AR directamente a una cuenta objetivo
echo 'X= 1000' | nc -q0 192.168.10.2 9095

# Salida manual y parada inmediata
echo 'DAX 500' | nc -q0 192.168.10.2 9095
echo 'DAX 0'   | nc -q0 192.168.10.2 9095
```

## Operación de ejes

### Consultar estado

```bash
source g2m/fns_g2m.sh
edog2mj

./rpi/estadopockets.sh
```

`rpi/estadopockets.sh` consulta `ESTADO` cada segundo en las cuatro
PocketBeagles. Es la vista recomendada para comparar `X`, `XD`, `XT`, `UX`,
`BIX`, `PIX` y `SW`.

### Abrir y cerrar lazos

> **PELIGRO - MOVIMIENTO FÍSICO:** cerrar un lazo puede producir movimiento
> inmediato hacia el objetivo almacenado.

```bash
source g2m/fns_g2m.sh

# Abrir lazos y llevar la salida a cero
abre_lazos_g2m

# Cerrar lazos PID
cierra_lazos_g2m
```

Para un solo eje:

```bash
ejear DAX 0
ejear CONTROL_PIDX
```

### Movimientos absolutos y relativos

> **PELIGRO - MOVIMIENTO FÍSICO:**

```bash
# Unidades de usuario por el intérprete
ag2m 'AR= 10'
ag2m 'DEC= -10'
ag2m 'FOCO= 20'

# Incremento configurado y movimiento relativo
ag2m 'PON_INC_DEC= 1'
ag2m 'DEC+'
ag2m 'DEC-'
```

Prefiera MQTT para operación ordinaria porque aplica límites a AR, DEC y FOCO.

### Buscar centros o inicios

> **PELIGRO - MOVIMIENTO FÍSICO:** una búsqueda de centro mueve el eje hasta
> detectar la referencia. Vigile switches y recorrido.

```bash
ag2m BUSCA_CENTRO_AR
ag2m CANCELA_INICIO_AR
ag2m POS_CENTRO_AR
```

Cambie el sufijo por `DEC`, `FOCO` o `ZOOM` según el eje.

Las banderas de inicio configuradas son `0x4` para AR/DEC y `0x2` para
FOCO/ZOOM. Los centros internos en cuentas son AR `220000`, DEC `260000`,
FOCO `216000` y ZOOM `1000`.

### Definir ceros

`define_coordenadas` por MQTT y los comandos `DEF_CERO_*` definen el cero de
usuario. El backend guarda offsets de AR, DEC y FOCO en
`/home/guiador/config/offsets-cero-mecanicos-2m.json`.

> **PELIGRO OPERATIVO:** cambiar un cero altera la interpretación de límites y
> destinos aunque no necesariamente mueva el eje en ese instante.

```bash
ag2m DEF_CERO_AR
```

### Movimiento manual en lazo abierto

> **PELIGRO - MOVIMIENTO FÍSICO:** use valores pequeños, observe el mecanismo
> continuamente y prepare `DAX 0` antes de comenzar.

```bash
source g2m/fns_g2m.sh
ejedec RST_S ERROR_MAXX 0
ejedec DAX 500
ejedec DAX 0
```

## Procedimiento recomendado de entonación

La entonación debe hacerse con un solo eje, recorrido libre y personal fuera
del mecanismo. No copie parámetros de otro eje: masa, transmisión y respuesta
son diferentes.

### Parámetros actuales

Valores autoritativos de `rpi/dist/guiador2m.cfg`:

| Eje | KPX | KIX | KDX | ILX | BITIX | VX | AX | CGANX | ERROR_MAXX | MAXPOSX | MINPOSX | Vel. normal / centrado |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| AR | 14.0 | 0.001 | 0.001 | 4000 | 4 | 4 | 0.001 | `5000 2` | 6000 | 50000000 | -50000000 | `4 / 1` |
| DEC | 14.0 | 0.001 | 0.001 | 4000 | 4 | 4 | 0.001 | `5000 2` | 6000 | 50000000 | -50000000 | `4 / 1` |
| ZOOM | 1.12 | 0.001 | 0.001 | 4000 | 2 | 5 | 0.1 | no definido | 1000 | 10000000 | -10000000 | no definido |
| FOCO | 10 | 0.001 | 0.001 | 4000 | 8 | 50 | 0.1 | no definido | 6000 | 10000000 | -10000000 | no definido |

`CCONTROL_PIDX` aparece literalmente en la línea de ZOOM y debe validarse antes
de asumir que el lazo se cierra al cargar el archivo.

### Preparación

1. Seleccione un solo eje y confirme su IP.
2. Abra una terminal de comandos y cargue `source g2m/fns_g2m.sh`.
   Las funciones `ejear`, `ejedec`, `ejefoco` y `ejezoom` agregan el
   terminador obligatorio `FCMD` automáticamente. Si usa `ag2m` para enviar
   comandos crudos `EJE*`, escriba siempre `FCMD` al final.
3. Abra otra terminal para retroalimentación continua:

   ```bash
   ./rpi/estadopockets.sh
   ```

4. Para observar sólo un eje:

   ```bash
   while sleep 1; do echo ESTADO | nc -w 1 192.168.10.2 9095; done
   ```

5. Registre los valores originales antes de modificar parámetros.
6. Prepare en la terminal de comandos la parada `ejear DAX 0`, sustituyendo la
   función según el eje.

### Secuencia de ajuste

> **PELIGRO - MOVIMIENTO FÍSICO:** todos los comandos de esta secuencia pueden
> provocar movimiento. Empiece con desplazamientos y ganancias pequeños.

El intérprete requiere `FCMD` para ejecutar cada instrucción directa de servo.
Esta secuencia comprobada para DEC muestra el protocolo completo:

```bash
source g2m/fns_g2m.sh

ag2m 'EJEDEC DAX 0 RST FCMD'
ag2m 'EJEDEC KPX 70 KIX 0.001 KDX 1 ILX 4000 FCMD'
ag2m 'EJEDEC VX= 2 AX= 0.001 FCMD'
ag2m 'EJEDEC CGANX 500 2 FCMD'
ag2m 'EJEDEC ERROR_MAXX 0 CONTROL_PIDX FCMD'
ag2m 'EJEDEC X= 3000 FCMD'
```

La misma secuencia usando la función `ejedec` se escribe sin `FCMD`, porque la
función lo agrega al enviarla:

```bash
ejedec DAX 0 RST
ejedec KPX 70 KIX 0.001 KDX 1 ILX 4000
ejedec VX= 2 AX= 0.001
ejedec CGANX 500 2
ejedec ERROR_MAXX 0 CONTROL_PIDX
ejedec X= 3000
```

No escriba `ejedec ... FCMD`: produciría dos terminadores porque
`g2m/fns_g2m.sh` añade otro automáticamente.

1. Abra el lazo y fuerce salida cero:

   ```bash
   ejear DAX 0
   ejear RST_S ERROR_MAXX 0
   ```

2. Aplique parámetros iniciales conservadores, un cambio a la vez:

   ```bash
   ejear KPX 1 KIX 0 KDX 0 ILX 4000 BITIX 4 VX= 1 AX= 0.001
   ```

3. Cierre el lazo sólo cuando el objetivo guardado sea seguro:

   ```bash
   ejear CONTROL_PIDX
   ```

4. Mueva por cuentas para evaluar directamente el servo:

   ```bash
   ejear X= 1000
   ejear X= 0
   ```

5. Mueva en unidades de usuario mediante el intérprete:

   ```bash
   ag2m 'AR= 1'
   ag2m 'AR= 0'
   ```

6. Aumente `KPX` gradualmente hasta obtener respuesta firme sin oscilación
   sostenida. Si aparece oscilación, reduzca `KPX`.
7. Introduzca `KDX` poco a poco para amortiguar sobreimpulso. Un valor excesivo
   puede amplificar ruido.
8. Introduzca `KIX` lentamente para reducir error estacionario. Vigile la
   acumulación integral y ajuste `ILX` para limitarla.
9. Ajuste `VX` y `AX` conservadoramente. Son límites de velocidad y
   aceleración de trayectoria; aumentarlos incrementa la exigencia mecánica.
10. Ajuste `CGANX` sólo cuando se comprenda su efecto en el servo del eje.
11. Mantenga `ERROR_MAXX` como protección durante la entonación; no deje el
    valor `0` como configuración persistente.
12. Repita movimientos positivos y negativos de distintas amplitudes.

### Criterios de evaluación

- **Convergencia:** `X` alcanza y permanece cerca de `XD`/`XT`.
- **Error estacionario:** diferencia final entre `X` y el objetivo.
- **Sobreimpulso:** `X` rebasa el objetivo antes de estabilizarse.
- **Oscilación:** cruces repetidos alrededor del objetivo sin amortiguamiento.
- **Esfuerzo:** `UX` no debe permanecer saturado ni crecer sin control.
- **Repetibilidad:** respuestas semejantes al repetir el mismo movimiento.
- **Seguridad:** `SW`, límites físicos y sonidos/vibraciones permanecen normales.

Ante respuesta inesperada, ejecute inmediatamente:

```bash
ejear DAX 0
```

Cambie `ejear` por `ejedec`, `ejefoco` o `ejezoom` según corresponda.

### Guardar y recargar la entonación

Los cambios enviados en vivo no sustituyen automáticamente la configuración
persistente. Para conservarlos:

1. Edite `rpi/dist/guiador2m.cfg`.
2. Copie el archivo validado a `/home/guiador/dist/guiador2m.cfg`.
3. Recargue desde el intérprete:

   ```bash
   source g2m/fns_g2m.sh
   ag2m LEECFG
   ```

> **PELIGRO - MOVIMIENTO FÍSICO:** `LEECFG` aplica parámetros y comandos de
> control del archivo. Revíselo completo antes de recargarlo.

## Límites mecánicos y ceros

La configuración autoritativa versionada está en
`rpi/config/limites-motores-guiador-2m.json`. En la Raspberry Pi debe instalarse
como `/home/guiador/config/limites-motores-guiador-2m.json`.

| Eje | Unidad | Switch mínimo | Switch máximo | Margen | Rango protegido MQTT |
|---|---|---:|---:|---:|---:|
| AR | arcsec | -1911.02 | 1744.23 | 10.0 | -1901.02 a 1734.23 |
| DEC | arcsec | -2482.26 | 1116.11 | 10.0 | -2472.26 a 1106.11 |
| FOCO | mm | -49.39 | 76.31 | 3.0 | -46.39 a 73.31 |

La versión comprobada es `g2m-2026-05-14`. ZOOM no tiene límites protegidos en
este JSON.

Los offsets versionados están en
`rpi/config/offsets-cero-mecanicos-2m.json` y se instalan en
`/home/guiador/config/offsets-cero-mecanicos-2m.json`. Los valores actuales del
repositorio son `0.0` para AR, DEC, FOCO y ZOOM; el backend administra offsets
persistentes de AR, DEC y FOCO.

Conversión autoritativa del backend:

| Parámetro | Valor |
|---|---:|
| `ESC_PLACA` inicial | 11.1 |
| `PPMMAR` | 1000.0 |
| `PPMMDEC` | 1000.0 |
| `PPMMFOCO` | 48000.0 |
| `PPGRADOZOOM` | 3600 |

La UI contiene valores iniciales distintos, pero recibe configuración del
backend. Para operación y mantenimiento prevalecen
`rpi/dist/instruccionesguiador.py`, la configuración instalada y el tópico
retained `config`.

## PocketBeagles

### Conexión SSH

```bash
ssh -p 2276 debian@192.168.7.2
ssh -p 2276 debian@192.168.8.2
ssh -p 2276 debian@192.168.9.2
ssh -p 2276 debian@192.168.10.2
```

No almacene contraseñas en este README ni en scripts versionados.

### Estado y puertos

```bash
ping -c 2 192.168.10.2
nc -vz 192.168.10.2 9095
nc -vz 192.168.10.2 2276
echo ESTADO | nc -w 1 192.168.10.2 9095
```

### Actualización

Ejemplo de copia al eje AR:

```bash
scp -P 2276 archivo debian@192.168.10.2:/home/debian/chava2/servo/
```

Después de copiar, valide permisos y contenido antes de reiniciar el servicio.
El arranque ejecuta `corre_servo_bb.sh`, que prepara pines, copia componentes a
`/dev/shm` y levanta el servidor del servo.

Cuando sea necesario editar el sistema de archivos de la PocketBeagle, móntelo
en lectura-escritura sólo durante el cambio y devuélvalo a sólo lectura al
terminar, siguiendo el procedimiento vigente del equipo.

Para sustituir hardware, actualice el serial USB correspondiente en
`rpi/dist/scripts/config_ips_g2m.sh`, despliegue el archivo y vuelva a aplicar
la configuración de red.

## Operación SACA ESPEJO

> **PELIGRO - MOVIMIENTO FÍSICO:** el botón **SACA ESPEJO** no controla un
> actuador independiente. Envía una maniobra de AR/DEC: AR va a `0` y DEC a
> una posición dependiente del secundario seleccionado.

| Secundario | Destino DEC |
|---|---:|
| F7.5 | -1700.0 |
| F13.5 | -963.0 |
| F30 | -360.0 |

Antes de usarlo, confirme que esos destinos siguen siendo válidos, que los
límites/offsets cargados son correctos y que el recorrido está libre.

## Logger MQTT

`g2m/G2M_Logger/mqtt_logger.py` escucha
`oan/control/2m/guiador/motores/status` en `192.168.0.237:1883` y guarda AR,
DEC y FOCO cada `1 s` durante una duración configurada de `12 h`.

La base SQLite es `mqtt_data.db`; la tabla `sensor_readings` contiene:
`id`, `timestamp`, `ar`, `dec` y `foco`.

```bash
cd g2m/G2M_Logger
./start.sh
./stop.sh

python3 data2excel.py
python3 plot_data.py
```

`start.sh` genera `mqtt_logger.pid` y escribe en `nohup.out`.
`data2excel.py` genera `sensor_data.xlsx`.

> **OPERACIÓN DESTRUCTIVA:** `clean_db.py` elimina permanentemente registros
> anteriores a la fecha configurada. Actualmente contiene la fecha fija
> `2025-06-01`; revísela y respalde `mqtt_data.db` antes de ejecutarlo.

## Diagnóstico y recuperación

### Verificar conectividad

```bash
ping -c 3 192.168.0.205
ping -c 3 192.168.0.237
ping -c 3 192.168.7.2
ping -c 3 192.168.8.2
ping -c 3 192.168.9.2
ping -c 3 192.168.10.2
```

### Verificar puertos

```bash
nc -vz 192.168.0.237 1883
nc -vz 192.168.0.205 9055
nc -vz 192.168.0.205 9001
nc -vz 192.168.10.2 9095
nc -vz 192.168.10.2 2276
```

### Estado general

```bash
source g2m/fns_g2m.sh
edog2mj

./rpi/estadopockets.sh
./rpi/estadorpi.sh

mosquitto_sub -h 192.168.0.237 -p 1883 \
  -t 'oan/control/2m/guiador/motores/#' -v
```

### Servicios y procesos

En la Raspberry Pi:

```bash
sudo supervisorctl status
sudo supervisorctl restart servg2m mqtt
tail -f /var/log/supervisor/supervisord.log
```

En la computadora de observación:

```bash
pgrep -af 'gscd|consolad|gscui|motgui-2m'
tail -f /tmp/gscd.log
tail -f /tmp/consolad.consolad.log
```

### Recuperación de comunicación

1. Confirme broker MQTT, Raspberry Pi y las cuatro PocketBeagles con `ping`.
2. Compruebe `1883`, `9055` y `9095`.
3. Consulte `EGJ` y luego `ESTADO` directo del eje afectado.
4. Si falla sólo MQTT, reinicie `mqtt` con Supervisor.
5. Si falla `9055`, reinicie `servg2m`.
6. Si una subred USB no aparece, vuelva a aplicar
   `/home/guiador/dist/scripts/config_ips_g2m.sh` y revise el serial USB.
7. Reinicie hardware sólo después de guardar diagnóstico y asegurar los ejes.

`g2m/recupera_comm.sh` y `g2m/soft_reset.sh` realizan acciones remotas y
contienen credenciales embebidas; deben revisarse y sanearse antes de usarse o
publicarse.

## Despliegue y configuración

### Raspberry Pi

Rutas instaladas comprobadas:

| Archivo versionado | Destino instalado |
|---|---|
| `rpi/dist/` | `/home/guiador/dist/` |
| `rpi/config/limites-motores-guiador-2m.json` | `/home/guiador/config/limites-motores-guiador-2m.json` |
| `rpi/config/offsets-cero-mecanicos-2m.json` | `/home/guiador/config/offsets-cero-mecanicos-2m.json` |
| `rpi/supervisor/guiador_services.conf` | `/etc/supervisor/conf.d/guiador_services.conf` |
| `rpi/supervisor/supervisord.conf` | Configuración de Supervisor del sistema |
| `rpi/dhcpcd.conf` | Configuración de red de la Raspberry Pi |

Después de desplegar cambios de Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

Las referencias antiguas a `dist.tgz`, `/dev/shm/dist` y `mntp3` no describen
el despliegue activo basado en Supervisor y `/home/guiador/dist`.

### Configuración EPL/UI

| Archivo | Función |
|---|---|
| `test_epl/epls/config/config_lugar.sh` | Broker, entorno y rutas de servicios EPL. |
| `test_epl/epls/scripts/config_lugar.sh` | Configuración usada por scripts EPL instalados. |
| `test_epl/uiepls/scripts/config_lugar_ui.sh` | Broker, entorno y rutas de UI. |
| `test_epl/uiepls/motoresui/src/centros-guiador-2m` | Posiciones de instrumentos y secundarios. |
| `test_epl/uiepls/motoresui/src/motgui-2m.py` | Interfaz principal de motores. |

Los archivos EPL/UI y el backend revisados configuran el broker
`192.168.0.237`.

### Centros de instrumentos comprobados

| Nombre | AR | DEC | FOCO | ZOOM | Secundario |
|---|---:|---:|---:|---:|---|
| CENTROS MECANICOS 7.5 | 0 | 0 | 20.0 | 0 | F7.5 |
| CENTROS MECANICOS 13.5 | 0 | 0 | 20.0 | 0 | F13.5 |
| CENTROS MECANICOS 30 | 0 | 0 | 20.0 | 0 | F30 |
| SPIN | -55.0 | 193.0 | 0.5 | 0 | F7.5 |
| FRENTE DE ONDA | -30.0 | -130.0 | 0.5 | 0 | F7.5 |

> **PELIGRO - MOVIMIENTO FÍSICO:** seleccionar un centro puede mover varios
> ejes. Valide la tabla instalada y los límites antes de usarla.

## Antes de publicar el repositorio

- Elimine contraseñas y credenciales embebidas; rótelas si ya fueron
  compartidas.
- Revise especialmente `rpi/leeme.txt`, notas de PocketBeagle,
  `g2m/soft_reset.sh` y `g2m/recupera_comm.sh`.
- No publique bases SQLite, archivos Excel, logs, PID, entornos virtuales,
  archivos temporales, `.DS_Store`, paquetes generados ni archivos swap.
- Revise que configuraciones locales no expongan infraestructura innecesaria.
- Confirme que límites, offsets y parámetros persistentes corresponden al
  hardware instalado antes de etiquetar una versión.

## Archivos importantes

| Archivo | Función |
|---|---|
| `rpi/dist/g2mdrvmqtt_edgar.py` | Puente MQTT, límites, offsets y publicación de estado/configuración. |
| `rpi/dist/servg2m_edgar_v2.py` | Servidor TCP principal `9055`. |
| `rpi/dist/instruccionesguiador.py` | Intérprete, conversiones, centros y comandos de ejes. |
| `rpi/dist/comservobbred.py` | Comunicación con servos de PocketBeagle. |
| `rpi/dist/guiador2m.cfg` | Parámetros persistentes PID y movimiento. |
| `rpi/dist/scripts/config_ips_g2m.sh` | Asociación serial USB, eje y subred. |
| `rpi/config/limites-motores-guiador-2m.json` | Límites y márgenes autoritativos. |
| `rpi/config/offsets-cero-mecanicos-2m.json` | Offsets iniciales versionados. |
| `rpi/estadopockets.sh` | Monitor continuo de las cuatro PocketBeagles. |
| `rpi/estadorpi.sh` | Estado de la Raspberry Pi. |
| `rpi/supervisor/guiador_services.conf` | Programas administrados por Supervisor. |
| `rpi/supervisor/supervisord.conf` | Socket, puerto y log de Supervisor. |
| `g2m/nuevo-guiador-motores.sh` | Arranque habitual de servicios e interfaces. |
| `g2m/fns_g2m.sh` | Funciones de operación TCP desde shell. |
| `g2m/G2M_Logger/mqtt_logger.py` | Registro de estado MQTT en SQLite. |
| `pocketbb/aplica.sh` | Arranque del chroot y SSH de PocketBeagle. |
| `pocketbb/app/aplica.sh` | Arranque de la aplicación de servo. |
| `test_epl/epls/gsc/gscmonitorepl.py` | Endpoint MQTT del GSC. |
| `test_epl/epls/consola/consolad/consola_oop_monitor.py` | Endpoint MQTT/socket de consola. |
| `test_epl/uiepls/motoresui/src/mgsubendp_2m.py` | Endpoint MQTT de la UI de motores. |
| `test_epl/uiepls/motoresui/src/motgui-2m.py` | Interfaz de motores. |

## Discrepancias conocidas

- El broker activo comprobado en backend, EPL y UI es `192.168.0.237`.
- ZOOM está implementado en backend y PocketBeagle, pero oculto en la UI actual
  mediante `enable_Zoom = False`.
- La UI publica `actualiza_coordenadas` y escucha `comando`; el backend MQTT
  activo de motores no maneja esos tópicos.
- La UI contiene conversiones iniciales distintas. Las autoritativas son las
  del backend y la configuración MQTT recibida.
- `rpi/dist/guiador2m.cfg` contiene `CCONTROL_PIDX` para ZOOM, posible error
  pendiente de validación.
- Supervisor descarta stdout/stderr de sus programas; sólo configura el log
  general `/var/log/supervisor/supervisord.log`.
- Hay credenciales embebidas y archivos generados dentro del árbol. Deben
  sanearse antes de publicar.
