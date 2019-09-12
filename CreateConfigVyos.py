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
InterfacePublic_yaml = new_map['InterfacePublic']
InterfacePrivate_yaml = new_map['InterfacePrivate']
RuleInitNumber_yaml = int(new_map['RuleInitNumber'])

# crear rangos privados y públicos disponibles
PublicsIP = dict()
list = 0 # mapping list to id

for subnet in PublicRange_yaml:
    list = list + 1
    PublicsIP[list] = dict()
    longIP = ip2long(subnet['SubnetID']) #creamos el long
    extremos = iprange(longIP,subnet['MaskBits']) #entregamos long y mascara
    PublicsIP[list]['range'] = range(extremos[0]+1,extremos[1]) #creamos un array
    PublicsIP[list]['MaskBits'] = subnet['MaskBits'] # guardamos mascara
    PublicsIP[list]['DiscardIP'] = subnet['DiscardIP'] # guardamos lista de IP,s no usables 
    PublicsIP[list]['Gateway'] = ip2long(subnet['Gateway']) # guardamos lista de IP,s no usables 
    


#f = open("commands.txt","w+")


ruleNumber = RuleInitNumber_yaml - 1

for i in range (1, list+1): #lo que sea
    for x in PublicsIP[i]['range']:
        discard = False
        for z in PublicsIP[i]['DiscardIP']:
            if ip2long(z) == x:
               discard = True
        if PublicsIP[i]['Gateway'] == x:
            discard = True
        if discard == False:
#            print (long2ip(x))
            ruleNumber = ruleNumber + 1
            print ("set interfaces ethernet {} address '{}'" .format(InterfacePublic_yaml, long2ip(x)))
            print ("set nat destination rule {} destination address '{}'" .format(ruleNumber, long2ip(x)))
            print ("set nat destination rule {} inbound-interface '{}'" .format(ruleNumber,InterfacePublic_yaml))
            print ("set nat source rule {} outbound-interface '{}'" .format(ruleNumber,InterfacePublic_yaml))
            print ("set nat source rule {} translation address '{}'" .format(ruleNumber, long2ip(x)))


print ("OK")