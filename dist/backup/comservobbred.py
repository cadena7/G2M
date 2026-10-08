
import time
import socket


from  cinterprete import Interprete 


def manda( str1 , ELIP,ELPORT):
    """ """
    #arch = "/usr/local/instrumentacion/com/servobb/socket"
    # arch = "/srv/com/servobb/socket"
    str2 = str1+"\n"
    ntry = 0
    while ntry < 5:
        try:
            #print( f"Conectando {ELIP} {ELPORT}" )
            #s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            s = socket.create_connection( (ELIP,ELPORT), timeout=0.75)
            # s.settimeout(1.5)
            #s.connect( (ELIP,ELPORT) )
            #s = socket(AF_UNIX, SOCK_STREAM)
            # s.connect(arch)
        except socket.error:
            print( "connect" )
            #s.close()
            s = None

        if s is None:
            print( 'could not open socket' )
            print("No mando: ", str1, "intento:",ntry )
            #return "Nada"
        else:
            break
        ntry = ntry +1

    if ntry == 5 and s is None:
        print("No mando: ", str1, "intento:",ntry )
        return "Nada"

    s.sendall( str2.encode('utf-8'  ) )
    time.sleep( 0.25 )
    total_data=[]
    while True:
        data = b''
        try:
            data = s.recv(1024)
        except Exception as e:
            print("EXC: ",e )
            pass
        if not data:
            break
        total_data.append(data)
        #print( "DATA",total_data )
        td = b''.join(total_data)
        if b'Ok' in td:
            break
    total_data = b''.join(total_data)
    s.close()
    data1 = str( total_data , 'UTF-8')
    ## data1 = total_data.replace("=", " ")
    ##print "DATA1",data1
    return( data1 )



