#!/usr/bin/python3

from pyModbusTCP.client import ModbusClient
from struct import *
import json
import re
import urllib.request
import urllib
import configparser
import argparse
c = configparser.ConfigParser()


TIMEOUT = 10
PORT = 502

SUNSPEC_I_COMMON_BLOCK_START = 40000
SUNSPEC_I_MODEL_BLOCK_START = 40069
SUNSPEC_M_COMMON_BLOCK_START = 40121
SUNSPEC_M_MODEL_BLOCK_START = 40188

parser = argparse.ArgumentParser(
                    prog = 'semodbus2domoticz',
                    description = 'Monitors SolarEdge inverters and sends the data to domoticz',
                    epilog = 'usage: semodbus2domoticz.py -c <path-to-config.ini>')

parser.add_argument('--config', dest='config',
                    default="/domoticz.ini",
                    help='provide the path to the .ini file with your local domoticz details')

args = parser.parse_args()

# with open(args.config, 'r') as f:
#   c = json.load(f)

c.read(args.config)

#####################################################################
# For Domoticz, please edit below to your own environment           # 
#####################################################################
domoip ="127.0.0.1" # Domoticz ipaddress.
dport = "8080" #Domoticz port number.
idxSEstat = 1000 # idx value of SolarEdge Status, Text device
idxActPwr = 1001 # idx value of SolarEdge Actual Power / Total Production, General, Kwh device
idxActPwr2 = 1002 # idx value of SolarEdge Actual Power / Total Production, General, Kwh device
idxACinv = 1003  # idx value of AC Inverter, Voltage device
idxac_i = 1004    # idx value of AC Inverter, Amp device
idxAC_f = 1005   # idx value of AC Inverter freqency text device
idxDCinv = 1006  # idx value of DC Inverter, Voltage device
idxdc_i = 1007     # idx value of DC Inverter, Amp device
idxEffin = 1008  # idx value of SolarEdge Efficiency, Percentage device
idxTemp  = 1009  # idx value of SolarEdge Temperature, Temperature device
idxTotPwr = 1010 # idx value of Total LifeTime Production, Custom Sensor

import os
print(os.environ['DOMOIP'])

if 'domoip' in os.environ['DOMOIP']:
    domoip=os.environ['DOMOIP']
elif 'domoip' in c['DOMOTICZ']:
    domoip=c['DOMOTICZ']['domoip']

if 'dport' in os.environ['DOMOTICZIP']:
    dport=os.environ['DOMOTICZPORT']
elif 'dport' in c['DOMOTICZ']:
    dport=c['DOMOTICZ']['dport']
if 'idxSEstat' in c['DOMOTICZ']:
    idxSEstat=c['DOMOTICZ']['idxSEstat']
if 'idxActPwr' in c['DOMOTICZ']:
    idxActPwr=c['DOMOTICZ']['idxActPwr']
if 'idxActPwr2' in c['DOMOTICZ']:
    idxActPwr2=c['DOMOTICZ']['idxActPwr2']
if 'idxACinv' in c['DOMOTICZ']:
    idxACinv=c['DOMOTICZ']['idxACinv']
if 'idxac_i' in c['DOMOTICZ']:
    idxac_i=c['DOMOTICZ']['idxac_i']
if 'idxAC_f' in c['DOMOTICZ']:
    idxAC_f=c['DOMOTICZ']['idxAC_f']
if 'idxDCinv' in c['DOMOTICZ']:
    idxDCinv=c['DOMOTICZ']['idxDCinv']
if 'idxdc_i' in c['DOMOTICZ']:
    idxdc_i=c['DOMOTICZ']['idxdc_i']
if 'idxEffin' in c['DOMOTICZ']:
    idxEffin=c['DOMOTICZ']['idxEffin']
if 'idxTemp' in c['DOMOTICZ']:
    idxTemp=c['DOMOTICZ']['idxTemp']
