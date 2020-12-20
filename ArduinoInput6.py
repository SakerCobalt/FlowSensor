#!/usr/bin/python

#reading data from Arduino
#Every 86400 seconds is 1 day.
#Version 4 incorporates MQTT messaging, database function moved to server
#Version 5 incorporates Process restart
#Version 6 changes over to UART connection through pins 8 and 10
#Version 6+ controlled via git

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

pauseWF = False
pauseWV = False
waterVolume=0.0
waterVolumeCum = 0.0
prevWaterVolumeCum = 0.0
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

#message (month,day,hr,minute,sec,flow_rate,pump_i,house_v)
def msgWaterFlow(flowRate,pumpCurrent,arduinoData):
    timeRunning = math.trunc(float(arduinoData[1])) #eliminate decimals.  This values increments seconds
    #convert the string serial data to numerical values
    blockTime = int(arduinoData[2])
    houseVoltage = float(arduinoData[7])
    mn,dy,hr,mi,sec = getCurrentTime()
    
    messageWF = ('"'+str(mn)+","+str(dy)+","+str(hr)+","+str(mi)+","+str(sec)+","+str(flowRate)+","
        +str(round(pumpCurrent,2))+","+str(houseVoltage)+'"')
    #print(messageWF)
    client.publish("FlowSensorPi/WaterFlow",messageWF)

def msgWaterVolume(pulseCount2,waterVolumeCum):
    global prevWaterVolumeCum
    waterVolume = pulseCount2/pulsesPerLiter
    waterVolumeCumUpdate = waterVolumeCum + waterVolume
    mn,dy,hr,mi,sec = getCurrentTime()
    #print(type(hr))
    messageWV = ('"'+str(mn)+","+str(dy)+","+str(hr)+","+str(mi)+","+str(round(waterVolume,2))+","
        +str(round(waterVolumeCumUpdate,2))+","+str(round(prevWaterVolumeCum,2))+'"')
    #print(messageWV)
    client.publish("FlowSensorPi/WaterVolume",messageWV)
    if hr==23:
        #print("in 1st if statement")
        if mi==59:
            #print("in reset if statement")
            prevWaterVolumeCum = waterVolumeCumUpdate
            #print(prevWaterVolumeCum)
            ser.flushInput()
            waterVolumeCumUpdate = 0
            
    #print(waterVolumeCumUpdate)
    return waterVolumeCumUpdate
        
def runFlowSensorPi():
    global pauseWF,pauseWV,waterVolumeCum
    while True:
        if ser.in_waiting>0:
            try:
                #print("serial data >0")
                arduinoData = getArduinoData()
                flowRate = round(float(arduinoData[4])/conversion,2) #Divide by Conversion factor to get L/min.
                pumpCurrent = float(arduinoData[6]) #Pump Current
                pulseCount2 = int(arduinoData[5])
            except:
                runFlowSensorPi()
                traceback.print_exc()
            if flowRate == 0:
                if pumpCurrent == 0:#to stop saving a lot of null data with no flow
            # allows 1 0 flow data to go through to verify that the data stopped when it is supposed to
                    if pauseWF: 
                        pass
                    else:
                        #print("1",flowRate,pumpCurrent,arduinoData)
                        msgWaterFlow(flowRate,pumpCurrent,arduinoData)
                        pauseWF = True 
                else:
                    pauseWF = False
                    #adds 1 non zero data to the list
                    msgWaterFlow(flowRate,pumpCurrent,arduinoData)
            else:
                pauseWF = False
                #adds 1 non zero data to the list
                msgWaterFlow(flowRate,pumpCurrent,arduinoData)
            cycle = int(arduinoData[3])
            #print ("cycle = ",cycle)
            if cycle == 1:
                #print("in if statement")
                waterVolumeCum = msgWaterVolume(pulseCount2,waterVolumeCum)
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