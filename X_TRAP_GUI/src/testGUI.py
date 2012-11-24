'''
Created on Dec 16, 2010

@author: David
'''
#Python Imports
from Tkinter import Button, Label, Frame, OptionMenu, Tk, StringVar, NORMAL, DISABLED, END, N, S, E, W, Entry, Menu
import thread
#Custom Library Imports
import moveCommands, serialCommands, dataManagement

values = ["Please","Press","Rescan"]
root = Tk()
root.title("Test GUI Application")
root.resizable(True,False)
global var
var = StringVar()
var.set("Please Press Rescan")
#serial Port
global ser
ser = None
#Frames in the grid
global lFrame, mFrame, rFrame
#Home/Store Buttons
global homeAllButton, homeStoreAllButton, zeroAllButton, returnZeroAllButton, storeCurrentButton, returnToStoredButton
#Serial Buttons
global setSettingsButton, submitButton, serialOptionMenu, closeSerialButton, clearSettingsButton
#move Buttons
global moveAllRelativeButton, moveAllAbsoluteButton
#move Entry sections
global stage1Entry, stage2Entry, stage3Entry, stage4Entry
#Frames specifications
global defaultWidth, defaultHeight
#button Specifications
global buttonWidth, buttonHeight, buttonBGColor, buttonFGColor, frameColor
#current position labels
global stage1Pos, stage2Pos, stage3Pos, stage4Pos
global divisions
divisions = 24
defaultWidth = 200
defaultHeight = 480
buttonWidth=1.0
buttonHeight=2.0/divisions
buttonBGColor="gold"
buttonFGColor="black"
frameColor="gray80"

def quit():
    global ser
    if ser is None:
        root.quit()
    else:
        closeSerial()
        root.quit()
    return

def setButtonStatus(status):
    """sets the status of the buttons to the status passed into the function"""
    #Home/Store Buttons
    global homeAllButton, homeStoreAllButton, zeroAllButton, returnZeroAllButton, storeCurrentButton, returnToStoredButton
    #Serial Buttons
    global setSettingsButton, submitButton, serialOptionMenu, closeSerialButton, clearSettingsButton
    #move Buttons
    global moveAllRelativeButton, moveAllAbsoluteButton
    #move Entry sections
    global stage1Entry, stage2Entry, stage3Entry, stage4Entry
    #wait for idle status
    global ser
    global stage1Pos, stage2Pos, stage3Pos, stage4Pos
    homeAllButton.configure(state=status)
    homeStoreAllButton.configure(state=status)
    zeroAllButton.configure(state=status)
    closeSerialButton.configure(state=status)
    clearSettingsButton.configure(state=status)
    returnZeroAllButton.configure(state=status)
    setSettingsButton.configure(state=status)
    submitButton.configure(state=status)
    serialOptionMenu.configure(state=status)
    rescanButton.configure(state=status)
    storeCurrentButton.configure(state=status)
    returnToStoredButton.configure(state=status)
    stage1Entry.configure(state=status)
    stage2Entry.configure(state=status)
    stage3Entry.configure(state=status)
    stage4Entry.configure(state=status)
    moveAllRelativeButton.configure(state=status)
    moveAllAbsoluteButton.configure(state=status)
    return