if 'idxTotPwr' in c['DOMOTICZ']:
    idxTotPwr=c['DOMOTICZ']['idxTotPwr']


######################################################################
# Domoticz extra variables  used                                     #
######################################################################
version ="1.2"
url =""
content=""
dwh=0
deff=0
dtemp=0
dac_f=0

if 'version' in c['DOMOTICZ']:
    version=c['DOMOTICZ']['version']
if 'url' in c['DOMOTICZ']:
    url=c['DOMOTICZ']['url']
if 'content' in c['DOMOTICZ']:
    content=c['DOMOTICZ']['content']
if 'dwh' in c['DOMOTICZ']:
    dwh=c['DOMOTICZ']['dwh']
if 'deff' in c['DOMOTICZ']:
    deff=c['DOMOTICZ']['deff']
if 'dtemp' in c['DOMOTICZ']:
    dtemp=c['DOMOTICZ']['dtemp']
if 'dac_f' in c['DOMOTICZ']:
    dac_f=c['DOMOTICZ']['dac_f']




I_STATUS = { 
    0: 'Unknown', 
    1: 'OFF', 
    2: 'SLEEPING',
    3: 'STARTING',
    4: 'ON (MPPT)',
    5: 'THROTTLED',
    6: 'SHUTTING DOWN',
    7: 'FAULT',
    8: 'STANDBY'
}

###################################################################################
# main program

verbose_mode = 1
debug_mode = 0
numeric_mode = 0
json_mode = 0
meter = 1
port = PORT
timeout = TIMEOUT
domoticz = 1


def get_inverter_common_block(ctx):
    adu = c.read_holding_registers(SUNSPEC_I_COMMON_BLOCK_START, 69)
    data= pack(">"+str(len(adu))+"H" ,*adu)
    cb={}   
    cb['C_SunSpec_ID']=str(unpack("4s",data[0:4]))
    cb['C_SunSpec_DID'] = str(unpack("!H",data[4:6]))
    cb['C_SunSpec_Length'] = str(unpack("!H",data[6:8]))
    cb['C_Manufacturer'] = str(unpack("32s",data[8:40]))    
    cb['C_Manufacturer'] = re.sub( "\\\\x00",'',cb['C_Manufacturer'] )
    cb['C_Model'] = str(unpack("32s",data[40:72]))
    cb['C_Model']  = re.sub( "\\\\x00",'',cb['C_Model'])
    cb['C_Version'] = str(unpack("16s",data[88:104]))
    cb['C_Version']  = re.sub( "\\\\x00",'',cb['C_Version'])
    cb['C_SerialNumber'] = str(unpack("32s",data[104:136]))
    cb['C_SerialNumber']  = re.sub( "\\\\x00",'',cb['C_SerialNumber'])
    cb['C_DeviceAddress'] = str(unpack("!H",data[136:138]))
    return cb

