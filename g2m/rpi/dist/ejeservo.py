
import time
import threading
from queue import Queue
import comservobbred as ServoPB


class Eje:
    """Manejo de un eje de mov comun"""
    def __init__( self, nombre,ip ):
        #self.pulsos_mm = 1000.0
        #self.pulsos_grado = 10.0
        self.usa_mm = True
        self.debug = True
        self.nombre = nombre
        self.mot =  ServoPB.ComServoRed()
        self.mot.pon_host( ip )
        self.colaMsg = Queue()
        #self.hebra_pide_estado
        self.hebra_eje = threading.Thread(target=self.hebra_comservo)
        self.buscando_inicio = False
        self.hallo_inicio = False
        self.estado_busca_inicio = 0 # 0 - idle, 1-buscando,  100-error
        self.pos_centro = 100
        self.bandera_inicio = 0x1
        self.vel_normal = 10.0
        self.vel_centrado = 1.0
        self.hebra_eje.start()

    def dame_estado_entrada_inicio(self):
        sal = False
        if int(self.mot.datos['SW']) & self.bandera_inicio != 0 :
            sal = True
        return sal
        
    def rst_banderas_inicio(self):
        self.hallo_inicio = False
        self.estado_busca_inicio = 0
        self.mot.datos['PIX'] = 0

    def set_debug(self,  d):
        self.debug = d

    def mueve(self, pos ):
        p = int(pos)
        if self.debug :
            print("MUEVE( ", self.nombre , "): ", p )
        self.mot.mueve_x( p )

    def mueve_rel(self, pos ):
        p = int(pos)
        if self.debug :
            print("MUEVE REL( ", self.nombre , "): ", p )
        self.mot.mueve_x_rel( p )


    def hebra_comservo(self):
        if self.debug :
            print("Hebra EJE: ", self.nombre, "arrancando")
        while True:
            m = self.colaMsg.get()
            if self.debug :
                print(f"HEBRA {self.nombre} {m}")
            if m[0] == 'E' :
                self.mot.pide_estado()
            if m[0] == 'M' :
                self.mueve( m[1] )
            if m[0] == 'R' : # mueve relativo
                self.mueve_rel( m[1] )
            if m[0] == 'C' :
                res = self.mot.manda_s( m[1] )
                print(res)
            if m[0] == 'X' :
                # cancela la busqueda de inicio
                self.buscando_inicio = False
            time.sleep(0.02)

    def pide_estado_q(self):
        self.colaMsg.put(('E','NADA'))

    def mueve_q(self,pos):
        self.colaMsg.put(('M',pos))

    def mueve_rel_q(self,pos):
        self.colaMsg.put(('R',pos))

    def cambia_velocidad_q(self, vel):
        self.velocidad = vel
        s = "VX= %4.2f" % (vel)
        self.colaMsg.put(('C',s))
