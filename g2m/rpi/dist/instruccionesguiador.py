
import time
import threading
import json

#import subprocess

from  cinterprete import Interprete

import ejeservo as ejes
import buscacentro as bcentros

Iitd = Interprete()

DatosGuiador = { 'ESC_PLACA' : 11.1,
                 'PPMMAR' : 1000.0,
                 'PPMMDEC' : 1000.0,
                 'PPMMFOCO':   (72000.0/1.5),
                 'PPGRADOZOOM' : 3600,
                 'OFFSET_CERO_AR': 0.0,
                 'OFFSET_CERO_DEC': 0.0,
                 'INC_AR': 1.0,
                 'INC_DEC': 1.0,
                 'INC_FOCO': 1.0,
                 'INC_ZOOM': 0.1,
                 'BUSCA_INICIO_AR': False,
                 'BUSCA_INICIO_DEC': False,
                 'BUSCA_INICIO_FOCO': False,
                 'BUSCA_INICIO_ZOOM': False
                }


def ar_arc_sec_2_pulsos( ar ):
    ppmar = DatosGuiador['PPMMAR']
    ep = DatosGuiador['ESC_PLACA']
    offsetCeroAR = DatosGuiador['OFFSET_CERO_AR']
    d = (ar / ep) * ppmar  - offsetCeroAR
    return d


def dec_arc_sec_2_pulsos( dec ):
    ppmdec = DatosGuiador['PPMMDEC']
    ep = DatosGuiador['ESC_PLACA']
    offsetCeroDEC = DatosGuiador['OFFSET_CERO_DEC']
    d = (dec / ep) * ppmdec  - offsetCeroDEC
    return d


def dame_str_tokens_con_token_final( itd , final):
    ok_manda = False
    l = []
    while  len( itd.cola_tokens ) != 0  :
        token,tipo = itd.cola_tokens.popleft()
        if token is None : continue
        if token == final :
            #print( "Fin de los mandos a motores" )
            ok_manda = True
            break
        else:
            l.append(token)
    #print( "LISTA",l )
    str1 = " ".join(l)
    #print( "String:", str1 )
    if ok_manda :
        sal =  str1 
    else:
        sal = f"Falta FIN DE CMD {final}"
    return sal, ok_manda



# Los ejes
# Modidicado marzo 2024 de acuerdo a JLOA (Chico y Cadena)
ejeAR = ejes.Eje( nombre="AR",ip="192.168.10.2")
ejeDEC = ejes.Eje( nombre="DEC",ip="192.168.9.2")
ejeFOCO = ejes.Eje( nombre="FOCO",ip="192.168.8.2")
ejeZOOM = ejes.Eje( nombre="ZOOM",ip="192.168.7.2")

ejeAR.pos_centro =   145000 + 75000
ejeDEC.pos_centro = 155000 + 105000
ejeZOOM.pos_centro = 1000
ejeFOCO.pos_centro = 72000*3

ejeAR.bandera_inicio = 0x4
ejeDEC.bandera_inicio = 0x4
ejeFOCO.bandera_inicio = 0x2
ejeZOOM.bandera_inicio = 0x2

ejeDEC.vel_normal = 40.0
ejeDEC.vel_centrado = 2.0


def fn_cambia_vel_normal_dec():
    v = Iitd.saca_token_numero()
    if v is None :
        return "Faltan params VEL NORMAL DEC"
    if v < 0 or v > 100 :
        return "Velocidad erronea"
    ejeDEC.vel_normal = v
    ejeDEC.cambia_velocidad_q(ejeDEC.vel_normal )
    return ""

def fn_cambia_vel_centrado_dec():
    v = Iitd.saca_token_numero()
    if v is None :
        return "Faltan params VEL CENTRADO DEC"
    if v < 0 or v > 100 :
        return "Velocidad erronea"
    ejeDEC.vel_centrado = v
    return ""


def fn_cambia_vel_normal_ar():
    v = Iitd.saca_token_numero()
    if v is None :
        return "Faltan params VEL NORMAL AR"
    if v < 0 or v > 100 :
        return "Velocidad erronea"
    ejeAR.vel_normal = v
    ejeAR.cambia_velocidad_q(ejeAR.vel_normal )
    return ""