def get_inverter_model_block(ctx):
    adu = c.read_holding_registers(SUNSPEC_I_MODEL_BLOCK_START, 52)
    data= pack(">"+str(len(adu))+"H" ,*adu)
    mb={}
    mb['C_SunSpec_DID'] = str(unpack("!H",data[0:0+2]))
    mb['C_SunSpec_Length'] = str(unpack("!H",data[2:4]))
    mb['I_AC_Current'] = unpack("!H",data[4:6])[0]
    mb['I_AC_CurrentA'] = int(unpack("!H",data[6:8])[0])
    mb['I_AC_CurrentB'] = int(unpack("!H",data[8:10])[0])
    mb['I_AC_CurrentC'] = int(unpack("!H",data[10:12])[0])
    mb['I_AC_Current_SF'] = int(unpack("!h",data[12:14])[0])
    mb['I_AC_VoltageAB'] = int(unpack("!H",data[14:16])[0])
    mb['I_AC_VoltageBC'] = int(unpack("!H",data[16:18])[0])
    mb['I_AC_VoltageCA'] = int(unpack("!H",data[18:20])[0])
    mb['I_AC_VoltageAN'] = int(unpack("!H",data[20:22])[0])
    mb['I_AC_VoltageBN'] = int(unpack("!H",data[22:24])[0])
    mb['I_AC_VoltageCN'] = int(unpack("!H",data[24:26])[0])
    mb['I_AC_Voltage_SF'] = int(unpack(">h",data[26:28])[0])
    mb['I_AC_Power'] = int(unpack("!H",data[28:30])[0])
    mb['I_AC_Power_SF'] = int(unpack("!h",data[30:32])[0])
    mb['I_AC_Frequency'] = int(unpack("!H",data[32:34])[0])
    mb['I_AC_Frequency_SF'] = int(unpack("!h",data[34:36])[0])
    mb['I_AC_VA'] = int(unpack("!H",data[36:38])[0])
    mb['I_AC_VA_SF'] = int(unpack("!h",data[38:40])[0])
    mb['I_AC_VAR'] = int(unpack("!H",data[40:42])[0])
    mb['I_AC_VAR_SF'] = int(unpack("!h",data[42:44])[0])
    mb['I_AC_PF'] = int(unpack("!H",data[44:46])[0])
    mb['I_AC_PF_SF'] = int(unpack("!H",data[46:48])[0])
    mb['I_AC_Energy_WH'] = int(unpack("!L",data[48:52])[0])
    mb['I_AC_Energy_WH_SF'] = int(unpack("!h",data[52:54])[0])
    mb['I_DC_Current'] = int(unpack("!H",data[54:56])[0])
    mb['I_DC_Current_SF'] = int(unpack("!h",data[56:58])[0])
    mb['I_DC_Voltage'] = int(unpack("!H",data[58:60])[0])
    mb['I_DC_Voltage_SF'] = int(unpack("!h",data[60:62])[0])
    mb['I_DC_Power'] = int(unpack("!H",data[62:64])[0])
    mb['I_DC_Power_SF'] = int(unpack("!h",data[64:66])[0])
    # 40103 unused
    mb['I_Temp_Sink'] = int(unpack("!H",data[68:70])[0])
    # 40105-40106 unused
    mb['I_Temp_Sink_SF'] = int(unpack("!h",data[74:76])[0])
    mb['I_Status'] = int(unpack("!H",data[76:78])[0])
    mb['I_Status_Vendor'] = int(unpack("!H",data[78:80])[0])
    mb['I_Event_1'] = int(unpack("!L",data[80:84])[0])
    mb['I_Event_2'] = int(unpack("!L",data[84:88])[0])
    mb['I_Event_1_Vendor'] = int(unpack("!L",data[88:92])[0])
    mb['I_Event_2_Vendor'] = int(unpack("!L",data[92:96])[0])
    mb['I_Event_3_Vendor'] = int(unpack("!L",data[96:100])[0])
    mb['I_Event_4_Vendor'] = int(unpack("!L",data[100:104])[0])
    return mb



# Send URL to domoticz to update sensors
# para  idx ,value, verbose  
#
def senddomo(idx, value,verbose):
  url = "http://"+domoip+":"+str(dport)+"/json.htm?"+urllib.parse.urlencode({'type': 'command', 'param': 'udevice', 'idx' : idx, 'svalue' : value }) 
  if (verbose):
    print(url)
  content = urllib.request.urlopen(url)


  #die "Can't GET url" if (! defined content)




# scale_value - scale input value using scale factor (SF)
#
def scale_value(val, sf):
    return val * (10 ** sf)

# TCP auto connect on first modbus request
c = ModbusClient(host="target.kroone.net", port=PORT, auto_open=True, timeout=TIMEOUT , auto_close=True)

cb=get_inverter_common_block(c)


# if cb:
#     print(json.dumps(cb, ensure_ascii=False).encode('utf8') )
# else:
#     print("read error")

mb = get_inverter_model_block(c)


