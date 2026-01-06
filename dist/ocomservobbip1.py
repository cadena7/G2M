
from subprocess import *
import re
import time

params = {
    'X': ['^X=([-|\d+]?\d+.\d+)'],
    'XD': ['^XD=([-|\d+]?\d+.\d+)'],
    'Y': ['^Y=([-|\d+]?\d+.\d+)'],
    'Z': ['^Z=([-|\d+]?\d+.\d+)'],
    'W': ['^W=([-|\d+]?\d+.\d+)'],
    'XT':['^XT=([-|\d+]?\d+.\d+)'],
    'YT':['^YT=([-|\d+]?\d+.\d+)'],
    'ZT':['^ZT=([-|\d+]?\d+.\d+)'],
    'WT':['^WT=([-|\d+]?\d+.\d+)'],
    'CTX':['^CTX=(\d+)'],
    'CTY':['^CTY=(\d+)'],
    'CTZ':['^CTZ=(\d+)'],
    'CTW':['^CTW=(\d+)'],
    'BIX':['^BIX=(.\w+)'],
    'PIX': ['^PIX=([-|\d+]?\d+.\d+)'],
    'UX' : [ 'UX=([-|\d+]?\d+)' ],
    'UY' : [ 'UY=([-|\d+]?\d+)' ],
    'UZ' : [ 'UZ=([-|\d+]?\d+)' ],
    'UW' : [ 'UW=([-|\d+]?\d+)' ], }
    
params2 = {
    'AH' : [ '^AH=([+|-]*\w+:\w+:\w+.\w+)' ],
    'DEC' : [ '^DEC=([+|-]*\w+:\w+:\w+.\w+)' ],
    'AR' : [ '^AR=(\w+:\w+:\w+.\w+)' ],
    'SW' : [ '^SW=(\w+)' ],
    'FRENOS' : ['FRENOS:(\w+)' ],
        
}


def pela_estado(l):
    hallo_x = False
    x = None
    dd = {'Base': 0 }
    for i in l:
        if( i.find("SW=" ) == 0 ):
            s1 = i+ l [ l.index(i)+1 ]
            i = s1
        if( i.find("FRENOS" ) == 0 ):
            s1 = i+ l [ l.index(i)+1 ]
            i = s1
        for p in params.items():
            #print p
            m = re.search(p[1][0],i)
            try:
                if( m ):
                    dd[ p[0] ] = float( m.group(1) )
            except Exception as e:
                dd[ p[0] ] = m.group(1)
                
        for p in params2.items():
            m = re.search(p[1][0],i)
            try:
                if( m ): dd[ p[0] ] = m.group(1)
            except:
                pass
    return dd


class OComServoIP:
    def __init__(self):
        self.host = "192.168.10.6"
        self.posicion = 0
        self.posicionDeseada = 0
        self.posicionDeseadaSP = 0
        self.u = 0
        
    def pon_host(self,h):
        self.host = h


    def manda(self,str1):
        qstr = "-q1" # p la raspberry
        qstr = "-q0"
        p1 = Popen(["echo", str1 ], stdout=PIPE)
        p2 = Popen(["nc", qstr,self.host, "9095"], stdin=p1.stdout, stdout=PIPE)
        p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        output = p2.communicate()[0]
        return output

    def mueve_a_posicion(self, pos):
        self.manda( f"X= {pos}")
        
    def pide_estado(self):
        qstr = "-q1"
        qstr = "-q0"
        p1 = Popen(["echo", "ESTADO" ], stdout=PIPE)
        p2 = Popen(["nc", qstr,self.host, "9095"], stdin=p1.stdout, stdout=PIPE)
        p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        outputb = p2.communicate()[0]
        output = outputb.decode()
        output = output.replace("\\n","\n")
        output = output.replace("[","")
        output = output.replace("'","")
        l1 = output.split()
        d1 = pela_estado(l1)
        if 'X' in d1.keys() :self.posicion = d1['X']
        if 'XT' in d1.keys() :self.posicionDeseada = d1['XT']
        if 'XD' in d1.keys() :self.posicionDeseadaSP = d1['XD']
        if 'UX' in  d1.keys() :self.u = d1['UX']
        return d1
    



    
if __name__ == '__main__' :
    
    #motx= OComServoIP()
    #motx.pon_host("192.168.10.6")
    
    moty =  OComServoIP()
    moty.pon_host("192.168.7.2")

    moty.manda("HABTASK")
    for i in [ -3300, 0  ] :
        #motx.manda("DAX %d" % i)
        moty.manda("DAX %d" % -i)
        #p = motx.pide_estado()
        
        #print(p)
        #print(motx.posicion)
        #print(motx.posicionDeseada)
        #print(motx.u)
        
        p = moty.pide_estado()
        print(p)
        print(moty.posicion)
        print(moty.posicionDeseada)
        print(moty.u)
        time.sleep(.5)
    print(">>>>inicia conf")
    moty.manda("RST RST")
    moty.manda("KPX 15 KIX .0015 KDX 4 AX= 0.0025 VX= 4.25")
    moty.manda("MAXPOSX 2000000 MINPOSX -2000000 CONTROL_PIDX")
    print(">>>fin conf")
    for i in [1000,2000,3000,2000,1000,0, -1000,-10000] :
        moty.mueve_a_posicion(i)
        edo = moty.pide_estado()
        print(moty.posicion)
        print(moty.posicionDeseada)
        print(moty.u)
        time.sleep(1)