def fn_cambia_vel_centrado_ar():
    v = Iitd.saca_token_numero()
    if v is None :
        return "Faltan params VEL CENTRADO AR"
    if v < 0 or v > 100 :
        return "Velocidad erronea"
    ejeAR.vel_centrado = v
    return ""




def fn_cmd_ejear():
    str2, ok =  dame_str_tokens_con_token_final( Iitd , "FCMD")
    if not ok  :
        return "Faltan params EJEAR"
    ejeAR.colaMsg.put( ('C', str2 ) )
    return ""


def fn_cmd_ejedec():
    str2, ok =  dame_str_tokens_con_token_final( Iitd , "FCMD")
    if not ok  :
        return "Faltan params EJEDEC"
    ejeDEC.colaMsg.put( ('C', str2 ) )
    return ""


def fn_cmd_ejezoom():
    str2, ok =  dame_str_tokens_con_token_final( Iitd , "FCMD")
    if not ok  :
        return "Faltan params EJEZOOM"
    ejeZOOM.colaMsg.put( ('C', str2 ) )
    return ""

def fn_cmd_ejefoco():
    str2, ok =  dame_str_tokens_con_token_final( Iitd , "FCMD")
    if not ok  :
        return "Faltan params EJEFOCO"
    ejeFOCO.colaMsg.put( ('C', str2 ) )
    return ""




def fn_mueve_ar():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params AR"
    ejeAR.mueve_q( ar_arc_sec_2_pulsos(h) )
    return ""

def fn_mueve_dec():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params DEC"
    # ejeDEC.mueve( h )
    ejeDEC.mueve_q( dec_arc_sec_2_pulsos(h) )
    return ""


def fn_mueve_foco():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params FOCO"
    ejeFOCO.mueve_q( h *  DatosGuiador['PPMMFOCO'])
    return ""


def fn_mueve_zoom():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params ZOOM"
    ejeZOOM.mueve_q( h*DatosGuiador['PPGRADOZOOM'] )
    return ""


def fn_esc_placa():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params ESC PLACA"
    if h < 1.0 or h > 40.0 :
        return "Error escala de placa"
    DatosGuiador['ESC_PLACA'] = h
    return ""

def fn_pon_inc_ar():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params PON INC AR"
    DatosGuiador['INC_AR'] = h
    return ""

def fn_pon_inc_dec():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params PON INC DEC"
    DatosGuiador['INC_DEC'] = h
    return ""

def fn_pon_inc_foco():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params PON INC FOCO"
    DatosGuiador['INC_FOCO'] = h
    return ""

def fn_pon_inc_zoom():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params PON INC ZOOM"
    DatosGuiador['INC_ZOOM'] = h
    return ""


def fn_set_debug():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params SETD"
    print("set debug", h )
    if h > 0 :
        ejeAR.set_debug( True )
        ejeDEC.set_debug( True )
        ejeFOCO.set_debug( True )
        ejeZOOM.set_debug( True )
    else:
        ejeAR.set_debug( False )
        ejeDEC.set_debug( False )
        ejeFOCO.set_debug( False )
        ejeZOOM.set_debug( False )
    return ""



def actualiza_estado_todos_los_ejes():
    ejeAR.pide_estado_q()
    ejeDEC.pide_estado_q()
    ejeFOCO.pide_estado_q()
    ejeZOOM.pide_estado_q()
    time.sleep( 0.5 )


