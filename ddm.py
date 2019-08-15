#!/usr/bin/env python

import sys
import logging
from jsonrpclib import Server
import subprocess
import re

baseOid = '.1.3.6.1.4.1.30065.100.1'

oidTable = {
  'oids':{
    1:{'name':'DDMTable',
       'oids':{
         1:{'name':'DDMEntry',
            'oids':{
              1:{'oid':1,'table':1,'name':'aristaDDMupdateTime','type':'TimeTicks'},
              2:{'oid':2,'table':1,'name':'aristaDDMtxPower','type':'Integer32'},
              3:{'oid':3,'table':1,'name':'aristaDDMtxBias','type':'Integer32'},
              4:{'oid':4,'table':1,'name':'aristaDDMrxPower','type':'Integer32'},
              5:{'oid':5,'table':1,'name':'aristaDDMvoltage','type':'Integer32'},
              6:{'oid':6,'table':1,'name':'aristaDDMtemperature','type':'Integer32'},
              7:{'oid':7,'table':1,'name':'aristaDDMvendorSn','type':'String'},
              8:{'oid':8,'table':1,'name':'aristaDDMnarrowBand','type':'Integer32'},
              9:{'oid':9,'table':1,'name':'aristaDDMmediaType','type':'String'}
             }
           }
         }
      }
   }
}

switch = Server("unix:/var/run/command-api.sock")

def getline():
    return sys.stdin.readline().strip()

def output(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def getPortDDM(param,port,obj):
    DDM = switch.runCmds(1,["show interfaces ethernet " + str(port) + " transceiver"])
    value = ''
    if (DDM[0] and DDM[0]["interfaces"] and DDM[0]["interfaces"]["Ethernet" + str(port)]):
        portDDM = DDM[0]["interfaces"]["Ethernet" + str(port)]
        if param == 'aristaDDMupdateTime':
            value = int(portDDM['updateTime'])
        if param == 'aristaDDMtxPower':
            value = int(float(portDDM['txPower'])*100)
        if param == 'aristaDDMtxBias':
            value = int(float(portDDM['txBias'])*100)
        if param == 'aristaDDMrxPower':
            value = int(float(portDDM['rxPower'])*100)
        if param == 'aristaDDMvoltage':
            value = int(float(portDDM['voltage'])*100)
        if param == 'aristaDDMtemperature':
            value = int(float(portDDM['temperature'])*100)
        if param == 'aristaDDMvendorSn':
            value = portDDM['vendorSn']
        if param == 'aristaDDMnarrowBand':
            value = 1 if portDDM['narrowBand'] == 'True' else 0
        if param == 'aristaDDMmediaType':
            value = portDDM['mediaType']
    return [obj['type'],str(value)]

def findOid(oids,oidsTable,oidsStr):
    if not oids:
        oids = [1]
    if "oids" in oidsTable[int(oids[0])]:
        return findOid(oids[1:],oidsTable[int(oids[0])]["oids"],oidsStr+str(oids[0])+'.')
    else:
        return [oidsTable[int(oids[0])]["name"]+'.'+'.'.join(oids[1:]),oidsTable[int(oids[0])],baseOid+'.'+oidsStr+oids[0]]

def parseOids(oid):
    match = re.search(r"^"+baseOid+'\.(.+)$',oid)
    if (match.group(1)):
        oids = match.group(1).split('.')
        return findOid(oids,oidTable["oids"],'')
    return []

def parsePortParam(name):
    (param,port) = name.split('.')
    if port:
        port = int(port)
    else:
        port = 0
    if (port < 1 or port > 52):
        port = 0
    return [param,port]

def main():
    try:
        while True:
            command = getline()
            if command == "":
                sys.exit(0)

            elif command == "PING":
                output("PONG")

            elif command == "set":
                oid = getline()
                type_and_value = getline()
                output("not-writable")

            elif command == "get":
                oid = getline()
                (name,obj,new_oids) = parseOids(oid)
                (param,port) = parsePortParam(name)
                if param and port:
                    (res_type, res_value) = getPortDDM(param,port,obj)
                    output(oid)
                    output(res_type)
                    output(res_value)
                else:
                    output('NONE')
                #output()

            elif command == "getnext":
                oid = getline()
                (name,obj,paramOid) = parseOids(oid)
                (param,port) = parsePortParam(name)
                if not port:
                    port = 1
                else:
                    port = port+1
                if param and port:
                    (res_type, res_value) = getPortDDM(param,port,obj)
                    output(paramOid+'.'+str(port))
                    output(res_type)
                    output(res_value)
                else:
                    output('NONE')
            else:
                oid = getline()
                output('NONE')

    except Exception, e:
        logging.exception("")
        raise

if __name__ == "__main__":
    main()
