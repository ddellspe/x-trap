'''
The dicomViewer file allows the user to load a dicom file, display the dicom file and get the pixel points of all of the points of interest
for the slice that the dicom file represents.  

@author: David Dellsperger
'''
from Tkinter import *
import ttk
import tempfile
import os
from tkSimpleDialog import Dialog
import tkFileDialog
import tkMessageBox
import ImageTk, Image, ImageEnhance

have_numpy=True
try:
    import numpy as np
except:
    have_numpy = False

import dicom

class dicomViewer(Dialog):
    '''
    HeightSelector is a Dialog that provides suggestions to user for the height of the collimtor and dimension of the aperature
    based on the dimensions of treatment size on the target.

    '''

    def __init__(self,mainGuiWindow,mainGui,title="Select Affine Points to Move to"):
        '''
        Constructor
        '''
        self.coordinates = [0,0,0,0,0,0,0,0,0,0,0]
        self.targetPoint = 0
        self.targetText = 0
        self.ninePoint = 0
        self.nineText = 0
        self.sixPoint = 0
        self.sixText = 0
        self.threePoint = 0
        self.threeText = 0
        self.helixPoint = 0
        self.helixText = 0
        self.mirror = IntVar()
        self.mirror.set(1)
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
        self.mainGui = mainGui
        
        self.mainGui.CANCELED = True

        self.result = None
        body = Frame(self)
        self.initial_focus = self.body(body)
        body.grid(column=0,row=0,padx=5, pady=5)
        self.buttonbox()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        if self.mainGuiWindow is not None:
            self.geometry("+%d+%d" % (mainGuiWindow.winfo_rootx() 
             + 50, mainGuiWindow.winfo_rooty() + 50))
        self.deiconify() # become visibile now
        self.initial_focus.focus_set()
        # wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.resizable(0, 0)
        self.grab_set()
        self.lift()
        self.getImage_Dicom()
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
        self.title("DICOM Viewer")
        self.box = Frame(self)
        self.box.grid(column=0,row=0)
        menubar = Menu(self)
        self['menu'] = menubar
        self.menu_file = Menu(menubar)
        menubar.add_cascade(menu=self.menu_file, label='File')
        self.menu_file.add_command(label='Load new Image', command=self.getImage_Dicom)
        self.menu_file.add_command(label='Clear Points', command=self.clearAllLabels)
        pictureFrame=ttk.Frame(self.box)
        pictureFrame.grid(column=0,row=0,columnspan=3)
        self.pictureLabel=ttk.Label(pictureFrame)
        self.pictureLabel.grid(row=1,column=0)
        self.photo_image = Image.open("defaultImage.gif")
        (self.x, self.y) = self.photo_image.size
        self.photo_image = self.photo_image.resize((int(self.x/1.5),int(self.y/1.5)))
        self.x = int(self.x/1.5)
        self.y = int(self.y/1.5)
        self.direction = StringVar()
        self.direction.set("Select your Picture")
        self.directionLabel = ttk.Label(pictureFrame, textvariable=self.direction, font="Serif 12")
        self.directionLabel.grid(row=0,column=0)
        self.photoCanvas = Canvas(self.pictureLabel, relief=SUNKEN)
        self.photoCanvas.config(width=700, height=500, highlightthickness=0)
        self.sbarV = ttk.Scrollbar(self.pictureLabel, orient=VERTICAL)
        self.sbarH = ttk.Scrollbar(self.pictureLabel, orient=HORIZONTAL)
        self.sbarV.config(command=self.photoCanvas.yview)
        self.sbarH.config(command=self.photoCanvas.xview)
        self.photoCanvas.config(yscrollcommand=self.sbarV.set)
        self.photoCanvas.config(xscrollcommand=self.sbarH.set)
        self.sbarV.grid(row=0,column=1,sticky=(N,S))
        self.sbarH.grid(row=1,column=0,columnspan=2,sticky=(E,W))
        self.photoCanvas.grid(row=0, column=0)
        self.ds = None
        
        pointSelectFrame=ttk.Frame(self.box)
        pointSelectFrame.grid(column=0,row=2,columnspan=3)
        targetPointButton = ttk.Button(pointSelectFrame, text="Select Target", width=20,
                                       command=self.targetSelect)
        targetPointButton.grid(row=0,column=0)
        ninePointButton = ttk.Button(pointSelectFrame, text="Select 9 o'clock Point", width=20,
                                       command=self.nineSelect)
        ninePointButton.grid(row=0,column=1)
        sixPointButton = ttk.Button(pointSelectFrame, text="Select 6 o'clock Point", width=20,
                                       command=self.sixSelect)
        sixPointButton.grid(row=0,column=2)
        threePointButton = ttk.Button(pointSelectFrame, text="Select 3 o'clock Point", width=20,
                                       command=self.threeSelect)
        threePointButton.grid(row=0,column=3)
        helixPointButton = ttk.Button(pointSelectFrame, text="Select Helical Point", width=20,
                                       command=self.helixSelect)
        helixPointButton.grid(row=0,column=4)
        
        buttonFrame=ttk.Frame(self.box)
        buttonFrame.grid(column=0,row=3,columnspan=3)
        
        w = ttk.Button(buttonFrame, text="OK", width=10, 
         command=self.ok, default=ACTIVE)
        w.grid(column=0,row=0, padx=5, pady=5,sticky=(E))
        w = ttk.Button(buttonFrame, text="Cancel", width=10, 
         command=self.cancel)
        w.grid(column=1,row=0, padx=5, pady=5,sticky=(W))
        l = ttk.Label(buttonFrame, text="Rotation Value:")
        l.grid(column=2, row=0, padx=5, pady=5, sticky=(E))
        self.rotationVariable = StringVar()
        self.rotationVariable.set("0")
        rotationEntry = Entry(buttonFrame, textvariable=self.rotationVariable, width=10)
        rotationEntry.config(highlightcolor="GOLD", bd=2, highlightthickness=1, relief=GROOVE)
        rotationEntry.grid(column=3, row=0, sticky=(W))
        self.mirrorBox = Checkbutton(buttonFrame, text="Mirror Coordinates", variable=self.mirror, onvalue=1, offvalue=0, command=self.mirrorCheck)
        self.mirrorBox.grid(column=4, row=0, sticky=(W))
        self.mirrorBox.select()
        self.clearButton = ttk.Button(buttonFrame, text="Clear Points", width=15, command=self.clearAllLabels)
        self.clearButton.grid(column=5, row=0, sticky=(W))
        self.setDefaultButton = ttk.Button(buttonFrame, text="Reset Sliders", width=15, command=self.setToDefault)
        self.setDefaultButton.grid(column=6, row=0, sticky=(W))
        
        scaleFrame=ttk.Frame(self.box)
        scaleFrame.grid(column=0,row=4,columnspan=3)
        l = ttk.Label(scaleFrame, text="Window Width:")
        l.grid(column=0, row=0, padx=5, pady=5, sticky=(E))
        self.widthLabel = ttk.Label(scaleFrame, text="", relief="groove", width=6, anchor=CENTER)
        self.widthScale = ttk.Scale(scaleFrame, orient=HORIZONTAL,
                  from_=0.0, to=10.0, length=150, 
                  command=self.updateWidth)
        self.widthTo = 10.0
        self.widthFrom = 0.0
        self.widthVal = 1.0
        self.widthValDefault = 1.0
        self.widthScale.set(self.widthVal)
        self.widthScale.grid(column=1, row=0, sticky=(E,W))
        self.widthLabel.grid(column=2, row=0, sticky=(E,W))
        l = ttk.Label(scaleFrame, text="Window Center:")
        l.grid(column=3, row=0, padx=5, pady=5, sticky=(E))
        self.centerLabel = ttk.Label(scaleFrame, text="", relief="groove", width=6, anchor=CENTER)
        self.centerScale = ttk.Scale(scaleFrame, orient=HORIZONTAL,
                  from_=0.0, to=10.0, length=150, 
                  command=self.updateCenter)
        self.centerTo = 10.0
        self.centerFrom = 0.0
        self.centerVal = 1.0
        self.centerValDefault = 1.0
        self.centerScale.set(self.centerVal)
        self.centerScale.grid(column=4, row=0,sticky=(E,W))
        self.centerLabel.grid(column=5, row=0, sticky=(E,W))
        self.updateScreen(self.photo_image, False, False)
        self.photoCanvas.xview_moveto(1.0)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        
    def updateWidth(self, value):
        self.widthVal = int(float(value))*10
        self.widthLabel['text'] = str(self.widthVal)
        if self.ds is not None:
            self.show_image_update(self.ds, self.widthVal, self.centerVal)
        
    def updateCenter(self, value):
        self.centerVal = int(float(value))*10
        self.centerLabel['text'] = str(self.centerVal)
        if self.ds is not None:
            self.show_image_update(self.ds, self.widthVal, self.centerVal)
            
    def setToDefault(self):
        self.widthVal = self.widthValDefault
        self.widthScale.set(self.widthVal/10)
        self.centerVal = self.centerValDefault
        self.centerScale.set(self.centerVal/10)
   
    def mirrorCheck(self):
        if self.mirror.get() == 1:
            tkMessageBox.showwarning("Information: Mirror", "Coordinates will now be mirrored\nLabels have been cleared")  
        else:
            tkMessageBox.showwarning("Information: No Mirror", "Coordinates will no longer be mirrored\nLabels have been cleared") 
        self.clearAllLabels()
              

    def ok(self, event=None):
        '''
        Proceeds to give suggestion for collimation if validation is ok. Call back function for the "ok" button on the GUI.
        '''
        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        try:
            self.applyInfo()
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
        if(self.isValid()==True):
            
            tubeValid = False
            if self.mirror.get() == 1:
                self.mirrorCoordinates()
            self.mainGui.setPlanCurrentCommand(self.coordinates)
            print self.coordinates
            newTubeCommand = self.mainGui.affineTransform(self.mainGui.planCurrentCommand)
            print newTubeCommand
            tubeValid=self.mainGui.setTubeCurrentCommand(20, newTubeCommand)
            if(tubeValid==False):
                tkMessageBox.showwarning("Invalid", "The movement command is out of bounds")
                return 0
            self.mainGui.CANCELED = False
            return 1
        
        else:
            tkMessageBox.showwarning("ERROR", "Whoops, you forgot to enter your rotation value broseph.")
            return 0
        
    def isValid(self):
        try:
            rotation = float(self.rotationVariable.get())
            self.coordinates[2] = rotation
            return True
        except:
            return False
    
    def applyInfo(self):
        '''
        Displays an information dialog to the user giving them the suggested parameters for collimation.
        '''
        pass
        
    def getImage_Dicom(self):
        filename = tkFileDialog.askopenfilename(initialdir="./", title="Please select the desired DICOM File")
        try:
            ds = dicom.read_file(filename)
            self.ds = ds
            self.title("DICOM Viewer - " + str(ds.PatientsName) + " " + str(ds.StudyDate[4:6]) 
                       + "/" + str(ds.StudyDate[6:8]) + "/" + str(ds.StudyDate[0:4]) + " Slice:" 
                       + str(ds.InstanceNumber) + "(" + str(ds.SliceLocation) + ")"  + " - "
                       + str(ds.Rows) + "x" + str(ds.Columns))
            self.show_image(ds)
        except:
            pass
        
    def get_PGM_bytedata_string(self, arr):
        '''Given a 2D numpy array as input write gray-value image data in the PGM 
        format into a byte string and return it.
        
        @param arr: single-byte unsigned int numpy array
        @param note: Tkinter's PhotoImage object seems to accept only single-byte data
        '''
        
        if arr.dtype != np.uint8:
            raise ValueError
        if len(arr.shape) != 2:
            raise ValueError
        
        # array.shape is (#rows, #cols) tuple; PGM input needs this reversed
        col_row_string = ' '.join(reversed(map(str, arr.shape)))
    
        bytedata_string = '\n'.join(('P5',
                                     col_row_string,
                                     str(arr.max()),
                                     arr.tostring()))
        return bytedata_string
    
    
    def get_PGM_from_numpy_arr(self, arr, window_center, window_width, 
                               lut_min=0, lut_max=255):
        '''real-valued numpy input  ->  PGM-image formatted byte string
        
        arr: real-valued numpy array to display as grayscale image
        window_center, window_width: to define max/min values to be mapped to the
                                     lookup-table range. WC/WW scaling is done
                                     according to DICOM-3 specifications.
        lut_min, lut_max: min/max values of (PGM-) grayscale table: do not change
        '''
    
        if np.isreal(arr).sum() != arr.size:
            raise ValueError
    
        # currently only support 8-bit colors
        if lut_max != 255:
            raise ValueError
    
        if arr.dtype != np.float64:
            arr = arr.astype(np.float64)
        
        # LUT-specific array scaling
        # width >= 1 (DICOM standard)
        window_width = max(1, window_width)
        
        wc, ww = np.float64(window_center), np.float64(window_width)
        lut_range = np.float64(lut_max) - lut_min
    
        minval = wc - 0.5 - (ww - 1.0) / 2.0
        maxval = wc - 0.5 + (ww - 1.0) / 2.0
    
        min_mask = (minval >= arr)
        to_scale = (arr > minval) & (arr < maxval)
        max_mask = (arr >= maxval)
        
        if min_mask.any(): arr[min_mask] = lut_min
        if to_scale.any(): arr[to_scale] = ((arr[to_scale] - (wc - 0.5)) /
                                            (ww - 1.0) + 0.5) * lut_range + lut_min
        if max_mask.any(): arr[max_mask] = lut_max 
        
        # round to next integer values and convert to unsigned int
        arr = np.rint(arr).astype(np.uint8)
        
        # return PGM byte-data string
        return self.get_PGM_bytedata_string(arr)
    
    
    def get_tkinter_photoimage_from_pydicom_image(self, data):
        '''
        Wrap data.pixel_array in a Tkinter PhotoImage instance, 
        after conversion into a PGM grayscale image.
        
        This will fail if the "numpy" module is not installed in the attempt of 
        creating the data.pixel_array.
    
        data:  object returned from pydicom.read_file()
        side effect: may leave a temporary .pgm file on disk
        '''
        
        # get numpy array as representation of image data
        arr = data.pixel_array.astype(np.float64)
        
        # pixel_array seems to be the original, non-rescaled array.
        # If present, window center and width refer to rescaled array
        # -> do rescaling if possible.
        if ('RescaleIntercept' in data) and ('RescaleSlope' in data):
            self.intercept = data.RescaleIntercept  # single value
            self.slope = data.RescaleSlope          # 
            arr = self.slope * arr + self.intercept
        
        # get default window_center and window_width values
        wc = (arr.max() + arr.min()) / 2.0
        ww = arr.max() - arr.min() + 1.0
        self.widthTo = ww/10
        self.centerTo = arr.max()/10
        self.centerFrom = arr.min()/10
        
        # overwrite with specific values from data, if available
        if ('WindowCenter' in data) and ('WindowWidth' in data):
            wc = data.WindowCenter
            ww = data.WindowWidth
            index = 0
            wwMax = ww[0]
            for i in range(len(ww)):
                if int(ww[i]) > int(wwMax):
                    index = i
                    wwMax = ww[i]
            try:
                wc = wc[index]            # can be multiple values
            except:
                pass
            try:
                ww = wwMax
            except:
                pass
        self.widthScale['to'] = self.widthTo
        self.centerScale['to'] = self.centerTo
        self.centerScale['from'] = self.centerFrom
        self.widthScale.set(ww/10)
        self.widthVal = ww
        self.widthValDefault = ww
        self.centerScale.set(wc/10)
        self.centerVal = wc
        self.centerValDefault = wc
        # scale array to account for center, width and PGM grayscale range,
        # and wrap into PGM formatted ((byte-) string
        pgm = self.get_PGM_from_numpy_arr(arr, wc, ww)
        
        # create a PhotoImage
    
        # write PGM file into temp dir
        (os_id, abs_path) = tempfile.mkstemp(suffix='.pgm')
        with open(abs_path, 'wb') as fd:
            fd.write(pgm)
            
        photo_image = Image.open(abs_path)
        #photo_image = photo_image.transpose(Image.FLIP_LEFT_RIGHT)
        
        # close and remove temporary file on disk
        # os.close is needed under windows for os.remove not to fail
        try:
            os.close(os_id)
            os.remove(abs_path)
        except:
            pass  # silently leave file on disk in temp-like directory
        
        return photo_image
    
    def show_image_update(self, data, width, center):
        arr = data.pixel_array.astype(np.float64)
        arr = self.slope * arr + self.intercept
        pgm = self.get_PGM_from_numpy_arr(arr, center, width)
        
        # create a PhotoImage
    
        # write PGM file into temp dir
        (os_id, abs_path) = tempfile.mkstemp(suffix='.pgm')
        with open(abs_path, 'wb') as fd:
            fd.write(pgm)
            
        self.photo_image = Image.open(abs_path)
        #photo_image = photo_image.transpose(Image.FLIP_LEFT_RIGHT)
        
        # close and remove temporary file on disk
        # os.close is needed under windows for os.remove not to fail
        try:
            os.close(os_id)
            os.remove(abs_path)
        except:
            pass  # silently leave file on disk in temp-like directory
        self.picture.paste(self.photo_image)
        
    
    def show_image(self, data):
        '''
        '''
        self.photo_image = self.get_tkinter_photoimage_from_pydicom_image(data)
        self.updateScreen(self.photo_image, True, True)
        self.clearAllLabels()
        self.direction.set("Image Loaded, please select the points to select")
        
        
    def updateScreen(self, inputImage, width, center):
        '''
        This Function updates the buttonbox with the desired image while also adding
        a 5x contrast increase
        '''
        self.width = width
        self.center = center
        (self.x,self.y) = inputImage.size
        self.photoCanvas.config(scrollregion=(0,0,self.x,self.y))
        self.picture = ImageTk.PhotoImage(inputImage) #sets the screen to the proper size
        self.photoCanvas.create_image(0,0,anchor="nw",image=self.picture)
         
    def selectObject(self):
        self.photoCanvas.bind("<Button-1>", self.getMousePosition) 
               
    def getMousePosition(self, event):
        canvas = event.widget
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        if self.point == "TARGET":
            self.coordinates[0] = x
            self.coordinates[1] = y
            (self.targetPoint, self.targetText) = self.addLabel(x, y, "Target", self.targetPoint, self.targetText)
        elif self.point == "NINE":
            self.coordinates[3] = x
            self.coordinates[4] = y
            (self.ninePoint, self.nineText) = self.addLabel(x, y, "9 o\'clock", self.ninePoint, self.nineText)
        elif self.point == "SIX":
            self.coordinates[5] = x
            self.coordinates[6] = y
            (self.sixPoint, self.sixText) = self.addLabel(x, y, "6 o\'clock", self.sixPoint, self.sixText)
        elif self.point == "THREE":
            self.coordinates[7] = x
            self.coordinates[8] = y
            (self.threePoint, self.threeText) = self.addLabel(x, y, "3 o\'clock", self.threePoint, self.threeText)
        elif self.point == "HELIX":
            self.coordinates[9] = x
            self.coordinates[10] = y
            (self.helixPoint, self.helixText) = self.addLabel(x, y, "Helix", self.helixPoint, self.helixText)
        self.direction.set("You selected the point at pixel value: (%.0f,%.0f)" % (x,y))
        self.photoCanvas.unbind("<Button-1>")
        
    def targetSelect(self):
        self.direction.set("Please select the target point")
        self.selectObject()
        self.removeLabel(self.targetPoint, self.targetText)
        self.point="TARGET"
              
    def nineSelect(self):
        self.direction.set("Please select the nine o'clock point") 
        self.selectObject()
        self.removeLabel(self.ninePoint, self.nineText)
        self.point="NINE"
             
    def sixSelect(self):
        self.direction.set("Please select the six o'clock point")
        self.selectObject()
        self.removeLabel(self.sixPoint, self.sixText)
        self.point="SIX"
               
    def threeSelect(self):
        self.direction.set("Please select the three o'clock point")
        self.selectObject()
        self.removeLabel(self.threePoint, self.threeText)
        self.point="THREE"
                
    def helixSelect(self):
        self.direction.set("Please select the helix point")
        self.selectObject()
        self.removeLabel(self.helixPoint, self.helixText)
        self.point="HELIX"
        
    def addLabel(self, x, y, name, curPoint, curText):
        try:
            self.photoCanvas.delete(curPoint)
            self.photoCanvas.delete(curText)
        except:
            pass
        point = self.photoCanvas.create_oval(x-3,y-3,x+3,y+3,fill="",outline="RED", width=3)
        label = self.photoCanvas.create_text(x,y-20,fill="RED",text=name,font="Serif 14")
        return(point,label)
    
    def removeLabel(self, curPoint, curText):
        try:
            self.photoCanvas.delete(curPoint)
            self.photoCanvas.delete(curText)
        except:
            pass
        
    def mirrorCoordinates(self):
        for i in (0,3,5,7,9):
            self.coordinates[i] = self.coordinates[i] * -1.0
        temp = [self.coordinates[7],self.coordinates[8]]
        self.coordinates[7] = self.coordinates[3]
        self.coordinates[8] = self.coordinates[4]
        self.coordinates[3] = temp[0]
        self.coordinates[4] = temp[1]
        
    def clearAllLabels(self):
        self.removeLabel(self.helixPoint, self.helixText)
        self.removeLabel(self.threePoint, self.threeText)
        self.removeLabel(self.sixPoint, self.sixText)
        self.removeLabel(self.ninePoint, self.nineText)
        self.removeLabel(self.targetPoint, self.targetText)
        self.coordinates = [0,0,0,0,0,0,0,0,0,0,0]
        self.direction.set("All Points were Cleared")