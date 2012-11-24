'''
The HeightSelector module only contains the HeighSelector class. It is intended to create a dialog that gives suggestions to the user
for collimation. I would highly suggest going to the tkdocs website (google it) for tutorials on widgets in ttk/tkinter.

@author: Collin
'''
from Tkinter import *
import ttk
from tkSimpleDialog import Dialog
import tkMessageBox

class HeightSelector(Dialog):
    '''
    HeightSelector is a Dialog that provides suggestions to user for the height of the collimtor and dimension of the aperature
    based on the dimensions of treatment size on the target.

    '''


    #constant defines for shape selection
    CIRCLE="CIRCLE"
    SQUARE="SQUARE"
    RECTANGLE="RECTANGLE"

    def __init__(self,mainGuiWindow,title="move"):
        '''
        Constructor
        '''

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

        self.result = None
        body = Frame(self)
        self.initial_focus = self.body(body)
        body.grid(column=0,row=0,padx=5, pady=5)
        self.buttonbox()
        #self.updateText([1,2,3,4])
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        if self.mainGuiWindow is not None:
            self.geometry("+%d+%d" % (mainGuiWindow.winfo_rootx() 
             + 50, mainGuiWindow.winfo_rooty() + 50))
        #self.updateText([32.1,12.7,5,13.4])
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
        
        
    def body(self, master):
        '''create dialog body.

        return widget that should have initial focus.
        This method should be overridden, and is called
        by the __init__ method.
        '''
        pass
    
    def buttonbox(self):
        '''
        Initializes most of the GUI components. Called by the constructor.
        '''
        self.title("Collimator")
        self.box = Frame(self)
        self.box.grid(column=0,row=0)
        self.plateHeight = 0.0
        self.collimatorBlank = 0.0
        self.collimatorBlankShape = "Circle"
        
        shapeSelectFrame=ttk.Labelframe(self.box,text="Select apperature shape")
        shapeSelectFrame.grid(row=0,column=0,padx=5,pady=5,columnspan=3)
        self.shape = StringVar()
        self.shape.set(HeightSelector.CIRCLE)
        circle = ttk.Radiobutton(shapeSelectFrame, text='Circle', variable=self.shape, value=HeightSelector.CIRCLE,command=self.selection)
        square = ttk.Radiobutton(shapeSelectFrame, text='Square', variable=self.shape, value=HeightSelector.SQUARE,command=self.selection)
        rectangle = ttk.Radiobutton(shapeSelectFrame, text='Rectangle', variable=self.shape, value=HeightSelector.RECTANGLE,command=self.selection)
        circle.grid(row=0,column=0)
        square.grid(row=0,column=1)
        rectangle.grid(row=0,column=2)
        
        self.dimensionLabel=ttk.Label(self.box,text="Diameter: ")
        self.dimensionLabel.grid(row=1,column=0)
        self.dimensionVariable=StringVar()
        self.dimensionEntry=Entry(self.box,textvariable=self.dimensionVariable)
        self.dimensionEntry.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        self.dimensionEntry.grid(column=1,row=1)
        dimensionUnits=ttk.Label(self.box,text="mm")
        dimensionUnits.grid(row=1,column=2)
        
        self.circleImg=PhotoImage(file="circle.gif")
        self.rectangleImg=PhotoImage(file="rectangle.gif")
        self.squareImg=PhotoImage(file="square.gif")
        self.imageLabel=ttk.Label(self.box,image=self.circleImg)
        self.imageLabel.grid(row=2,column=0,columnspan=3,pady=5)

        buttonFrame=ttk.Frame(self.box)
        buttonFrame.grid(column=0,row=3,columnspan=3)
        
        w = ttk.Button(buttonFrame, text="OK", width=10, 
         command=self.ok, default=ACTIVE)
        w.grid(column=0,row=0, padx=5, pady=5,sticky=(E))
        w = ttk.Button(buttonFrame, text="cancel", width=10, 
         command=self.cancel)
        w.grid(column=1,row=0, padx=5, pady=5,sticky=(W))
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        self.height = 564.5
        self.bottomLimit = 423.0
        self.topLimit = 203.7
        self.topRatio = self.height/self.topLimit
        self.bottomRatio = self.height/self.bottomLimit 
        self.squareSizes = [24.0,14.0,9.0,5.0,3.0]  #size of the square blanks in descending size
        self.circleSizes = [8.0,4.0,2.0,1.6,1.0,0.5]  #size of the circle blanks in descending size
        self.rectangleSizes = [6.0,3.0] #side of the rectangle blanks in descending size
        self.message = ""
        

    def ok(self, event=None):
        '''
        Proceeds to give suggestion for collimation if validation is ok. Call back function for the "ok" button on the GUI.
        '''
        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return
        self.calculateHeight()
        self.withdraw()
        self.update_idletasks()
        try:
            self.apply()
        finally:
            self.cancel()
    
    def cancel(self, event=None):
        '''
        Called to destroy the dialog and set focus back to the main GUI. Can be called as a call back function for the "cancel" button or
        at the last step after pressing the "ok" button.
        '''
        # put focus back to the parent window
        if self.mainGuiWindow is not None:
            self.mainGuiWindow.focus_set()

        self.destroy()
    

    def validate(self):
        '''
        Validates that the user entered a number.
        This method is called automatically to validate the data before the dialog is destroyed. 
        '''
        try:
            float(self.dimensionVariable.get())
            return 1
        except:
            return 0
    
    def apply(self):
        '''
        Displays an information dialog to the user giving them the suggested parameters for collimation.
        '''
        tkMessageBox.showinfo("Suggestion", "%s" % self.message) 
    
    def selection(self):
        '''
        Handles the users selection for aperature shape. Call back function for the three radiobuttons (circle, square, and rectangle).
        '''
        if(self.shape.get()==HeightSelector.CIRCLE):
            self.dimensionLabel['text']="Diameter: "
            self.imageLabel['image']=self.circleImg
        if(self.shape.get()==HeightSelector.SQUARE):
            self.dimensionLabel['text']="Length: "
            self.imageLabel['image']=self.squareImg
        if(self.shape.get()==HeightSelector.RECTANGLE):
            self.dimensionLabel['text']="Height: "
            self.imageLabel['image']=self.rectangleImg
    
    def calculateHeight(self):
        '''
        Based on the users entered shape and size, calculateHeight figures out the suggested settings for collimation. Stores
        the suggestion in self.message.
        '''
        
        desiredSize = float(self.dimensionVariable.get())
        
        if(self.shape.get()==HeightSelector.CIRCLE):
            '''calculate the height using the circle array'''
            self.collimatorBlankShape="diameter circle"
            if desiredSize/self.circleSizes[0] > self.topRatio:
                self.plateHeight = 0.00
                self.collimatorBlank = 0.00
            else:
                i = 0
                ratio = desiredSize/self.circleSizes[i]
                while (ratio < self.bottomRatio or ratio > self.topRatio) and i < len(self.circleSizes)-1:
                    i = i + 1
                    ratio = desiredSize/self.circleSizes[i]
                if i >= len(self.circleSizes)-1 and ratio < self.bottomRatio:
                    self.collimatorBlank = 1.0
                    self.plateHeight = 1.0
                else:
                    self.collimatorBlank = self.circleSizes[i]
                    self.plateHeight = (self.bottomRatio/ratio)*self.bottomLimit
                                                                      
        if(self.shape.get()==HeightSelector.SQUARE):
            
            '''calculate the height using the square array'''
            self.collimatorBlankShape="length square"
            if desiredSize/self.squareSizes[0] > self.topRatio:
                self.plateHeight = 0.00
                self.collimatorBlank = 0.00
            else:
                i = 0
                ratio = desiredSize/self.squareSizes[i]
                while (ratio < self.bottomRatio or ratio > self.topRatio) and i < len(self.squareSizes)-1:
                    i = i + 1
                    ratio = desiredSize/self.squareSizes[i]
                if i >= len(self.squareSizes)-1 and ratio < self.bottomRatio:
                    self.collimatorBlank = 1.0
                    self.plateHeight = 1.0
                else:
                    self.collimatorBlank = self.squareSizes[i]
                    self.plateHeight = (self.bottomRatio/ratio)*self.bottomLimit
                
        
        if(self.shape.get()==HeightSelector.RECTANGLE):
            
            '''calculate the height using the rectangle array'''
            self.collimatorBlankShape="height rectangle"
            if desiredSize/self.rectangleSizes[0] > self.topRatio:
                self.plateHeight = 0.00
                self.collimatorBlank = 0.00
            else:
                i = 0
                ratio = desiredSize/self.rectangleSizes[i]
                while (ratio < self.bottomRatio or ratio > self.topRatio) and i < len(self.rectangleSizes)-1:
                    i = i + 1
                    ratio = desiredSize/self.rectangleSizes[i]
                if i >= len(self.rectangleSizes)-1 and ratio < self.bottomRatio:
                    self.collimatorBlank = 1.0
                    self.plateHeight = 1.0
                else:
                    self.collimatorBlank = self.rectangleSizes[i]
                    self.plateHeight = (self.bottomRatio/ratio)*self.bottomLimit
                
        if self.plateHeight == 1.00:
            self.message = "The requested hole size is too small for the current collimator blanks."
        elif self.plateHeight == 0.00:
            self.message = "The requested hole size is too large for the current collimator blanks."
        else:
            self.message = "Collimator Distance: %.2f cm\nCollimator Blank: %.2f mm %s." % ( self.plateHeight/10.0, self.collimatorBlank, self.collimatorBlankShape)
            


        