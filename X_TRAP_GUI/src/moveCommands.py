'''
The moveCommands.py file contains all of the methods and functions that are used to control
the zaber stages that make up the x-TRAP device.  

@note: This set of functions requires the stages to be in the configuration Z, Rotation, X, Y
@author: David Dellsperger
'''
#custom Library Imports
import dataManagement
import serialCommands
import time

def stop(ser, s1, s2, s3, s4, zeroPosition, gui):
    '''
    Sends the command to all stages to stop movement, should only be used as an emergency
    stop function as it causes other problems with the stages after a stop command is sent
    
    @param ser: The Serial port that has the stages connected to and open
    @param s1: String var for stage 1's movement (z-axis)
    @param s2: String var for stage 2's movement (rotary axis)
    @param s3: String var for stage 3's movement (x-axis)
    @param s4: String var for stage 4's movement (y-axis)
    @param zeroPosition: 4-tuple containing the set zero position of the stages
    @param gui: the reference to the main gui
    '''
    stop = [0,23,0,0,0,0]
    serialCommands.send(ser, stop)
    gui.enable()

def moveAllAbsolute(ser, mag1, mag2, mag3, mag4, s1, s2, s3, s4, zeroPosition, gui):
    '''
    checks for valid move, then proceeds with the move based on the information sent in
    mag1, mag2, mag3, mag4 are the moves for the stages z, rotation, x, y in order
    s1, s2, s3, s4 are the StringVars that will be used to return the current stage position to the loading meters
    
    @param ser: The Serial port that has the stages connected to and open
    @param mag1: Desired movement for stage 1 (z-axis)
    @param mag2: Desired movement for stage 2 (rotary axis)
    @param mag3: Desired movement for stage 3 (x-axis)
    @param mag4: Desired movement for stage 4 (y-axis)
    @param s1: String var for stage 1's movement (z-axis)
    @param s2: String var for stage 2's movement (rotary axis)
    @param s3: String var for stage 3's movement (x-axis)
    @param s4: String var for stage 4's movement (y-axis)
    @param zeroPosition: 4-tuple containing the set zero position of the stages
    @param gui: the reference to the main gui
    '''
    #zeroPosition contains all zero positions (x, y, z, rotation) in that order
    move1 = mag1+zeroPosition[2] # calculates z-axis move based on the zero position and the move relative to that position (anything less than 0 will be ignored)
    move2 = mag2+zeroPosition[3] # calculates rotation based on the zero position and the move relative to that position (anything less than 0 will be ignored)
    move3 = mag3+zeroPosition[0] # calculates x-axis move based on the zero position and the move relative to that position (anything less than 0 or greater than 50 will be ignored) 
    move4 = mag4+zeroPosition[1] # calculates y-axis move based on the zero position and the move relative to that position (anything less than 0 or greater than 50 will be ignored)
    #error check inputs
    if move1 < 0 or move1 > 150:
        print "Position selected for Z-axis is out of the bounds of the Z-Axis Stage"
    else:     
        time.sleep(0.1)   
        moveOne(ser, 1, move1, 20)
    if move2 < 0:
        print "Position selected for Rotary Axis is out of bounds of the Rotary Axis Stage"
    else:
        time.sleep(0.1)   
        moveOne(ser, 2, move2, 20)
    if move3 < 0 or move3 > 50:
        print "Position selected for X-axis is out of the bounds of the X-Axis Stage"
    else:
        time.sleep(0.1)   
        moveOne(ser, 3, move3, 20)
    if move4 < 0 or move4 > 50:
        print "Position selected for Y-axis is out of the bounds of the Y-Axis Stage"
    else:
        time.sleep(0.1)   
        moveOne(ser, 4, move4, 20)
    serialCommands.waitForIdleWithUpdate(ser, s1, s2, s3, s4, zeroPosition, gui)
    gui.updateCurrentPosition()
    gui.enable()
    gui.progressVar.set("Move Complete")
    gui.updateCurrentPosition()
    gui.updateCurrentPositionText()
    return