class ComServoRed:
    def __init__(self):
        self.host = "192.168.10.2"
        self.posicion = 0
        self.posicionDeseada = 0
        self.posicionDeseadaSP = 0
        self.u = 0
        self.datos = { 'X':0.0 ,
                       'Y': 0.0,
                       'XD':0.0,
                       'YD':0.0,
                       'XT':0.0,
                       'YT':0.0,
                       'PIX':0.0,
                       'PIY':0.0,
                       'BIX':0,
                       'BIY':0,
                       'SW':0,
                       'CA_AHD':0.0,
                       'ENLINEA' : 0
                      }
        self.miInt = Interprete()
        self.inicia()

    def en_posicion(self):
        sal = False
        if abs( self.datos['X'] - self.datos['XD'] ) < 100 :
            sal = True
        return sal

    def fin_trayectoria(self):
        sal = False
        if abs( self.datos['XD'] - self.datos['XT'] ) < 5 :
            sal = True
        return sal
    
        
    def inicia(self):
        self.miInt.pon_mando('X', self.fn_pos_x)
        self.miInt.pon_mando('Y', self.fn_pos_y)
        self.miInt.pon_mando('XD', self.fn_pos_xd)
        self.miInt.pon_mando('YD', self.fn_pos_yd)
        self.miInt.pon_mando('XT', self.fn_pos_xt)
        self.miInt.pon_mando('YT', self.fn_pos_yt)
        self.miInt.pon_mando('PIX', self.fn_pos_inicio_x)
        self.miInt.pon_mando('PIY', self.fn_pos_inicio_y)
        self.miInt.pon_mando('BIX', self.fn_b_inicio_x)
        self.miInt.pon_mando('BIY', self.fn_b_inicio_y)
        self.miInt.pon_mando('SW', self.fn_sw)
        self.miInt.pon_mando('CA_AHD', self.fn_ca_ahd)
        self.miInt.pon_mando('CTX', self.fn_ctx)
        self.miInt.pon_mando('UX', self.fn_ux)



    def pon_host(self,h):
        self.host = h


    def manda_s(self, str1 ):
        res = manda( str1, self.host, 9095 )
        return res

    def fn_ca_ahd(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print(  "CA_AHD=", n1 )
            self.datos['CA_AHD'] = n1
        return n1

    def fn_ctx(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            self.datos['CTX'] = n1
        return n1

    def fn_ux(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            self.datos['UX'] = n1
        return n1



    def fn_pos_x(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print  "pos x=", n1
            self.datos['X'] = n1
        return n1

    def fn_pos_xd(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print  "pos x=", n1
            self.datos['XD'] = n1
        return n1


    def fn_pos_xt(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print  "pos x=", n1
            self.datos['XT'] = n1
        return n1




    def fn_pos_y(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print  "pos y=", n1
            self.datos['Y'] = n1
        return n1


    def fn_pos_yd(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print  "pos y=", n1
            self.datos['YD'] = n1
        return n1

    def fn_pos_yt(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print  "pos y=", n1
            self.datos['YT'] = n1
        return n1



    def fn_pos_inicio_x(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print  "pos ini x=", n1
            self.datos['PIX'] = n1
        return n1


    def fn_pos_inicio_y(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print  "pos ini y=", n1
            self.datos['PIY'] = n1
        return n1



    def fn_b_inicio_x(self):
        n1 = self.miInt.saca_token_numero()
        if n1 != None :
            #print  "b ini x=", "0x%x" % n1
            self.datos['BIX'] = n1
        return n1


    def fn_b_inicio_y(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print  "b ini y=", "0x%x" % n1
            self.datos['BIY'] = n1
        return n1


    def fn_sw(self):
        n1 = self.miInt.saca_token_numero()
        if n1 is not None :
            #print(  "sw=", n1 )
            self.datos['SW'] = n1
        else:
            print("COMSERVO No cambio el SW ")
        return n1
    

    def pide_estado(self):
        s = manda('ESTADO', self.host, 9095)
        s2 = s.replace("="," ")
        s2 = s2.replace("\n"," ")
        if s2 == "Nada" :
            self.datos['ENLINEA'] = 0
            print("No se pudo conectar")
            return
        self.datos['ENLINEA'] = 1
        print("Interpreta ",s2)
        self.miInt.interpreta( s2)


    def mueve_x(self,pos):
        str1 = "X= %d" % pos
        self.manda_s(str1)

    def mueve_x_rel(self,pos):
        str1 = "X= %d" % ( self.datos['X'] + pos  )
        self.manda_s(str1)

    def pon_bandera_busca_inicio_x(self,pos):
        str1 = "BBIX %d" % ( pos & 1 )
        self.manda_s(str1)

    def inicia_busca_inicios_x(self):
        self.pon_bandera_busca_inicio_x( 0 )
        time.sleep(0.3)
        self.pon_bandera_busca_inicio_x( 1 )

#### FIN CLASE ####
## ComServoRed

def mueve_y(pos):
    try:
        str1 = "Y= %d" % pos
        manda(str1)
    except:
        print( "mueve_y: Error al mandar",pos )




def pon_bandera_busca_inicio_y(pos):
    try:
        str1 = "BBIY %d" % ( pos & 1)
        manda(str1)
    except:
        print( "BBIY : Error al mandar",pos )





def cancela_busca_inicios_x():
    pon_bandera_busca_inicio_x( 0 )



def inicia_busca_inicios_y():
    pon_bandera_busca_inicio_y( 0 )
    time.sleep(0.1)
    pon_bandera_busca_inicio_y( 1 )

def cancela_busca_inicios_y():
    pon_bandera_busca_inicio_y( 0 )





def reset_motores():
    #p1 = subprocess.Popen(['sh', './inicia_mot.sh'], stdout=subprocess.PIPE)
    #sal = p1.communicate()[0]
    #print sal
    manda("RST_S")
    time.sleep(0.1)
    manda("BITIX 16 BITIY 32")
    manda("CONTROL_PIDX CONTROL_PIDY")
    print( "reset motores" )


if __name__ == '__main__' :
    # inicia()
    obx = ComServoRed()
    obx.pon_host("192.168.9.2")
    s1= obx.manda_s("ESTADO")
    print( s1 )
    s1= obx.manda_s("X= 10000 Y= 20000")
    print( s1 )
    s1= obx.manda_s("ESTADO")
    print( s1 )
    obx.mueve_x( -1000 )
    obx.pide_estado()
    print( obx.datos )
