import tkinter as tk

from os import path
from os import listdir
from PIL import Image, ImageTk
from copy import deepcopy

class listWalker():
    def __init__(self, n):
        self.list = n
        self.index = 0
        self.error = 'O.K.'
    def advance(self):
        if self.index < len(self.list)-1:
            self.index +=1
        else:
            self.error = "No more images to the right."
            raise IndexError
        return self.list[self.index]
    
    def back(self):
        if self.index != 0:
            self.index -=1
        else:
            self.error = "No more images to the left."
            raise IndexError
        return self.list[self.index]

    def current(self):
        return self.list[self.index]

    def delete_entry(self):
        del self.list[self.index]
        if self.index == len(self.list):
            self.index -= 1
        
class imageBuddy():
    def __init__(self):
        self.thermal_dir = path.join('data','thermal')
        self.rgb_dir = path.join('data','rgb')
        self.log_dir = 'log.txt'
        
        self._importImagePaths()
        self._checkLog()

    
        
    def _importImagePaths(self):
        self.imageDict = {}
        for thermal in listdir(self.thermal_dir):
            if '.jpg' in thermal:
                self.imageDict[thermal] = {'thermal':path.join(self.thermal_dir, thermal)}
       
        for rgb in listdir(self.rgb_dir):
            if '.jpg' in rgb:
                try:
                    self.imageDict[rgb].update({'rgb':path.join(self.rgb_dir, rgb)})
                except KeyError:
                    self.imageDict[rgb] = {'rgb':path.join(self.rgb_dir, rgb)}
                    print('WARN: no matching thermal image for {}'.format(rgb))
        
    def _checkLog(self, suppress_warnings = True):
        if not path.exists(self.log_dir):
            with open(self.log_dir, 'w'):
                pass
            
        with open(self.log_dir, 'r') as log_file:
            log = log_file.readlines()
        
        for entry in log:
            image = entry.split(' ')[0]
            image = path.basename(image)
            try:
                self.imageDict[image].update({'logged':True})
            except KeyError:
                if not suppress_warnings:
                    print('WARN: log contains entries not in data')
    
    def saveAnnotation(self, image):
        boxes = self.imageDict.get(image).get('rects')
        box_string = [','.join((','.join(map(lambda x: str(int(x)), x['coords'])), x['label'])) for x in boxes.values()]
        out_string = self.imageDict.get(image).get('thermal')
        out_string += ' ' +' '.join(box_string)
        with open(self.log_dir, 'a') as log_file:
            log_file.write(out_string +'\n')
        self.imageDict[image].update({'logged':True})
        
        
