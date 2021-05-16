# https://github.com/MenxLi/tkSliderWidget/blob/master/tkSliderWidget.py


from tkinter import *
from tkinter.ttk import *



class Slider(Frame):
    LINE_COLOR = "#476b6b"
    LINE_WIDTH = 3
    BAR_COLOR_INNER = "#5c8a8a"
    BAR_COLOR_OUTTER = "#c2d6d6"
    BAR_RADIUS = 10
    BAR_RADIUS_INNER = BAR_RADIUS-5
    DIGIT_PRECISION = '.0f' # for showing in the canvas
    def __init__(self, master, width = 400, height = 80, min_val = 0, max_val = 1, init_lis = None, show_value = True, lowHMSVars = None, highHMSVars = None, bg_color="#ffffff"):

        s = Style()
        s.configure('My.TFrame', background=bg_color)

        Frame.__init__(self, master, height = height, width = width, style="My.TFrame")
        
        self.master = master

        if init_lis == None:
            init_lis = [min_val]
        self.init_lis = init_lis

        self.lowHMSVars = lowHMSVars
        self.highHMSVars = highHMSVars

        self.max_val = max_val
        self.min_val = min_val
        self.show_value = show_value
        self.H = height
        self.W = width
        self.canv_H = self.H
        self.canv_W = self.W
        if not show_value:
            self.slider_y = self.canv_H/2 # y pos of the slider
        else:
            self.slider_y = self.canv_H*2/5
        self.slider_x = Slider.BAR_RADIUS # x pos of the slider (left side)

        self.bars = []
        self.selected_idx = None # current selection bar index
        for value in self.init_lis:
            pos = (value-min_val)/(max_val-min_val)
            ids = []

            hours, minutes, seconds = self.getHMS(value)

            bar = {"Pos":pos, "Ids":ids, "TotalSeconds": value, "Hours":hours, "Minutes":minutes, "Seconds":seconds, "X":self.slider_x, "Offset":False}
            self.bars.append(bar)


        self.canv = Canvas(self, height = self.canv_H, width = self.canv_W, bg=bg_color, bd=0, highlightthickness=0, relief='ridge')
        self.canv.pack(padx=10, pady=10)
        self.canv.bind("<Motion>", self._mouseMotion)
        self.canv.bind("<B1-Motion>", self._moveBar)

        self.__addTrack(self.slider_x, self.slider_y, self.canv_W-self.slider_x, self.slider_y)
        for bar in self.bars:
            bar["Ids"] = self.__addBar(bar["Pos"], bar)

    def bind(self, event, func):
        self.canv.bind(event, func)

    def getValues(self):
        values = [bar["TotalSeconds"] for bar in self.bars]
        return sorted(values) 
    
    def _mouseMotion(self, event):
        x = event.x; y = event.y
        selection = self.__checkSelection(x,y)
        if selection[0]:
            self.canv.config(cursor = "hand2")
            self.selected_idx = selection[1]
        else:
            self.canv.config(cursor = "")
            self.selected_idx = None

    def moveBar(self):
        lowVarH = self.lowHMSVars[0]
        lowVarM = self.lowHMSVars[1]
        lowVarS = self.lowHMSVars[2]
        highVarH = self.highHMSVars[0]
        highVarM = self.highHMSVars[1]
        highVarS = self.highHMSVars[2]
        try:
            secondsOne = (int(lowVarH.get())*3600) + (int(lowVarM.get())*60) + int(lowVarS.get())
            secondsTwo = (int(highVarH.get())*3600) + (int(highVarM.get())*60) + int(highVarS.get())
        except: 
            # Cut Range Invalid
            return False

        if secondsOne > self.max_val or secondsOne < 0 or secondsTwo > self.max_val or secondsTwo < 0:
            # Cut Range Out of Bounds
            return False


        allIds = []
        for i in self.bars:
            allIds += i["Ids"]

        for id in allIds:
            self.canv.delete(id)

        posOne = secondsOne / self.max_val
        posTwo = secondsTwo / self.max_val
        
        bothPos = [posOne, posTwo]

        i=0
        for bar in self.bars:
            pos = bothPos[i]
            bar["Pos"] = pos
            bar["TotalSeconds"] = int(pos*(self.max_val - self.min_val)+self.min_val)
            bar["Hours"], bar["Minutes"], bar["Seconds"] = self.getHMS(secondsOne if i == 0 else secondsTwo)
            bar["Ids"] = self.__addBar(pos, bar)
            i += 1
        
        if (secondsOne > secondsTwo):
            temp = secondsOne
            secondsOne = secondsTwo
            secondsTwo = temp
        
        lowH, lowM, lowS = self.getHMS(secondsOne)
        highH, highM, highS = self.getHMS(secondsTwo)

        lowVarH.set(str(lowH))
        lowVarM.set(str(lowM))
        lowVarS.set(str(lowS))

        highVarH.set(str(highH))
        highVarM.set(str(highM))
        highVarS.set(str(highS))



    def _moveBar(self, event):
        x = event.x; y = event.y
        if self.selected_idx == None:
            return False
        pos = self.__calcPos(x)
        idx = self.selected_idx
        self.__moveBar(idx,pos)

    def __addTrack(self, startx, starty, endx, endy):
        id1 = self.canv.create_line(startx, starty, endx, endy, fill = Slider.LINE_COLOR, width = Slider.LINE_WIDTH)
        return id

    def __addBar(self, pos, bar):
        """@ pos: position of the bar, ranged from (0,1)"""
        if pos <0 or pos >1:
            raise Exception("Pos error - Pos: "+str(pos))
        R = Slider.BAR_RADIUS
        r = Slider.BAR_RADIUS_INNER
        L = self.canv_W - 2*self.slider_x
        y = self.slider_y
        x = self.slider_x+pos*L
        id_outer = self.canv.create_oval(x-R,y-R,x+R,y+R, fill = Slider.BAR_COLOR_OUTTER, width = 2, outline = "")
        id_inner = self.canv.create_oval(x-r,y-r,x+r,y+r, fill = Slider.BAR_COLOR_INNER, outline = "")

        if self.show_value:
            y_value = y+Slider.BAR_RADIUS+8

            value = ":".join(self.stringifyHMS(self.getHMS(int(bar["TotalSeconds"]))))

            if (x < 30):
                x = 30
            if x > self.W-30:
                x=self.W-30
        
            if (self.__checkCollision(bar)):
                y_value -= 34
            

            id_value = self.canv.create_text(x,y_value, text = value)
            self.handleStringVars()
            return [id_outer, id_inner, id_value]
        else:
            self.handleStringVars()
            return [id_outer, id_inner]

    def __checkCollision(self, thisBar):
        for otherBar in self.bars:
            if (otherBar is thisBar):
                continue
            if (abs(otherBar["Pos"] - thisBar["Pos"]) < 0.20) and (otherBar["Offset"] == False):
                thisBar["Offset"] = True
                return True
        thisBar["Offset"] = False
        return False

    def __moveBar(self, idx, pos):
        ids = self.bars[idx]["Ids"]
        for id in ids:
            self.canv.delete(id)

        self.bars[idx]["Pos"] = pos
        self.bars[idx]["TotalSeconds"] = pos*(self.max_val - self.min_val)+self.min_val
        self.bars[idx]["Ids"] = self.__addBar(pos, self.bars[idx])
        self.bars[idx]["Hours"], self.bars[idx]["Minutes"], self.bars[idx]["Seconds"] = self.getHMS(self.bars[idx]["TotalSeconds"])



    def __calcPos(self, x):
        """calculate position from x coordinate"""
        pos = (x - self.slider_x)/(self.canv_W-2*self.slider_x)
        if pos<0:
            return 0
        elif pos>1:
            return 1
        else:
            return pos

    def __checkSelection(self, x, y):
        """
        To check if the position is inside the bounding rectangle of a Bar
        Return [True, bar_index] or [False, None]
        """
        for idx in range(len(self.bars)):
            id = self.bars[idx]["Ids"][0]
            bbox = self.canv.bbox(id)
            if bbox[0] < x and bbox[2] > x and bbox[1] < y and bbox[3] > y:
                return [True, idx]
        return [False, None]

    def getHMS(self, seconds):
        seconds = seconds % (24 * 3600) 
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return int(hours), int(minutes), int(seconds)

    def stringifyHMS(self, HMS):
        newHMS = [str(val) for val in HMS]
        for i in range(len(newHMS)):
            if int(newHMS[i]) < 10:

                newHMS[i] = "0" + newHMS[i]
        return newHMS

    def handleStringVars(self):
        if self.lowHMSVars != None and self.highHMSVars != None:
            twoSeconds = self.getValues()
            lowHMS = self.getHMS(int(twoSeconds[0]))
            self.lowHMSVars[0].set(lowHMS[0])
            self.lowHMSVars[1].set(lowHMS[1])
            self.lowHMSVars[2].set(lowHMS[2])

            highHMS = self.getHMS(int(twoSeconds[1]))
            self.highHMSVars[0].set(highHMS[0])
            self.highHMSVars[1].set(highHMS[1])
            self.highHMSVars[2].set(highHMS[2])
    