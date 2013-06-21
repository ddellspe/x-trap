'''
Test edit to see if edits will push to google code.

The guiStuff module contains the class guiStuff which is meant to be instantiated to run the stage control software. Actual commands to
the stages and associated details are handled in modules like serialCommands, dataManagement, and moveCommands. The module guiStuff just
ensures that the user interfaces calls and validates proper low-level move commands. The module guiStuff contains most of the useful user
interface however a few things like HeightSelector.py is found in a different module. I would highly suggest going to the tkdocs website
(google it) for tutorials on widgets in ttk/tkinter.


@note: The class guiStuff attribute zeroPosition will need to be adjusted everytime the stages are assembled.
@author: Collin
'''
import ttk
from Tkinter import *
import csv
import tkFileDialog
import tkMessageBox
import numpy
from tkSimpleDialog import Dialog
import webbrowser
import os
import serialCommands
import thread
import moveCommands 
import HeightSelector
import ConfigParser
from numpy import *
from scipy import *
import AffineTransform # new affine transform
import dicomViewer
import traceback



class guiStuff:
    """
    guiStuff is the class that is the main interface for the user in the StageControlGui project. Class guiStuff instantiation is necesary
    and sufficient to allow the user full functionality of the StageControlGui project (This is done in Driver.py). Class guiStuff has two
    nested classes, GetFiducialPoints and CreateCsv. GetFiducialPoints obtains the necessary fiducial points when executing a move originating
    from CT coordinates. CreateCsv is an editor for lists of moves. guiStuff contains attributes tubeCurrentCommand (which is what is executed
    in a move) and planCurrentCommand (which is the CT coordinates + fiducials of the current command). There are a similar list versions
    of the previous attributes that are accessed in the GUI only at the value of listIndex. zeroPosition contains the zero position of the stages.

    """
    
    currentPosition = (float(0), float(0), float(0), float(180)) #order is [x,y,z,rotation]
    tubeListCommand = [["x", "y", "z", "degree"]]
    tubeCurrentCommand = (float(0), float(0), float(0), float(0)) #order is [x,y,z,rotation] like tubeListCommand
    planListCommand = [['x', 'y', 'degree', '9 o\'clock x', '9 o\'clock y', '6 o\'clock x', '6 o\'clock y', '3 o\'clock x', '3 o\'clock y', 'helix x', 'helix y']]
    planCurrentCommand = [] #for order see header of planListCommand (above)
    listIndex = 0 #index of active command in a list
    zeroPosition = [ 30.789, 29.875, 11.164 , 180.0] # [x zero, y zero , z zero, rotation zero]
    defaultZeroPosition = [ 30.789, 29.875, 11.164 , 180.0]
    tubeDimension=[31.75,116.000] #[diameter, tube length] all lengths in mm
    defaultTubeDimension=[31.75,116.000] 
    version = [1,5,1,0]
    
    
    def __init__(self, debug = False):
        '''
        Initializes GUI to serve as the main interface for stage control.
        '''

            

        self.root = Tk()
        self.root.title("x-TRAP Version "+self.getVersion())
        self.root.iconbitmap(default='iowa_logo.ico')
        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        
        self.root.bind("<Control-h>", self.heightSelect)
        self.root.option_add('*tearOff', FALSE)
        self.debug = debug
        menubar = Menu(self.root)
        self.root['menu'] = menubar
        self.menu_file = Menu(menubar)
        menu_help = Menu(menubar)
        menubar.add_cascade(menu=self.menu_file, label='File')
        menubar.add_cascade(menu=menu_help, label='Help')
        self.menu_file.add_command(label='Load CSV', command=self.loadCsv)
        self.menu_file.add_command(label='Create List', command=self.createCsv)
        self.menu_file.add_command(label='Edit List', command=self.makeCsv)
        self.menu_file.add_command(label='Save List', command=self.writeList)
        self.menu_file.add_command(label='Quit', command=self.quit)
        menu_help.add_command(label='About', command=self.about)
        menu_help.add_command(label='Help', command=self.help)
        menu_help.add_command(label='Documentation', command=self.goToDocumentation)
        
        par = ttk.Frame(self.root)
        par.grid(column=0, row=0)
        par['padding'] = (10)
        leftFrame = ttk.Frame(par)
        leftFrame.grid(column=0, row=0)
        
        self.n = ttk.Notebook(par)
        self.n.bind("<<NotebookTabChanged>>",self.moveTabChanged)
        self.n.grid(column=1, row=0)
        self.n['padding'] = (10)
        self.f1 = ttk.Frame(self.n) # first page
        f2 = ttk.Frame(self.n) # second page
        f3 = ttk.Frame(self.n) # third page
        self.f1['padding'] = (10)
        f2['padding'] = (10)
        f3['padding'] = (10)
        self.f4 = ttk.Frame(self.n)
        self.f5=ttk.Frame(self.n)
        self.f4['padding'] = (10)
        self.f5['padding'] = (10)
        self.n.add(self.f1, text='Move')
        self.n.add(f2, text='Home')
        self.n.add(f3, text='Other')
        self.n.add(self.f4, text='Configuration')
        self.n.add(self.f5, text='Progress')
        self.n.select(f2)
        
        self.xVal = DoubleVar()
        self.yVal = DoubleVar()
        self.zVal = DoubleVar()
        self.degVal = DoubleVar()
        self.progressVar = StringVar()
        self.xVal.set(0.000)
        self.yVal.set(0.000)
        self.zVal.set(0.000)
        self.degVal.set(0.000)
        self.progressVar.set("No move in progress")
        self.currentProgress = ttk.Label(self.f5, textvariable=self.progressVar, font="Serif 10 bold")
        self.currentProgress.grid(column=0, row=0, sticky=(W), columnspan=2)
        self.xPositionProgress = ttk.Label(self.f5, text="X position: ", font="Serif 10")
        self.xPositionProgress.grid(column=0, row=1, sticky=(E))
        self.yPositionProgress = ttk.Label(self.f5, text="Y position: ", font="Serif 10")
        self.yPositionProgress.grid(column=0, row=2, sticky=(E))
        self.zPositionProgress = ttk.Label(self.f5, text="Z position: ", font="Serif 10")
        self.zPositionProgress.grid(column=0, row=3, sticky=(E))
        self.rotationPositionProgress = ttk.Label(self.f5, text="Roll: ", font="Serif 10")
        self.rotationPositionProgress.grid(column=0, row=4, sticky=(E))
        self.xProgress = ttk.Progressbar(self.f5, orient=HORIZONTAL, length=200, mode='determinate', maximum=100, value=0, variable=self.xVal)
        self.xProgress.grid(column=1, row=1)
        self.yProgress = ttk.Progressbar(self.f5, orient=HORIZONTAL, length=200, mode='determinate', maximum=100, value=0, variable=self.yVal)
        self.yProgress.grid(column=1, row=2)
        self.zProgress = ttk.Progressbar(self.f5, orient=HORIZONTAL, length=200, mode='determinate', maximum=100, value=0, variable=self.zVal)
        self.zProgress.grid(column=1, row=3)
        self.degProgress = ttk.Progressbar(self.f5, orient=HORIZONTAL, length=200, mode='determinate', maximum=100, value=0, variable=self.degVal)
        self.degProgress.grid(column=1, row=4)
        self.stopButton = ttk.Button(self.f5, text="Emergency Stop", command=self.stop)
        self.stopButton.grid(column=0, row=5, columnspan=2, sticky=(W))

        
        #notebook within the move tab
        self.moveNotebook = ttk.Notebook(self.f1,width=350)
        self.moveNotebook.grid(column=0, row=0)
        self.moveNotebook.bind("<<NotebookTabChanged>>",self.moveTabChanged)
        self.moveNotebook['padding'] = (2)
        self.movePlanTab = ttk.Frame(self.moveNotebook) # first page
        self.moveTubeTab = ttk.Frame(self.moveNotebook) # second page
        self.moveRelativeTab = ttk.Frame(self.moveNotebook) # third page
        self.movePlanTab['padding'] = (2)
        self.moveTubeTab['padding'] = (2)
        self.moveRelativeTab['padding'] = (2)
        self.moveNotebook.add(self.movePlanTab, text='CT')
        self.moveNotebook.add(self.moveTubeTab, text='Tube Absolute')
        self.moveNotebook.add(self.moveRelativeTab, text='Tube Relative')
        self.moveNotebook.select(self.movePlanTab)
        
        #Tube tab within the move tab
        #Widgets that deal with x direction movement
        self.xEntry = StringVar()
        self.xTextField = Entry(self.moveTubeTab, textvariable=self.xEntry)
        self.xTextField.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.xTextField.grid(column=1, row=1, padx=3, pady=3)
        xLabel = ttk.Label(self.moveTubeTab, text="X movement: ")
        xLabel.grid(column=0, row=1, padx=3, pady=3, sticky=(E))
        xUnitLabel = ttk.Label(self.moveTubeTab, text="mm")
        xUnitLabel.grid(column=2, row=1, padx=3, pady=3, sticky=(W))
        #Widgets that deal with y direction movement
        self.yEntry = StringVar()
        self.yTextField = Entry(self.moveTubeTab, textvariable=self.yEntry)
        self.yTextField.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.yTextField.grid(column=1, row=2, padx=3, pady=3)
        yLabel = ttk.Label(self.moveTubeTab, text="Y movement: ")
        yLabel.grid(column=0, row=2, padx=3, pady=3, sticky=(E))
        yUnitLabel = ttk.Label(self.moveTubeTab, text="mm")
        yUnitLabel.grid(column=2, row=2, padx=3, pady=3, sticky=(W))
        #Widgets that deal with z direction movement
        self.zEntry = StringVar()
        self.zTextField = Entry(self.moveTubeTab, textvariable=self.zEntry)
        self.zTextField.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.zTextField.grid(column=1, row=3, padx=3, pady=3)
        zLabel = ttk.Label(self.moveTubeTab, text="Z movement: ")
        zLabel.grid(column=0, row=3, padx=3, pady=3, sticky=(E))
        zUnitLabel = ttk.Label(self.moveTubeTab, text="mm")
        zUnitLabel.grid(column=2, row=3, padx=3, pady=3, sticky=(W))
        #Widgets that deal with rotation
        self.degreeEntry = StringVar()
        self.degreeTextField = Entry(self.moveTubeTab, textvariable=self.degreeEntry)
        self.degreeTextField.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.degreeTextField.grid(column=1, row=4, padx=3, pady=3)
        degreeLabel = ttk.Label(self.moveTubeTab, text="Roll: ")
        degreeLabel.grid(column=0, row=4, padx=3, pady=3, sticky=(E))
        degreeUnitLabel = ttk.Label(self.moveTubeTab, text="degrees")
        degreeUnitLabel.grid(column=2, row=4, padx=3, pady=3, sticky=(W))
        #Move button for manual entry commands
        self.moveTube = ttk.Button(self.moveTubeTab, text="Move Absolute", command=self.move)
        self.moveTube.grid(column=1, row=5, padx=3, pady=3)
                
        #Tube Relative tab within the move tab
        #Widgets that deal with x direction movement
        self.xEntry_rel = StringVar()
        self.xTextField_rel = Entry(self.moveRelativeTab, textvariable=self.xEntry_rel)
        self.xTextField_rel.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.xTextField_rel.grid(column=1, row=1, padx=3, pady=3)
        xLabel_rel = ttk.Label(self.moveRelativeTab, text="X movement: ")
        xLabel_rel.grid(column=0, row=1, padx=3, pady=3, sticky=(E))
        xUnitLabel_rel = ttk.Label(self.moveRelativeTab, text="mm")
        xUnitLabel_rel.grid(column=2, row=1, padx=3, pady=3, sticky=(W))
        #Widgets that deal with y direction movement
        self.yEntry_rel = StringVar()
        self.yTextField_rel = Entry(self.moveRelativeTab, textvariable=self.yEntry_rel)
        self.yTextField_rel.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.yTextField_rel.grid(column=1, row=2, padx=3, pady=3)
        yLabel_rel = ttk.Label(self.moveRelativeTab, text="Y movement: ")
        yLabel_rel.grid(column=0, row=2, padx=3, pady=3, sticky=(E))
        yUnitLabel_rel = ttk.Label(self.moveRelativeTab, text="mm")
        yUnitLabel_rel.grid(column=2, row=2, padx=3, pady=3, sticky=(W))
        #Widgets that deal with z direction movement
        self.zEntry_rel = StringVar()
        self.zTextField_rel = Entry(self.moveRelativeTab, textvariable=self.zEntry_rel)
        self.zTextField_rel.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.zTextField_rel.grid(column=1, row=3, padx=3, pady=3)
        zLabel_rel = ttk.Label(self.moveRelativeTab, text="Z movement: ")
        zLabel_rel.grid(column=0, row=3, padx=3, pady=3, sticky=(E))
        zUnitLabel_rel = ttk.Label(self.moveRelativeTab, text="mm")
        zUnitLabel_rel.grid(column=2, row=3, padx=3, pady=3, sticky=(W))
        #Widgets that deal with rotation
        self.degreeEntry_rel = StringVar()
        self.degreeTextField_rel = Entry(self.moveRelativeTab, textvariable=self.degreeEntry_rel)
        self.degreeTextField_rel.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.degreeTextField_rel.grid(column=1, row=4, padx=3, pady=3)
        degreeLabel_rel = ttk.Label(self.moveRelativeTab, text="Roll: ")
        degreeLabel_rel.grid(column=0, row=4, padx=3, pady=3, sticky=(E))
        degreeUnitLabel_rel = ttk.Label(self.moveRelativeTab, text="degrees")
        degreeUnitLabel_rel.grid(column=2, row=4, padx=3, pady=3, sticky=(W))
        #Move button for manual entry commands
        self.moveRelative = ttk.Button(self.moveRelativeTab, text="Move Relative", command=self.move)
        self.moveRelative.grid(column=1, row=5, padx=3, pady=3)
        
        #CT tab within the move tab
        #Widgets that deal with x direction movement
        self.xEntry_CT = StringVar()
        self.xTextField_CT = Entry(self.movePlanTab, textvariable=self.xEntry_CT)
        self.xTextField_CT.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.xTextField_CT.grid(column=2, row=0, padx=3, pady=3)
        xLabel_CT = ttk.Label(self.movePlanTab, text="X coordinate: ")
        xLabel_CT.grid(column=1, row=0, padx=3, pady=3, sticky=(E))
        #Widgets that deal with y direction movement
        self.yEntry_CT = StringVar()
        self.yTextField_CT = Entry(self.movePlanTab, textvariable=self.yEntry_CT)
        self.yTextField_CT.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.yTextField_CT.grid(column=2, row=1, padx=3, pady=3)
        yLabel_CT = ttk.Label(self.movePlanTab, text="Y coordinate: ")
        yLabel_CT.grid(column=1, row=1, padx=3, pady=3, sticky=(E))
        #Widgets that deal with rotation
        self.degreeEntry_CT = StringVar()
        self.degreeTextField_CT = Entry(self.movePlanTab, textvariable=self.degreeEntry_CT)
        self.degreeTextField_CT.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.degreeTextField_CT.grid(column=2, row=2, padx=3, pady=3)
        degreeLabel_CT = ttk.Label(self.movePlanTab, text="Roll (degrees): ")
        degreeLabel_CT.grid(column=1, row=2, padx=3, pady=3, sticky=(E))
        #Move button for manual entry commands
        self.move_CT = ttk.Button(self.movePlanTab, text="Enter Fiducials", command=self.move)
        self.move_CT.grid(column=1, row=3, padx=3, pady=3, columnspan=2)
        self.CT_EntryMethodFrame = ttk.Labelframe(self.movePlanTab, text="Entry Method")
        self.CT_EntryMethodFrame.grid(row=0, column=0, rowspan=3, padx=5, pady=5)
        self.move_Image = ttk.Button(self.CT_EntryMethodFrame, text="Image Entry", command=self.dicomMove, width=12)
        self.move_Image.grid(column=0, row=1, padx=3, pady=3, columnspan=2)
        self.move_Image_Manual = ttk.Button(self.CT_EntryMethodFrame, text="Manual Entry", command=self.manualEntry, width=12)
        self.move_Image_Manual.grid(column=0, row=0, padx=3, pady=3)
        
        
        #Label widgets to show current command
        previousPositionLabel = ttk.Labelframe(leftFrame, text="Current position")
        previousPositionLabel.grid(column=0, row=1, sticky=(E, W))
        self.xpreviousPosition = ttk.Label(previousPositionLabel, text="X position: ", font="Serif 10")
        self.xpreviousPosition.grid(column=0, row=0, sticky=(E))
        self.ypreviousPosition = ttk.Label(previousPositionLabel, text="Y position: ", font="Serif 10")
        self.ypreviousPosition.grid(column=0, row=1, sticky=(E))
        self.zpreviousPosition = ttk.Label(previousPositionLabel, text="Z position: ", font="Serif 10")
        self.zpreviousPosition.grid(column=0, row=2, sticky=(E))
        self.rotationpreviousPosition = ttk.Label(previousPositionLabel, text="Roll: ", font="Serif 10")
        self.rotationpreviousPosition.grid(column=0, row=3, sticky=(E))
        self.xCurrentVar = StringVar()
        self.yCurrentVar = StringVar()
        self.zCurrentVar = StringVar()
        self.degCurrentVar = StringVar()
        self.xpreviousPositionValue = ttk.Label(previousPositionLabel, text=" ", font="Serif 10", textvar=self.xCurrentVar)
        self.xpreviousPositionValue.grid(column=1, row=0, sticky=(W))
        self.ypreviousPositionValue = ttk.Label(previousPositionLabel, text=" ", font="Serif 10", textvar=self.yCurrentVar)
        self.ypreviousPositionValue.grid(column=1, row=1, sticky=(W))
        self.zpreviousPositionValue = ttk.Label(previousPositionLabel, text=" ", font="Serif 10", textvar=self.zCurrentVar)
        self.zpreviousPositionValue.grid(column=1, row=2, sticky=(W))
        self.rotationpreviousPositionValue = ttk.Label(previousPositionLabel, text=" ", font="Serif 10", textvar=self.degCurrentVar)
        self.rotationpreviousPositionValue.grid(column=1, row=3, sticky=(W))
        self.updatePositionButton = ttk.Button(previousPositionLabel, text="Refresh Position Information", command=self.refreshCurrentPosition)
        self.updatePositionButton.grid(columnspan=2, row=4, sticky=(S))
        #label widgets to show current selected command
        self.xCurrentPlan = StringVar()
        self.yCurrentPlan = StringVar()
        self.zCurrentPlan = StringVar()
        self.degCurrentPlan = StringVar()
        self.xCurrentTube = StringVar()
        self.yCurrentTube = StringVar()
        self.zCurrentTube = StringVar()
        self.degCurrentTube = StringVar()
        self.xCurrentPlan.set(' ')
        self.yCurrentPlan.set(' ')
        self.zCurrentPlan.set(' ')
        self.degCurrentPlan.set(' ')
        self.xCurrentTube.set(' ')
        self.yCurrentTube.set(' ')
        self.zCurrentTube.set(' ')
        self.degCurrentTube.set(' ')
        self.position = ttk.Labelframe(leftFrame, text="Current list command ")
        self.position.grid(column=0, row=0, sticky=(E, W))
        self.xPosition = ttk.Label(self.position, text="X position: ", font="Serif 10")
        self.xPosition.grid(column=0, row=0, sticky=(E))
        self.yPosition = ttk.Label(self.position, text="Y position: ", font="Serif 10")
        self.yPosition.grid(column=0, row=1, sticky=(E))
        self.zPosition = ttk.Label(self.position, text="Z position: ", font="Serif 10")
        self.zPosition.grid(column=0, row=2, sticky=(E))
        self.rotationPosition = ttk.Label(self.position, text="Roll: ", font="Serif 10")
        self.rotationPosition.grid(column=0, row=3, sticky=(E))
        self.xPositionValue = ttk.Label(self.position, text=" ", font="Serif 10", textvar=self.xCurrentPlan)
        self.xPositionValue.grid(column=2, row=0, sticky=(W))
        self.yPositionValue = ttk.Label(self.position, text=" ", font="Serif 10", textvar=self.yCurrentPlan)
        self.yPositionValue.grid(column=2, row=1, sticky=(W))
        self.zPositionValue = ttk.Label(self.position, text=" ", font="Serif 10", textvar=self.zCurrentPlan)
        self.zPositionValue.grid(column=2, row=2, sticky=(W))
        self.rotationPositionValue = ttk.Label(self.position, text=" ", font="Serif 10", textvar=self.degCurrentPlan)
        self.rotationPositionValue.grid(column=2, row=3, sticky=(W))
        self.xTubePositionValue = ttk.Label(self.position, text=" ", font="Serif 10", textvar=self.xCurrentTube)
        self.xTubePositionValue.grid(column=1, row=0, sticky=(W))
        self.yTubePositionValue = ttk.Label(self.position, text=" ", font="Serif 10", textvar=self.yCurrentTube)
        self.yTubePositionValue.grid(column=1, row=1, sticky=(W))
        self.zTubePositionValue = ttk.Label(self.position, text=" ", font="Serif 10", textvar=self.zCurrentTube)
        self.zTubePositionValue.grid(column=1, row=2, sticky=(W))
        self.rotationTubePositionValue = ttk.Label(self.position, text=" ", font="Serif 10", textvar=self.degCurrentTube)
        self.rotationTubePositionValue.grid(column=1, row=3, sticky=(W))
        
        #Buttons to move through a loaded list of commands and to execute those commands
        leftFrameSouth = ttk.Frame(leftFrame)
        leftFrameSouth.grid(column=0, row=2)
        self.previousButton = ttk.Button(leftFrameSouth, text='< Previous', command=self.previous)
        self.previousButton.grid(column=0, row=0, ipadx=4)
        self.positionListMove = ttk.Button(leftFrameSouth, text="Move", command=self.listMove)
        self.positionListMove.grid(column=1, row=0)
        self.nextButton = ttk.Button(leftFrameSouth, text='Next >', command=self.next)
        self.nextButton.grid(column=2, row=0)
        
        otherFrame = ttk.Frame(f3)
        otherFrame.grid(column=0, row=0)
        loadFileLabel = ttk.Label(otherFrame, text="Loaded file:")
        loadFileLabel.grid(row=0, column=0, padx=3, pady=5, sticky=(E))
        self.fileNameLabel = ttk.Label(otherFrame, text="None")
        self.fileNameLabel.grid(row=0, column=1, padx=3, pady=5)
        self.browseButton = ttk.Button(otherFrame, text="Browse", command=self.loadCsv)
        self.browseButton.grid(row=0, column=2, padx=3, pady=5)
        self.serPortSelection = StringVar()
        self.serialComboBox = ttk.Combobox(otherFrame, textvariable=self.serPortSelection)
        self.serialComboBox.bind('<<ComboboxSelected>>', self.serialCallBack)
        self.serialComboBox["state"] = "readonly"
        self.serialComboBox.grid(row=1, column=1, padx=3)
        ttk.Label(otherFrame, text='Serial port:').grid(row=1, column=0, padx=3, pady=5, sticky=(E))
        rescanButton = ttk.Button(otherFrame, text='rescan', command=self.rescan)
        rescanButton.grid(row=1, column=2, padx=3)
        ttk.Label(otherFrame, text="Collimator height:").grid(row=2, column=0, padx=3, sticky=(E))
        heightSelectorButton = ttk.Button(otherFrame, text='Enter', command=self.heightSelect)
        heightSelectorButton.grid(row=2, column=1, padx=3)
        
        self.homePosition = ttk.Labelframe(self.f4, text="Zero position")
        self.homePosition.grid(column=0, row=0, sticky=(E, W), ipadx=5, padx=5)
        self.xHomePosition = ttk.Label(self.homePosition, text="X position: ", font="Serif 10")
        self.xHomePosition.grid(column=0, row=0, padx=5, sticky=(E))
        self.yHomePosition = ttk.Label(self.homePosition, text="Y position: ", font="Serif 10")
        self.yHomePosition.grid(column=0, row=1, padx=5, sticky=(E))
        self.zHomePosition = ttk.Label(self.homePosition, text="Z position: ", font="Serif 10")
        self.zHomePosition.grid(column=0, row=2, padx=5, sticky=(E))  
        self.rotationHomePosition = ttk.Label(self.homePosition, text="Roll: ", font="Serif 10")
        self.rotationHomePosition.grid(column=0, row=3, padx=5, sticky=(E))
        self.xZeroText=StringVar()
        self.yZeroText=StringVar()
        self.zZeroText=StringVar()
        self.degZeroText=StringVar()
        self.xZeroText.set("%0.3f"%self.zeroPosition[0])
        self.yZeroText.set("%0.3f"%self.zeroPosition[1])
        self.zZeroText.set("%0.3f"%self.zeroPosition[2])
        self.degZeroText.set("%0.3f"%self.zeroPosition[3])
        self.xHomePositionValue = ttk.Label(self.homePosition, textvariable=self.xZeroText)
        self.xHomePositionValue.grid(column=1, row=0, sticky=(W))
        self.yHomePositionValue = ttk.Label(self.homePosition, textvariable=self.yZeroText)
        self.yHomePositionValue.grid(column=1, row=1, sticky=(W))
        self.zHomePositionValue = ttk.Label(self.homePosition, textvariable=self.zZeroText)
        self.zHomePositionValue.grid(column=1, row=2, sticky=(W))
        self.rotationHomePositionValue = ttk.Label(self.homePosition, textvariable=self.degZeroText)
        self.rotationHomePositionValue.grid(column=1, row=3, sticky=(W))
        self.setZeroButton=ttk.Button(self.homePosition,text="Modify Zero",command=self.setZero).grid(row=4,column=0,columnspan=2)
        
        self.tubeDimensionFrame = ttk.Labelframe(self.f4, text="Tube Dimension")
        self.tubeDimensionFrame.grid(column=1, row=0, sticky=(E,W,N), ipadx=5, padx=5)
        self.diameterLabel = ttk.Label(self.tubeDimensionFrame, text="Diameter: ", font="Serif 10")
        self.diameterLabel.grid(column=0, row=0, padx=5, sticky=(E))
        self.lengthLabel = ttk.Label(self.tubeDimensionFrame, text="Length: ", font="Serif 10")
        self.lengthLabel.grid(column=0, row=1, padx=5, sticky=(E))
        self.diameter=StringVar()
        self.length=StringVar()
        self.diameter.set("%0.3f"%self.tubeDimension[0])
        self.length.set("%0.3f"%self.tubeDimension[1])
        self.diameterText=ttk.Label(self.tubeDimensionFrame,textvariable=self.diameter)
        self.diameterText.grid(column=1,row=0,sticky=(W))
        self.lengthText=ttk.Label(self.tubeDimensionFrame,textvariable=self.length)
        self.lengthText.grid(column=1,row=1,sticky=(W))
        self.setTubeDimensionButton=ttk.Button(self.tubeDimensionFrame,text="Modify Dimension",command=self.setTubeDimension)
        self.setTubeDimensionButton.grid(row=2,column=0,columnspan=2)
        self.settingsFrame = ttk.Labelframe(self.f4, text="Settings Options")
        self.settingsFrame.grid(column=0, row=1, columnspan=2, sticky=(E,W), ipadx=5, padx=5)
        self.enableSettingsButton = ttk.Button(self.settingsFrame, text="Allow Settings Modification", command=self.enableSettingsModification)
        self.enableSettingsButton.grid(column=0, row=0, padx=5, pady=5)
        self.clearSettingsButton = ttk.Button(self.settingsFrame, text="Clear Settings", command=self.clearSettings)
        self.clearSettingsButton.grid(column=1, row=0, padx=5, pady=5)
        self.setSettingsButton = ttk.Button(self.settingsFrame, text="Set Settings", command=self.setSettings)
        self.setSettingsButton.grid(column=2, row=0, padx=5, pady=5)
        
        homeButtonFrame = ttk.Frame(f2)
        homeButtonFrame.grid(column=0, row=0)
        self.homeButton = ttk.Button(homeButtonFrame, text="Reset for Fault", command=self.home, width=21)
        self.homeButton['state'] = DISABLED
        self.homeButton.grid(column=0, row=2, padx=3, pady=3)
        self.setZeroPoint = ttk.Button(homeButtonFrame, text="Initialize", command=self.setZeroPoint, width=21)
        self.setZeroPoint.grid(column=0, row=0, padx=3, pady=3)
        self.returnToZeroPoint = ttk.Button(homeButtonFrame, text="Return to Tube Zero", command=self.returnToZero, width=21)
        self.returnToZeroPoint.grid(column=0, row=1, padx=3, pady=3)
        self.returnToZeroPoint['state'] = DISABLED
        self.centerTubeButton = ttk.Button(homeButtonFrame, text="Center for imaging", command=self.centerTube, width=21)
        self.centerTubeButton.grid(column=0, row=3, padx=3, pady=3)
        if self.debug:
            self.zeroed = True
        else:
            self.zeroed = False
        self.CANCELED = False
        
        
        try:
            with open(os.getcwd()+'\\ZeroPosition.cfg','r') as configReader:
                config=ConfigParser.RawConfigParser()
                config.readfp(configReader)
                zeroPositionList=[config.getfloat('Zero Position','x'),config.getfloat('Zero Position','y'),config.getfloat('Zero Position','z'),config.getfloat('Zero Position','degree')]
                if(self.isValidZeroConfig(zeroPositionList[0],zeroPositionList[1],zeroPositionList[2],zeroPositionList[3])==True):
                    guiStuff.zeroPosition=[zeroPositionList[0],zeroPositionList[1],zeroPositionList[2],zeroPositionList[3]]
                    self.updateZeroPositionText()
        except:
            with open(os.getcwd()+'\\ZeroPosition.cfg','w') as configWriter:
                configs = ConfigParser.RawConfigParser()
                configs.add_section('Zero Position')
                configs.set('Zero Position','x','%0.3f'%guiStuff.defaultZeroPosition[0])
                configs.set('Zero Position','y','%0.3f'%guiStuff.defaultZeroPosition[1])
                configs.set('Zero Position','z','%0.3f'%guiStuff.defaultZeroPosition[2])
                configs.set('Zero Position','degree','%0.3f'%guiStuff.defaultZeroPosition[3])
                configs.write(configWriter)
                
        try:
            with open(os.getcwd()+'\\Dimension.cfg','r') as configReader2:
                configDimension=ConfigParser.RawConfigParser()
                configDimension.readfp(configReader2)
                dimensionList=[configDimension.getfloat('Tube Dimension','Diameter'),configDimension.getfloat('Tube Dimension','Length')]
                if(self.isValidDimensionConfig(dimensionList[0],dimensionList[1])):
                    guiStuff.tubeDimension=[dimensionList[0],dimensionList[1]]
                    self.updateDimensionText()
        except:
            with open(os.getcwd()+'\\Dimension.cfg','w') as configWriter2:
                configsDimension=ConfigParser.RawConfigParser()
                configsDimension.add_section('Tube Dimension')
                configsDimension.set('Tube Dimension','Diameter','%0.3f'%guiStuff.defaultTubeDimension[0])
                configsDimension.set('Tube Dimension','Length','%0.3f'%guiStuff.defaultTubeDimension[1])
                configsDimension.write(configWriter2)
        
        newvalues = serialCommands.scan()
        self.serialComboBox['values'] = newvalues
        if(len(newvalues) > 0):
            self.serPortSelection.set(newvalues[0])
            self.ser = serialCommands.openSerialGUI(int(newvalues[0][0]))
            self.enable()
        else:
            if not self.debug:
                self.disable()
            self.ser = None
        self.root.mainloop()
        

    def about(self):
        '''
        Opens the wiki for the stage control project.
        '''
        
        webbrowser.open("http://daviddellsperger.com/Senior_Design/about.php")
        


    def affineTransform(self, plan_command):
        '''
        Converts the CT coordinate of the treatment target to the proper stage movement coordinate in The x-TRAP. Uses the xy cordinates
        of three fiducials (9 o'clock, 6 o'clock, 3 o'clock) to find the xy coordinates of the x-TRAP movement. The
        helical fiducial is transformed to tube coordinates in order to find the angle of the helical fiducial relative
        to the positive x-axis(3 o'clock). The angle determines the z coordinate of the desired movement.
        from_pts are 9 o'clock, 6 o'clock, 3 o'clock in tuples of (x,y)
        to_pts are 9 o'clock, 6 o'clock, 3 o'clock in tuples of (x,y)
        The transform will get the point in the x/y plane, but to move to that point
        the stages will have to move the opposite way (i.e. positive x means negative x
        movement).  That is the reason for the weird target creation.  
        @param plan_command: Command to be affine transformed into tube coordinates
        '''
        
        
        from_pts = ((plan_command[3], plan_command[4]), (plan_command[5], plan_command[6]), (plan_command[7], plan_command[8]))
        to_pts = ((-guiStuff.tubeDimension[0]/2,0),(0,guiStuff.tubeDimension[0]/2),(guiStuff.tubeDimension[0]/2,0)) 
        trn = AffineTransform.AffineTransform(from_pts, to_pts)
        helicalFiducial=trn.Transform(plan_command[9], plan_command[10])
        zTarget = -1 * (numpy.arctan2(helicalFiducial[1], helicalFiducial[0]) * 180 / numpy.pi) / 180 * guiStuff.tubeDimension[1] #the helical fiducial starts at 0 degrees and moves to -180 degrees as the helix progresses toward the tube connection to the stages
        xyTarget=trn.Transform(plan_command[0],plan_command[1])
        target=[-xyTarget[0]]+[-xyTarget[1]]+[zTarget]+[plan_command[2]]
        return target    
    

    def centerTube(self):
        '''
        Centers the tube under the radiation source for imaging.
        '''
        
        self.disable()
        self.progressVar.set("Centering the Tube under the Radiation Source")
        guiStuff.tubeCurrentCommand = (0, 0, 63.5, 0)
        self.n.select(self.f5)
        self.moveStages()
        return
    
    def clearSettings(self):
        thread.start_new_thread(serialCommands.clearSettings, (self.ser,))
    
    def createCsv(self):
        '''
        Clears the loaded list and then allows the user to create a completely new command list. CreateCsv is instantiated to
        make the list much like self.makeCsv (it actually gets called) but createCsv does not load the previous made
        list and instead deletes it.
        '''
        #set list variables to have no commands
        guiStuff.planListCommand=[['x', 'y', 'degree', '9 o\'clock x', '9 o\'clock y', '6 o\'clock x', '6 o\'clock y', '3 o\'clock x', '3 o\'clock y', 'helix x', 'helix y']]
        guiStuff.tubeListCommand = [["x", "y", "z", "degree"]]
        #Opens a dialog for user to create list
        self.makeCsv()
        
    
    def dicomMove(self):
        self.CANCELED=False
        self.disable()
        dicomViewer.dicomViewer(self.root, self)
        self.enable()
        try:              
            if(self.CANCELED == False):  #makes sure the user hit the ok button
                if self.isValidRow(guiStuff.tubeCurrentCommand) == True and not self.debug:
                    self.n.select(self.f5)
                    self.progressVar.set("Move in progress . . .")
                    self.moveStages()
                else:
                    tkMessageBox.showwarning("Command error", "Command: " + str(guiStuff.tubeCurrentCommand) + " is invalid\nCoordinates: " +str(guiStuff.planCurrentCommand))
                    self.root.lift()
        except:
            tkMessageBox.showwarning("Command error 2", "Command: " + str(guiStuff.tubeCurrentCommand) + " is invalid")
             
    
    def getVersion(self):
        versionText = str(self.version[0])+"."+str(self.version[1])+"."+str(self.version[2])+"."+str(self.version[3])
        return versionText    
    
    def disable(self):
        '''
        During stage movement buttons are disabled by the disable method.
        '''
        
        self.nextButton['state'] = DISABLED
        self.previousButton['state'] = DISABLED
        self.positionListMove['state'] = DISABLED
        self.browseButton['state'] = DISABLED
        self.moveTube['state'] = DISABLED
        self.move_CT['state']=DISABLED
        self.returnToZeroPoint['state'] = DISABLED
        self.setZeroPoint['state'] = DISABLED
        self.moveRelative['state'] = DISABLED
        self.centerTubeButton['state'] = DISABLED
        self.manualEntry(False)
        self.enableSettingsModification(False)
        self.move_Image_Manual['state'] = DISABLED
        self.move_Image['state'] = DISABLED
        self.clearSettingsButton['state'] = DISABLED
        self.setSettingsButton['state'] = DISABLED
        self.enableSettingsButton['state'] = DISABLED
        
    def enableSettingsModification(self, state=True):
        if state:
            state = tkMessageBox.askokcancel("Change Settings", "Changing settings may cause errors in the future.  Are you sure that you want to change the settings?")
        else:
            pass
        if state:
            self.clearSettingsButton['state'] = NORMAL
            self.setSettingsButton['state'] = NORMAL
        else:
            self.clearSettingsButton['state'] = DISABLED
            self.setSettingsButton['state'] = DISABLED
   
    
    def enable(self):
        '''
        enable sets all the buttons to normal functionality after a move command.
        '''
        
        
        self.homeButton['state'] = NORMAL
        self.browseButton['state'] = NORMAL
        self.setZeroPoint['state'] = NORMAL
        self.nextButton['state'] = NORMAL
        self.previousButton['state'] = NORMAL
        self.enableSettingsButton['state'] = NORMAL
        if self.zeroed == False:
            self.homeButton['state'] = DISABLED
            self.returnToZeroPoint['state'] = DISABLED
            self.moveTube['state'] = DISABLED
            self.moveRelative['state'] = DISABLED
            self.move_CT['state']=DISABLED
            self.positionListMove['state'] = DISABLED
            self.centerTubeButton['state'] = DISABLED
            self.move_Image_Manual['state'] = DISABLED
            self.move_Image['state'] = DISABLED
        else:
            self.homeButton['state'] = NORMAL
            self.returnToZeroPoint['state'] = NORMAL
            self.moveTube['state'] = NORMAL
            self.moveRelative['state'] = NORMAL
            self.move_CT['state']=NORMAL
            self.positionListMove['state'] = NORMAL
            self.centerTubeButton['state'] = NORMAL
            self.move_Image_Manual['state'] = NORMAL
            self.move_Image['state'] = NORMAL


    def goToDocumentation(self):
        '''
        Opens page that contains documentation links.
        '''
        webbrowser.open("http://daviddellsperger.com/Senior_Design")

    def heightSelect(self, *args):
        '''
        Starts a dialog that suggests elevation of collimator and size of apperature given a treatment size.
        '''
        HeightSelector.HeightSelector(self.root)
        return
    
    def help(self):
        '''
        Opens the help manual.
        '''
        os.startfile('http://daviddellsperger.com/Senior_Design/x-Trap%20User%20Guide.pdf')
        
    def home(self):
        '''
        Homes all stages to the absolute zero point of the stages (not to middle of the stages as defined by guiStuff.zeroPoint). See moveCommands.homeAll for detailed
        move instructions.
        '''
        self.disable()
        thread.start_new_thread(moveCommands.homeAll, (self.ser, self.zCurrentVar, self.degCurrentVar, self.xCurrentVar, self.yCurrentVar, self, self.zeroPosition))
        return
        
        
    def isValid(self):
        '''
        Checks for valid csv file format. Ignores the first line which should be column headers.
        
        @return: true or false for validity of the contents of a csv file. Checks if the information has valid numbers.
        '''

        tubeValues = guiStuff.tubeListCommand[1:]
        for row in tubeValues:
            if(self.isValidRow(row) == True):
                pass #do nothing
            else:
                return False
        return True
    
    
    def isValidZeroConfig(self,x,y,z,degree):
        
        try:
            if(x<float(0) or x>float(50)):
                return False
            if(y<float(0) or y>float(50)):
                return False
            if(z<float(0) or z>float(150)):
                return False
            if(degree<float(0) or degree>float(720)):
                return False
        except:
            return False
        
        return True
    
    def isValidDimensionConfig(self,diameter,length):
        try:
            if(diameter<float(10)):
                return False
            if(length<float(10)):
                return False
        except:
            return False
        return True

    
    def isValidRow(self, row):
        '''
        Checks if a single command row is valid. Ensures the command is within bounds of the stages and is actually all numbers.
        
        @param row: A single command entry for validity checking
        '''
        
        command_index = 0
        try:
            for commands in row:
                stageCommand = commands
                if(command_index == 0):
                    if((stageCommand + self.zeroPosition[0] < float(0)) or (stageCommand + self.zeroPosition[0] > float(50))):
                        return False
                elif(command_index == 1):
                    if(stageCommand + self.zeroPosition[1] < float(0) or stageCommand + self.zeroPosition[1] > float(50)):
                        return False
                elif(command_index == 2):
                    if(stageCommand + self.zeroPosition[2] < float(0) or stageCommand + self.zeroPosition[2] > float(150)):
                        return False
                elif(command_index == 3):
                    if(stageCommand + self.zeroPosition[3] < float(0) or stageCommand + self.zeroPosition[3] > float(720)):
                        return False
                command_index += 1
            return True
        except:
            return False

            
    def isValidRowRelative(self, row):
        '''
        Checks if a single command row is valid. Ensures the command is within bounds of the stages and is actually all numbers.
        
        @param row: A single command entry for validity checking
        '''
        self.refreshCurrentPosition()
        command_index = 0
        try:
            for commands in row:
                stageCommand = commands
                if(command_index == 0):
                    if((stageCommand + self.zeroPosition[0] + guiStuff.currentPosition[0] < float(0)) or (stageCommand + self.zeroPosition[0] + guiStuff.currentPosition[0] > float(50))):
                        print "Problem with x-value:"+str(stageCommand + self.zeroPosition[0] + guiStuff.currentPosition[0])
                        return False
                elif(command_index == 1):
                    if((stageCommand + self.zeroPosition[1] + guiStuff.currentPosition[1] < float(0)) or (stageCommand + self.zeroPosition[1] + guiStuff.currentPosition[1] > float(50))):
                        print "Problem with y-value:"+str(stageCommand + self.zeroPosition[1] + guiStuff.currentPosition[1])
                        return False
                elif(command_index == 2):
                    if((stageCommand + self.zeroPosition[2] + guiStuff.currentPosition[2] < float(0)) or (stageCommand + self.zeroPosition[2] + guiStuff.currentPosition[2] > float(150))):
                        print "Problem with z-value:"+str(stageCommand + self.zeroPosition[2] + guiStuff.currentPosition[2])
                        return False
                elif(command_index == 3):
                    if((stageCommand + self.zeroPosition[3] + guiStuff.currentPosition[3] < float(0)) or (stageCommand + self.zeroPosition[3] + guiStuff.currentPosition[3] > float(720))):
                        print "Problem with rotation value:"+str(stageCommand + self.zeroPosition[3] + guiStuff.currentPosition[3])
                        return False
                command_index += 1
            return True
        except:
            return False
        
        
    def listAffineTransform(self):
        '''
        When a list of commands is loaded by loadCsv, the listAffineTransform is called to transform all commands to tube coordinates and return the values.
        
        @return: list of tube coordinate commands
        '''
        
        for row in guiStuff.planListCommand[1:]:
            guiStuff.tubeListCommand.append(self.affineTransform(row))
            
        return guiStuff.tubeListCommand
        
    def listMove(self):
        '''
        Move method that executes the current move command in the loaded CSV file. The current command is defined as the command
        in csvFile that represents the value in positionNumber. Call back function for self.positionListMove button
        '''
        
        if(self.isValidRow(guiStuff.tubeCurrentCommand) == True):
            self.n.select(self.f5)
            self.progressVar.set("Move in progress . . .")
            self.moveStages()
        else:
            tkMessageBox.showwarning("Command error", "Command: " + str(guiStuff.tubeCurrentCommand) + " is invalid")
        
        self.root.lift()
        
        
    def loadCsv(self, *args):
        '''
        loadCsv allows the user to choose the CSV file from a file dialog. If there is an error in 
        reading the CSV file then a warning box alerts the user. Problems in loading could be do to empty/no file or the commands could
        be out of bounds. Call back function for the "Load CSV" command in self.menu_file.
        '''
        
        try:
            root2 = Tk()
            root2.withdraw()
            filename = tkFileDialog.askopenfilename(initialdir="C:")
            guiStuff.planListCommand = self.readCsv(filename)
            guiStuff.tubeListCommand = self.listAffineTransform()
            if(self.isValid() == True):
                self.updateCsvInfo()
                self.fileNameLabel['text'] = filename.split("/")[-1]
            else:
                guiStuff.tubeListCommand = [['x', 'y', 'z', 'degree']]
                guiStuff.planListCommand = [['x', 'y', 'degree', '9 o\'clock x', '9 o\'clock y', '6 o\'clock x', '6 o\'clock y', '3 o\'clock x', '3 o\'clock y', 'helix x', 'helix y']]
                tkMessageBox.showwarning("Open file", "The file contains invalid data\n(%s)" % filename)
        except:
            guiStuff.tubeListCommand = [['x', 'y', 'z', 'degree']]
            guiStuff.planListCommand = [['x', 'y', 'degree', '9 o\'clock x', '9 o\'clock y', '6 o\'clock x', '6 o\'clock y', '3 o\'clock x', '3 o\'clock y', 'helix x', 'helix y']]
            if(filename != ""):    #if a file was selected but could not be loaded
                tkMessageBox.showwarning("Open file", "Cannot open this file\n(%s)\n\nThe follow error occured:\n\n%s" % (filename, traceback.format_exc()))
        self.root.lift()
       
    def makeCsv(self, *args):
        '''Instantiates a CreateCsv object to allow user to edit a list and/or create a csv file. Call back function 
        for the "Edit list" command in self.menu_file.
        '''
        guiStuff.CreateCsv(self, self.root) 
        
    def manualEntry(self, state=True):
        if state:
            self.move_CT['state']=NORMAL
            self.xTextField_CT['state']=NORMAL
            self.yTextField_CT['state']=NORMAL
            self.degreeTextField_CT['state']=NORMAL
        else:
            self.move_CT['state']=DISABLED
            self.xTextField_CT['state']=DISABLED
            self.yTextField_CT['state']=DISABLED
            self.degreeTextField_CT['state']=DISABLED
            

    def move(self, *args):
        '''
        Stage move command method that moves the stages to the manually entered values present in the text entry fields in the
        move tab of the gui. Note no parameters are needed since the commands are extracted from the users entry. This method is
        only called by the "move" button found below the entry fields in the move tab. Depending on the selected radiobuttons it
        will either ask for fiducials (a "PLAN" move) or not (a "TUBE" move). Call back function for the self.move button.
        '''

        if(self.moveNotebook.select() == self.moveNotebook.tabs()[0]):
            try:
                temp = [float(self.xEntry_CT.get()), float(self.yEntry_CT.get()), float(self.degreeEntry_CT.get())]
                guiStuff.planCurrentCommand = temp + [float(0), float(0), float(0), float(0), float(0), float(0), float(0), float(0), float(0)]
                self.disable()
                fiducial = guiStuff.GetFiducialPoints(self, True, self.root) #true parameter indicates move after getting fiducials
                self.enable()
                
                if(fiducial.CANCELED == False):  #makes sure the user hit the ok button
                    if(self.isValidRow(guiStuff.tubeCurrentCommand) == True):
                        self.n.select(self.f5)
                        self.progressVar.set("Move in progress . . .")
                        self.moveStages()
                    else:
                        tkMessageBox.showwarning("Command error", "Command: " + str(guiStuff.tubeCurrentCommand) + " is invalid")
                self.root.lift()
            except:
                tkMessageBox.showwarning("Command error 2", "Command: " + str(guiStuff.tubeCurrentCommand) + " is invalid")
                
        elif(self.moveNotebook.select() == self.moveNotebook.tabs()[1]):
            try:
                if(self.setTubeCurrentCommand(20, [float(self.xTextField.get()), float(self.yTextField.get()), float(self.zTextField.get()), float(self.degreeTextField.get())]) == True):
                    self.n.select(self.f5)
                    self.progressVar.set("Move in progress . . .")
                    self.moveStages()
                else:
                    tkMessageBox.showwarning("Command error", "Command: " + str(guiStuff.tubeCurrentCommand) + " is invalid")
            except:
                tkMessageBox.showwarning("Command error 2", "Command: " + str(guiStuff.tubeCurrentCommand) + " is invalid")
                                
        elif(self.moveNotebook.select() == self.moveNotebook.tabs()[2]):
            try:
                if(self.setTubeCurrentCommand(21, [float(self.xTextField_rel.get()), float(self.yTextField_rel.get()), float(self.zTextField_rel.get()), float(self.degreeTextField_rel.get())]) == True):
                    self.n.select(self.f5)
                    self.progressVar.set("Move in progress . . .")
                    self.moveStagesRelative()
                else:
                    tkMessageBox.showwarning("Command error", "Command: " + str(guiStuff.tubeCurrentCommand) + " is invalid")
            except:
                tkMessageBox.showwarning("Command error 2", "Command: " + str(guiStuff.tubeCurrentCommand) + " is invalid")
                print "Exception encountered" + str(sys.exc_info()[0])
                print "Exception encountered" + str(sys.exc_info()[1])
                print "Exception encountered" + str(sys.exc_info()[2])
                                           
    def moveStages(self):
        '''
        Issues move command to stages based on the current tube command (guiStuff.tubeCurrentCommand). Calls moveCommands.moveAllAbsolute with the serial connection, current tube command, and StringVar to update the current position text.
        '''
        
        self.disable()
        self.zeroBars()
        thread.start_new_thread(moveCommands.moveAllAbsolute, (self.ser, guiStuff.tubeCurrentCommand[2], guiStuff.tubeCurrentCommand[3], guiStuff.tubeCurrentCommand[0], guiStuff.tubeCurrentCommand[1], self.zCurrentVar, self.degCurrentVar, self.xCurrentVar, self.yCurrentVar, self.zeroPosition, self))
        return
    
    def moveStagesRelative(self):
        '''
        Issues the move command to the stages based on the current tube command (guiStuff.tubeCurrentCommand), zeroPosition and the current position of the tube
        Calls the moveCommands.moveAllRelative command with the serial port, current command, all of the string vars for progress bars, zero position, current position and a reference to this GUI
        '''
        
        self.disable()
        self.zeroBars()
        thread.start_new_thread(moveCommands.moveAllRelative, (self.ser, guiStuff.tubeCurrentCommand[2], guiStuff.tubeCurrentCommand[3], guiStuff.tubeCurrentCommand[0], guiStuff.tubeCurrentCommand[1], self.zCurrentVar, self.degCurrentVar, self.xCurrentVar, self.yCurrentVar, self.zeroPosition, guiStuff.currentPosition, self))
        return
    
    def refreshCurrentPosition(self):
        #self.disable()
        thread.start_new_thread(serialCommands.updatePositionLabel, (self.ser, self.zCurrentVar, self.degCurrentVar, self.xCurrentVar, self.yCurrentVar, self.zeroPosition, self))
    
    def moveTabChanged(self, event):
        self.manualEntry(False)
        self.enableSettingsModification(False)
            
    def next(self):
        '''
        Updates the current command to the next command in the list. Also, updates the current list command text.
        Call back function for the self.nextButton button.
        
        @note:  Does not execute a move command.
        '''
        
        if((guiStuff.listIndex < len(guiStuff.tubeListCommand) - 1) and (guiStuff.listIndex < len(guiStuff.planListCommand) - 1)):
            guiStuff.listIndex += 1
            guiStuff.planCurrentCommand = guiStuff.planListCommand[guiStuff.listIndex]
            guiStuff.tubeCurrentCommand = guiStuff.tubeListCommand[guiStuff.listIndex]
            self.position['text'] = "Current list command: " + str(guiStuff.listIndex)
            try:
                currentPlanList = guiStuff.planListCommand[guiStuff.listIndex][:4]
                currentTubeList = guiStuff.tubeListCommand[guiStuff.listIndex]
                self.setCurrentCommandText(currentTubeList[0], currentTubeList[1], currentTubeList[2], currentTubeList[3], currentPlanList[0], currentPlanList[1], currentPlanList[2], currentPlanList[3])
            except:
                tkMessageBox.showerror("List", "Error with accessing list command")

    def previous(self):
        '''
        Updates the current command to the previous command in the list. Also, updates the current list command text.
        Call back function for the self.previousButton button.
        
        @note:  Does not execute a move command.
        '''
        
        if(guiStuff.listIndex > 1):
            guiStuff.listIndex -= 1
            guiStuff.planCurrentCommand = guiStuff.planListCommand[guiStuff.listIndex]
            guiStuff.tubeCurrentCommand = guiStuff.tubeListCommand[guiStuff.listIndex]
            self.position['text'] = "Current list command: " + str(guiStuff.listIndex)
            
            try:
                currentPlanList = guiStuff.planListCommand[guiStuff.listIndex][:4]
                currentTubeList = guiStuff.tubeListCommand[guiStuff.listIndex]
                self.setCurrentCommandText(currentTubeList[0], currentTubeList[1], currentTubeList[2], currentTubeList[3], currentPlanList[0], currentPlanList[1], currentPlanList[2], currentPlanList[3])
            except:
                tkMessageBox.showerror("List", "Error with accessing list command")
                

    def quit(self):
        """
        Exits the program. Called by a menu bar option File->Quit. However, closes serial port connection before quiting.
        It is the call back function for the "Quit" command in self.menu_file.
        """
        if self.ser is not None:
            serialCommands.closeSerial(self.ser)
        self.root.quit()
    

    def readCsv(self, readPath):
        '''
        readCsv reads a csv file and returns the contents of the csv file in the form of a list.
        
        @type readPath: String
        @param readPath: full file path of the csv file
        @return: returns the csv file contents as a list
        '''
        
        csvfile = open(readPath, "r+")
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        readList = []
        floatRow = []
        index = 0
        for row in reader:
            if(index > 0):
                for element in row:
                    floatRow.append(float(element))
            else:
                floatRow = row
            readList.append(floatRow)
            floatRow = []
            index += 1
        return readList

    def rescan(self, *args):
        '''
        Rescans the available serial ports and updates the serial selection combobox. Call back function for the rescanButton button.
        '''
        
        newvalues = serialCommands.scan()
        self.serialComboBox['values'] = newvalues
        self.enable()

    def resetRotation(self):
        thread.start_new_thread(moveCommands.resetSpeed, (self.ser,))
    
    
    def returnToZero(self):
        '''
        Moves stges back to zero point specified in guiStuff.zeroPoint. Call back function for the self.returnToZeroPoint button.
        '''
        
        self.disable()
        self.progressVar.set("Returning to Zero Point")
        guiStuff.tubeCurrentCommand = (0, 0, 0, 0)
        self.n.select(self.f5)
        self.moveStages()
        return
    
    def saveExecutedCommands(self):
        '''work in progress'''
        self.writeCsv(self.exectutedCommands_tubeCoordinates)
    
    def serialCallBack(self, *args):
        '''
        Handles manual selection of serial ports (combo box in the other tab). Merely changing the selection will change the
        serial port connection. Call back function for the self.serialComboBox combobox.
        '''
        serialCommands.closeSerial(self.ser)
        com = self.serPortSelection.get()#gets the current selection in the serial port dropdown box
        if com[1:4].isdigit():#if it's a 3-digit number
            index = int(com[1:4])
        elif com[1:3].isdigit():#if it's a 2-digit number
            index = int(com[1:3])
        elif com[1:2].isdigit():#if it's a 1-digit number
            index = int(com[1:2])
        self.ser = serialCommands.openSerialGUI(index)#create port based on the index, not com number
        self.resetRotation(self.ser)
        
    def setSettings(self):
        thread.start_new_thread(serialCommands.setSettings, (self.ser,))
        
    
    def setCurrentCommandText(self, xTube, yTube, zTube, degTube, xPlan, yPlan, zPlan, degPlan):
        '''
        Sets the current list command text (text that shows the commands in the loaded list). The command in tube coordinates
        is displayed without parenthesis and the originally entered ct coordinates are displayed in parenthesis. The current list 
        command text is displayed in the upper left of the main gui. Parameters are entered tube coordinates first (x,y,z,rotation) followed
        by the plan command (ct coordinates). Note only the value of the actual point for the plan (not fiducials) is entered
        as a parameter. The plan coordinates of the actual point of interest is displayed to double check list position for the user.
        '''
        try:
            self.xCurrentTube.set("%0.3f mm" % xTube)
            self.yCurrentTube.set("%0.3f mm" % yTube)
            self.zCurrentTube.set("%0.3f mm" % zTube)
            self.degCurrentTube.set("%0.3f %c" % (degTube, unichr(176)))
            
            ##### The "plan" coordinates changed when the affine transform changed, currently the text is being set incorrectly so I just removed the plan text all together #######
            #self.xCurrentPlan.set("(%0.3f)" % xPlan)
            #self.yCurrentPlan.set("(%0.3f)" % yPlan)
            #self.zCurrentPlan.set("(%0.3f)" % zPlan)
            #self.degCurrentPlan.set("(%0.3f)" % degPlan)
            self.xCurrentPlan.set('')
            self.yCurrentPlan.set('')
            self.zCurrentPlan.set('')
            self.degCurrentPlan.set('')
        except:
            self.xCurrentTube.set('')
            self.yCurrentTube.set('')
            self.zCurrentTube.set('')
            self.degCurrentTube.set('')
            self.xCurrentPlan.set('')
            self.yCurrentPlan.set('')
            self.zCurrentPlan.set('')
            self.degCurrentPlan.set('')
    
    
    def setListIndex(self, listPosition):
        '''
        Sets the list index (which marks the active command in command lists) to the entered parameter if valid.
        
        @param listPosition: integer to set as current position in command lists
        '''
        
        if(listPosition >= 0):
            guiStuff.listIndex = listPosition
        
    def setPlanCurrentCommand(self, planCommand):
        '''
        Sets the current planed CT coordinate move (point plus fiducials) to the entered parameter.
        
        @param planCommand: planed CT coordinate move that has the point of interest and fiducial points
        '''
        
        guiStuff.planCurrentCommand = planCommand    
    
    def setPlanListCommand(self, command):
        '''
        Adds a command in CT coordinates with associated fiducial points to the list of commands (self.planListCommand). The method will insert the command based on the value of the list index (guiStuff.listIndex).
        The set method will appropriately append or insert in the middle.
        
        @param command: Command in CT coordinates with associated fiducial points
        '''

        if(guiStuff.planListCommand == [['x', 'y', 'degree', '9 o\'clock x', '9 o\'clock y', '6 o\'clock x', '6 o\'clock y', '3 o\'clock x', '3 o\'clock y', 'helix x', 'helix y']]):
            guiStuff.planListCommand.append(command)
        elif(guiStuff.listIndex == len(guiStuff.planListCommand)):
            guiStuff.planListCommand.append(command)
        else:
            guiStuff.planListCommand.pop(guiStuff.listIndex)
            guiStuff.planListCommand.insert(guiStuff.listIndex, command)
            
    def setTubeCurrentCommand(self, moveType, tubeCommand):
        '''
        Sets the current tube command (self.tubeCurrentCommand) to the entered parameter if it is valid.
        
        @param moveType: 20 or 21, 20 for absolute move, 21 for relative move
        @param tubeCommand: tube command to be set as the current tube command
        '''
        if(moveType == 20): #absolute movement
            if(self.isValidRow([float(tubeCommand[0]), float(tubeCommand[1]), float(tubeCommand[2]), float(tubeCommand[3])])):
                guiStuff.tubeCurrentCommand = tubeCommand 
                return True
            else:
                return False  
        elif(moveType == 21): #relative movement
            if(self.isValidRowRelative([float(tubeCommand[0]), float(tubeCommand[1]), float(tubeCommand[2]), float(tubeCommand[3])])):
                guiStuff.tubeCurrentCommand = tubeCommand 
                return True
            else:
                return False     
    
    
    def setTubeDimension(self):
        guiStuff.SetTubeDimension(self,self.root)
        return
    
    def setTubeListCommand(self, newTubeCommand):
        if(guiStuff.tubeListCommand == [['x', 'y', 'z', 'degree']] or guiStuff.listIndex == len(guiStuff.tubeListCommand)):
            guiStuff.tubeListCommand.append(newTubeCommand)
        else:
            guiStuff.tubeListCommand.pop(guiStuff.listIndex)
            guiStuff.tubeListCommand.insert(guiStuff.listIndex, newTubeCommand)
            
    def setZero(self):
        
        guiStuff.SetZeroPoint(self,self.root)
            
    def setZeroPoint(self):
        '''
        First homes stages and then moves to the zero point identified in the class attribute zeroPoint. Calls moveCommands.SetZeroPoint in a new thread to execute movement.
        '''
        
        self.disable()
        self.selectProgressBars()
        self.progressVar.set("Homing the Stages")
        thread.start_new_thread(moveCommands.setZeroPoint, (self.ser, self.zCurrentVar, self.degCurrentVar, self.xCurrentVar, self.yCurrentVar, self.zeroPosition, self))
        return

    def stop(self):
        '''
        Stops movement of stages. Calls moveCommands.stop which then updates the position where stages stoped.
        '''
        thread.start_new_thread(moveCommands.stop, (self.ser, self.zCurrentVar, self.degCurrentVar, self.xCurrentVar, self.yCurrentVar, self.zeroPosition, self))
        self.quit()
        return            
 
        
    def updateCsvInfo(self):
        '''
        updateCsvInfo updates the csv information in the current command labels after loading a csv. If there is not a 
        single command then warning dialog box alerts user. Note the first line in a csv does not count as a command since
        it should be the header.
        '''
        
        try:
            self.setListIndex(1)
            currentPlanList = guiStuff.planListCommand[1][:4]
            currentTubeList = guiStuff.tubeListCommand[1]
            self.position['text'] = "Current list command: " + str(guiStuff.listIndex)
            self.setCurrentCommandText(currentTubeList[0], currentTubeList[1], currentTubeList[2], currentTubeList[3], currentPlanList[0], currentPlanList[1], currentPlanList[2], currentPlanList[3])
            guiStuff.planCurrentCommand = guiStuff.planListCommand[1]
            guiStuff.tubeCurrentCommand = guiStuff.tubeListCommand[1]
        except:
            tkMessageBox.showwarning("List", "List has no commands")
        
    def updateCurrentPlan(self):
        '''talk to david'''
        
        xStage = guiStuff.tubeCurrentCommand[0]
        self.xCurrentPlan.set("%.3f mm" % xStage)
        
        yStage = guiStuff.tubeCurrentCommand[1]
        self.yCurrentPlan.set("%.3f mm" % yStage)
        
        zStage = guiStuff.tubeCurrentCommand[2]
        self.zCurrentPlan.set("%.3f mm" % zStage)
        
        degStage = guiStuff.tubeCurrentCommand[3]
        self.degCurrentPlan.set("%.3f %c" % (degStage, unichr(176)))
        
    def updateCurrentPosition(self):
        '''
        talk to david.
        '''
        xStage = self.xCurrentVar.get()
        holder = xStage.split(' ')
        xStagePos = float(holder[0])
      
        yStage = self.yCurrentVar.get()
        holder = yStage.split(' ')
        yStagePos = float(holder[0])
        
        zStage = self.zCurrentVar.get()
        holder = zStage.split(' ')
        zStagePos = float(holder[0])
        
        degStage = self.degCurrentVar.get()
        holder = degStage.split(' ')
        degStagePos = float(holder[0])
        
        guiStuff.currentPosition = [xStagePos, yStagePos, zStagePos, degStagePos]
        
    def updateCurrentPositionText(self):
        ''' Believe is obsolete'''
        self.xpreviousPositionValue['text'] = str(self.currentPosition[0])
        self.ypreviousPositionValue['text'] = str(self.currentPosition[1])
        self.zpreviousPositionValue['text'] = str(self.currentPosition[2])
        self.rotationpreviousPositionValue['text'] = str(self.currentPosition[3])
        
    def updateDimensionText(self):
        try:
            self.diameter.set("%0.3f mm"%(guiStuff.tubeDimension[0]))
            self.length.set("%0.3f mm"%(guiStuff.tubeDimension[1]))
        except:
            guiStuff.tubeDimension=guiStuff.defaultTubeDimension
            self.diameter.set("%0.3f mm"%(guiStuff.tubeDimension[0]))
            self.length.set("%0.3f mm"%(guiStuff.tubeDimension[1]))
        
    def updateExecutedCommands(self, planCommand, tubeCommand):
        '''
        Work in progress
        '''
        self.executedCommands_planCoordinates.append(planCommand)
        self.exectutedCommands_tubeCoordinates.append(tubeCommand)
        
    def updateProgress(self):
        '''
        Updates the progress bar for a move. Peculiarly, it uses the current position text (bottom left in the main gui) to find the current position of the text. Based 
        on the current actual position, initial position (guiStuff.currentPosition), and the command position (guiStuff.tubeCurrentCommand) it updates the progress bar.
        The usage of string processing of text to find the actual position of the stages is needed since the move commands only update the current position text while
        in a move (the text is represented by self.xCurrentVar.get() and so forth).
        '''
        xStage = self.xCurrentVar.get()
        holder = xStage.split(' ')
        xStagePos = float(holder[0])
        try:
            xPercent = abs(xStagePos - guiStuff.currentPosition[0]) / abs(guiStuff.tubeCurrentCommand[0] - guiStuff.currentPosition[0]) * 100
            self.xVal.set(xPercent)
        except ZeroDivisionError:
            self.xVal.set(100)
        yStage = self.yCurrentVar.get()
        holder = yStage.split(' ')
        yStagePos = float(holder[0])
        try:
            yPercent = abs(yStagePos - guiStuff.currentPosition[1]) / abs(guiStuff.tubeCurrentCommand[1] - guiStuff.currentPosition[1]) * 100
            self.yVal.set(yPercent)
        except ZeroDivisionError:
            self.yVal.set(100)
        zStage = self.zCurrentVar.get()
        holder = zStage.split(' ')
        zStagePos = float(holder[0])
        try:
            zPercent = abs(zStagePos - guiStuff.currentPosition[2]) / abs(guiStuff.tubeCurrentCommand[2] - guiStuff.currentPosition[2]) * 100
            self.zVal.set(zPercent)
        except ZeroDivisionError:
            self.zVal.set(100)
        degStage = self.degCurrentVar.get()
        holder = degStage.split(' ')
        degStagePos = float(holder[0])
        try:
            degPercent = abs(degStagePos - guiStuff.currentPosition[3]) / abs(guiStuff.tubeCurrentCommand[3] - guiStuff.currentPosition[3]) * 100
            self.degVal.set(degPercent)
        except ZeroDivisionError:
            self.degVal.set(100)
        return
    
    def updateZeroPositionText(self):
        
        try:
            self.xZeroText.set("%0.3f mm"%(guiStuff.zeroPosition[0]))
            self.yZeroText.set("%0.3f mm"%(guiStuff.zeroPosition[1]))
            self.zZeroText.set("%0.3f mm"%(guiStuff.zeroPosition[2]))
            self.degZeroText.set("%0.3f %c"%(guiStuff.zeroPosition[3], unichr(176)))
        except:
            guiStuff.zeroPosition=guiStuff.defaultZeroPosition
            self.xZeroText.set("%0.3f mm"%guiStuff.zeroPositon[0])
            self.yZeroText.set("%0.3f mm"%guiStuff.zeroPositon[1])
            self.zZeroText.set("%0.3f mm"%guiStuff.zeroPositon[2])
            self.degZeroText.set("%0.3f %c"%guiStuff.zeroPositon[3], unichr(176))
    
    def writeCsv(self, csvList):
        '''
        Writes the entered parameter list as a csv. A save file dialog allows user to choose what to save the file as.
        
        @param csvList: List containing commands to be written.
        '''
        
        writeFilename = tkFileDialog.asksaveasfilename(initialdir="C:")
        csvHandler = csv.writer(open(writeFilename, "wb"))
        csvHandler.writerows(csvList)
        
    def selectProgressBars(self):
        self.zeroBars()
        self.n.select(self.f5)
        
    def writeList(self): 
        '''
        Writes the contents of the planed commands to a csv file. Users enter where to save the file through a file dialog. Note,
        the plan command (in CT coordinates) is written to the file.
        '''
        
        writeFilename = tkFileDialog.asksaveasfilename(initialdir="C:")
        self.root.lift() #puts the main window at top of gui stack
        csvHandler = csv.writer(open(writeFilename, "wb"))
        csvHandler.writerows(guiStuff.planListCommand)
    
    def zeroBars(self):
        '''
        Sets movement progress bars to zero before a move.
        '''
        
        self.degVal.set(0);
        self.xVal.set(0);
        self.yVal.set(0);
        self.zVal.set(0);
        return
        