class Annotator():
    def __init__( self, window):
        #tk.Frame.__init__(self, window)
        self.window = window
        self.window.configure(background = 'grey')
        
        self.imageBuddy = imageBuddy()
        self.unsaved = self._makeListWalker()
        
        self.thermal_var = tk.BooleanVar()
        self.infobar_display = tk.StringVar()
        self.vision_mode = 'rgb'
        self.okay_status = 'Status O.K.'
        #self.window.grid_columnconfigure(3, minsize=400)
        self._createWidgets()
        self._createLayout()
        self._createBindings()
        
        self._createCanvasVariables()
        #self._startupProgram()
        
        self.rect_dict ={}
        self._listRectFM = {}
        self._listRectRM = {}
        
    def switchView(self):
        if self.thermal_var.get():
            self.vision_mode = 'thermal'
        else:
            self.vision_mode = 'rgb'
        
        self.currentImage()
        
    def _makeListWalker(self, log_mode = False):
        walkable_images = []
        if log_mode:
            for image, info in self.imageBuddy.imageDict.items():
                if info.get('logged') != True and info.get('rects'):
                    walkable_images.append(image)
        else:
            for image, info in self.imageBuddy.imageDict.items():
                if info.get('logged') != True:
                    walkable_images.append(image)
        return listWalker(walkable_images)

    def currentImage(self):
        image = Image.open(self.imageBuddy.imageDict.get(self.unsaved.current()).get(self.vision_mode))
        photo = ImageTk.PhotoImage(image)
        
        self.img = photo
        
        self.canvas.delete(self.background_object)
        self.img = photo
        self.background_object = self.canvas.create_image((0,0), anchor = tk.NW, image=self.img)    
        self.canvas.tag_lower(self.background_object)
        
    def _endProgram(self):
        self._destroyAllRects()
        self.canvas.delete(self.background_object)
        image = Image.open('end.jpg')
        self.img = ImageTk.PhotoImage(image)
        self.background_object = self.canvas.create_image((0,0), anchor = tk.NW, image=self.img)    
        
        self.infobar_display.set('All images annotated.')
        self._dismantleWindow()
        
    def replaceCanvas(self):
        try:
            cur_image = self.unsaved.current()
        except:
            self.unsaved = self._makeListWalker(log_mode=False)
            cur_image = self.unsaved.current()
        self.canvas.delete(self.background_object)
        image = Image.open(self.imageBuddy.imageDict.get(cur_image).get(self.vision_mode))
        self.img = ImageTk.PhotoImage(image)
        self.background_object = self.canvas.create_image((0,0), anchor = tk.NW, image=self.img)    
        self.canvas.tag_lower(self.background_object)
        #retrieve stored dictionary
        tempdict = self.imageBuddy.imageDict.get(cur_image).get('rects')
        if tempdict == None:
            tempdict = {}

        #create all new objects out of that dictionary, but return a new dictionary
        #with the new object id numbers
        newdict = {}        
        for rect, data in tempdict.items():
            self.rectx0, self.recty0, self.rectx1, self.recty1 = data.get('coords')
            self.active_rect = self.canvas.create_rectangle(self.rectx0, self.recty0,
                                                     self.rectx1, self.recty1,
                                                     width = 2,
                                                     outline = 'red')
            newdict[self.active_rect] = data
        
        
        #destroy all old objects        
        self._destroyAllRects()
        
        #replace active dictionary with newly build objects dictionary
        self.rect_dict = deepcopy(newdict)
        self.active_rect = None
        self._update()
    
    def _destroyAllRects(self):
        temp_for_delete = [rect for rect in self.rect_dict.keys()]
        for rect in temp_for_delete:
            self.active_rect = rect
            self.destroyRect()
        del temp_for_delete
        
            
    def saveCurrent(self):
        cur_image = self.unsaved.current()
        if not self.rect_dict:
            self.infobar_display.set("Cannot save image with no annotations. Nullate instead.")
        else:
            self.imageBuddy.imageDict.get(cur_image).update({'rects':self.rect_dict.copy()})
            self.imageBuddy.saveAnnotation(cur_image)
            try:
                self.unsaved.delete_entry()
                self.replaceCanvas()
                self.infobar_display.set('Last image saved.')
            except IndexError:
                self._endProgram()
        
    
    def next_image(self):
        self.infobar_display.set(self.okay_status)
        cur_image = self.unsaved.current()
        self.imageBuddy.imageDict.get(cur_image).update({'rects':self.rect_dict.copy()})
        try:
            self.unsaved.advance()
        except IndexError:  
            self.infobar_display.set(self.unsaved.error)
        self.replaceCanvas()
    
    def prev_image(self):
        self.infobar_display.set(self.okay_status)
        cur_image = self.unsaved.current()
        self.imageBuddy.imageDict.get(cur_image).update({'rects':self.rect_dict.copy()})
        try:
            self.unsaved.back()
        except IndexError:  
            self.infobar_display.set(self.unsaved.error)
        self.replaceCanvas()
        
    def _startupProgram(self):
        if self.thermal_var.get():
            self.vision_mode = 'thermal'
        else:
            self.vision_mode = 'rgb'
        try:
            cur_image = self.unsaved.current()
            image = Image.open(self.imageBuddy.imageDict.get(cur_image).get(self.vision_mode))
            self.img= ImageTk.PhotoImage(image)
            self.infobar_display.set(self.okay_status)
        except IndexError:
            image = Image.open('end.jpg')
            self.img = ImageTk.PhotoImage(image)
            self.infobar_display.set('No unannotated images found in working directory.')

            self._dismantleWindow()
            
    def doNothing(self):
        '''
        Do-nothing "command" for hidden buttons associated with a key-press.
        '''
        pass
    
    def _dismantleWindow(self):
        buttons_to_dismantle = [
                self.advanceButton,
                self.backButton,
                self.thermalCheck,
                self.saveButton,
                self.nullButton,
                self.logButton]
        for button in buttons_to_dismantle:
            button.grid_forget()
            button.configure(command=self.doNothing)
        self.L.delete(0, tk.END)

        
    def _createCanvasVariables(self):
        self.rectx0 = 0
        self.recty0 = 0
        self.rectx1 = 0
        self.recty1 = 0
        
        self.drag_refx = 0
        self.drag_refy = 0
        self.cursorx = 0
        self.cursory=0
        self.make_mode = False
        self.drag_mode = False
        self.active_rect = None
        self.active_label = 'human'
        self.background_objcect = None
        
    def _createWidgets(self):
        self.canvas = tk.Canvas(self.window, width = 640, height = 512,
                                bg = "white",borderwidth=0, highlightthickness=0) 
        self.labelForm = tk.Text(self.window, width = 10, height = 1)
        self.advanceButton = tk.Button(self.window,
                                       command = self.next_image,
                                       width = 10,
                                       text = 'NEXT')
        self.backButton = tk.Button(self.window,
                                    command = self.prev_image,
                                    width = 10,
                                    text = 'PREV')
        
        self.labelButton = tk.Button(self.window, text = 'LABEL', command = self.pushLabel, width = 10)
        self.labelForm.insert(tk.END, 'human')
        
        self.thermalCheck = tk.Checkbutton(self.window, 
                                           text = 'Thermal', 
                                           variable =self.thermal_var,
                                           command = self.switchView)
        self.L = tk.Listbox(self.window, highlightbackground = 'red')
       # self.labelListBox = tk.Listbox(self.window, highlightbackground = 'blue')
        self.saveButton = tk.Button(self.window,
                                    text = 'SAVE',
                                    command =self.saveCurrent,
                                    width =10)
        self.infobar = tk.Label(self.window,
                                textvariable = self.infobar_display,
                                anchor = tk.W)
        self.logButton = tk.Button(self.window,
                                   text= 'LOG',
                                   command = self.logAll,
                                   width = 10)
        self.nullButton = tk.Button(self.window,
                                    text = 'NULL',
                                    command =self.nullCurrent,
                                    width=10)
        self.quitButton = tk.Button(self.window,
                                    text = 'QUIT',
                                    command = self.window.destroy,
                                    width=25)
    
     
    def _createLayout(self):
        self.window.grid_columnconfigure(0, minsize=30)
        self.window.grid_rowconfigure(0, minsize=30)

        self.canvas.grid(row=1, column=1, columnspan = 10,rowspan = 10)
        self.window.grid_rowconfigure(11, minsize=15)
        self.advanceButton.grid(row=12,column=7)
        self.saveButton.grid(row=12, column=5)
        self.backButton.grid(row=12,column=3)
       # self.window.grid_rowconfigure(13, minsize=10)
        
        self.window.grid_columnconfigure(11, minsize=30)
        self.L.config(width=30)
        self.L.grid(row=1, column =12, columnspan =3,rowspan =2, sticky='nw')
      #  self.labelListBox.grid(row=3, column=12, columnspan =3, sticky='w')
        self.labelForm.grid(row=4, column=12, sticky='w')
        self.labelForm.configure(width=15)
        self.labelButton.grid(row=4, column=13, sticky='w')
        self.thermalCheck.grid(row=5, column=12, sticky='w')
        
        self.nullButton.grid(row=7, column=12, sticky='w')
        self.logButton.grid(row=7, column =13, sticky='w')
        self.infobar.grid(row=0, column=1, columnspan=10, sticky='sw')
        
        self.quitButton.grid(row =10, column=12, columnspan=3, sticky='sw')
        
        self.img = tk.PhotoImage(file="testimg.jpg")  
        self._startupProgram()
        self.background_object = self.canvas.create_image((0,0), anchor = tk.NW, image=self.img)    


    def logAll(self):
        cur_image = self.unsaved.current()
        self.imageBuddy.imageDict.get(cur_image).update({'rects':self.rect_dict.copy()})
        self.unsaved = self._makeListWalker(log_mode =True)
        logcount = len(self.unsaved.list)
        self.replaceCanvas()
        
        for x in range(logcount):
            self.saveCurrent()
        self.infobar_display.set("{} images logged.".format(logcount))
        
    def nullCurrent(self):
        cur_image = self.unsaved.current()
        nullbox = {'rects':{1:{'coords':[],'label':'null'}}}
        self.imageBuddy.imageDict.get(cur_image).update(nullbox)
        self.imageBuddy.saveAnnotation(cur_image)
        try:
            self.unsaved.delete_entry()
            self.replaceCanvas()
            self.infobar_display.set('Last image nullated.')
        except IndexError:
            self._endProgram()
        
                
    def pushLabel(self):
        self.active_label = self.labelForm.get("1.0",'end-1c')
        if self.active_rect:
            self.add2Dictionary(self.active_rect,
                                coords = self.canvas.coords(self.active_rect),
                                label = self.active_label,
                                force_label = True)
      
        self._update()
        self.L.focus_set()
      
    def _createBindings(self):
        self.canvas.bind( "<Button-1>", self.clickCanvas)
        self.canvas.bind( "<ButtonRelease-1>", self.releaseCanvas)
        self.window.bind("<Key>", self.keyHandler)
        self.L.bind("<<ListboxSelect>>", self.listHandler)
        self.canvas.bind("<Button-2>", self.enterResizeMode)
        self.canvas.bind("<ButtonRelease-2>", self.exitResizeMode)
      
        # self.canvas.bind( "<Key>", self. keyHandler)

    def enterResizeMode(self,event):
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<ButtonRelease-1>")
        
        self.cursorx = self.canvas.canvasx(event.x)
        self.cursory = self.canvas.canvasy(event.y) 
        if self.active_rect:
                self.rectx0, self.recty0, self.rectx1, self.recty1 = self.canvas.coords(self.active_rect)
                self.drag_refx = self.cursorx
                self.drag_refy = self.cursory
                self.canvas.bind( "<Motion>", self.resizeRect)
        
    def exitResizeMode(self, event):
        self.canvas.bind( "<Button-1>", self.clickCanvas)
        self.canvas.bind( "<ButtonRelease-1>", self.releaseCanvas)
        self.canvas.unbind("<Motion>")
        if self.active_rect:
            self._validateRect()
            self.add2Dictionary(self.active_rect,
                                coords = self.canvas.coords(self.active_rect),
                                label = self.active_label)
      
        self._update()
        
        
    def resizeRect(self, event):
        self.cursorx = self.canvas.canvasx(event.x)
        self.cursory = self.canvas.canvasy(event.y) 
        x_shift = self.cursorx - self.drag_refx
        y_shift = self.cursory - self.drag_refy
        self.canvas.coords(self.active_rect,
                               self.rectx0, self.recty0,
                               #self.cursorx, self.cursory)
                               self.rectx1+x_shift, self.recty1+y_shift)
     
    def _validateRect(self):
        cur_x0, cur_y0, cur_x1, cur_y1 = self.canvas.coords(self.active_rect)
   
        cur_x0, cur_x1 = [0 if x<0 else 640 if x>640 else x for x in [cur_x0, cur_x1]]
        cur_y0, cur_y1 = [0 if y<0 else 512 if y>512 else y for y in [cur_y0, cur_y1]]
        
        self.canvas.coords(self.active_rect,
                           cur_x0, cur_y0, cur_x1, cur_y1)

    
    def listHandler(self, event):
        i = self.L.curselection()
        if i:
            self.active_rect = self._listRectFM[i[0]]
            self._update()
    
    def _update(self):

        self._updateText()
        self._highlightActive()
        #self.infobar_display.set(self.okay_status)
        
    def _highlightActive(self):
        for rect in self.rect_dict.keys():
            if rect != self.active_rect:
                self.canvas.itemconfig(rect, outline='green')
            else:
                self.canvas.itemconfig(rect, outline = 'red')
        if self.active_rect:
            self.L.activate(self._listRectRM[self.active_rect])

        
        
    def clickCanvas(self, event):
        self.cursorx = self.canvas.canvasx(event.x)
        self.cursory = self.canvas.canvasy(event.y) 
        
        selected_rect = self.canvas.find_overlapping(self.cursorx-3, self.cursory-3,
                                         self.cursorx+3, self.cursory+3)
        
        #Do this to deal with the find_overlapping function finding the image.
        if selected_rect:
            if selected_rect[0] == self.background_object:
                if len(selected_rect)>1:
                    selected_rect = selected_rect[1]
                else:
                    selected_rect = None
            else:
                selected_rect = selected_rect[0]
        
        if selected_rect:
            if selected_rect == self.active_rect:
                self.rectx0, self.recty0, self.rectx1, self.recty1 = self.canvas.coords(self.active_rect)
                self.drag_refx = self.cursorx
                self.drag_refy = self.cursory
                self.canvas.bind( "<Motion>", self.dragRect)
            else:
                self.active_rect  = selected_rect
                
        else:
            self.rectx0, self.recty0 = self.cursorx, self.cursory
            self.rectx1, self.recty1 = self.rectx0, self.recty0
            self.active_rect = self.canvas.create_rectangle(self.rectx0, self.recty0,
                                                     self.rectx1, self.recty1,
                                                     width = 2,
                                                     outline = 'red')

            #self.rect_objects.append(self.active_rect)
            self.canvas.bind( "<Motion>", self.drawRect)
 
    def drawRect(self, event):
        self.rectx1 = self.canvas.canvasx(event.x)
        self.recty1 = self.canvas.canvasy(event.y) 
        
        self.canvas.coords(self.active_rect,
                           self.rectx0, self.recty0,
                           self.rectx1, self.recty1)

        
    def dragRect(self, event):
        self.cursorx = self.canvas.canvasx(event.x)
        self.cursory = self.canvas.canvasy(event.y) 
        x_shift = self.cursorx - self.drag_refx
        y_shift = self.cursory - self.drag_refy
        self.canvas.coords(self.active_rect,
                               self.rectx0+x_shift, self.recty0+y_shift,
                               self.rectx1+x_shift, self.recty1+y_shift)

    def destroyRect(self):
        if self.active_rect:
            self.canvas.delete(self.active_rect)
            del self.rect_dict[self.active_rect]
            
            del self._listRectFM[self._listRectRM[self.active_rect]]
            del self._listRectRM[self.active_rect]
            
        try:
            self.active_rect = sorted(self.rect_dict.keys())[-1]
        except:
            self.active_rect = None
            
            
            
    def add2Dictionary(self, rect, coords = None, label = None, force_label = False):
        #this is to prevent labels from being overwritten by accident/not existing
        #labels should only be placed if there is no label or if the LABEL button is pressed
        try:
            if coords:
                self.rect_dict[rect].update({'coords':coords})
            else:
                self.rect_dict[rect].update({'coords':[]})
            if force_label:
                self.rect_dict[rect].update({'label':label})
            elif label == None:
                self.rect_dict[rect].update({'label':'null'})
        except KeyError:
            self.rect_dict[rect] = {}
            self.add2Dictionary(rect, coords=coords, label=label, force_label=True)

    def releaseCanvas(self, event):
        self.canvas.unbind("<Motion>")

        if self.active_rect:
            self._validateRect()
            self.add2Dictionary(self.active_rect,
                                coords = self.canvas.coords(self.active_rect),
                                label = self.active_label)
      
        self._update()
        
    def _updateText(self):
        self.L.delete(0, tk.END)
 #       self._listBoxRectRef = {}
        for i, (rect, info) in enumerate(self.rect_dict.items()):
            item_string = ' '.join((str(info['coords']), info['label']))
            self.L.insert(tk.END, item_string)
            
            self._listRectFM[i] = rect
            self._listRectRM[rect] = i

    def keyHandler(self, event):
        if (self.window.focus_get() != self.labelForm): #not trying to type into textbox!
            if event.char == 'x':
                self.destroyRect()
            elif event.char == 't':
                self.thermalCheck.invoke()
            elif event.char == 'e':
                self.advanceButton.invoke()
            elif event.char == 'w':
                self.backButton.invoke()
            elif event.char == 's':
                self.saveButton.invoke()
            elif event.char == 'n':
                self.nullButton.invoke()
            self._update()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry( "1000x600" )
    root.title('Thermal Annotator')
    ann = Annotator(root)
    root.mainloop()