def enableButtons():
    #Home/Store Buttons
    global homeAllButton, homeStoreAllButton, zeroAllButton, returnZeroAllButton, storeCurrentButton, returnToStoredButton
    #Serial Buttons
    global setSettingsButton, submitButton, serialOptionMenu, closeSerialButton, clearSettingsButton
    #move Buttons
    global moveAllRelativeButton, moveAllAbsoluteButton
    #move Entry sections
    global stage1Entry, stage2Entry, stage3Entry, stage4Entry
    if ser is None:
        print "serial Port not initialized"
    else:
        if ser.isOpen():
            homeAllButton.configure(state=NORMAL)
            homeStoreAllButton.configure(state=NORMAL)
            zeroAllButton.configure(state=NORMAL)
            closeSerialButton.configure(state=NORMAL)
            clearSettingsButton.configure(state=NORMAL)
            submitButton.configure(state=DISABLED)
            serialOptionMenu.configure(state=DISABLED)
            rescanButton.configure(state=DISABLED)
            storeCurrentButton.configure(state=NORMAL)
            returnToStoredButton.configure(state=NORMAL)
            stage1Entry.configure(state=NORMAL)
            stage2Entry.configure(state=NORMAL)
            stage3Entry.configure(state=NORMAL)
            stage4Entry.configure(state=NORMAL)
            moveAllRelativeButton.configure(state=NORMAL)
            moveAllAbsoluteButton.configure(state=NORMAL)
        else:
            homeAllButton.configure(state=DISABLED)
            homeStoreAllButton.configure(state=DISABLED)
            zeroAllButton.configure(state=DISABLED)
            closeSerialButton.configure(state=DISABLED)
            clearSettingsButton.configure(state=DISABLED)
            returnZeroAllButton.configure(state=DISABLED)
            setSettingsButton.configure(state=DISABLED)
            submitButton.configure(state=NORMAL)
            serialOptionMenu.configure(state=NORMAL)
            rescanButton.configure(state=NORMAL)
            storeCurrentButton.configure(state=DISABLED)
            returnToStoredButton.configure(state=DISABLED)
            stage1Entry.configure(state=DISABLED)
            stage2Entry.configure(state=DISABLED)
            stage3Entry.configure(state=DISABLED)
            stage4Entry.configure(state=DISABLED)
            moveAllRelativeButton.configure(state=DISABLED)
            moveAllAbsoluteButton.configure(state=DISABLED)
    return

def setSerial():
    global setSettingsButton, var, ser
    com = var.get()
    if com[1:4].isdigit():
        ser = serialCommands.openSerialGUI(int(com[1:4]))
    elif com[1:3].isdigit():
        ser = serialCommands.openSerialGUI(int(com[1:3]))
    elif com[1:2].isdigit():
        ser = serialCommands.openSerialGUI(int(com[1:2]))
    if ser.isOpen():
        setSettingsButton.configure(state=NORMAL)
        enableButtons()
        var.set("Serial Open")
    else:
        updateOptionMenu()
    return
    
def updateOptionMenu():
    global submitButton, serialOptionMenu, var
    newvalues = serialCommands.scan()
    if len(newvalues) == 0:
        newvalues = ["no ports available"]
        submitButton.configure(state=DISABLED)
    else:
        submitButton.configure(state=NORMAL)
    menu = serialOptionMenu.children['menu']
    menu.delete(0,END)
    for val in newvalues:
        menu.add_command(label=val,command=lambda v=var,l=val:var.set(l))
    var.set(newvalues[0])
    return

def storeCurrent():
    global ser
    thread.start_new_thread(moveCommands.storeCurrent,(ser, 1))
    return

def moveToStored():
    global ser
    global stage1Pos, stage2Pos, stage3Pos, stage4Pos
    thread.start_new_thread(moveCommands.moveAllToStored,(ser, 1, stage1Pos, stage2Pos, stage3Pos, stage4Pos))
    return

def setSettings():
    global ser
    thread.start_new_thread(serialCommands.setSettings,(ser,))
    return

def homeAll():
    global ser
    global stage1Pos, stage2Pos, stage3Pos, stage4Pos
    thread.start_new_thread(moveCommands.homeAll,(ser, stage1Pos, stage2Pos, stage3Pos, stage4Pos))
    return

def closeSerial():
    global ser, var
    try:
        serialCommands.closeSerial(ser)
        updateOptionMenu()
    except NameError:
        print ""            
    enableButtons()
    ser = None
    return

def setZeroPoint():
    global ser
    global returnZeroAllButton
    global stage1Pos, stage2Pos, stage3Pos, stage4Pos
    thread.start_new_thread(moveCommands.setZeroPoint,(ser, stage1Pos, stage2Pos, stage3Pos, stage4Pos))
    returnZeroAllButton.configure(state=NORMAL)
    return

def clearSettings():
    global ser
    thread.start_new_thread(serialCommands.clearSettings,(ser,))
    return

def returnToZeroPoint():
    global ser
    global stage1Pos, stage2Pos, stage3Pos, stage4Pos
    thread.start_new_thread(moveCommands.moveAllToStored,(ser, 0, stage1Pos, stage2Pos, stage3Pos, stage4Pos))
    return

def getMovement():
    global stage1Entry, stage2Entry, stage3Entry, stage4Entry
    stage1 = float(stage1Entry.get())
    stage1Entry.delete(0,END)
    stage2 = float(stage2Entry.get())
    stage2Entry.delete(0,END)
    stage3 = float(stage3Entry.get())
    stage3Entry.delete(0,END)
    stage4 = float(stage4Entry.get())
    stage4Entry.delete(0,END)
    return [stage1, stage2, stage3, stage4]

