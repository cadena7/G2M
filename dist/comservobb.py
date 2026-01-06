
import sys
import os
import time
from  socket import *
import subprocess

from  cinterprete import Interprete 

datos = { 'X':0.0 ,
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
          'CA_AHD':0.0
          }
          
          
miInt = Interprete()

def inicia():
    miInt.pon_mando('X', fn_pos_x)
    miInt.pon_mando('Y', fn_pos_y)
    miInt.pon_mando('XD', fn_pos_xd)
    miInt.pon_mando('YD', fn_pos_yd)
    miInt.pon_mando('XT', fn_pos_xt)
    miInt.pon_mando('YT', fn_pos_yt)
    miInt.pon_mando('PIX', fn_pos_inicio_x)
    miInt.pon_mando('PIY', fn_pos_inicio_y)
    miInt.pon_mando('BIX', fn_b_inicio_x)
    miInt.pon_mando('BIY', fn_b_inicio_y)
    miInt.pon_mando('SW', fn_sw)
    miInt.pon_mando('CA_AHD', fn_ca_ahd)


def manda( str1 ):
    """ """
    #arch = "/usr/local/instrumentacion/com/servobb/socket"
    arch = "/srv/com/servobb/socket"
    try:
        s = socket(AF_UNIX, SOCK_STREAM)
        s.connect(arch)
    except IOError:
        print( "connect" )
        s.close()
        s = None
    
    if s is None:
        print( 'could not open socket' )
        return "Nada"

    ## s.settimeout(.1)
    s.send( str1.encode('utf-8'  ) )
       
    total_data=[]
    while True:
        data = s.recv(1024)
        if not data: 
            break
        total_data.append(data)
        ##print "DATA",total_data
        td = b''.join(total_data)
        if b'Ok' in td:
            break
    total_data = b''.join(total_data)
    s.close()
    data1 = str( total_data , 'UTF-8')
    ## data1 = total_data.replace("=", " ")
    ##print "DATA1",data1
    return( data1 )



def mueve_x(pos):
    try:
        str1 = "X= %d" % pos
        manda(str1)
    except:
        print( "mueve_x: Error al mandar",pos )


def mueve_y(pos):
    try:
        str1 = "Y= %d" % pos
        manda(str1)
    except:
        print( "mueve_y: Error al mandar",pos )


def pon_bandera_busca_inicio_x(pos):
    try:
        str1 = "BBIX %d" % ( pos & 1 )
        manda(str1)
    except:
        print( "BBIX : Error al mandar",pos  )


def pon_bandera_busca_inicio_y(pos):
    try:
        str1 = "BBIY %d" % ( pos & 1)
        manda(str1)
    except:
        print( "BBIY : Error al mandar",pos )



def inicia_busca_inicios_x():
    pon_bandera_busca_inicio_x( 0 )
    time.sleep(0.1)
    pon_bandera_busca_inicio_x( 1 )

def cancela_busca_inicios_x():
    pon_bandera_busca_inicio_x( 0 )



def inicia_busca_inicios_y():
    pon_bandera_busca_inicio_y( 0 )
    time.sleep(0.1)
    pon_bandera_busca_inicio_y( 1 )

def cancela_busca_inicios_y():
    pon_bandera_busca_inicio_y( 0 )


def fn_ca_ahd():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        print(  "CA_AHD=", n1 )
        datos['CA_AHD'] = n1
    return n1
    


def fn_pos_x():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        #print  "pos x=", n1
        datos['X'] = n1
    return n1

def fn_pos_xd():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        #print  "pos x=", n1
        datos['XD'] = n1
    return n1


def fn_pos_xt():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        #print  "pos x=", n1
        datos['XT'] = n1
    return n1




def fn_pos_y():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        #print  "pos y=", n1
        datos['Y'] = n1
    return n1


def fn_pos_yd():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        #print  "pos y=", n1
        datos['YD'] = n1
    return n1

def fn_pos_yt():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        #print  "pos y=", n1
        datos['YT'] = n1
    return n1



def fn_pos_inicio_x():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        #print  "pos ini x=", n1
        datos['PIX'] = n1
    return n1


def fn_pos_inicio_y():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        #print  "pos ini y=", n1
        datos['PIY'] = n1
    return n1



def fn_b_inicio_x():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        #print  "b ini x=", "0x%x" % n1
        datos['BIX'] = n1
    return n1


def fn_b_inicio_y():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        #print  "b ini y=", "0x%x" % n1
        datos['BIY'] = n1
    return n1



    
def fn_sw():
    n1 = miInt.saca_token_numero()
    if n1 != None :
        ## print  "sw=", n1
        datos['SW'] = n1
    return n1
    

def pide_estado():
    s1 = manda('ESTADO')
    s2 = s1.replace("="," ")
    s2 = s2.replace("\n"," ")
    miInt.interpreta( s2)



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
    inicia()
    s1= manda("ESTADO")
    print( s1 )
    s1= manda("X= 10000 Y= 20000")
    print( s1 )
    s1= manda("ESTADO")
    print( s1 )
    pide_estado()
    print( datos )