def fn_estado_json():
    actualiza_estado_todos_los_ejes()
    edo = {}
    edo['ESC_PLACA'] = DatosGuiador['ESC_PLACA']
    edo['AR'] = ejeAR.mot.datos['X'] / ar_arc_sec_2_pulsos( 1.0 )
    edo['DEC'] = ejeDEC.mot.datos['X'] / dec_arc_sec_2_pulsos( 1.0 )
    edo['FOCO'] = ejeFOCO.mot.datos['X'] / DatosGuiador['PPMMFOCO']
    edo['ZOOM'] = ejeZOOM.mot.datos['X'] / DatosGuiador['PPGRADOZOOM']
    for eje in (ejeAR,ejeDEC,ejeFOCO,ejeZOOM):
        if eje.estado_busca_inicio == 100:
            edo['ERROR_BI_'+eje.nombre ] = True
            eje.buscando_inicio = False # si hay un error aca pues rest. la var de buscar inicio
        if eje.buscando_inicio :
            edo['INICIANDO_'+eje.nombre ] = True
        if eje.hallo_inicio:
            edo[ 'OK_CENTRO_' + eje.nombre ] = True
        if eje.mot.datos['ENLINEA'] == 0 :
            edo[ 'ERROR_COM_' + eje.nombre ] = True
    res = json.dumps(edo)
    return res

def fn_estado():
    actualiza_estado_todos_los_ejes()
    ar = ejeAR.mot.datos['X'] / ar_arc_sec_2_pulsos( 1.0 )
    dec = ejeDEC.mot.datos['X'] / dec_arc_sec_2_pulsos( 1.0 )
    foco = ejeFOCO.mot.datos['X'] / DatosGuiador['PPMMFOCO']
    zoom = ejeZOOM.mot.datos['X'] / DatosGuiador['PPGRADOZOOM']
    res = f"AR= {ar}  "
    res1 = f"DEC= {dec}   "
    res2 = f"FOCO= {foco}  "
    res3 = f"ZOOM= {zoom} "
    for eje in (ejeAR,ejeDEC,ejeFOCO,ejeZOOM):
        if eje.buscando_inicio :
            res3 += " INICIANDO_" + eje.nombre + " "
        if eje.estado_busca_inicio == 100:
            res3 += " EBC=" + eje.nombre.lower() + " "
        if eje.hallo_inicio:
            res3 += " OK_CENTRO_" + eje.nombre + " "
    return res+res1+res2+res3


def fn_estado_mas():
    ejeAR.pide_estado_q()
    ejeDEC.pide_estado_q()
    ejeFOCO.pide_estado_q()
    ejeZOOM.pide_estado_q()
    time.sleep( 0.5 )

    res = f"AR: {ejeAR.mot.datos['X']} , ARD={ejeAR.mot.datos} "
    res1 = f"DEC: {ejeDEC.mot.datos['X']} DECD={ejeDEC.mot.datos} "
    res2 = f"FOCO: {ejeFOCO.mot.datos['X']} FOCOD={ejeFOCO.mot.datos} "
    res3 = f"ZOOM: {ejeZOOM.mot.datos['X']} ZOOMD={ejeZOOM.mot.datos} "
    return res+res1+res2+res3


def fn_leearchcfg ():
    lines = [line.rstrip() for line in open('guiador2m.cfg')]
    #print (lines )
    for i in lines:
        Iitd.interpreta(i)
    return ""


def fn_ar_mas():
    pos = ar_arc_sec_2_pulsos(DatosGuiador['INC_AR'])
    ejeAR.colaMsg.put( ('R', pos) )
    return ""

def fn_ar_mas_len():
    pos = ar_arc_sec_2_pulsos( DatosGuiador['INC_AR']/10.0 )
    ejeAR.colaMsg.put( ('R', pos) )
    return ""

def fn_ar_menos():
    pos = ar_arc_sec_2_pulsos( -DatosGuiador['INC_AR'])
    ejeAR.colaMsg.put( ('R', pos) )
    return ""

def fn_ar_menos_len():
    pos = ar_arc_sec_2_pulsos( -DatosGuiador['INC_AR']/10 )
    ejeAR.colaMsg.put( ('R', pos) )
    return ""


def fn_dec_mas():
    pos = dec_arc_sec_2_pulsos(DatosGuiador['INC_DEC'])
    ejeDEC.colaMsg.put( ('R', pos) )
    return ""

def fn_dec_mas_len():
    pos = dec_arc_sec_2_pulsos( DatosGuiador['INC_DEC']/10.0 )
    ejeDEC.colaMsg.put( ('R', pos) )
    return ""