def moveAllAbsolute():
    global ser
    global stage1Pos, stage2Pos, stage3Pos, stage4Pos
    [stage1, stage2, stage3, stage4] = getMovement()
    if stage1 < 0 or stage2 < 0 or stage3 < 0 or stage4 < 0:
        print "invalid movement dimensions"
    else:
        thread.start_new_thread(moveCommands.moveAllAbsolute, (ser, stage1, stage2, stage3, stage4, stage1Pos, stage2Pos, stage3Pos, stage4Pos))
    return

def setupFrames():
    global lFrame, mFrame, rFrame
    global defaultWidth, defaultHeight, frameColor
    
    #lFrame is the top-left frame of the window
    lFrame = Frame(root, width=defaultWidth, height=defaultHeight, bg=frameColor)
    lFrame.grid(row = 0, column = 0, sticky=N+S+E+W)
    lFrame.pack_propagate(0)
    #mFrame is the top-middle frame of the window
    mFrame = Frame(root, width=defaultWidth, height=defaultHeight, bg=frameColor)
    mFrame.grid(row = 0, column = 1, sticky = N+S+E+W)
    mFrame.pack_propagate(0)
    #rFrame is the top-right frame of the window
    rFrame = Frame(root, width=defaultWidth, height=defaultHeight, bg=frameColor)
    rFrame.grid(row = 0, column = 2, sticky = N+S+E+W)
    rFrame.pack_propagate(0)
    return

