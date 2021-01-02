#!/usr/bin/python

#reading data from Arduino
#Every 86400 seconds is 1 day.
#Version 4 incorporates MQTT messaging, database function moved to server
#Version 5 incorporates Process restart
#Version 6 changes over to UART connection through pins 8 and 10
#Version 6+ controlled via git
#Version 7 - FlowSensor - Sends messages without time to be logged by server as they come in

import serial
import string
import time
import math
import paho.mqtt.client as mqtt
import traceback
import sys
import atexit

pulsesPerLiter = 330 #pulses per liter for flow meter
conversion = 5.5 #convert pulses per second to L/min

maxFlowRate = 0.0
kWhPump = 0.0
index = 0
serialData=""

broker_address="192.168.50.201"
client = mqtt.Client("WaterFlowPi")
client.connect(broker_address)
client.loop_start()

def on_exit():
    client.loop_stop()
    print("client loop stopped")
    
atexit.register(on_exit)


def initiateSerial():
    try:
        global ser
        print("Connecting")
        ser = serial.Serial('/dev/ttyS0', 2400, 8, 'N',1,timeout=1)
        ser.flushInput()
    except:
        #To try to reconnect if the first connection fails
        traceback.print_exc()
        time.sleep(5)
        ser.flushInput()
        initiateSerial()
        

def getArduinoData():
    try:
        serialData = ser.readline()
        string = str(serialData)
        array = string.split(",") #split the converted serial data into usable values as string
        if len(array)<7:
            Print("Array length ",len(array))
            getArduinoData()
    except:
        print("Failed to getArduinoData",len(array))
        getArduinoData()
    #print(array)
    return array

def getCurrentTime():
    #timeNow = time.localtime()
    #year = time.localtime().tm_year
    month = time.localtime().tm_mon
    day = time.localtime().tm_mday
    hour = time.localtime().tm_hour
    minute = time.localtime().tm_min
    second = time.localtime().tm_sec
    return month,day,hour,minute,second

#message (flow_rate)
def msgWaterFlow(flowRate):
    messageWF = (str(flowRate)) #Sending only numerical data for flow rate
    #print(messageWF)
    client.publish("FlowSensorPi/WaterFlow",messageWF)

#message (waterVolume, maxFlow, kWhPump) all for the last 60 sec
def msgWaterVolume(pulseCount2, maxFlow, kWhPump):
    waterVolume = pulseCount2/pulsesPerLiter
    if waterVolume <0:
        waterVolume = 0
    messageWV = ('"'+str(round(waterVolume,2))+","+str(maxFlow)+","+str(kWhPump)+'"')
    client.publish("FlowSensorPi/waterVolume",messageWV)
        
def runFlowSensorPi():
    global maxFlowRate,kWhPump
    while True:
        if ser.in_waiting>0:
            try:
                #print("serial data >0")
                arduinoData = getArduinoData()
            except:
                runFlowSensorPi()
                traceback.print_exc()
                
            flowRate = round(float(arduinoData[4])/conversion,2) #Divide by Conversion factor to get L/min
            kWhPump += (float(arduinoData[6])/15) #Pump Current converted to kWh for last sec
            cycle = int(arduinoData[3])
            pulseCount2 = int(arduinoData[5])
            
            msgWaterFlow(flowRate)
            
            if flowRate > maxFlowRate:
                maxFlowRate = flowRate
            
            if cycle == 1:
                msgWaterVolume(pulseCount2,maxFlowRate,kWhPump)
                maxFlowRate = 0.0
                kWhPump = 0.0
                ser.flushInput()
            time.sleep(1)
        else:
            print("Serial = 0")
            time.sleep(1)
            
def restartProgram():
    #Restarts program with file objects and cleanup
    try:
        os.execl(sys.python3, os.path.abspath(ArduinoInput4.py))
    except:
        print("Failed to Restart")
        time.sleep(10)
        restartProgram()

try:
    initiateSerial()
    runFlowSensorPi()
except ValueError:
    time.sleep(2)
    traceback.print_exc()
    runFlowSensorPi()
except UnboundLocalError:
    time.sleep(1)
    traceback.print_exc()
    runFlowSensorPi()
except IndexError:
    time.sleep(1)
    traceback.print_exc()
    runFlowSensorPi()
except OSError:
    traceback.print_exc()
    time.sleep(5)
    #restartProgram()   