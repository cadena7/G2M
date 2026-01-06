
import time


BIT_HOME_FOCO = 8

def busca_centro_foco( eje ):
    eje.estado_busca_inicio = 0 # idle
    eje.hallo_inicio = False
    eje.colaMsg.put(('C','RST_S CONTROL_PIDX') )
    time.sleep( 0.5)
    eje.pide_estado_q()
    time.sleep( 0.5 )

    print("Inicia busca inicio ", eje.nombre )
    edo = int(eje.mot.datos['SW']) & BIT_HOME_FOCO
    posExtrema = (72000*150*10)/15
    eje.mot.inicia_busca_inicios_x()
    if edo :
        eje.mueve_q( -posExtrema )
    else:
        eje.mueve_q( posExtrema )
    time.sleep(1)
    cta = 0
    halloCambio = False

    while cta < 120 :
        eje.pide_estado_q()
        time.sleep( 0.5 )
        if int(eje.mot.datos['BIX']) & 0x800 == 0x800:
            print("Hallo home")
            halloCambio = True
            eje.mueve_q( eje.mot.datos['PIX'] )
            break
        cta = cta +1
        if eje.mot.fin_trayectoria() or eje.mot.en_posicion() :
            print("eje fin de tray:", eje.nombre)
            break
        if not eje.buscando_inicio:
            print("Cancela la busqueda:", eje.nombre)
            break

    eje.mot.pon_bandera_busca_inicio_x( 0 )

    if not halloCambio :
        print("Error no hallo home:", eje.nombre)
        eje.hallo_inicio = False
        eje.buscando_inicio = False
        eje.estado_busca_inicio = 100 # error
        return False

    pd = eje.mot.datos['PIX']  + eje.pos_centro
    eje.mueve_q(  pd )
    time.sleep( 0.5 )
    cta = 0
    halloCambio = False
    while cta < 120 :
        eje.pide_estado_q()
        time.sleep( 0.5 )
        if eje.mot.en_posicion() :
            halloCambio = True
            break
        if not eje.buscando_inicio:
            print("Cancela la busqueda")
            break
        cta = cta + 1

    if not halloCambio :
        eje.hallo_inicio = False
        eje.buscando_inicio = False
        eje.estado_busca_inicio = 100 # error
        return False

    eje.colaMsg.put(('C', "RST_S") )
    time.sleep(0.5)
    eje.colaMsg.put(('C', "CONTROL_PIDX") )
    eje.hallo_inicio = True
    eje.buscando_inicio = False
    eje.estado_busca_inicio = 0
    return True


def identif_pos_regla(eje):
    print("Inicio de la ident. pos regleta heid. ",eje.nombre)
    eje.hallo_inicio = False
    eje.colaMsg.put(('C', "RST_S") )
    time.sleep(0.5)
    eje.colaMsg.put(('C', "CONTROL_PIDX") )
    time.sleep(0.5)
    eje.mot.inicia_busca_inicios_x()
    eje.pide_estado_q()
    time.sleep( 0.5 )
    eje.mueve_q( 1.5*10000.0 ) # 1.5 cm
    cta = 0
    while cta<60: # 30 segs
        eje.pide_estado_q()
        time.sleep( 0.5 )
        if int(eje.mot.datos['BIX']) & 0x800 == 0x800 :
            break
        if not eje.buscando_inicio:
            print("Cancela la busqueda")
            eje.estado_busca_inicio = 100 # error
            return -1
        cta = cta +1

    eje.pide_estado_q()
    time.sleep( 0.5 )
    pos1 = 0
    if int(eje.mot.datos['BIX']) & 0x800 == 0x800 :
        pos1 = eje.mot.datos['PIX']
    else:
        print("No hallo el cambio en la entrada de inicio")
        eje.estado_busca_inicio = 100 # error
        return -1
    print("POS 1", eje.nombre,pos1)

    eje.mot.inicia_busca_inicios_x()
    eje.mueve_q( 2.5*10000.0 ) # a 2.5 cm
    time.sleep(.5)
    cta = 0
    while cta<60: # 30 segs
        eje.pide_estado_q()
        time.sleep( 0.5 )
        if int(eje.mot.datos['BIX']) & 0x800 == 0x800 :
            break
        if not eje.buscando_inicio:
            print("Cancela la busqueda")
            return
        cta = cta +1

    if not eje.buscando_inicio:
        print("Cancela la busqueda")
        eje.estado_busca_inicio = 100 # error
        return -1

    eje.pide_estado_q()
    time.sleep( 0.5 )
    pos2 = eje.mot.datos['PIX']
    print("POS 2", eje.nombre,pos2)
    # eje.buscando_inicio = False
    d = pos2 - pos1
    if  d <= 0 :
        print("Error pos2 < pos1 ")
        return -1
    # para simular q identifico las pos1 y pos2
    #if d >= 20000 or d <= 5000:
    #    return 45000
    if d >= 20000 or d <= 5000:
        print("Dif muy peq en las pos de la regleta")
        return -1
    # si llega aca es q identif la pos de la regleta
    if d > 10000 :
        n = d -10000
        p1 = ((n-20)*10000)/10
    else:
        k1 = 10000 - d
        p1 = ((k1-20)/10 +1 )*10000 + k1
    return p1