def setupHomeAndZeroSection():
    global homeAllButton, homeStoreAllButton, storeCurrentButton, returnToStoredButton, zeroAllButton, returnZeroAllButton
    global buttonWidth, buttonHeight, buttonBGColor, buttonFGColor
    global divisions
    
    homeAndZeroLabel = Label(mFrame, text="Home and Zero Commands", font=("Times New Roman", 16), wraplength=200, bg="white")
    homeAndZeroLabel.place(relx=.5, rely=1.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    
    homeAllButton = Button(mFrame, text="Home All", command=homeAll, bg=buttonBGColor, fg=buttonFGColor)
    homeAllButton.place(relx=.5, rely=3.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    homeAllButton.configure(state=DISABLED)
    
    homeStoreAllButton = Button(mFrame, text="Home All and Store", command=homeStoreAll, bg=buttonBGColor, fg=buttonFGColor)
    homeStoreAllButton.place(relx=.5, rely=5.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    homeStoreAllButton.configure(state=DISABLED)
    
    zeroAllButton = Button(mFrame, text="Set Zero Point", command=setZeroPoint, bg=buttonBGColor, fg=buttonFGColor)
    zeroAllButton.place(relx=.5, rely=7.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    zeroAllButton.configure(state=DISABLED)
    
    returnZeroAllButton = Button(mFrame, text="Return to Zero Point", command=returnToZeroPoint, bg=buttonBGColor, fg=buttonFGColor)
    returnZeroAllButton.place(relx=.5, rely=9.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    returnZeroAllButton.configure(state=DISABLED)
    
    storeCurrentButton = Button(mFrame, text="Store Current Position", command=storeCurrent, bg=buttonBGColor, fg=buttonFGColor)
    storeCurrentButton.place(relx=.5, rely=11.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    storeCurrentButton.configure(state=DISABLED)
    
    returnToStoredButton = Button(mFrame, text="Return to Stored Position", command=moveToStored, bg=buttonBGColor, fg=buttonFGColor)
    returnToStoredButton.place(relx=.5, rely=13.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    returnToStoredButton.configure(state=DISABLED)
    return

def setupSerialSection():
    global submitButton, rescanButton, serialOptionMenu, setSettingsButton
    global closeSerialButton, clearSettingsButton
    global buttonWidth, buttonHeight, buttonBGColor, buttonFGColor
    global divisions
    
    serialLabel = Label(lFrame, text="Serial Commands", font=("Times New Roman", 16), wraplength=200, bg="white")
    serialLabel.place(relx=.5, rely=1.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    
    rescanButton = Button(lFrame, text="Rescan", command=updateOptionMenu, bg=buttonBGColor, fg=buttonFGColor)
    rescanButton.place(relx=.5, rely=3.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
      
    serialOptionMenu = OptionMenu(lFrame, var, *values)
    serialOptionMenu.place(relx=.5, rely=5.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    serialOptionMenu['bg'] = buttonBGColor
    serialOptionMenu['fg'] = buttonFGColor
    serialOptionMenu.configure(activebackground=buttonBGColor, activeforeground=buttonFGColor, highlightthickness = 0)
    serialOptionMenu.configure(borderwidth = 0)
    dropMenu = serialOptionMenu['menu']
    dropMenu.configure(bg=buttonBGColor, fg=buttonFGColor, activeborderwidth=0)
    
    submitButton = Button(lFrame, text="Submit", command=setSerial, bg=buttonBGColor, fg=buttonFGColor)
    submitButton.place(relx=.5, rely=7.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    submitButton.configure(state=DISABLED)
    
    setSettingsButton = Button(lFrame, text="Set Stage Settings", command=setSettings, bg=buttonBGColor, fg=buttonFGColor)
    setSettingsButton.place(relx=.5, rely=9.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    setSettingsButton.configure(state=DISABLED)
    
    clearSettingsButton = Button(lFrame, text="Clear Stage Settings", command=clearSettings, bg=buttonBGColor, fg=buttonFGColor)
    clearSettingsButton.place(relx=.5, rely=11.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    clearSettingsButton.configure(state=DISABLED)
    
    closeSerialButton = Button(lFrame, text="Close Serial", command=closeSerial, bg=buttonBGColor, fg=buttonFGColor)
    closeSerialButton.place(relx=.5, rely=13.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    closeSerialButton.configure(state=DISABLED)
    return

def setupMoveSection():
    global defaultWidth, defaultHeight
    global buttonWidth, buttonHeight, buttonBGColor, buttonFGColor
    global stage1Entry, stage2Entry, stage3Entry, stage4Entry
    global moveAllRelativeButton, moveAllAbsoluteButton
    global divisions
    
    moveLabel = Label(rFrame, text="Move Commands", font=("Times New Roman", 16), wraplength=200, bg="white")
    moveLabel.place(relx=.5, rely=1.0/divisions, anchor="c", relwidth=buttonWidth, relheight=buttonHeight)
    
    stageEntryFrame = Frame(rFrame, width=buttonWidth, bg="white")
    stageEntryFrame.place(relx=.5, rely=7.0/divisions, anchor="c")
    
    stage1Label = Label(stageEntryFrame, text="Slide Mouse in", bg="white", fg="black", font=("Times New Roman", 12))
    stage1Label.grid(row=0, columnspan=2)
    
    stage1Entry = Entry(stageEntryFrame, font=("Times New Roman", 12), width=15)
    stage1Entry.grid(row=1, column=0)
    stage1Entry.configure(state=DISABLED)
    
    stage1Units = Label(stageEntryFrame, text="mm", anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage1Units.grid(row=1, column=1)
    
    stage2Label = Label(stageEntryFrame, text="Rotation about Axis", bg="white", fg="black", font=("Times New Roman", 12))
    stage2Label.grid(row=2, columnspan=2)
    
    stage2Entry = Entry(stageEntryFrame, font=("Times New Roman", 12), width=15)
    stage2Entry.grid(row=3, column=0)
    stage2Entry.configure(state=DISABLED)
    
    stage2Units = Label(stageEntryFrame, text="degrees", anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage2Units.grid(row=3, column=1)
    
    stage3Label = Label(stageEntryFrame, text="Rotary Axis Y-point", bg="white", fg="black", font=("Times New Roman", 12))
    stage3Label.grid(row=4, columnspan=2)
    
    stage3Entry = Entry(stageEntryFrame, font=("Times New Roman", 12), width=15)
    stage3Entry.grid(row=5, column=0)
    stage3Entry.configure(state=DISABLED)
    
    stage3Units = Label(stageEntryFrame, text="mm", anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage3Units.grid(row=5, column=1)
    
    stage4Label = Label(stageEntryFrame, text="Rotary Axis X-point", bg="white", fg="black", font=("Times New Roman", 12))
    stage4Label.grid(row=6, columnspan=2)
    
    stage4Entry = Entry(stageEntryFrame, font=("Times New Roman", 12), width=15)
    stage4Entry.grid(row=7, column=0)
    stage4Entry.configure(state=DISABLED)
    
    stage4Units = Label(stageEntryFrame, text="mm", anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage4Units.grid(row=7, column=1)
    
    moveAllRelativeButton = Button(rFrame, text="Move All Stages Relative", bg=buttonBGColor, fg=buttonFGColor, command=moveAllRelative)
    moveAllRelativeButton.place(relx=.5, rely=13.0/divisions, relwidth=buttonWidth, relheight=buttonHeight, anchor="c")
    moveAllRelativeButton.configure(state=DISABLED)
    
    moveAllAbsoluteButton = Button(rFrame, text="Move All Stages Absolute", bg=buttonBGColor, fg=buttonFGColor, command=moveAllAbsolute)
    moveAllAbsoluteButton.place(relx=.5, rely=15.0/divisions, relwidth=buttonWidth, relheight=buttonHeight, anchor="c")
    moveAllAbsoluteButton.configure(state=DISABLED)
    return

def setupMovementLabels():
    global defaultWidth, defaultHeight
    global buttonWidth, buttonHeight, buttonBGColor, buttonFGColor
    global stage1Pos, stage2Pos, stage3Pos, stage4Pos
    global divisions
    stage1Pos = StringVar()
    stage2Pos = StringVar()
    stage3Pos = StringVar()
    stage4Pos = StringVar()
    stage1Pos.set("please home stages")
    stage2Pos.set("please home stages")
    stage3Pos.set("please home stages")
    stage4Pos.set("please home stages")
    #make frame on the bottom of the window
    currentPosFrame = Frame(root, width=3*defaultWidth, height=50, bg="white")
    currentPosFrame.grid(row = 1, columnspan=3)
    currentPosFrame.pack_propagate(0)
    #make the label areas
    stage1Area = Frame(currentPosFrame, bg="white", height=2/30*600, width=0.75*200)
    stage1Area.place(relx=0, rely=0, relwidth=buttonWidth*.75, relheight=1)
    
    stage2Area = Frame(currentPosFrame, bg="white", height=2/30*600, width=0.75*200)
    stage2Area.place(relx=0.25, rely=0, relwidth=buttonWidth*.75, relheight=1)
    
    stage3Area = Frame(currentPosFrame, bg="white", height=2/30*600, width=0.75*200)
    stage3Area.place(relx=0.5, rely=0, relwidth=buttonWidth*.75, relheight=1)
    
    stage4Area = Frame(currentPosFrame, bg="white", height=2/30*600, width=0.75*200)
    stage4Area.place(relx=0.75, rely=0, relwidth=buttonWidth*.75, relheight=1)
    #make labels to indicate the stage number
    stage1Label = Label(stage1Area, text="Z-Axis", anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage1Label.grid(row=0, column=0)
    
    stage2Label = Label(stage2Area, text="Rotary Axis", anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage2Label.grid(row=0, column=0)
    
    stage3Label = Label(stage3Area, text="Y-Axis", anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage3Label.grid(row=0, column=0)
    
    stage4Label = Label(stage4Area, text="X-Axis", anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage4Label.grid(row=0, column=0)
    #make labels to indicate the current position
    stage1Position = Label(stage1Area, textvariable=stage1Pos, anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage1Position.grid(row=1, column=0)
    
    stage2Position = Label(stage2Area, textvariable=stage2Pos, anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage2Position.grid(row=1, column=0)
    
    stage3Position = Label(stage3Area, textvariable=stage3Pos, anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage3Position.grid(row=1, column=0)
    
    stage4Position = Label(stage4Area, textvariable=stage4Pos, anchor=W, bg="white", fg="black", font=("Times New Roman", 12))
    stage4Position.grid(row=1, column=0)
    return

def updatePositions():
    #import all of the labels for the positions. 
    global ser 
    global stage1Pos, stage2Pos, stage3Pos, stage4Pos
    dataManagement.setCurrentPositionLabel(ser, stage1Pos, stage2Pos, stage3Pos, stage4Pos)
    return

menubar = Menu(root)
fileMenu = Menu(menubar, tearoff=0)
fileMenu.add_command(label="Quit", command=quit)
menubar.add_cascade(label="File", menu=fileMenu)
root.config(menu=menubar)
setupFrames()
setupSerialSection()
setupHomeAndZeroSection()
setupMoveSection()
setupMovementLabels()
updateOptionMenu()

root.mainloop()