def fn_dec_menos():
    pos = dec_arc_sec_2_pulsos( -DatosGuiador['INC_DEC'])
    ejeDEC.colaMsg.put( ('R', pos) )
    return ""

def fn_dec_menos_len():
    pos = dec_arc_sec_2_pulsos( -DatosGuiador['INC_DEC']/10 )
    ejeDEC.colaMsg.put( ('R', pos) )
    return ""


def fn_foco_mas():
    pos = DatosGuiador['INC_FOCO'] * DatosGuiador['PPMMFOCO']
    ejeFOCO.colaMsg.put( ('R', pos) )
    return ""

def fn_foco_mas_len():
    pos = DatosGuiador['INC_FOCO'] * DatosGuiador['PPMMFOCO']
    ejeFOCO.colaMsg.put( ('R',  pos/10.0 ) )
    return ""

def fn_foco_menos():
    pos = DatosGuiador['INC_FOCO'] * DatosGuiador['PPMMFOCO']
    ejeFOCO.colaMsg.put( ('R', -pos) )
    return ""

def fn_foco_menos_len():
    pos = DatosGuiador['INC_FOCO'] * DatosGuiador['PPMMFOCO']
    ejeFOCO.colaMsg.put( ('R', -pos/10.0) )
    return ""


def fn_zoom_mas():
    pos = DatosGuiador['INC_ZOOM'] * DatosGuiador['PPGRADOZOOM']
    ejeZOOM.colaMsg.put( ('R', pos) )
    return ""


def fn_zoom_mas_len():
    pos = DatosGuiador['INC_ZOOM'] * DatosGuiador['PPGRADOZOOM']
    ejeZOOM.colaMsg.put( ('R', pos/10.0) )
    return ""

def fn_zoom_menos():
    pos = DatosGuiador['INC_ZOOM'] * DatosGuiador['PPGRADOZOOM']
    ejeZOOM.colaMsg.put( ('R', -pos) )
    return ""

def fn_zoom_menos_len():
    pos = DatosGuiador['INC_ZOOM'] * DatosGuiador['PPGRADOZOOM']
    ejeZOOM.colaMsg.put( ('R', -pos/10.0) )
    return ""



def fn_busca_inicio_foco():
    if ejeFOCO.buscando_inicio :
        return "YA ESTA BUSCANDO INICIO"
    DatosGuiador['BUSCA_INICIO_FOCO'] = True
    ejeFOCO.buscando_inicio = True
    return ""

def fn_busca_inicio_ar():
    if ejeAR.buscando_inicio :
        return "YA ESTA BUSCANDO INICIO"
    DatosGuiador['BUSCA_INICIO_AR'] = True
    ejeAR.buscando_inicio = True
    return ""


def fn_busca_inicio_dec():
    if ejeDEC.buscando_inicio :
        return "YA ESTA BUSCANDO INICIO"
    DatosGuiador['BUSCA_INICIO_DEC'] = True
    ejeDEC.buscando_inicio = True
    return ""

def fn_busca_inicio_zoom():
    if ejeZOOM.buscando_inicio :
        return "YA ESTA BUSCANDO INICIO"
    DatosGuiador['BUSCA_INICIO_ZOOM'] = True
    ejeZOOM.buscando_inicio = True
    return ""


def fn_cancela_inicio_foco():
    #DatosGuiador['BUSCA_INICIO_FOCO'] = False
    ejeFOCO.buscando_inicio = False
    return ""


def fn_cancela_inicio_ar():
    #DatosGuiador['BUSCA_INICIO_AR'] = False
    ejeAR.buscando_inicio = False
    return ""


def fn_cancela_inicio_dec():
    #DatosGuiador['BUSCA_INICIO_DEC'] = False
    ejeDEC.buscando_inicio = False
    return ""

def fn_cancela_inicio_zoom():
    #DatosGuiador['BUSCA_INICIO_ZOOM'] = False
    ejeZOOM.buscando_inicio = False
    return ""



