#!/usr/bin/python3

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
pumpWh = 0.0
pumpI = 0.0
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
        #print(array)
    except:
        print("Failed to getArduinoData",len(array))
        getArduinoData()
    #print(array)
    return array

#message (flow_rate)
def msgWaterFlow(flowRate):
    messageWF = (str(flowRate)) #Sending only numerical data for flow rate
    #print(messageWF)
    client.publish("FlowSensorPi/WaterFlow",messageWF)

#message (waterVolume, maxFlow, kWhPump) all for the last 60 sec
def msgWaterVolume(pulseCount2, maxFlow, pumpWh):
    waterVolume = pulseCount2/pulsesPerLiter
    if waterVolume <0:
        waterVolume = 0
    messageWV = ('"'+","+str(round(waterVolume,2))+","+str(maxFlow)+","+str(round(pumpWh,2))+","+'"')
    client.publish("FlowSensorPi/WaterVolume",messageWV)
        
def runFlowSensorPi():
    global maxFlowRate,pumpWh
    while True:
        if ser.in_waiting>0:
            try:
                #print("serial data >0")
                arduinoData = getArduinoData()
            except:
                runFlowSensorPi()
                traceback.print_exc()
            #print(len(arduinoData))
            if len(arduinoData)==9:
                flowRate = round(float(arduinoData[4])/conversion,2) #Divide by Conversion factor to get L/min
            
                pumpI = (float(arduinoData[6])) #Pump Current, RMS value
                cycle = int(arduinoData[3])
                pulseCount2 = int(arduinoData[5])
                
                msgWaterFlow(flowRate)
                
                if flowRate > maxFlowRate:
                    maxFlowRate = flowRate
                if pumpI > 1.5:
                    pumpWh = pumpWh + (pumpI/15*.8) #Conver W to Wh for 1 second at 240V, 0.8pf
                
                if cycle == 1:
                    msgWaterVolume(pulseCount2,maxFlowRate,pumpWh)
                    maxFlowRate = 0.0
                    pumpWh = 0.0
                    pumpI=0.0
                    ser.flushInput()
                    
            else:
                runFlowSensorPi()
                print("rerun FlowSensorPi, array too short")
            time.sleep(1)
        else:
            print("Serial = 0")
            time.sleep(1)
            
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
except:
    traceback.print_exc()