class GetFiducialPoints(Dialog):
    '''
    Fiducial dialog to obtain the fiducial points necessary to transform a treatment point in a CT image to the tube coordinates.
    There are four fiducials that need to be entered (9 o\'clock (negative x),6 o\'clock (positive y),3 o\'clock (positive x),and helical fiducial). 
    They correspond to the left, bottom,right,and helical fiducial on the tube when looking at the open end of the tube. 
    The information in the main gui program is automatically updated after pressing ok, if the information is valid.
    '''


    def __init__(self, mainGuiObject, moveFlag, mainGuiWindow, title="move"):
        '''
        Creates and initializes the fiducial dialog where fiducial points are entered by the user.
        '''
        self.CANCELED = True #set cancel flag to true (ie they did not hit the ok button) until move is validated after ok button
        
        Toplevel.__init__(self, mainGuiWindow)
        self.withdraw() # remain invisible for now
        # If the master is not viewable, don't
        # make the child transient, or else it
        # would be opened withdrawn
        if mainGuiWindow.winfo_viewable():
            self.transient(mainGuiWindow)
        if title:
            self.title(title)
        
        self.mainGuiWindow = mainGuiWindow
        
        self.mainGuiObject = mainGuiObject
        self.moveAfterFlag = moveFlag

        self.result = None
        body = Frame(self)
        self.initial_focus = self.body(body)
        body.grid(column=0, row=0, padx=5, pady=5)
        self.buttonbox()
        #self.updateText([1,2,3,4])
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel) #binds hitting X button to the self.cancel method
        if self.mainGuiWindow is not None:
            self.geometry("+%d+%d" % (mainGuiWindow.winfo_rootx() 
             + 50, mainGuiWindow.winfo_rooty() + 50))
        self.deiconify() # become visibile now
        self.initial_focus.focus_set()
        # wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.lift()
        self.wait_window(self)
        


    
    def destroy(self):
        '''Destroy the window'''
        self.initial_focus = None
        Toplevel.destroy(self)
        
    
    def buttonbox(self):
        '''
        Instantiates widgets. Called by constructor.
        '''
        self.title("Move")
        box = Frame(self)
        box.grid(column=0, row=0)
        
        l = ttk.Label(box, text="Enter fiducial points:",font="Serif 12 bold")
        l.grid(column=0, row=0, columnspan=2)
        
        tabGui = ttk.Notebook(box)
        tabGui.grid(column=0, row=1, columnspan=2)
        tabGui['padding'] = (10)
        self.tab1 = ttk.Frame(tabGui); # first page
        self.tab2 = ttk.Frame(tabGui); # second page
        self.tab3 = ttk.Frame(tabGui); # third page
        self.tab4 = ttk.Frame(tabGui)
        self.tab1['padding'] = (10)
        self.tab2['padding'] = (10)
        self.tab3['padding'] = (10)
        self.tab4['padding'] = (10)
        tabGui.add(self.tab1, text='9 o\'clock')
        tabGui.add(self.tab2, text='6 o\'clock')
        tabGui.add(self.tab3, text='3 o\'clock')
        tabGui.add(self.tab4, text='helix')
        
        #Code regarding the 9 o'clock fiducial entry
        fiducial9 = ttk.Labelframe(self.tab1, text="Negative X")
        fiducial9.grid(column=0, row=1)
        #Widgets that deal with x direction
        self.xEntry_fiducial9 = StringVar()
        self.xTextField_fiducial9 = Entry(fiducial9, textvariable=self.xEntry_fiducial9)
        self.xTextField_fiducial9.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.xTextField_fiducial9.grid(column=1, row=1, padx=3, pady=3)
        xLabel_fiducial9 = ttk.Label(fiducial9, text="X: ")
        xLabel_fiducial9.grid(column=0, row=1, padx=3, pady=3)
        #Widgets that deal with y direction
        self.yEntry_fiducial9 = StringVar()
        self.yTextField_fiducial9 = Entry(fiducial9, textvariable=self.yEntry_fiducial9)
        self.yTextField_fiducial9.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.yTextField_fiducial9.grid(column=1, row=2, padx=3, pady=3)
        yLabel_fiducial9 = ttk.Label(fiducial9, text="Y: ")
        yLabel_fiducial9.grid(column=0, row=2, padx=3, pady=3)


 
        #6 o'clock fiducial entry
        fiducial6 = ttk.Labelframe(self.tab2, text="Positive Y")
        fiducial6.grid(column=1, row=1)
        #Widgets that deal with x direction
        self.xEntry_fiducial6 = StringVar()
        self.xTextField_fiducial6 = Entry(fiducial6, textvariable=self.xEntry_fiducial6)
        self.xTextField_fiducial6.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.xTextField_fiducial6.grid(column=1, row=1, padx=3, pady=3)
        xLabel_fiducial6 = ttk.Label(fiducial6, text="X: ")
        xLabel_fiducial6.grid(column=0, row=1, padx=3, pady=3)
        #Widgets that deal with y direction
        self.yEntry_fiducial6 = StringVar()
        self.yTextField_fiducial6 = Entry(fiducial6, textvariable=self.yEntry_fiducial6)
        self.yTextField_fiducial6.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.yTextField_fiducial6.grid(column=1, row=2, padx=3, pady=3)
        yLabel_fiducial6 = ttk.Label(fiducial6, text="Y: ")
        yLabel_fiducial6.grid(column=0, row=2, padx=3, pady=3)

        
        #3 o'clock fiducial entry
        fiducial3 = ttk.Labelframe(self.tab3, text="Positive X")
        fiducial3.grid(column=0, row=2)
        #Widgets that deal with x direction
        self.xEntry_fiducial3 = StringVar()
        self.xTextField_fiducial3 = Entry(fiducial3, textvariable=self.xEntry_fiducial3)
        self.xTextField_fiducial3.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.xTextField_fiducial3.grid(column=1, row=1, padx=3, pady=3)
        xLabel_fiducial3 = ttk.Label(fiducial3, text="X: ")
        xLabel_fiducial3.grid(column=0, row=1, padx=3, pady=3)
        #Widgets that deal with y direction
        self.yEntry_fiducial3 = StringVar()
        self.yTextField_fiducial3 = Entry(fiducial3, textvariable=self.yEntry_fiducial3)
        self.yTextField_fiducial3.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.yTextField_fiducial3.grid(column=1, row=2, padx=3, pady=3)
        yLabel_fiducial3 = ttk.Label(fiducial3, text="Y: ")
        yLabel_fiducial3.grid(column=0, row=2, padx=3, pady=3)

        
        #Helical fiducial entry
        fiducialHelix = ttk.Labelframe(self.tab4, text="helix")
        fiducialHelix.grid(column=1, row=2)
        #Widgets that deal with x direction
        self.xEntry_fiducialHelix = StringVar()
        self.xTextField_fiducialHelix = Entry(fiducialHelix, textvariable=self.xEntry_fiducialHelix)
        self.xTextField_fiducialHelix.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.xTextField_fiducialHelix.grid(column=1, row=1, padx=3, pady=3)
        xLabel_fiducialHelix = ttk.Label(fiducialHelix, text="X: ")
        xLabel_fiducialHelix.grid(column=0, row=1, padx=3, pady=3)
        #Widgets that deal with y direction
        self.yEntry_fiducialHelix = StringVar()
        self.yTextField_fiducialHelix = Entry(fiducialHelix, textvariable=self.yEntry_fiducialHelix)
        self.yTextField_fiducialHelix.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.yTextField_fiducialHelix.grid(column=1, row=2, padx=3, pady=3)
        yLabel_fiducialHelix = ttk.Label(fiducialHelix, text="Y: ")
        yLabel_fiducialHelix.grid(column=0, row=2, padx=3, pady=3)


        self.tubeImg=PhotoImage(file="tube_combined.gif")
        self.imageLabel=ttk.Label(box,image=self.tubeImg)
        self.imageLabel.grid(row=2,column=0,columnspan=2)

        
        w = ttk.Button(box, text="OK", width=10,
         command=self.ok, default=ACTIVE)
        w.grid(column=0, row=3, padx=5, pady=5, sticky=(E))
        w = ttk.Button(box, text="cancel", width=10,
         command=self.cancel)
        w.grid(column=1, row=3, padx=5, pady=5, sticky=(W))
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        

    

    def ok(self, event=None):
        '''
        Checks if entered fiducial information is valid. If so it closes the dialog and updates command information. 
        Otherwise it allows user to re-enter fiducials.
        '''
        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        try:
            self.apply()  #note self.apply does nothing but as kept as convention (ie inherited method from Dialog)
        finally:
            self.cancel()
    
    def cancel(self, event=None):
        '''
        Called to destroy the dialog. Also puts the main gui window into focus.
        '''
        
        # put focus back to the parent window
        if self.mainGuiWindow is not None:
            self.mainGuiWindow.focus_set()

        self.destroy()
    

    def validate(self):
        '''validate the data

        This method is called automatically to validate the 
         data before the
        dialog is destroyed. By default, it always validates 
         OK.
        '''
        if(self.isValid() == True):
            
            tubeValid=False #flag for valid tube command
            
            if(self.moveAfterFlag == True):
                guiStuff.setPlanCurrentCommand(self.mainGuiObject, guiStuff.planCurrentCommand[:3] + [float(self.xEntry_fiducial9.get()), float(self.yEntry_fiducial9.get()), float(self.xEntry_fiducial6.get()), float(self.yEntry_fiducial6.get()), float(self.xEntry_fiducial3.get()), float(self.yEntry_fiducial3.get()), float(self.xEntry_fiducialHelix.get()), float(self.yEntry_fiducialHelix.get())])
                tubeValid=guiStuff.setTubeCurrentCommand(self.mainGuiObject, 20, guiStuff.affineTransform(self.mainGuiObject, guiStuff.planCurrentCommand))
                if(tubeValid==False):
                    tkMessageBox.showwarning("Invalid", "The movement command is out of bounds")
                    return 0
            elif(self.moveAfterFlag == False):
                
                guiStuff.setPlanCurrentCommand(self.mainGuiObject, guiStuff.planCurrentCommand[:3] + [float(self.xEntry_fiducial9.get()), float(self.yEntry_fiducial9.get()), float(self.xEntry_fiducial6.get()), float(self.yEntry_fiducial6.get()), float(self.xEntry_fiducial3.get()), float(self.yEntry_fiducial3.get()), float(self.xEntry_fiducialHelix.get()), float(self.yEntry_fiducialHelix.get())])
                newTubeCommand = guiStuff.affineTransform(self.mainGuiObject, guiStuff.planCurrentCommand)
                tubeValid=guiStuff.setTubeCurrentCommand(self.mainGuiObject, 20, newTubeCommand)
                if(tubeValid==False):
                    tkMessageBox.showwarning("Invalid", "The movement command is out of bounds")
                    return 0
                    
            self.CANCELED = False
            return 1 # override
        else:
            tkMessageBox.showwarning("Invalid position", "The specified position is invalid")
            return 0
    
         
    
    def isValid(self):
        '''
        Checks if fiducial points are actually numbers instead of a string. Returns True if all fiducial entries are numbers.
        Returns False if they are not.
        
        @return: True or false for all fiducial points having only numbers (not a string,etc.)
        '''
        try:
            float(self.xEntry_fiducial9.get())
            float(self.yEntry_fiducial9.get())
            float(self.xEntry_fiducial6.get())
            float(self.yEntry_fiducial6.get())
            float(self.xEntry_fiducial3.get())
            float(self.yEntry_fiducial3.get())
            float(self.xEntry_fiducialHelix.get())
            float(self.yEntry_fiducialHelix.get())
            return True
        except:
            return False
    

