
import re
from  collections import deque



NUM_HEX = 'NUM_HEX'
NUM_ENT = 'NUM_ENT'
NUM_FLT = 'NUM_FLT'
INSTRUCCION = 'INSTRUCCION'

tokens_exprs = [
    (r'\+[A|D]', INSTRUCCION ),
    (r'^\+|^-[A-Za-z]+' , INSTRUCCION),
    (r'[A-Za-z][A-Za-z0-9_,.=]*' ,    INSTRUCCION),
    (r'[A-Za-z][A-Za-z0-9_,+-]*' ,    INSTRUCCION),
    (r'[A-Za-z][A-Za-z0-9_,+-?]*' ,    INSTRUCCION),
    (r'(0x)[A-F0-9]+' ,                 NUM_HEX),
    (r'^\+|^-[\d]+' ,                    NUM_ENT),
    (r'[\d]+' ,                                NUM_ENT),
    (r'^\+|^-[\d]+\.[\d]+' ,         NUM_FLT),
    (r'[\d]+\.[\d]+' ,                     NUM_FLT),
    (r'^\+|^-\.[\d]+' ,         NUM_FLT),
    (r'^\.[\d]+' ,         NUM_FLT)
]




class Interprete():
    """
    clase para una cola de tokens sencilla
    decodifica numeros y strings
    """
    cola_tokens = []
    mandos = []
    lista_re = []

    def __init__(self):
        self.cola_tokens = deque()
        self.mandos={ 'Nada': None }
        self.lista_re = self.crea_regexps()
        ##def inicia_modulo():


        
    def  pon_mando( self, nombre, fn ):
        self.mandos.update( {nombre:fn} )
        
    def hay_tokens(self):
        sal = False
        if( len( self.cola_tokens) > 0 ):
            sal = True
        return sal

    def checa_token_tipo(self):
        tipo = None
        ## print self.cola_tokens
        if( self.hay_tokens() ):
            token,tipo = self.cola_tokens[0]
            ## print "tipo :",tipo
        return tipo

    def saca_token(self):
        token,tipo = self.cola_tokens.popleft()
        return ( token,tipo )


    def pon_token( self, token ):
        self.cola_tokens.append( token )


    def checa_tipo_token_re(self, tok, lista_re ):
        for i in lista_re :
            regex, tag = i
            match = regex.match( tok )
            if ( match  and (match.end() == len(tok) )) :
                return ( (tok, tag ) )
        return ( (None, None) )


    def convierte_str_a_tokens(self, inst, lista_re ):
        l = inst.split(' ')
    ##print len(l),l
        for i in l:
            if( i != '' ):
                token, tipo = self.checa_tipo_token_re( i, lista_re )
            ## print token, tipo
                self.pon_token( (token,tipo) )
            
    
    
    def ejec_cola(self):
        l1=[]
        while ( len( self.cola_tokens ) != 0 ) :
            token,tipo = self.cola_tokens.popleft()
        ## print "saco token",token,tipo
            if( token in self.mandos ):
                ## print "ejec",token
                inst=self.mandos[token]
                l1.append( inst() )
        return l1



    def crea_regexps(self):
        lista_re = []
        for i in tokens_exprs :
            patron, tag = i
            regex = re.compile(patron)
            lista_re.append( (regex,tag) )
        return lista_re

    def interpreta(self, string1 ):
        self.convierte_str_a_tokens(string1, self.lista_re )
        ## print "Cola tokens", self.cola_tokens
        l1 = self.ejec_cola()
        return str(l1)

    def interpreta_sin_ejec(self, string1 ):
        self.convierte_str_a_tokens(string1, self.lista_re )
    

    def saca_token_numero(self):
        tipo = self.checa_token_tipo()
        if(  tipo == NUM_ENT or tipo == NUM_FLT   ):
            n2,tipo = self.saca_token()
            try:
                nx = float(n2)
                pass
            except:
                nx = 0.0
                return None
            return( float(nx) )
        if(  tipo == NUM_HEX   ):
            n2,tipo = self.saca_token()
            try:
                n3 = int(n2,16)
                n3 = float(n3)
            except:
                return None
            return( n3 )
        return None
