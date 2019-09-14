#!/usr/bin/env python3

from os import path
import socket
import struct 
import yaml

def ip2long(ip): #convierte octetos a long
  return struct.unpack("!L", socket.inet_aton(ip))[0]

def long2ip(ip): #convierte long en octetos
  return socket.inet_ntoa(struct.pack("!L",ip))

def ipmask(bits): #crea un mascara de la cantidad bits en formato long
  return ((1<<(bits))-1)<<(32-bits)

def iprange(ip,mask): #entrega una tupla con la primera y ultima ip del rango
  return [ip&ipmask(mask),ip|(ipmask(mask)^(1<<32)-1)]
  
############################################################################################

# sacar configuración del yaml

assert path.exists("Settings.yml"), 'Settings file not found: Settings.yml'
new_map = yaml.load(open("Settings.yml"), Loader=yaml.FullLoader)
PublicRange_yaml = new_map['PublicRange']
PrivateRange_yaml = new_map['PrivateRange']
RuleInitNumber_yaml = int(new_map['RuleInitNumber'])

# crear rangos públicos disponibles y configuración vyos (interfaces y nat)

PublicsIP = dict()
listWan = 0 # mapping list to id

for subnet in PublicRange_yaml:
    listWan = listWan + 1
    PublicsIP[listWan] = dict()
    longIP = ip2long(subnet['SubnetID']) #creamos el long
    extremos = iprange(longIP,subnet['MaskBits']) #entregamos long y mascara
    PublicsIP[listWan]['range'] = range(extremos[0]+1,extremos[1]) #creamos un array
    PublicsIP[listWan]['MaskBits'] = subnet['MaskBits'] # guardamos mascara
    PublicsIP[listWan]['DiscardIP'] = subnet['DiscardIP'] # guardamos lista de IP,s no usables 
    PublicsIP[listWan]['Gateway'] = ip2long(subnet['Gateway']) # guardamos lista de IP,s no usables 
    PublicsIP[listWan]['Interface'] = subnet['Interface'] # guardamos interface subnet pública
    
# creamos/sobreescribimos archivo de texto donde se guardarán todos los comandos
    
f = open("commands.txt","w+")

# Creamos listado IP públicas disponibles y creamos reglas nat.

ruleNumber = RuleInitNumber_yaml - 1

for i in range (1, listWan+1):
    for x in PublicsIP[i]['range']:
        discard = False
        for z in PublicsIP[i]['DiscardIP']:
            if ip2long(z) == x:
               discard = True
        if PublicsIP[i]['Gateway'] == x:
            discard = True
        if discard == False:
            ruleNumber = ruleNumber + 1
            f.write ("set interfaces ethernet {} address '{}/{}'\n" .format(PublicsIP[i]['Interface'], long2ip(x), PublicsIP[i]['MaskBits']))
            f.write ("set nat destination rule {} destination address '{}'\n" .format(ruleNumber, long2ip(x)))
            f.write ("set nat destination rule {} inbound-interface '{}'\n" .format(ruleNumber,PublicsIP[i]['Interface']))
            f.write ("set nat source rule {} outbound-interface '{}'\n" .format(ruleNumber,PublicsIP[i]['Interface']))
            f.write ("set nat source rule {} translation address '{}'\n" .format(ruleNumber, long2ip(x)))

# Creamos listado IP privadas y asociamos IP pública disponible con IP privada (hasta acabar IP,s públicas) y crear configuración vyos

PrivateIP = dict()
listLan = 0 # mapping list to id

for lannet in PrivateRange_yaml:
    listLan = listLan + 1
    PrivateIP[listLan] = dict()
    longIPLan = ip2long(lannet['SubnetID']) #creamos el long
    extremosLan = iprange(longIPLan,lannet['MaskBits']) #entregamos long y mascara
    PrivateIP[listLan]['rangeLan'] = range(extremosLan[0]+1,extremosLan[1]) #creamos un array
    PrivateIP[listLan]['discardLanIP'] = lannet['DiscardIP'] # guardamos lista de IP,s no usables 
    PrivateIP[listLan]['gatewayLan'] = ip2long(lannet['Gateway'])
    f.write ("set interfaces ethernet {} address '{}/{}'\n" .format(lannet['Interface'], lannet['Gateway'], lannet['MaskBits']))
    
ruleLanNumber = RuleInitNumber_yaml - 1

for i in range (1, listLan+1):
    for r in PrivateIP[i]['rangeLan']:
            discard = False
            for s in PrivateIP[i]['discardLanIP']:
                if ip2long(s) == r:
                   discard = True
            if PrivateIP[i]['gatewayLan'] == r:
                discard = True
            if discard == False:
                ruleLanNumber = ruleLanNumber + 1
                if ruleLanNumber <= ruleNumber:
                    f.write ("set nat destination rule {} translation address '{}'\n" .format(ruleLanNumber, long2ip(r)))
                    f.write ("set nat source rule {} source address '{}'\n" .format(ruleLanNumber, long2ip(r)))
                    
# Creamos ruta estática por defecto a las puertas de enlace públicas disponibles

for i in range (1, listWan+1):
    f.write ("set protocols static route 0.0.0.0/0 next-hop '{}'\n" .format(long2ip(PublicsIP[i]['Gateway'])))
    
# cerramos archivo y finalizamos.
    
f.close() 

print ("OK")