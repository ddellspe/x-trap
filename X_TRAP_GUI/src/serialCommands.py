'''
The serialCommands module contains all of the methods that are called using the serial port

@author: David
'''
#python Importrs
import serial, time
import sys
#custom Library Imports
import dataManagement



def scan():
    '''
    scans for available serial ports and returns a list of tuples (index, name)
    
    @return tuples that code for the COM port index and name (index, name)
    '''
    available = []
    for i in range(256):
        try:
            s = serial.Serial(i)
            available.append( (i, s.portstr))
            s.close()
        except serial.SerialException:
            pass
    return available

def openSerialGUI(value):
    '''
    Create Serial Port from the given value sent to the function
    
    @param value: the serial port index that should be used to create the serial port
    '''
    s = serial.Serial(value)
    time.sleep(.2)
    return s
    

def closeSerial(ser):
    '''
    Closes the serial port of the parameter ser
    
    @param ser: serial port object that is to be closed
    '''
    ser.close()
    return

def clearSettings(ser):
    '''
    Clears the settings of all Zaber devices connected to the serial port
    
    @param ser: serial port that has the stages connected to it
    '''
    send(ser, [0,36,0,0,0,0])
    return

def send(ser, inst):
    '''
    Sends the 6-byte instruction array through to the serial port
    
    @param ser: serial port that has the stages connected to it
    @param inst: 6-byte instruction array that has the format [device, instruction, data, data, data, data]
    '''
    ser.flushInput()
    ser.flushOutput()
    time.sleep(.1)
    for i in range (6):
        ser.write(chr(inst[i]))
    return
   
def receive(ser, dev, command_type):
    '''
    Sends and the promptly receives the information from the desired stage
    
    @param ser: serial port that has the stages connected to it
    @param dev: device to send and receive information from
    @param type: the type of command to be sent
    '''
    ser.flushInput()
    ser.flushOutput()
    correct = 0
    while correct == 0:
        r = [0,0,0,0,0,0]
        send(ser, [dev,command_type,0,0,0,0])
        time.sleep(.1)
        for i in range (6):
            try:
                r[i]=ord(ser.read(1))
            except TypeError:
                pass
        if r[0] == dev and r[1] == command_type:
            correct = 1
        else:
            ser.flushInput()
            ser.flushOutput()    
    return r


def waitForIdleWithUpdate(ser, s1, s2, s3, s4, zeroPosition, gui):
    '''
    Waits for the stages to be idle with updating the stringvars for the position of stages 1-4, 
    when the stages are idle (i.e. not moving or processing information) the method will be over
    
    @param ser: serial port that has the stages connected to it
    @param s1: String var for stage 1's movement (z-axis)
    @param s2: String var for stage 2's movement (rotary axis)
    @param s3: String var for stage 3's movement (x-axis)
    @param s4: String var for stage 4's movement (y-axis)
    @param zeroPosition: 4-tuple containing the set zero position of the stages
    @param gui: the reference to the main gui
    '''
    status = 1
    status1 = 1
    status2 = 1
    status3 = 1
    status4 = 1
    while status !=0:
        dataManagement.setCurrentPositionLabel(ser, s1, s2, s3, s4, zeroPosition)
        gui.updateProgress()
        if status1 != 0:
            status1 = dataManagement.bytesToData(receive(ser, 1, 54))
            dataManagement.setCurrentPositionLabel(ser, s1, s2, s3, s4, zeroPosition)
            gui.updateProgress()
        if status2 != 0:
            status2 = dataManagement.bytesToData(receive(ser, 2, 54))
            dataManagement.setCurrentPositionLabel(ser, s1, s2, s3, s4, zeroPosition)
            gui.updateProgress()
        if status3 != 0:
            status3 = dataManagement.bytesToData(receive(ser, 3, 54))
            dataManagement.setCurrentPositionLabel(ser, s1, s2, s3, s4, zeroPosition)
            gui.updateProgress()
        if status4 != 0:
            status4 = dataManagement.bytesToData(receive(ser, 4, 54))
            dataManagement.setCurrentPositionLabel(ser, s1, s2, s3, s4, zeroPosition)
            gui.updateProgress()
        status = status1+status2+status3+status4
    dataManagement.setCurrentPositionLabel(ser, s1, s2, s3, s4, zeroPosition)
    gui.updateProgress()
    return
#updatePositionLabel(self.ser, self.zCurrentVar, self.degCurrentVar, self.xCurrentVar, self.yCurrentVar, self.zeroPosition, self.zeroPosition, self)
def updatePositionLabel(ser, s1, s2, s3, s4, zeroPosition, gui):
    try:
        dataManagement.setCurrentPositionLabel(ser, s1, s2, s3, s4, zeroPosition)
        gui.updateCurrentPosition()
    except:
        print "Error updating Labels"
        print "Exception encountered" + str(sys.exc_info()[0])
        print "Exception encountered" + str(sys.exc_info()[1])
        print "Exception encountered" + str(sys.exc_info()[2])
    gui.enable()
    return
    
def waitForIdle(ser):
    '''
    Waits for the stages to be idle, when the stages are idle (i.e. not moving or processing information) 
    The method will be over
    
    @param ser: serial port that has the stages connected to it
    '''
    time.sleep(0.1)
    status = 1
    status1 = 1
    status2 = 1
    status3 = 1
    status4 = 1
    #checks the status of all devices, and waits until they 
    #are no longer moving to continue
    while status != 0:
        if status1 != 0:
            status1 = dataManagement.bytesToData(receive(ser, 1, 54))
        if status2 != 0:
            status2 = dataManagement.bytesToData(receive(ser, 2, 54))
        if status3 != 0:
            status3 = dataManagement.bytesToData(receive(ser, 3, 54))
        if status4 != 0:
            status4 = dataManagement.bytesToData(receive(ser, 4, 54))
        status = status1+status2+status3+status4
        time.sleep(.1)
    return

def setSettings(ser):
    '''
    Sets the settings for the stages as needed for this application
    
    @param ser: serial port that has the stages connected to it
    '''
    ser.flushInput()
    ser.flushOutput()
    send(ser, [0,36,0,0,0,0])
    time.sleep(.2)
    send(ser, [0,2,0,0,0,0]) #renumbers the devices
    time.sleep(.2)
    ser.flushInput()
    ser.flushOutput()
    time.sleep(.4)
    send(ser, [1,40,9,0,0,0])
    time.sleep(.4)
    send(ser, [2,40,9,1,0,0])
    time.sleep(.4)
    send(ser, [3,40,9,0,0,0])
    time.sleep(.4)
    send(ser, [4,40,9,0,0,0])
    time.sleep(.4)
    ser.flushOutput()
    ser.flushInput()
    return