def arranca_hebra_inicio_foco():
    DatosGuiador['BUSCA_INICIO_FOCO'] = False
    res = bcentros.busca_centro_foco( ejeFOCO )
    print("Termino busca inicio FOCO")

def arranca_hebra_inicio_ar():
    DatosGuiador['BUSCA_INICIO_AR'] = False
    #res = bcentros.identif_pos_regla( ejeAR)
    #if res == -1 :
    #    print("No identif eje AR ")
    bcentros.busca_centro_regleta( ejeAR )
    print("Termino busca inicio AR")

def arranca_hebra_inicio_dec():
    DatosGuiador['BUSCA_INICIO_DEC'] = False
    #res = bcentros.identif_pos_regla( ejeDEC)
    #if res == -1 :
    #    print("No identif eje DEC ")
    bcentros.busca_centro_regleta( ejeDEC )
    print("Termino busca inicio DEC")

def arranca_hebra_inicio_zoom():
    DatosGuiador['BUSCA_INICIO_ZOOM'] = False
    res = bcentros.busca_centro_zoom( ejeZOOM)
    print("Termino busca inicio zoom")


def  fn_pos_centro_ar():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params POS_CENTRO AR"
    ejeAR.pos_centro = h
    return ""




def  fn_pos_centro_dec():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params POS_CENTRO DEC"
    ejeDEC.pos_centro = h

    

def  fn_pos_centro_foco():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params POS_CENTRO FOCO"
    ejeFOCO.pos_centro = h
    return ""


def  fn_pos_centro_zoom():
    h = Iitd.saca_token_numero()
    if h is None :
        return "Faltan params POS_CENTRO ZOOM"
    ejeZOOM.pos_centro = h
    return ""

def fn_def_cero_zoom():
    ejeZOOM.colaMsg.put( ('C', 'RST_S' ) )
    return ""


def fn_def_cero_ar():
    ejeAR.colaMsg.put( ('C', 'RST_S' ) )
    return ""

def fn_def_cero_dec():
    ejeDEC.colaMsg.put( ('C', 'RST_S' ) )
    return ""

def fn_def_cero_foco():
    ejeFOCO.colaMsg.put( ('C', 'RST_S' ) )
    return ""


def fn_rst_bandera_err():
    for eje in ( ejeAR, ejeDEC, ejeFOCO, ejeZOOM ):
        eje.rst_banderas_inicio()
    return "RST BANDERAS"



def hebra_busca_ceros():
    print("Inicia hebra busca inicios")
    while True:
        time.sleep(0.5)
        if DatosGuiador['BUSCA_INICIO_FOCO'] :
            hebra = threading.Thread(target=arranca_hebra_inicio_foco)
            hebra.start()
        if DatosGuiador['BUSCA_INICIO_AR'] :
            hebra = threading.Thread(target=arranca_hebra_inicio_ar)
            hebra.start()
        if DatosGuiador['BUSCA_INICIO_DEC'] :
            hebra = threading.Thread(target=arranca_hebra_inicio_dec)
            hebra.start()
        if DatosGuiador['BUSCA_INICIO_ZOOM'] :
            hebra = threading.Thread(target=arranca_hebra_inicio_zoom)
            hebra.start()





