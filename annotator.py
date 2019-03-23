import tkinter as tk

class Annotator(tk.Frame):
    def __init__( self, window):
        tk.Frame.__init__(self, window)
        self.window = window
        self.window.configure(background = 'grey')
        #self.window.grid_columnconfigure(3, minsize=400)
        self._createWidgets()
        self._createLayout()
        self._createBindings()
        
        self._createCanvasVariables()
        
        self.rect_dict ={}
        self._listRectFM = {}
        self._listRectRM = {}

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
       # self.rect_objects = []
        self.active_rect = None
        self.active_label = 'human'
        self.background_objcect = None
        
    def _createWidgets(self):
        self.canvas = tk.Canvas(self.window, width = 640, height = 512,
                                bg = "white",borderwidth=0, highlightthickness=0) 
        self.labelForm = tk.Text(self.window, width = 10, height = 1)
        self.B = tk.Button(self.window, command = self.pressMe, width = 20)
        self.labelButton = tk.Button(self.window, text = 'LABEL', command = self.pushLabel, width = 10)
        self.labelForm.insert(tk.END, 'human')
        self.L = tk.Listbox(self.window, highlightbackground = 'red')
        
    def _createLayout(self):

        self.L.config(width=30)
        #self.frame = tk.Button(self.window, width = 200, height = 200)
        #self.frame2 = tk.Button(self.window, width = 200, height = 200)
        
        self.canvas.grid(row=0, column=1, rowspan=10)
        self.labelForm.grid(row=0, column=2)
        self.labelButton.grid(row=0, column=3)
        self.L.grid(row=1, column =2, columnspan=1, rowspan=1)
        self.B.grid(row=1,column=1)
        
        
        self.img = tk.PhotoImage(file="testimg.jpg")   
        self.background_object = self.canvas.create_image((0,0), anchor = tk.NW, image=self.img)    
        
       # self.frame2.grid(row=1, column=0, sticky='nsew')
       # self.frame.grid(row=0, column=2, sticky='nsew')
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
       # self.canvas.bind( "<Key>", self. keyHandler)

    def pressMe(self):
        self.canvas.delete(self.background_object)
        self.img = tk.PhotoImage(file="testimg2.jpg")
        self.background_object = self.canvas.create_image((0,0), anchor = tk.NW, image=self.img)    
        self.canvas.tag_lower(self.background_object)
        
    def listHandler(self, event):
        i = self.L.curselection()
        if i:
            self.active_rect = self._listRectFM[i[0]]
            self._update()
    
    def _update(self):

        self._updateText()
        self._highlightActive()
        
    def _highlightActive(self):
        #print(self.active_rect)
        #for rect in self.rect_objects:
        #    if rect != self.active_rect:
        #        self.canvas.itemconfig(rect, outline='black')
        #    else:
        #        self.canvas.itemconfig(rect, outline = 'red')
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
 #           self.active_rect = self.active_rect[0]
            #print('highlighting')
            
            #self.canvas.itemconfig(self.active_rect, outline='red')
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
        #self.cursorx = self.canvas.canvasx(event.x)
        #self.cursory = self.canvas.canvasy(event.y) 
       # if not self.active_rect:
       #     self.rectx1, self.recty1 = self.cursorx, self.cursory
        if self.active_rect:
            self.add2Dictionary(self.active_rect,
                                coords = self.canvas.coords(self.active_rect),
                                label = self.active_label)
      
        #self._updateText()    
        #self.highlightActive()
        self._update()
        
    def _updateText(self):
        self.L.delete(0, tk.END)
        self._listBoxRectRef = {}
        for i, (rect, info) in enumerate(self.rect_dict.items()):
            item_string = ' '.join((str(info['coords']), info['label']))
            self.L.insert(tk.END, item_string)
            
            self._listRectFM[i] = rect
            self._listRectRM[rect] = i

    def keyHandler(self, event):
        if event.char == 'x':
            self.destroyRect()
        if event.char == 't':
            print(self.canvas.bbox(self.background_object))
        self._update()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry( "1200x600" )
    ann = Annotator(root)
    root.mainloop()
