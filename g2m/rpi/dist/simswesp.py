
from machine import Pin
import time

p22 = Pin(22,Pin.OUT)
p23 = Pin(23,Pin.OUT)

p16 = Pin(16,Pin.OUT)
p17 = Pin(17,Pin.OUT)

def pon_alto_index_dec():
    p23.on()
    p22.off()

def pon_bajo_index_dec():
    p23.off()
    p22.on()

def pon_alto_index_ar():
    p17.on()
    p16.off()

def pon_bajo_index_ar():
    p17.off()
    p16.on()



def has_togle_index_dec(tiempo):
    pon_alto_index_dec()
    time.sleep_ms(tiempo)
    pon_bajo_index_dec()


def has_togle_index_ar(tiempo):
    pon_alto_index_ar()
    time.sleep_ms(tiempo)
    pon_bajo_index_ar()


def simula_ciclo_dec(tiempo):
    pon_alto_index_dec()
    time.sleep_ms(800)
    pon_bajo_index_dec()
    time.sleep_ms( 400 )
    has_togle_index_dec(tiempo)
    
pon_bajo_index_dec()
pon_bajo_index_ar()

def simula_una_busca_dec(t1,t2,t3):
    pon_alto_index_dec()
    print("en alto")
    time.sleep_ms(t1)
    pon_bajo_index_dec()
    print("en bajo")
    time.sleep_ms(t2)
    has_togle_index_dec(t3)
    print("fin")

def simula_una_busca_ar(t1,t2,t3):
    pon_alto_index_ar()
    print("en alto")
    time.sleep_ms(t1)
    pon_bajo_index_ar()
    print("en bajo")
    time.sleep_ms(t2)
    has_togle_index_ar(t3)
    print("fin")
