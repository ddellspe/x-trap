'''
This python file does the data processing for the stages including converting distance in mm or degrees
to steps and vice cersa, but also gets the position of the stages using the serialCommands.py file

@author: David
'''
#custom Library Imports
import serialCommands

def calculateSpeed(desiredSpeed):
    '''
    Calculates the data portion for the speed changing where the desired speed is given in degrees per minute
    
    @param desiredSpeed: The desired speed in degrees per minute
    '''
    speed_second = desiredSpeed/60 #convert speed from deg/min to deg/s
    microstepSize = 0.000234375 #size of each microstep
    return int(speed_second / (microstepSize * 9.375))

def dataToBytes(data):
    '''
    converts the data in base 10 to bytes (base 256)
    
    @param data: the data (base 10) being converted to bytes (base 256)
    @return inst: the array containing the bytes that were converted from the input data
    '''
    inst = [0,0,0,0,0,0]
    if data < 0:
        data = 256**4 + data
        inst[5] = data/(256**3)
        data = data%(256**3)
        inst[4] = data/(256**2)
        data = data%(256**2)
        inst[3] = data/256
        data = data%256
        inst[2] = data
    else:
        inst[5] = data/(256**3)
        data = data%(256**3)
        inst[4] = data/(256**2)
        data = data%(256**2)
        inst[3] = data/256
        data = data%256
        inst[2] = data
    return inst

def bytesToData(array):
    '''
    Converts base 256 information in an array to base 10 information in an integer
    
    @param array: array containing 4-bytes of information to be converted to an integer
    @return data: the base 10 information.  
    '''
    data = 256**3*array[5] + 256**2*array[4] + 256*array[3] + array[2]
    if array[5] > 127:
        data = data - 256**4;
    return data

def calcSteps(dev, magnitude):
    '''
    Calculates the number of microsteps for the device (dev) to move the magnitude passed
    into the method
    
    @param dev: the device number (1-4) standing for the Z, rotary, X, and Y stage
    @param magnitude: the distance in mm or degrees of the movement
    @return data: the number of microsteps that the device needs to move to have the stage move the desired magnitude
    '''
    if dev == 1:
        factor = 1.27
    if dev == 2:
        factor = 3.0
    if dev == 3:
        factor = 0.6096;
    if dev == 4:
        factor = 0.6096;
    data = int(magnitude*200.0/factor/(1/64.0))
    return data

def calcDistance(ser, dev):
    '''
    Calculates the distance that the stage is from the home position
    
    @param ser: serial port that all the stages are connected to
    @param dev: the device number (1-4) standing for the Z, rotary, X, and Y stage
    @return [distance, unit]: connected to the distance moved and the unit of the stage (mm or degrees)
    '''
    if dev == 1:
        factor = 1.27
        unit = "mm"
    if dev == 2:
        factor = 3.0
        unit = "degrees"
    if dev == 3:
        factor = 0.6096
        unit = "mm"
    if dev == 4:
        factor = 0.6096
        unit = "mm"
    currentPosition = bytesToData(serialCommands.receive(ser, dev, 60))#gets the current position data packet
    distance = int(currentPosition)#converts the number of steps to a rounded value
    distance = distance*(1/64.0)*factor/200.0#converts the integer to the distance for the specific stage
    distance = round(distance,4)#rounds the distance to 4 decimal places
    return [distance, unit]#returns an array of the distance and string for units

def getOnePosition(ser, dev):
    '''
    returns the position of the desired device
    
    @param ser: serial port that all the stages are connected to
    @param dev: the device number (1-4) standing for the Z, rotary, X, and Y stage
    @return position: position of stage number dev
    '''
    position = calcDistance(ser, dev)#gets the position of a specified stage
    return position

def getAllPositions(ser):
    '''
    returns the position of all stages
    
    @param ser: serial port that all the stages are connected to
    @return [position1, position2, position3, position4]: the position of the 4 stages
    '''
    position1 = getOnePosition(ser, 1)
    position2 = getOnePosition(ser, 2)
    position3 = getOnePosition(ser, 3)
    position4 = getOnePosition(ser, 4)
    return [position1, position2, position3, position4]

def setCurrentPositionLabel(ser, stage1Pos, stage2Pos, stage3Pos, stage4Pos, zeroPosition):
    '''
    Sets the current position label of all stages
    
    @param ser: serial port that all the stages are connected to
    @param stage1Pos: Label connected to stage1 in the main gui
    @param stage2Pos: Label connected to stage2 in the main gui
    @param stage3Pos: Label connected to stage3 in the main gui
    @param stage4Pos: Label connected to stage4 in the main gui
    @param zeroPosition: the pre-set zeroPosition of the whole system
    '''
    [pos1, pos2, pos3, pos4] = getAllPositions(ser)
    s1 = pos1[0]-zeroPosition[2]
    s2 = pos2[0]-zeroPosition[3]
    s3 = pos3[0]-zeroPosition[0]
    s4 = pos4[0]-zeroPosition[1]
    stage1Pos.set("%.3f mm" % s1)
    stage2Pos.set("%.3f %s" % (s2, unichr(176)))
    stage3Pos.set("%.3f mm" % s3)
    stage4Pos.set("%.3f mm" % s4)
    #function to update positions with current position in the GUI code
    return