def moveAllRelative(ser, mag1, mag2, mag3, mag4, s1, s2, s3, s4, zeroPosition, currentPosition, gui):
    '''
    checks for valid move, then proceeds with the move based on the information sent in
    mag1, mag2, mag3, mag4 are the moves for the stages z, rotation, x, y in order
    s1, s2, s3, s4 are the StringVars that will be used to return the current stage position
    to the loading progress bars.  This function differs from the moveAllAbsolute, because if the magnitude
    is able to be used, the function called will be a relative move, not an absolute move
    
    @param ser: The Serial port that has the stages connected to and open
    @param mag1: Desired movement for stage 1 (z-axis)
    @param mag2: Desired movement for stage 2 (rotary axis)
    @param mag3: Desired movement for stage 3 (x-axis)
    @param mag4: Desired movement for stage 4 (y-axis)
    @param s1: String var for stage 1's movement (z-axis)
    @param s2: String var for stage 2's movement (rotary axis)
    @param s3: String var for stage 3's movement (x-axis)
    @param s4: String var for stage 4's movement (y-axis)
    @param zeroPosition: 4-tuple containing the set zero position of the stages
    @param currentPosition: 4-tuple containing the current position of the stages
    @param gui: the reference to the main gui
    '''
    #zeroPosition contains all zero positions (x, y, z, rotation) in that order
    move1 = mag1+zeroPosition[2]+currentPosition[2] # calculates z-axis move based on the zero position and the move relative to that position (anything less than 0 will be ignored)
    move2 = mag2+zeroPosition[3]+currentPosition[3] # calculates rotation based on the zero position and the move relative to that position (anything less than 0 will be ignored)
    move3 = mag3+zeroPosition[0]+currentPosition[0] # calculates x-axis move based on the zero position and the move relative to that position (anything less than 0 or greater than 50 will be ignored) 
    move4 = mag4+zeroPosition[1]+currentPosition[1] # calculates y-axis move based on the zero position and the move relative to that position (anything less than 0 or greater than 50 will be ignored)
    #error check inputs
    if move1 < 0 or move1 > 150:
        print "Position selected for Z-axis is out of the bounds of the Z-Axis Stage"
    else:     
        time.sleep(0.1)   
        moveOne(ser, 1, mag1, 21)
    if move2 < 0:
        print "Position selected for Rotary Axis is out of bounds of the Rotary Axis Stage"
    else:
        time.sleep(0.1)   
        moveOne(ser, 2, mag2, 21)
    if move3 < 0 or move3 > 50:
        print "Position selected for X-axis is out of the bounds of the X-Axis Stage"
    else:
        time.sleep(0.1)   
        moveOne(ser, 3, mag3, 21)
    if move4 < 0 or move4 > 50:
        print "Position selected for Y-axis is out of the bounds of the Y-Axis Stage"
    else:
        time.sleep(0.1)   
        moveOne(ser, 4, mag4, 21)
    serialCommands.waitForIdleWithUpdate(ser, s1, s2, s3, s4, zeroPosition, gui)
    gui.updateCurrentPosition()
    gui.enable()
    gui.progressVar.set("Move Complete")
    gui.updateCurrentPosition()
    gui.updateCurrentPositionText()
    return

def moveOne(ser, dev, mag, cmd):
    '''
    This is the call to move one stage based on the magnitude given and command type (21 or 20 for relative/absolute)
    The magnitude is converted to the number of micro steps and then the send command is used
    
    @param ser: The Serial port that has the stages connected to and open
    @param dev: The device number being moved (1-4)
    @param mag: The magnitude to move mm for dev 1, 3, 4, and degrees for 2
    @param cmd: The command being issued 20 for Absolute move, 21 for Relative move. 
    '''
    move = dataManagement.dataToBytes(dataManagement.calcSteps(dev, mag))
    move[0] = dev
    move[1] = cmd
    serialCommands.send(ser, move)
    return

def homeAll(ser, s1, s2, s3, s4, gui, zeroPosition):
    '''
    Sends the command to all stages to move to the home position.  This is required at the beginning of the
    program in order to initialize the stages as well as if something goes wrong with the stages
    
    @param ser: The Serial port that has the stages connected to and open
    @param s1: String var for stage 1's movement (z-axis)
    @param s2: String var for stage 2's movement (rotary axis)
    @param s3: String var for stage 3's movement (x-axis)
    @param s4: String var for stage 4's movement (y-axis)
    @param gui: the reference to the main gui
    @param zeroPosition: 4-tuple containing the set zero position of the stages
    '''
    homeAll = [0,1,0,0,0,0]
    s1.set("homing the stage")
    s2.set("homing the stage")
    s3.set("homing the stage")
    s4.set("homing the stage")
    serialCommands.send(ser, homeAll)
    serialCommands.waitForIdle(ser)
    dataManagement.setCurrentPositionLabel(ser, s1, s2, s3, s4, zeroPosition)
    gui.updateCurrentPosition()
    gui.enable()
    return