class CreateCsv(Dialog):
    '''
    CreateCsv is a Dialog (inherits from Dialog) that edits and creates list commands. The list can be saved to a csv file.
    
    '''

    def __init__(self, MainObject, mainObjectWindow, title="Edit"):
        '''
        Initialize edit list dialog
        '''

        
        Toplevel.__init__(self, mainObjectWindow)
        self.withdraw() # remain invisible for now
        # If the master is not viewable, don't
        # make the child transient, or else it
        # would be opened withdrawn
        if mainObjectWindow.winfo_viewable():
            self.transient(mainObjectWindow)
        if title:
            self.title(title)
        
        self.mainGuiWindow = mainObjectWindow

        self.result = None

        #self.updateText([1,2,3,4])
        #if not self.createCsvWindow.initial_focus:
            #self.createCsvWindow.initial_focus = self

        if self.mainGuiWindow is not None:
            self.geometry("+%d+%d" % (self.mainGuiWindow.winfo_rootx() 
             + 50, self.mainGuiWindow.winfo_rooty() + 50))


        self.createCsvWindow = self#self.createCsvWindow=Tk()
        self.createCsvWindow.title("Edit")
        self.createCsvWindow.iconbitmap(default='iowa_logo.ico')
        self.createCsvWindow.option_add('*tearOff', FALSE)
        self.createCsvWindow.protocol('WM_DELETE_WINDOW', self.quit)
        self.createCsvFrame = ttk.Frame(self.createCsvWindow)
        self.createCsvFrame.grid(column=0, row=0, padx=10, pady=10)
        

        self.main_object = MainObject
        self.planList = self.main_object.planListCommand#csv file contained in a list
        #self.main_object.listIndex=1 #position sequence number
        self.main_object.setListIndex(1)
        

        menubar = Menu(self.createCsvWindow)
        self.createCsvWindow['menu'] = menubar
        menu_file = Menu(menubar)
        menubar.add_cascade(menu=menu_file, label='File')
        menu_file.add_command(label='Write CSV', command=self.writeListCsv)
        menu_file.add_command(label='Quit', command=self.quit)
        
        self.entryFrame = ttk.Labelframe(self.createCsvFrame, text="Position")
        self.entryFrame.grid(column=0, row=0)
        
        #Widgets that deal with x direction movement        
        self.xEnter = StringVar()
        self.xEnterField = Entry(self.entryFrame, textvariable=self.xEnter)
        self.xEnterField.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.xEnterField.grid(column=1, row=0, padx=3, pady=3)
        self.xLab = ttk.Label(self.entryFrame, text="X coordinate: ")
        self.xLab.grid(column=0, row=0, padx=3, pady=3)
        
        #Widgets that deal with y direction movement
        self.yEnter = StringVar()
        self.yEnterField = Entry(self.entryFrame, textvariable=self.yEnter)
        self.yEnterField.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.yEnterField.grid(column=1, row=1, padx=3, pady=3)
        self.yLab = ttk.Label(self.entryFrame, text="Y coordinate: ")
        self.yLab.grid(column=0, row=1, padx=1, pady=3)
        
        #Widgets that deal with degree movement        
        self.degreeEnter = StringVar()
        self.degreeEnterField = Entry(self.entryFrame, textvariable=self.degreeEnter)
        self.degreeEnterField.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.degreeEnterField.grid(column=1, row=2, padx=3, pady=3)
        self.degreeLab = ttk.Label(self.entryFrame, text="Rotation: ")
        self.degreeLab.grid(column=0, row=2, padx=2, pady=3)
        
        self.buttonFrame = ttk.Frame(self.createCsvFrame)
        self.buttonFrame.grid(column=0, row=1)
        self.enterButton = ttk.Button(self.buttonFrame, text="Enter", command=self.updateCsv)
        self.enterButton.grid(column=1, row=0, pady=3, padx=3)
        self.forward = ttk.Button(self.buttonFrame, text="Next >", command=self.positionNumberForward)
        self.forward.grid(column=2, row=0, sticky=(W), padx=3)
        self.back = ttk.Button(self.buttonFrame, text="< Previous", command=self.positionNumberBack)
        self.back.grid(column=0, row=0, sticky=(E), padx=3)
        
        self.labelFrame = ttk.Labelframe(self.createCsvFrame, text="Position: 1")
        self.labelFrame.grid(column=1, row=0, padx=10, sticky=("N", "S"))
        self.xValueStored = ttk.Label(self.labelFrame, text="X: ")
        self.xValueStored.grid(column=0, row=0, pady=5)
        self.yValueStored = ttk.Label(self.labelFrame, text="Y: ")
        self.yValueStored.grid(column=0, row=1, pady=5)
        self.degreeValueStored = ttk.Label(self.labelFrame, text="Roll: ")
        self.degreeValueStored.grid(column=0, row=2, pady=5)
        
        self.main_object.setListIndex(1)  
        
        try:  
            if(self.main_object.planListCommand[0] != ['x', 'y', 'degree', '9 o\'clock x', '9 o\'clock y', '6 o\'clock x', '6 o\'clock y', '3 o\'clock x', '3 o\'clock y', 'helix x', 'helix y']):
                self.main_object.setListIndex(0) #want to set header at begining of plan list
                self.main_object.setPlanListCommand([['x', 'y', 'degree', '9 o\'clock x', '9 o\'clock y', '6 o\'clock x', '6 o\'clock y', '3 o\'clock x', '3 o\'clock y', 'helix x', 'helix y']])
                self.main_object.setListIndex(1)
            if(self.main_object.planListCommand[1] != 'y'):
                firstPosition = self.main_object.planListCommand[1]
                self.xValueStored['text'] = "X: " + ("%0.3f" % firstPosition[0])
                self.yValueStored['text'] = "Y: " + ("%0.3f" % firstPosition[1])
                self.zValueStored['text'] = "Z: " + ("%0.3f" % firstPosition[2])
                self.degreeValueStored['text'] = "Roll: " + ("%0.3f" % firstPosition[3])
        except:
            pass
        
        self.deiconify() # become visibile now
        self.createCsvFrame.focus_set()
        # wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.lift()
        self.wait_window(self)
        
        
    def quit(self):
        '''
        Called to close the list edit dialog (CreateCsv gui). Called by either the X button or File->quit in the gui. Updates
        the list information in the main gui then destroys the dialog.
        '''
        
        self.main_object.updateCsvInfo()
        self.main_object.root.lift()
        self.createCsvWindow.destroy()
    
    def positionNumberForward(self):
        '''
        Moves to the next item in the list only if it is within bounds. Handles the button press of the "next" button on the gui.
        Besides updating the list index of the main gui (self.main_object.listIndex), it updates the text to the command, if present, for that
        position in the list.Call back function for the button self.forward.
        '''

        if(self.main_object.listIndex + 1 <= len(self.main_object.planListCommand)):
            self.main_object.listIndex += 1
            self.labelFrame['text'] = "Position: " + str(self.main_object.listIndex)
            try:
                currentPositionList = self.main_object.planListCommand[self.main_object.listIndex]
                self.xValueStored['text'] = "X: " + ("%0.3f" % currentPositionList[0])
                self.yValueStored['text'] = "Y: " + ("%0.3f" % currentPositionList[1])
                self.zValueStored['text'] = "Z: " + ("%0.3f" % currentPositionList[2])
                self.degreeValueStored['text'] = "Roll: " + ("%0.3f" % currentPositionList[3])
            except:
                self.xValueStored['text'] = 'X: '
                self.yValueStored['text'] = 'Y: '
                self.zValueStored['text'] = 'Z: '
                self.degreeValueStored['text'] = 'Roll: '
        
    def positionNumberBack(self):
        '''
        Moves to the previous item in the list only if it is within bounds. Handles the button press of the "previous" button on the gui.
        Besides updating the list index of the main gui (self.main_object.listIndex), it updates the text to the command, if present, for that
        position in the list. Call back function for the button self.back.
        '''

        if(self.main_object.listIndex - 1 > 0):
            self.main_object.listIndex -= 1
            self.labelFrame['text'] = "Position: " + str(self.main_object.listIndex)
            try:
                currentPositionList = self.main_object.planListCommand[self.main_object.listIndex]
                self.xValueStored['text'] = "X: " + ("%0.3f" % currentPositionList[0])
                self.yValueStored['text'] = "Y: " + ("%0.3f" % currentPositionList[1])
                self.zValueStored['text'] = "Z: " + ("%0.3f" % currentPositionList[2])
                self.degreeValueStored['text'] = "Roll: " + ("%0.3f" % currentPositionList[3])
            except:
                self.xEnterField['text'] = 'X: '
                self.yEnterField['text'] = 'Y: '
                self.zEnterField['text'] = 'Z: '
                self.degreeEnterField['text'] = 'Roll: '
            
    def writeListCsv(self):
        '''
        Writes the contents of the planed commands to a csv file. Users enter where to save the file through a file dialog. Note,
        the plan command (in CT coordinates) is written to the file.
        '''
        
        self.main_object.writeList()
        self.createCsvWindow.lift()
    
    def updateCsv(self):
        
        if(self.isValidRow() == True):
            temp = [float(self.xEnterField.get()), float(self.yEnterField.get()), float(self.degreeEnterField.get())]
            temp = (temp + [float(0), float(0), float(0), float(0), float(0), float(0), float(0), float(0)])
            self.main_object.setPlanCurrentCommand(temp)
            self.disable()
            self.GetFiducialPoints = guiStuff.GetFiducialPoints(self.main_object, False, self.main_object.root)
            self.enable()
            self.main_object.root.lift()
            self.createCsvWindow.lift()
            if(self.GetFiducialPoints.CANCELED == False):
                if(self.main_object.planListCommand == [['x', 'y', 'degree', '9 o\'clock x', '9 o\'clock y', '6 o\'clock x', '6 o\'clock y', '3 o\'clock x', '3 o\'clock y', 'helix x', 'helix y']] or self.main_object.listIndex == len(self.main_object.planListCommand)):
                    self.main_object.planListCommand.append(self.main_object.planCurrentCommand)
                    self.main_object.tubeListCommand.append(self.main_object.tubeCurrentCommand)
                    currentPositionList = self.main_object.planListCommand[self.main_object.listIndex]
                    self.xValueStored['text'] = "X: " + str(currentPositionList[0])
                    self.yValueStored['text'] = "Y: " + str(currentPositionList[1])
                    self.degreeValueStored['text'] = "Roll: " + str(currentPositionList[2])
                else:
                    #self.main_object.planListCommand[:self.main_object.listIndex-1]+temp+self.main_object.planListCommand[self.main_object.listIndex+1:]
                    self.main_object.planListCommand.insert(self.main_object.listIndex, self.main_object.planCurrentCommand)
                    self.main_object.planListCommand.pop(self.main_object.listIndex + 1)
                    self.main_object.tubeListCommand.insert(self.main_object.listIndex, self.main_object.tubeCurrentCommand)
                    self.main_object.tubeListCommand.pop(self.main_object.listIndex + 1)
    
                    currentPositionList = self.main_object.planListCommand[self.main_object.listIndex]
                    self.xValueStored['text'] = "X: " + str(currentPositionList[0])
                    self.yValueStored['text'] = "Y: " + str(currentPositionList[1])
                    self.degreeValueStored['text'] = "Roll: " + str(currentPositionList[2])
        else:
            tkMessageBox.showwarning("Move command", "Invalid entry")
            
    
    def isValidRow(self):
        

        #command_index = 0
        try:

            float(self.xEnter.get())
            float(self.yEnter.get())
            float(self.degreeEnter.get())
            return True
        except:
            return False

    def enable(self):
        '''
        Called when enter button is pressed (in self.updateCsv) to re-enable buttons after user enters fiducials.
        '''
        
        self.forward['state'] = NORMAL
        self.back['state'] = NORMAL
        self.enterButton['state'] = NORMAL
        
        
    def disable(self):
        '''
        Called when enter button is pressed (in self.updateCsv) to disable buttons when the user enters fiducials. 
        '''
        
        self.forward['state'] = DISABLED
        self.back['state'] = DISABLED
        self.enterButton['state'] = DISABLED
            