print( scale_value( mb['I_AC_Power'],  mb['I_AC_Power_SF']))


status = I_STATUS[mb['I_Status']]
ac_power = scale_value(mb['I_AC_Power'],mb['I_AC_Power_SF'])
dc_power = scale_value(mb['I_DC_Power'],mb['I_DC_Power_SF'])
temp = scale_value(mb['I_Temp_Sink'],mb['I_Temp_Sink_SF'])
#eff = (dc_power > 0 ? ac_power/dc_power*100 : 0)
if(dc_power > 0):
    eff=ac_power/dc_power*100
else:
    eff=0

dc_v = scale_value(mb['I_DC_Voltage'],mb['I_DC_Voltage_SF'])
ac_v = scale_value(mb['I_AC_VoltageAB'],mb['I_AC_Voltage_SF'])
ac_i = scale_value(mb['I_AC_Current'],mb['I_AC_Current_SF'])
dc_i = scale_value(mb['I_DC_Current'],mb['I_DC_Current_SF'])
ac_f = scale_value(mb['I_AC_Frequency'],mb['I_AC_Frequency_SF'])
wh = scale_value(mb['I_AC_Energy_WH'],mb['I_AC_Energy_WH_SF'])


if (verbose_mode):
  print("            Status: "+status)
  print(" Power Output (AC): %12.0f W" % ac_power)
  print("  Power Input (DC): %12.0f W" % dc_power)
  #print("        Efficiency: %12.2f %" % eff)
  print("  Total Production: %12.3f kWh" % (wh/1000) )
  print("      Voltage (AC): %12.2f V (%.2f Hz)" % (ac_v,ac_f))
  print("      Current (AC): %12.2f A" % ac_i)
  print("      Voltage (DC): %12.2f V"% dc_v)
  print("      Current (DC): %12.2f A" % dc_i)
  print("       Temperature: %12.2f C (heatsink)" % temp)
  #print Dumper($mb) if ($debug_mode)
  print("\n")


# if mb:
#     print(json.dumps(mb, ensure_ascii=False).encode('utf8') )
# else:
#     print("read error")

# print 
if (domoticz):
  if (verbose_mode):
    print("********************************************\n")
    print("domo update mode entered  \n")
  ## SolarEdge SolarEdge Status, Text device
  senddomo (idxSEstat,status,verbose_mode)
  ## SolarEdge AC Inverter, Voltage device
  senddomo (idxACinv ,ac_v,verbose_mode)
  ## SolarEdge AC Inverter, Amp device
  senddomo (idxac_i ,ac_i,verbose_mode)
  ## SolarEdge AC Inverter, Hertz device
  dac_f = "%.2f Hz" % ac_f
  senddomo (idxAC_f ,dac_f,verbose_mode)
  ## SolarEdge DC Inverter, Voltage device
  senddomo (idxDCinv ,dc_v,verbose_mode)
  ## SolarEdge DC Inverter, Amp device
  senddomo (idxdc_i ,dc_i,verbose_mode)
  ## SolarEdge Actual Power / Total Production, General, Kwh device
  acpwr_f="%.2f" % ac_power
  senddomo (idxActPwr ,acpwr_f,verbose_mode)
  ## SolarEdge Effinciency, Percentage device
  deff = "%.2f" % eff
  senddomo (idxEffin,deff,verbose_mode)
  ## SolarEdge Temparetuur, Temperature device
  dtemp = "%.2f" % temp
  senddomo (idxTemp  ,dtemp,verbose_mode)
  ## SolarEdge Total Production, General, Kwh device
  dwh = "%.3f" % (wh / 1000)
  senddomo (idxTotPwr,dwh,verbose_mode) 
  
  wh_f = "%.0f" % wh
  ac_power = acpwr_f + ";" + str(wh_f)
  #print "\ncombinetest :";
  #print $ac_power;
  #print "\n";
  senddomo (idxActPwr2 ,ac_power,verbose_mode)
  