def moveAllToStored(ser, store, s1, s2, s3, s4, gui, zeroPosition):
    '''
    Moves all stages to the desired stored value (0-15) which can be stored using the store current method
    
    @param ser: The Serial port that has the stages connected to and open
    @param store: The store bank value (0-15)
    @param s1: String var for stage 1's movement (z-axis)
    @param s2: String var for stage 2's movement (rotary axis)
    @param s3: String var for stage 3's movement (x-axis)
    @param s4: String var for stage 4's movement (y-axis)
    @param gui: the reference to the main gui
    @param zeroPosition: 4-tuple containing the set zero position of the stages
    '''
    if store >= 15:
        store = 0
    moveOneToStored(ser, 1, store)
    moveOneToStored(ser, 2, store)
    moveOneToStored(ser, 3, store)
    moveOneToStored(ser, 4, store)
    serialCommands.waitForIdleWithUpdate(ser, s1, s2, s3, s4, zeroPosition, gui) 
    gui.enable()  
    return
    
def moveOneToStored(ser, dev, store):
    '''
    Moves one stage to the desired stored value (0-15) which can be stored using the store current method
    
    @param ser: The Serial port that has the stages connected to and open
    @param dev: The device number being moved (1-4)
    @param store: The store bank value (0-15)
    '''
    if store >= 15:
        store = 0
    serialCommands.send(ser, [dev,18,store,0,0,0])
    return

def storeCurrent(ser, store):
    '''
    Stores the current position of all stages to the desired store value
    
    @param ser: The Serial port that has the stages connected to and open
    @param store: The store bank value (0-15)
    '''
    if store >= 15:
        store = 0
    serialCommands.waitForIdle(ser)
    serialCommands.send(ser, [0,16,store,0,0,0])
    return

def arcTreatment(ser, mag, speed, s1, s2, s3, s4, zeroPosition, gui):
    '''
    Changes the speed of the stage, then rotates the rotary stage, then returns the speed of the stage to default
    
    @param ser: Serial port that has been opened int he main gui
    @param mag: Magnitude of the move (in degrees)
    @param speed: Desired speed to rotate the stages
    @param s1: String var for stage 1's movement (z-axis)
    @param s2: String var for stage 2's movement (rotary axis)
    @param s3: String var for stage 3's movement (x-axis)
    @param s4: String var for stage 4's movement (y-axis)
    @param zeroPosition: 4-tuple containing the set zero position of the stages
    @param gui: the reference to the main gui
    '''    
    data = dataManagement.calculateSpeed(speed)
    packet = dataManagement.dataToBytes(data)
    packet[0] = 2
    packet[1] = 42
    serialCommands.send(ser, packet) #sends the instruction to change speed to the stage
    moveOne(ser, 2, mag, 21) #moves stage 2 (the rotary stage) a distance of mag degrees relatively
    serialCommands.waitForIdleWithUpdate(ser, s1, s2, s3, s4, zeroPosition, gui) #wait for idle while updating the progress bars
    resetSpeed(ser)
    gui.enable()
    
    
    return

def setZeroPoint(ser, s1, s2, s3, s4, zeroPosition, gui):
    '''
    Initialization step which is required before any other movement command.  This homes the devices (in order to 
    reset the zero position of the stage's memory) then moves the stages to the zero position.  
    
    @param ser: The Serial port that has the stages connected to and open
    @param s1: String var for stage 1's movement (z-axis)
    @param s2: String var for stage 2's movement (rotary axis)
    @param s3: String var for stage 3's movement (x-axis)
    @param s4: String var for stage 4's movement (y-axis)
    @param zeroPosition: 4-tuple containing the set zero position of the stages
    @param gui: the reference to the main gui
    '''
    homeAll(ser, s1, s2, s3, s4, gui, zeroPosition)
    gui.disable()
    gui.progressVar.set("Moving to Zero Point")
    gui.zeroBars()
    moveAllAbsolute(ser, 0, 0, 0, 0, s1, s2, s3, s4, zeroPosition, gui)
    gui.disable()
    storeCurrent(ser, 0)
    gui.zeroed = True
    serialCommands.waitForIdleWithUpdate(ser, s1, s2, s3, s4, zeroPosition, gui)
    gui.updateCurrentPosition()
    gui.enable()
    return

def resetSpeed(ser):
    data = dataManagement.calculateSpeed(360) #go back to rotating at 360 degrees/minute
    packet = dataManagement.dataToBytes(data)
    packet[0] = 2
    packet[1] = 42
    serialCommands.send(ser, packet) #sends the instructino to return to default speed to the stage