class SetZeroPoint(Dialog):
    
    def __init__(self,mainGuiObject, parent, title = None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.main_object=mainGuiObject
        self.parent = parent

        self.result = None

        self.myFrame = Frame(self)
        self.myFrame.grid(row=0,column=0,padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))


        self.wait_window(self)
        
    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = ttk.Frame(self.myFrame)
        
        ttk.Label(box,text="Enter zero point:",font="Serif 10 bold").grid(row=0,column=0,columnspan=3)
        ttk.Label(box,text="X Offset: ").grid(row=1,column=0,pady=3,padx=3,sticky=(E))
        ttk.Label(box,text="Y Offset: ").grid(row=2,column=0,pady=3,padx=3,sticky=(E))
        ttk.Label(box,text="Z Offset: ").grid(row=3,column=0,pady=3,padx=3,sticky=(E))
        ttk.Label(box,text="Roll:").grid(row=4,column=0,pady=3,padx=3,sticky=(E))
        ttk.Label(box,text="mm").grid(row=1,column=2,pady=3,sticky=(W))
        ttk.Label(box,text="mm").grid(row=2,column=2,pady=3,sticky=(W))
        ttk.Label(box,text="mm").grid(row=3,column=2,pady=3,sticky=(W))
        ttk.Label(box,text="degrees").grid(row=4,column=2,pady=3,sticky=(W))
        
        self.xZero=StringVar()
        self.yZero=StringVar()
        self.zZero=StringVar()
        self.degreeZero=StringVar()
        self.xZero.set("%0.3f"%guiStuff.zeroPosition[0])
        self.yZero.set("%0.3f"%guiStuff.zeroPosition[1])
        self.zZero.set("%0.3f"%guiStuff.zeroPosition[2])
        self.degreeZero.set("%0.3f"%guiStuff.zeroPosition[3])
        x = Entry(box,textvariable=self.xZero)
        x.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        x.grid(row=1,column=1,pady=3)
        y = Entry(box,textvariable=self.yZero)
        y.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        y.grid(row=2,column=1,pady=3)
        z = Entry(box,textvariable=self.zZero)
        z.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        z.grid(row=3,column=1,pady=3)
        degree = Entry(box,textvariable=self.degreeZero)
        degree.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        degree.grid(row=4,column=1,pady=3)               
        
        buttonFrame=ttk.Frame(box)
        buttonFrame.grid(row=5,column=0,columnspan=3)
        w = ttk.Button(buttonFrame, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.grid(row=0,column=0,padx=5, pady=5,sticky=(W))
        w = ttk.Button(buttonFrame, text="Cancel", width=10, command=self.cancel)
        w.grid(row=0,column=1,padx=5, pady=5)
        w = ttk.Button(buttonFrame, text="Default", width=10, command=self.default)
        w.grid(row=0,column=3,padx=5, pady=5,sticky=(E))

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()
        
    def ok(self, event=None):

        if not self.validate():
            self.parent.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()
    
    def validate(self):

        if(self.isValid()==True):
            try:
                with open(os.getcwd()+'\\ZeroPosition.cfg','r+') as writeHandle: #if you are wondering what the with command is, it automatically closes a file when the code exits the with section
                    config = ConfigParser.RawConfigParser()
                    config.set('Zero Position','x','%0.3f'%float(self.xZero.get()))
                    config.set('Zero Position','y','%0.3f'%float(self.yZero.get()))
                    config.set('Zero Position','z','%0.3f'%float(self.zZero.get()))
                    config.set('Zero Position','degree','%0.3f'%float(self.degreeZero.get()))
                    config.write(writeHandle)
                    guiStuff.zeroPosition=[float(self.xZero.get()),float(self.yZero.get()),float(self.zZero.get()),float(self.degreeZero.get())]
                    self.main_object.zeroed=False
                return True
            except ConfigParser.NoSectionError:
                with open(os.getcwd()+'\\ZeroPosition.cfg','r+') as writeHandle:
                    config = ConfigParser.RawConfigParser()
                    config.add_section('Zero Position')
                    config.set('Zero Position','x','%0.3f'%float(self.xZero.get()))
                    config.set('Zero Position','y','%0.3f'%float(self.yZero.get()))
                    config.set('Zero Position','z','%0.3f'%float(self.zZero.get()))
                    config.set('Zero Position','degree','%0.3f'%float(self.degreeZero.get()))
                    config.write(writeHandle)
                    guiStuff.zeroPosition=[float(self.xZero.get()),float(self.yZero.get()),float(self.zZero.get()),float(self.degreeZero.get())]
                    self.main_object.zeroed=False
                return True
            except:
                tkMessageBox.showwarning("Zero position", "The zero position was unable to be changed (Likely because of xtrap.cfg).")
                return False
        else:
            tkMessageBox.showwarning("Zero position", "The zero position is out of bounds. "+str([float(self.xZero.get()),float(self.yZero.get()),float(self.zZero.get()),float(self.degreeZero.get())]))


    def isValid(self):
        
        try:
            if(float(self.xZero.get())<float(0) or float(self.xZero.get())>float(50)):
                return False
            if(float(self.yZero.get())<float(0) or float(self.xZero.get())>float(50)):
                return False
            if(float(self.zZero.get())<float(0) or float(self.zZero.get())>float(150)):
                return False
            if(float(self.degreeZero.get())<float(0) or float(self.degreeZero.get())>float(720)):
                return False
        except:
            return False
        
        return True
    
    def cancel(self):
        '''
        Cancel Option
        '''

        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()
        
    def apply(self):
        '''
        Updates the Zero Position Text (is called by OK)
        '''
        self.main_object.updateZeroPositionText()
        
    def default(self):
        '''
        Sets the text boxes to the default value that we have assigned.
        '''
        
        self.xZero.set("%0.3f"%guiStuff.defaultZeroPosition[0])
        self.yZero.set("%0.3f"%guiStuff.defaultZeroPosition[1])
        self.zZero.set("%0.3f"%guiStuff.defaultZeroPosition[2])
        self.degreeZero.set("%0.3f"%guiStuff.defaultZeroPosition[3])


class SetTubeDimension(Dialog):
    
    def __init__(self,mainGuiObject, parent, title = None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.main_object=mainGuiObject
        self.parent = parent

        self.result = None

        self.myFrame = Frame(self)
        self.myFrame.grid(row=0,column=0,padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))


        self.wait_window(self)
        
    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = ttk.Frame(self.myFrame)
        
        ttk.Label(box,text="Enter Tube Dimensions:",font="Serif 10 bold").grid(row=0,column=0,columnspan=3)
        ttk.Label(box,text="Diameter: ").grid(row=1,column=0,pady=3,padx=3,sticky=(E))
        ttk.Label(box,text="Length: ").grid(row=2,column=0,pady=3,padx=3,sticky=(E))
        ttk.Label(box,text="mm").grid(row=1,column=2,pady=3,sticky=(W))
        ttk.Label(box,text="mm").grid(row=2,column=2,pady=3,sticky=(W))

        
        self.diameterVariable=StringVar()
        self.lengthVariable=StringVar()
        self.diameterVariable.set("%0.3f"%guiStuff.tubeDimension[0])
        self.lengthVariable.set("%0.3f"%guiStuff.tubeDimension[1])
        dia = Entry(box,textvariable=self.diameterVariable)
        dia.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        dia.grid(row=1,column=1,pady=3)
        len = Entry(box,textvariable=self.lengthVariable)
        len.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        len.grid(row=2,column=1,pady=3)             
        
        buttonFrame=ttk.Frame(box)
        buttonFrame.grid(row=3,column=0,columnspan=3)
        w = ttk.Button(buttonFrame, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.grid(row=0,column=0,padx=5, pady=5,sticky=(W))
        w = ttk.Button(buttonFrame, text="Cancel", width=10, command=self.cancel)
        w.grid(row=0,column=1,padx=5, pady=5)
        w = ttk.Button(buttonFrame, text="Default", width=10, command=self.default)
        w.grid(row=0,column=3,padx=5, pady=5,sticky=(E))

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()
        
    def ok(self, event=None):

        if not self.validate():
            self.parent.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()
    
    def validate(self):

        if(self.isValid()==True):
            try:
                with open(os.getcwd()+'\\Dimension.cfg','r') as writeHandle: #if you are wondering what the with command is, it automatically closes a file when the code exits the with section
                    config = ConfigParser.ConfigParser()
                    config.set('Tube Dimension','diameterVariabl','%0.3f'%float(self.diameterVariable.get()))
                    config.set('Tube Dimension','Length','%0.3f'%float(self.lengthVariable.get()))
                    config.write(writeHandle)
                    guiStuff.tubeDimension=[float(self.diameterVariable.get()),float(self.lengthVariable.get())]
                return True
            except ConfigParser.NoSectionError:
                with open(os.getcwd()+'\\Dimension.cfg','r+') as writeHandle:
                    configs = ConfigParser.RawConfigParser()
                    configs.add_section('Tube Dimension')
                    configs.set('Tube Dimension','Diameter','%0.3f'%float(self.diameterVariable.get()))
                    configs.set('Tube Dimension','Length','%0.3f'%float(self.lengthVariable.get()))
                    configs.write(writeHandle)
                    guiStuff.tubeDimension=[float(self.diameterVariable.get()),float(self.lengthVariable.get())]
                return True
            except:
                tkMessageBox.showwarning("Tube Dimension", "The tube dimension was unable to be changed (Likely because of xtrap.cfg).")
                return False
        else:
            tkMessageBox.showwarning("Tube Dimension", "Invalid. The entered values were either not a number or to small to be viable. "+str([float(self.diameterVariable.get()),float(self.lengthVariable.get())]))


    def isValid(self):
        
        try:
            if(float(self.diameterVariable.get())<float(10)):
                return False
            if(float(self.lengthVariable.get())<float(10)):
                return False
        except:
            return False
        
        return True
    
    def cancel(self):
        '''
        Cancel Option
        '''

        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()
        
    def apply(self):
        '''
        Updates the Zero Position Text (is called by OK)
        '''
        self.main_object.updateDimensionText()
        
    def default(self):
        '''
        Sets the text boxes to the default value that we have assigned.
        '''
        
        self.diameterVariable.set("%0.3f"%guiStuff.defaultTubeDimension[0])
        self.lengthVariable.set("%0.3f"%guiStuff.defaultTubeDimension[1])


#The following lines declare the preceeding classes as nested classes of guiStuff
guiStuff.SetZeroPoint=SetZeroPoint
guiStuff.GetFiducialPoints = GetFiducialPoints
guiStuff.CreateCsv = CreateCsv
guiStuff.SetTubeDimension=SetTubeDimension

if __name__ == '__main__':
    debug = False
    try:
        if sys.argv[1] == '--debug' or sys.argv[1] == '-d':
            guiStuff(debug = True)
        else:
            guiStuff()
    except IndexError:
        guiStuff()