def inicia():
    Iitd.pon_mando('SETD', fn_set_debug)
    Iitd.pon_mando('AR=', fn_mueve_ar)
    Iitd.pon_mando('DEC=', fn_mueve_dec)
    Iitd.pon_mando('FOCO=', fn_mueve_foco)
    Iitd.pon_mando('ZOOM=', fn_mueve_zoom)
    Iitd.pon_mando('EG?', fn_estado)
    Iitd.pon_mando('EGJ', fn_estado_json)
    Iitd.pon_mando('EG+', fn_estado_mas)
    Iitd.pon_mando('ESC_PLACA=', fn_esc_placa)
    Iitd.pon_mando('AR+', fn_ar_mas)
    Iitd.pon_mando('ARL+', fn_ar_mas_len)
    Iitd.pon_mando('AR-', fn_ar_menos)
    Iitd.pon_mando('ARL-', fn_ar_menos_len)
    Iitd.pon_mando('DEC+', fn_dec_mas)
    Iitd.pon_mando('DECL+', fn_dec_mas_len)
    Iitd.pon_mando('DEC-', fn_dec_menos)
    Iitd.pon_mando('DECL-', fn_dec_menos_len)
    Iitd.pon_mando('FOC+', fn_foco_mas)
    Iitd.pon_mando('FOCL+', fn_foco_mas_len)
    Iitd.pon_mando('FOC-', fn_foco_menos)
    Iitd.pon_mando('FOCL-', fn_foco_menos_len)
    Iitd.pon_mando('Z+', fn_zoom_mas)
    Iitd.pon_mando('ZL+', fn_zoom_mas_len)
    Iitd.pon_mando('Z-', fn_zoom_menos)
    Iitd.pon_mando('ZL-', fn_zoom_menos_len)
    Iitd.pon_mando('RESTABLECE_BANDERA_ERR', fn_rst_bandera_err)
    Iitd.pon_mando('BUSCA_CENTRO_FOCO', fn_busca_inicio_foco)
    Iitd.pon_mando('CANCELA_INICIO_FOCO', fn_cancela_inicio_foco)
    Iitd.pon_mando('BUSCA_CENTRO_AR', fn_busca_inicio_ar)
    Iitd.pon_mando('CANCELA_INICIO_AR', fn_cancela_inicio_ar)
    Iitd.pon_mando('BUSCA_CENTRO_DEC', fn_busca_inicio_dec)
    Iitd.pon_mando('CANCELA_INICIO_DEC', fn_cancela_inicio_dec)
    Iitd.pon_mando('BUSCA_CENTRO_ZOOM', fn_busca_inicio_zoom)
    Iitd.pon_mando('CANCELA_INICIO_ZOOM', fn_cancela_inicio_zoom)
    Iitd.pon_mando('POS_CENTRO_AR', fn_pos_centro_ar)
    Iitd.pon_mando('POS_CENTRO_DEC', fn_pos_centro_dec)
    Iitd.pon_mando('POS_CENTRO_FOCO', fn_pos_centro_foco)
    Iitd.pon_mando('POS_CENTRO_ZOOM', fn_pos_centro_zoom)
    Iitd.pon_mando('PON_INC_AR=', fn_pon_inc_ar)
    Iitd.pon_mando('PON_INC_DEC=', fn_pon_inc_dec)
    Iitd.pon_mando('PON_INC_FOCO=', fn_pon_inc_foco)
    Iitd.pon_mando('PON_INC_ZOOM=', fn_pon_inc_zoom)
    Iitd.pon_mando('DEF_CERO_AR', fn_def_cero_ar)
    Iitd.pon_mando('DEF_CERO_DEC', fn_def_cero_dec)
    Iitd.pon_mando('DEF_CERO_FOCO', fn_def_cero_foco)
    Iitd.pon_mando('DEF_CERO_ZOOM', fn_def_cero_zoom)
    Iitd.pon_mando('EJEAR', fn_cmd_ejear)
    Iitd.pon_mando('EJEDEC', fn_cmd_ejedec)
    Iitd.pon_mando('EJEFOCO', fn_cmd_ejefoco)
    Iitd.pon_mando('EJEZOOM', fn_cmd_ejezoom)
    Iitd.pon_mando('VEL_NORMAL_DEC', fn_cambia_vel_normal_dec)
    Iitd.pon_mando('VEL_CENTRADO_DEC',  fn_cambia_vel_centrado_dec)
    Iitd.pon_mando('VEL_NORMAL_AR', fn_cambia_vel_normal_ar)
    Iitd.pon_mando('VEL_CENTRADO_AR',  fn_cambia_vel_centrado_ar)
    Iitd.pon_mando('LEECFG', fn_leearchcfg)
    fn_leearchcfg()
    

def interpreta(str1):
    #if checa_si_esta_buscando_inicios():
    #    return "Ocupado " + "ESTADO_G= " + str(telvars['ESTADO']) + " "
    s = Iitd.interpreta(str1)
    time.sleep( .04 )
    return s