def busca_entrada_indice_cero(eje):
    """ Se asegura q el indice este en nivel cero"""
    i=0
    eje.pide_estado_q()
    time.sleep( 0.5 )
    pd = eje.mot.datos['X']
    print("INICIA BUSQUEDA DE SW EN CERO: ", eje.nombre)
    while i < 5 :
        eje.pide_estado_q()
        time.sleep( 0.5 )
        if eje.dame_estado_entrada_inicio() :
            pd = pd - 5*1000 # 5 mm p atras
            eje.mueve_q( pd )
            time.sleep(.5)
        else:
            return True # hallo cero en el indice
        # espera eje en posicion
        nt = 0
        eje.pide_estado_q()
        time.sleep( 0.5 )
        
        while nt < 20 and not eje.mot.fin_trayectoria() :
            eje.pide_estado_q()
            time.sleep( 0.5 )
            if eje.dame_estado_entrada_inicio() == 0 :
                print("Hallo cambio sw a cero", eje.nombre)
                break
            nt = nt + 1
            print("Esperando q llegue a -5 mm(rel)", eje.nombre)
        i = i + 1
    print("No hallo cambio en 5 intentos (INDICE)", eje.nombre)
    return False

def busca_centro_regleta(eje):
    eje.estado_busca_inicio = 0 # idle
    eje.cambia_velocidad_q( eje.vel_centrado )
    if busca_entrada_indice_cero(eje) == False :
        print("No cambia estado SW  eje  ", eje.nombre)
        eje.estado_busca_inicio = 100 # error
        eje.cambia_velocidad_q( eje.vel_normal )
        return False
    res = identif_pos_regla( eje )
    if res == -1 :
        print("No identif eje  ", eje.nombre)
        eje.estado_busca_inicio = 100 # error
        eje.cambia_velocidad_q( eje.vel_normal )
        return False
    print(">>>> Pos regleta = ", res)
    eje.estado_busca_inicio = 1 # mueve al centro
    eje.cambia_velocidad_q( eje.vel_normal )
    pd = eje.pos_centro - res
    eje.mueve_q( pd ) 
    time.sleep(.5)
    cta = 0
    #eje.buscando_inicio = True
    while cta < 240 :
        cta = cta + 1
        eje.pide_estado_q()
        time.sleep( 0.5 )
        if eje.mot.fin_trayectoria() or eje.mot.en_posicion() :
        #if  eje.mot.en_posicion() :
            print("eje fin de tray:", eje.nombre)
            break
        if not eje.buscando_inicio:
            print("Cancela la busqueda:", eje.nombre)
            eje.estado_busca_inicio = 100 # error
            return False
            

    eje.colaMsg.put(('C', "RST_S CONTROL_PIDX") )
    eje.estado_busca_inicio = 0 # OK
    eje.buscando_inicio = False
    eje.hallo_inicio = True
    return True


def busca_centro_zoom( eje ):
    eje.hallo_inicio = False
    eje.estado_busca_inicio = 0 # idle
    eje.colaMsg.put(('C','RST_S CONTROL_PIDX') )
    time.sleep( 1.5 )
    eje.mueve_q( -(100.0*10.0 ))
    time.sleep( 1 )
    cta = 0
    while cta < 120:
        eje.pide_estado_q()
        time.sleep( 0.5 )
        if eje.mot.fin_trayectoria() or eje.mot.en_posicion() :
            print("eje fin de tray:", eje.nombre)
            break
        if not eje.buscando_inicio:
            print("Cancela la busqueda:", eje.nombre)
            eje.estado_busca_inicio = 100 # error
            break
        cta = cta + 1

    eje.colaMsg.put(('C','RST_S CONTROL_PIDX') )
    time.sleep( 1.5 )
    cta = 0
    eje.estado_busca_inicio = 1 # mueve al centro
    eje.mueve_q( eje.pos_centro )
    time.sleep( 1 )
    d = eje.mot.datos['X']
    while cta < 120:
        eje.pide_estado_q()
        time.sleep( 0.5 )
        # d =  d - eje.mot.datos['X'] 
        # if abs(d) < 4 :
        #     print("No se mueve eje")
        #     break
        if  eje.mot.en_posicion() or eje.mot.fin_trayectoria() :
            print("Eje en pos central")
            break
        if not eje.buscando_inicio:
            print("Cancela la busqueda:", eje.nombre)
            eje.estado_busca_inicio = 100 # error
            break
        cta = cta +1
        d =  eje.mot.datos['X']
        
    eje.colaMsg.put(('C','RST_S CONTROL_PIDX') )
    eje.hallo_inicio = True
    eje.buscando_inicio = False
    return True
