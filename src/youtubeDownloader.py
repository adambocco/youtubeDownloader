import os
import sys
from moviepy.editor import AudioFileClip, VideoFileClip
import pytube                           # install from git :: python3 -m pip install git+https://github.com/nficano/pytube.git
import string
from tkinter import *
from tkinter import filedialog as fd
from eyed3 import load as eyed3Load
from PIL import Image, ImageTk
from io import BytesIO
from requests import get as requestsGet
from Downloadable import Downloadable
from tkSliderWidget import Slider
from youtubesearchpython import VideosSearch
from helpers import formatSeconds, addLineBreaks, HMStoSeconds


BG="#ffffff"
COLOR_DELETE = "#feaeae"
TITLE_FONT = ("Helvetica", 20)
FONT_XS = ("Helvetica", 8)
FONT_SM = ("Helvetica", 10)
FONT_MD = ("Helvetica", 12)
FONT_LG =  ("Helvetica", 16)
FONT_XL = ("Helvetica", 18)
ID3_TAG_OPTIONS = ['Title', 'Contributing Artists', 'Album', 'Album Artist', 'Year', 'Track Number']    


class App(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.config(bg=BG)

        self.vcmdInt = (master.register(self.validateInt),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        # Contains all [Downloadable] objects 
        self.downloadables = {}

        # textvariable for url entry
        self.searchVar = StringVar()                                                                                  
        self.searchVar.set("Enter a YouTube URL or Search Query")
        
        # textvariable for name change entry 
        self.nameChangeVar = StringVar()                                                                                      

        # listvariable for fetched urls added to listbox
        self.downloadableListVar = Variable(value=[])         

         # textvariable for count of songs added label                                       
        self.audioCountVar = StringVar()                                                                           
        self.audioCountVar.set('Audio: 0')

         # textvariable for count of videos added label
        self.videoCountVar = StringVar()                                                                            
        self.videoCountVar.set('Video: 0')

        # text variable for holding application status (ALL user notifications pop up here)
        self.statusVar = StringVar()
        self.statusVar.set('')

        # textvariable for dropdown list of songs
        self.tagChangeVar = StringVar()                                                                            
        self.tagChangeVar.set('Enter tag descriptor')

        # textvariable for holding currently selected metadata tag
        self.tagVar = StringVar()                                                                                   
        self.tagVar.set(ID3_TAG_OPTIONS[0])

        # integer variable for volume slider
        self.volumeVar = IntVar()
        self.volumeVar.set(1)

        # boolvariables for checkbox options
        self.deleteOnDownloadVar = BooleanVar()
        self.deleteOnDownloadVar.set(False)

        self.allowRepeatsVar = BooleanVar()
        self.allowRepeatsVar.set(True)

        self.keepTryingVar = BooleanVar()
        self.keepTryingVar.set(True)

        self.triesVar = IntVar()
        self.triesVar.set(2)

        self.playlistRangeVar = BooleanVar()
        self.playlistRangeVar.set(False)

        # bool var for whether or not to extract ID3 tags from metadata
        self.addMdTagsVar = BooleanVar()
        self.addMdTagsVar.set(True)

        # bool var for whether or not to extract ID3 tags from youtube title
        self.addTitleTagsVar = BooleanVar()
        self.addTitleTagsVar.set(True)

        # textvaraibles for holding range of videos in playlist to download, only active when [self.playlistRangeVar] is true
        # 1-indexed, lower and upper range is inclusive
        self.playlistLowerRangeVar = StringVar()
        self.playlistLowerRangeVar.set('1')
        self.playlistUpperRangeVar = StringVar()
        self.playlistUpperRangeVar.set('999')

        # textvariables for holding range to cut media
        # only active when [self.cutVar] is true
        self.cutLowerVarH = StringVar()
        self.cutLowerVarH.set('00')
        self.cutLowerVarM = StringVar()
        self.cutLowerVarM.set('00')
        self.cutLowerVarS = StringVar()
        self.cutLowerVarS.set('00')

        self.cutUpperVarH = StringVar()
        self.cutUpperVarH.set('00')
        self.cutUpperVarM = StringVar()
        self.cutUpperVarM.set('00')
        self.cutUpperVarS = StringVar()
        self.cutUpperVarS.set('00')

        self.previewCutLowVarH = StringVar()
        self.previewCutLowVarH.set('00')
        self.previewCutLowVarM = StringVar()
        self.previewCutLowVarM.set('00')
        self.previewCutLowVarS = StringVar()
        self.previewCutLowVarS.set('00')

        self.previewCutHighVarH = StringVar()
        self.previewCutHighVarH.set('00')
        self.previewCutHighVarM = StringVar()
        self.previewCutHighVarM.set('00')
        self.previewCutHighVarS = StringVar()
        self.previewCutHighVarS.set('00')
 

        self.clearSearchEntryNextClick = True
        self.clearTagEntryNextClick = True

        # holds URL and data for currently selected video/song
        self.previewDownloadableFrame = None
        self.previewDownloadable = None
        
        self.createWidgets()


    def createWidgets(self): 

        # Top frame widgets for adding Downloadables, downloading and other options
        self.controlFrame = Frame(self, padx=10, pady=10, bg=BG, borderwidth=2, relief="groove", width=80)
        self.controlFrame.pack(expand=True, padx=5, pady=5)

        self.searchEntry = Entry(self.controlFrame, textvariable = self.searchVar,font=FONT_MD, width=50)
        self.searchEntry.grid(column=1, row=1, columnspan=4, padx=5, pady=5)
        self.searchEntry.bind('<Button-1>',self.clearSearchEntry)                                             

        self.startDownloadButton = Button(self.controlFrame, text="Start Download", command=self.download, bg="#90be6d",width=15, height=3, padx=5, pady=7, font=FONT_LG)
        self.startDownloadButton.grid(column=3, row=2, rowspan=2)

        self.deleteOnDownload = Checkbutton(self.controlFrame, text="Clear List\nAfter Downloading", variable=self.deleteOnDownloadVar, bg=BG, highlightthickness=0)
        self.deleteOnDownload.grid(column=3, row=4)

        self.addPlaylistAudioButton = Button(self.controlFrame, text="Playlist Audio", command= lambda : self.addPlaylist(True), bg="#f9c74f",width=15, padx=5, pady=5, font=FONT_MD)
        self.addPlaylistAudioButton.grid(column=1, row=3)
        
        self.addSingleAudioButton = Button(self.controlFrame, text="Single Audio", command=lambda : self.addSingle(True), bg="#ffe3b0",width=15,  padx=5, pady=5, font=FONT_MD)
        self.addSingleAudioButton.grid(column=1, row=2)

        self.addPlaylistVideoButton = Button(self.controlFrame, text="Playlist Video", command=lambda : self.addPlaylist(False), bg="#f3524c",width=15, padx=5, pady=5, font=FONT_MD)
        self.addPlaylistVideoButton.grid(column=2, row=3)

        self.addSingleVideoButton = Button(self.controlFrame, text="Single Video", command=lambda : self.addSingle(False), bg="#f3a29c",width=15, padx=5, pady=5, font=FONT_MD)
        self.addSingleVideoButton.grid(column=2, row=2)

        # Frame below URL input, displays status of URL retrieval success, errors, and download progress
        self.statusFrame = Frame(self, padx=10, pady=10,bg=BG, borderwidth=2, relief="groove", width=80)
        self.statusFrame.pack(expand=True, padx=5, pady=5)

        self.audioCountLabel = Label(self.statusFrame, textvariable = self.audioCountVar, padx=10,font=FONT_MD, bg=BG)
        self.audioCountLabel.grid(column=0, row=1)

        self.videoCountLabel = Label(self.statusFrame, textvariable = self.videoCountVar, padx=10,font=FONT_MD, bg=BG)
        self.videoCountLabel.grid(column=1, row=1)

        self.statusLabel = Label(self.statusFrame, textvariable = self.statusVar, padx=10, font=FONT_LG, bg=BG)
        self.statusLabel.grid(column=0,columnspan=2, row=2)

        self.deleteAllAudioBtn = Button(self.statusFrame, text="Delete All Audio", command=lambda:self.deleteAllMedia("audio"), bg=COLOR_DELETE)
        self.deleteAllAudioBtn.grid(column=2, row=1, pady=2)

        self.deleteAllVideoBtn = Button(self.statusFrame, text="Delete All Video", command=lambda:self.deleteAllMedia("video"), bg=COLOR_DELETE)
        self.deleteAllVideoBtn.grid(column=2, row=2, pady=2)

        # Top right frame for controlling playlist range to be retrieved
        self.optionsFrame = Frame(self.controlFrame, padx=5, pady=5, bg=BG, borderwidth=2, relief="groove")
        self.optionsFrame.grid(padx=5, pady=5, row=1,rowspan=10, column=5, columnspan=3)

        self.optionsLabel = Label(self.optionsFrame, text="Options:", font=FONT_MD, bg=BG)
        self.optionsLabel.grid(column=1, row=0, padx=10, pady=10)

        self.playlistRangeCheckbox = Checkbutton(self.optionsFrame, text="Playlist range", variable=self.playlistRangeVar, bg=BG)
        self.playlistRangeCheckbox.grid(column=1, columnspan=3, row=1)

        self.playlistLowerRange = Entry(self.optionsFrame, textvariable=self.playlistLowerRangeVar, width=4)
        self.playlistLowerRange.grid(column=1, row=2)

        self.playlistRangeDashLabel = Label(self.optionsFrame, text="-", bg=BG)
        self.playlistRangeDashLabel.grid(column=2, row=2)

        self.playlistUpperRange = Entry(self.optionsFrame, textvariable=self.playlistUpperRangeVar, width=4)
        self.playlistUpperRange.grid(column=3, row=2)

        self.allowRepeatsCheckbox = Checkbutton(self.optionsFrame, text="Allow Repeats", variable=self.allowRepeatsVar,bg=BG)
        self.allowRepeatsCheckbox.grid(column=1, columnspan=3, row=3, padx=10, pady=10)
        

        self.keepTryingCheckbox = Checkbutton(self.optionsFrame, text="Tries Before Skipping\nWhen Fetching From YouTube", variable=self.keepTryingVar,bg=BG)
        self.keepTryingCheckbox.grid(column=1, columnspan=1, row=4, padx=10, pady=10)

        self.keepTryingEntry = Entry(self.optionsFrame, textvariable = self.triesVar, width=5, bg="#DDFFAA", validate="key", validatecommand=self.vcmdInt)
        self.keepTryingEntry.grid(row=4, column=2, padx=2, pady=2)
        self.keepTryingEntry.bind("<KeyRelease>", self.applyTries)

        self.keepTryingLabel = Label(self.optionsFrame, text=str(self.triesVar.get()), bg=BG)
        self.keepTryingLabel.grid(row=4, column=3)


        self.addMdTags = Checkbutton(self.optionsFrame, text="Add tags from\nYouTube metadata\n(Priority 1)", variable=self.addMdTagsVar, bg=BG)
        self.addMdTags.grid(column=5, columnspan=3, row=0, rowspan=3, pady=10)

        self.addTitleTags = Checkbutton(self.optionsFrame, text="Add tags from title\nSplit on '-'\nEx) Artist - Song\n(Priority 2)", variable=self.addTitleTagsVar, bg=BG)
        self.addTitleTags.grid(column=5, columnspan=3, row=3,rowspan=3, pady=10)

        # Middle frame/scrollbox for holding URLs retrieved and ready to be customized or downloaded

        self.downloadablesListFrame = Frame(self, padx=5, pady=10, bg=BG)
        self.downloadablesListFrame.pack()

        self.scrollFrame = Frame(self.downloadablesListFrame, padx=5, pady=10, bg=BG)
        self.scrollFrame.grid(column=1, row=2, columnspan=10)

        self.scroll_bar = Scrollbar(self.scrollFrame) 
        self.scroll_bar.pack(side=RIGHT, fill=Y) 

        self.mylist = Listbox(self.scrollFrame, yscrollcommand=self.scroll_bar.set, width= 120, listvariable=self.downloadableListVar, exportselection=False) 
        self.mylist.pack( side = LEFT, fill = BOTH ) 
        self.mylist.bind("<<ListboxSelect>>", self.showUrl)

        self.scroll_bar.config( command = self.mylist.yview ) 
        self.previewFrame = Frame(self, padx=10, pady=10, bg=BG)
        self.previewFrame.pack()


    def validateInt(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
        if value_if_allowed:
            try:
                int(value_if_allowed)
                return True
            except ValueError:
                return False
        elif value_if_allowed == "":
            return True
        else:
            return False



    def applyTries(self,ev):
        try:
            newTries = self.triesVar.get()
        except:
            newTries = 2
        if newTries < 2:
            newTries = 2
        self.keepTryingLabel["text"] = newTries

    # Shows all data retrieved from youtube and options to customize before downloading
    # Loads into preview frame (bottom frame)
    # Binds to 'self.mylist'
    def showUrl(self, ev):                                                             

         # Destroy currently in preview frame to show currently selecte done
        if self.previewDownloadableFrame != None:                                               
            self.previewDownloadableFrame.destroy()
            self.previewDownloadable = None

        # Get downloadable display name from listbox
        try:
            downloadableKey = ev.widget.get(ev.widget.curselection()[0])
        except IndexError:
            return
        
        downloadable = self.downloadables[downloadableKey]
                       
        # Reset entry variables
        self.nameChangeVar.set(downloadable.name)
        self.tagChangeVar.set('')


        urlFrame = Frame(self.previewFrame, padx=5, pady=5, bg=BG, borderwidth=2, relief="groove")                             
        urlFrame.pack(expand=True)

        urlName = Label(urlFrame, text=downloadable.name, bg=BG, font=TITLE_FONT)                                                      
        urlName.grid(row=0, column=0, columnspan=3)

        urlDelete = Button(urlFrame, text="Delete",command=lambda:self.deleteUrl(downloadableKey), bg="#FF9999")
        urlDelete.grid(row=0, column=6)

        urlNameChangeEntry = Entry(urlFrame, textvariable = self.nameChangeVar, width=50, bg="#bbdddd", font=("Helvetica", 16))
        urlNameChangeEntry.grid(row=1, column=1, columnspan=2)

        urlChangeName = Button(urlFrame,text="Change Name", command=lambda:self.changeName(downloadable, urlName), bg="#99BBBB", height=2)
        urlChangeName.grid(row=1, column=3, columnspan=1, padx=5)

        mediaManipulationFrame = Frame(urlFrame, bg=BG)
        mediaManipulationFrame.grid(row=4,column=0,columnspan=20)

        urlInfoAndCutFrame = Frame(urlFrame, bg=BG, borderwidth=2, relief="groove")
        urlInfoAndCutFrame.grid(row=3, column=1)

        optionsFrame = Frame(mediaManipulationFrame, padx=5, pady=5, bg=BG, borderwidth=2, relief="groove")
        optionsFrame.grid(row=0, column=0, padx=10, pady=10)

        cutLabel = Label(optionsFrame, text="Cut Media:", font=("Helvetica",16), bg=BG)
        cutLabel.grid(row=0, column=1, columnspan=5, pady=3)

        # <----- CUT SLIDER FOR BOTH LOW-CUT AND HIGH-CUT----->
        cutSlider = Slider(optionsFrame, width = 400, height = 60, min_val = 0, max_val = downloadable.length, init_lis = [downloadable.lowCut, downloadable.highCut], show_value = True,
                             lowHMSVars=[self.previewCutLowVarH,  self.previewCutLowVarM,  self.previewCutLowVarS],
                             highHMSVars=[self.previewCutHighVarH,  self.previewCutHighVarM,  self.previewCutHighVarS])
        cutSlider.grid(column=1, columnspan=20, row=3)

        # <----- CUT TEXT INPUTS AND LABELS (H[____] M[____] S[____] --TO-- H[____] M[____] S[____]) ----->

        cutVarArgs = {  "lowH":self.previewCutLowVarH, 
                        "lowM":self.previewCutLowVarM,
                        "lowS":self.previewCutLowVarS,
                        "highH": self.previewCutHighVarH,
                        "highM":self.previewCutHighVarM,
                        "highS":self.previewCutHighVarS
                     }

        labelH = Label(optionsFrame, text="H", bg=BG)
        labelH.grid(row=1, column=1)
        lowH = Entry(optionsFrame, textvariable = self.previewCutLowVarH, width=5, bg="#DDFFAA", )
        lowH.grid(row=1, column=2, padx=2, pady=2)
        lowH.bind("<FocusOut>", lambda event, arg=cutVarArgs: cutSlider.moveBar(event, arg))
        
        labelM = Label(optionsFrame, text="M", bg=BG)
        labelM.grid(row=1, column=3)
        lowM = Entry(optionsFrame, textvariable = self.previewCutLowVarM, width=5, bg="#DDFFAA", )
        lowM.grid(row=1, column=4, padx=2, pady=2)
        lowM.bind("<FocusOut>", lambda event, arg=cutVarArgs: cutSlider.moveBar(event, arg))

        labelS = Label(optionsFrame, text="S", bg=BG)
        labelS.grid(row=1, column=5)
        lowS = Entry(optionsFrame, textvariable = self.previewCutLowVarS, width=5, bg="#DDFFAA", )
        lowS.grid(row=1, column=6, padx=2, pady=2)
        lowS.bind("<FocusOut>", lambda event, arg=cutVarArgs: cutSlider.moveBar(event, arg))

        labelTo = Label(optionsFrame, text="--TO--", bg=BG)
        labelTo.grid(row=1, column=7, padx=4, pady=2)

        labelH = Label(optionsFrame, text="H", bg=BG)
        labelH.grid(row=1, column=8)
        highH = Entry(optionsFrame, textvariable = self.previewCutHighVarH, width=5, bg="#DDFFAA", )
        highH.grid(row=1, column=9, padx=2, pady=2)
        highH.bind("<FocusOut>", lambda event, arg=cutVarArgs: cutSlider.moveBar(event, arg))

        labelM = Label(optionsFrame, text="M", bg=BG)
        labelM.grid(row=1, column=10)
        highM = Entry(optionsFrame, textvariable = self.previewCutHighVarM, width=5, bg="#DDFFAA", )
        highM.grid(row=1, column=11, padx=2, pady=2)
        highM.bind("<FocusOut>", lambda event, arg=cutVarArgs: cutSlider.moveBar(event, arg))

        labelS = Label(optionsFrame, text="S", bg=BG)
        labelS.grid(row=1, column=12)
        highS = Entry(optionsFrame, textvariable = self.previewCutHighVarS, width=5, bg="#DDFFAA", )
        highS.grid(row=1, column=13, padx=2, pady=2)
        highS.bind("<FocusOut>", lambda event, arg=cutVarArgs: cutSlider.moveBar(event, arg))

        cutRangeBtn = Button(optionsFrame, text="Make Cut",command= lambda:self.makeCut(downloadable, cutSlider), font=("Helvetica", 14), bg="#e9f9a9")
        cutRangeBtn.grid(column=1, columnspan=5, row=4, pady=5)

        if downloadable.cut:
            formattedInfo = self.formatCutInfo(downloadable.lowCut, downloadable.highCut, downloadable.length)
        else:
            formattedInfo = "Length: " + downloadable.getLengthString()

        urlInfo = Label(optionsFrame, text=formattedInfo, bg=BG)
        urlInfo.grid(row=4, column=6, columnspan=10)

        # Add metadata tags if downloading audio only
        # TODO: Add support for adding tags to .mp4

        metadataTagsFrame = Frame(mediaManipulationFrame, borderwidth=2, relief="groove", bg=BG)
        metadataTagsFrame.grid(row=0, column=1, padx=10, pady=2)

        metadataLabel = Label(metadataTagsFrame, text="Format ID3 Tags:", font=("Helvetica",16), bg=BG)
        metadataLabel.grid(row=0, column=1, pady=2)

        if downloadable.onlyAudio:
            urlTags = Frame(metadataTagsFrame, padx=5, pady=5, bg=BG)
            urlTags.grid(row=3, column=1, columnspan=10, padx=5, pady=5)

            urlTagsTitle = Label(urlTags, text="Tags: ", font=("Helvetica",14), bg=BG)
            urlTagsTitle.pack(side=LEFT)

            for tag in [*downloadable.tags]:       
                if downloadable.tags[tag] != "":                                  # Load any tags previously selected
                    tagDeleteFrame = Frame(urlTags, borderwidth=2, relief="groove", bg=BG)
                    tagDeleteFrame.pack(side=BOTTOM)
                    tagDeleteButton = Button(tagDeleteFrame, text="X",bg="#ff6655")
                    tagDeleteButton.pack(side=LEFT)
                    urlTagsTitle = Label(tagDeleteFrame, text=tag+" : "+downloadable.tags[tag], bg=BG)
                    urlTagsTitle.pack(side=LEFT)
                    downloadable.tagIds[tag] = tagDeleteFrame
                    downloadable.tagIds[tag+"Label"] = urlTagsTitle
                    data={"tagKey": tag, "tagValue": downloadable.tags[tag], 'downloadableKey':downloadable.displayName}
                    tagDeleteButton.bind("<Button-1>", lambda event, arg=data: self.deleteTag(event, arg))
                
            tagSelect = OptionMenu(metadataTagsFrame, self.tagVar, *ID3_TAG_OPTIONS)
            tagSelect.grid(row=1, column=1, columnspan=5,padx=3)
            tagSelect.config(width=40, bg="#DDFFAA")

            tagEntry = Entry(metadataTagsFrame, textvariable = self.tagChangeVar, width=40, bg="#DDFFAA")
            tagEntry.grid(row=2, column=1, columnspan=3, padx=10, pady=5)
            tagEntry.bind('<Button-1>', self.clearTagEntry)

            addTag = Button(metadataTagsFrame, text="Add Tag",command=lambda:self.addTag(downloadable.displayName), bg="#DDFFAA")
            addTag.grid(row=2, column=4, columnspan=1, padx=5, pady=5)

            downloadable.widgetIds["urlTags"] = urlTags

        self.volumeVar.set(downloadable.volumeMultiplier)

        volumeMultiplierFrame = Frame(mediaManipulationFrame, bg=BG, borderwidth=2, relief="groove")
        volumeMultiplierFrame.grid(row=0, column=3)

        volumeSliderLabel = Label(volumeMultiplierFrame, text="Volume\nAdjust",font=("Helvetica",16), bg=BG)
        volumeSliderLabel.grid(row=0, column=0)

        volumeSlider = Scale(volumeMultiplierFrame, variable=self.volumeVar, from_=100, to=-100, length=150, bg=BG, bd=0, highlightthickness=0, relief='ridge')
        volumeSlider.grid(row=1, column=0, padx=10, pady=10)
        volumeSlider.bind("<ButtonRelease-1>", lambda event, arg=downloadable: self.applyVolumeMultiplier(event, arg))

        volumeEntry = Entry(volumeMultiplierFrame, textvariable = self.volumeVar, width=5, bg="#DDFFAA", )
        volumeEntry.grid(row=1, column=1, padx=2, pady=2)
        volumeEntry.bind("<KeyRelease>", lambda event, arg=downloadable: self.applyVolumeMultiplier(event, arg))

        imgUrl = requestsGet(downloadable.youtubeObject.thumbnail_url)
        img = Image.open(BytesIO(imgUrl.content))
        img = img.resize((160,90))
        render = ImageTk.PhotoImage(img)
        imageLabel = Label(urlFrame, image=render, width=160, height=90, bg=BG)
        imageLabel.grid(row=0,rowspan=2,column=5)
        imageLabel.image = render


        videoPreviewButton = Button(mediaManipulationFrame, text="Preview Video" ,command=downloadable.previewClip, bg="#DDFFAA")
        videoPreviewButton.grid(row=2, column=0, columnspan=5, padx=5, pady=5)
    

        # Assign references to the widgets in preview frame to url dict entry                          
        downloadable.widgetIds["urlDelete"] = urlDelete
        downloadable.widgetIds["urlInfo"] = urlInfo
        downloadable.widgetIds["urlFrame"] = urlFrame
        self.previewDownloadableFrame = urlFrame
        self.previewDownloadable = downloadable.displayName

    def resetVolumeSlider(self):
        self.volumeVar.set(0)

    def applyVolumeMultiplier(self, event, downloadable):
        downloadable.volumeMultiplier = int(self.volumeVar.get())

    def deleteUrl(self, downloadableKey):
        downloadable = self.downloadables[downloadableKey]
        downloadable.widgetIds["urlFrame"].destroy()                                       
        self.previewDownloadable = None
        self.mylist.delete(self.mylist.curselection()[0])
        if downloadable.onlyAudio:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])-1))     
        else:
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])-1))   

        del self.downloadables[downloadableKey]

    def formatCutInfo(self, low, high, length):
        formattedInfo = ""
        formattedInfo += "Original Length: " + formatSeconds(length) +"\n"
        formattedInfo += "Cut Length: " + formatSeconds(high - low) + "\n"
        formattedInfo += "Cut Range: "+ formatSeconds(low) + " - " + formatSeconds(high)
        return formattedInfo

    # Handles cutting in URL preview frame after fetching
    # When user makes a cut on a song or video, calculate and save new range
    def makeCut(self, downloadable, slider):
        low, high = slider.getValues()
        low = int(low)
        high = int(high)
        if downloadable.changeCut(low, high):
            downloadable.widgetIds['urlInfo']['text'] = self.formatCutInfo(low, high, downloadable.length)
        else:
            downloadable.widgetIds['urlInfo']['text'] = "Length: " + formatSeconds(downloadable.length) +"\n"

    # Handle changing name 
    def changeName(self, downloadable, nameLabel):
        oldKey = downloadable.displayName
        newName = self.nameChangeVar.get()
        nameLabel.config(text=newName)
        self.mylist.delete(self.mylist.curselection()[0])
        downloadable.name = newName
        downloadable.displayName =  newName + " --- " + ("Audio" if downloadable.onlyAudio else "Video")
        self.downloadables[downloadable.displayName] = self.downloadables.pop(oldKey)
        self.previewDownloadable = downloadable.displayName

        # Update media tag at the end of URL in list view
        self.mylist.insert(END, downloadable.displayName) 
        self.mylist.selection_set('end') 


    def deleteAll(self):
        self.downloadables = {}
        self.mylist.delete('0', 'end')
        self.audioCountVar.set('Audio: 0')
        self.videoCountVar.set('Video: 0')
        if self.previewDownloadableFrame != None: 
            self.previewDownloadableFrame.destroy()
            self.previewDownloadable = None

    # Delete all fetched audio URLs
    def deleteAllMedia(self, mediaType):
        isAudio = True if mediaType == "audio" else False
        deleteList = []
        for downloadableKey, downloadable in self.downloadables.items():
            if not(downloadable.onlyAudio ^ isAudio):
                if downloadableKey == self.previewDownloadable:
                    downloadable.widgetIds["urlFrame"].destroy()    
                    downloadable.widgetIds                                    
                    if self.previewDownloadableFrame != None and self.downloadables[self.previewDownloadable].onlyAudio == isAudio: 
                        self.previewDownloadableFrame.destroy()
                        self.previewDownloadable = None
                if isAudio:
                    self.audioCountVar.set('Audio: 0')
                else:
                    self.videoCountVar.set('Video: 0') 
                downloadableKeysList = self.downloadableListVar.get()
                for index, dk in enumerate(downloadableKeysList):
                    if dk == downloadableKey:
                        self.mylist.delete(index)
                deleteList.append(downloadableKey)

        for dk in deleteList:
            del self.downloadables[dk]


    # Manually add a metadata tag
    def addTag(self, downloadableKey):
        self.clearTagEntryNextClick = True
        tagKey = self.tagVar.get()
        tagValue = self.tagChangeVar.get()

        downloadable = self.downloadables[downloadableKey]

        tagText = tagKey+" : "+tagValue

        if downloadable.tags[tagKey] == "":
        # Add new tag and event handlers
            tagDeleteFrame = Frame(downloadable.widgetIds["urlTags"], borderwidth=2, relief="groove", bg=BG)
            tagDeleteFrame.pack(side=BOTTOM)
            tagDeleteButton = Button(tagDeleteFrame, text="X",bg="#ff6655")
            tagDeleteButton.pack(side=LEFT)
            urlTagsTitle = Label(tagDeleteFrame, text=tagText, bg=BG)
            urlTagsTitle.pack(side=LEFT)
            downloadable.tagIds[tagKey] = tagDeleteFrame
            downloadable.tagIds[tagKey+"Label"] = urlTagsTitle
            data={"tagKey": tagKey, "tagValue": downloadable.tags[tagKey], 'downloadableKey':downloadable.displayName}
            tagDeleteButton.bind("<Button-1>", lambda event, arg=data: self.deleteTag(event, arg))

        else:
            downloadable.tagIds[tagKey+"Label"].config(text=tagText)
        self.update()
        downloadable.tags[tagKey] = tagValue
    
    # < ---------- On click event handlers ---------- >

    def deleteTag(self, ev, arg):
        downloadable = self.downloadables[arg["downloadableKey"]]
        ev.widget.destroy()
        downloadable.tags[arg["tagKey"]] = ""
        downloadable.tagIds[arg["tagKey"]].destroy()
        downloadable.tagIds[arg["tagKey"]] = None

    def clearSearchEntry(self, ev):
        self.searchEntry['bg'] = "white" 
        if self.clearSearchEntryNextClick:
            self.clearSearchEntryNextClick = False
            self.searchVar.set('')
    
    def clearTagEntry(self, ev):
        if self.clearTagEntryNextClick:
            self.clearTagEntryNextClick = False
            self.tagChangeVar.set('')

    # < ---------- On click event handlers ---------- >

    # Fetch entire playlist from single URL
    def addPlaylist(self, onlyAudio):
        inputPlaylist = self.searchVar.get()

        try:
            playlistUrls = pytube.Playlist(inputPlaylist).video_urls
        except KeyError:
            self.updateStatus("Failed to fetch playlist", "red")
            return

        # Some URLs may fail to load
        totalCount = str(len(playlistUrls))
        successCount = 0

        # If user specified a playlist range, check if it is valid, and if so, shorten [playlistUrls] accordingly
        if self.playlistRangeVar.get():
            try:
                if (int(self.playlistLowerRangeVar.get()) < 1) or (int(self.playlistUpperRangeVar.get())>len(playlistUrls)):
                    raise IndexError

                playlistUrls = playlistUrls[int(self.playlistLowerRangeVar.get())-1:int(self.playlistUpperRangeVar.get())]
            except IndexError:
                self.updateStatus("Playlist out of range (In playlist: " + str( len(playlistUrls) ) + ")", "red")
                return
            except (TypeError, ValueError):
                self.updateStatus("Invalid range (In playlist: " + str( len(playlistUrls) ) + ")", "red")
                return


        for url in playlistUrls:

            # Check if single URL of playlist is already in list
            downloadable = self.addUrl(onlyAudio, url)
            if downloadable == False:
                continue

            successCount+=1

            self.updateStatus("Succeeded: "+str(successCount) + "/" + str(len(playlistUrls)) +" : Total: "+totalCount, "blue")
        


        # When all URLs in playlist have been processed, 
        self.clearSearchEntryNextClick = True
        self.updateStatus('Done! : Succeeded: '+str(successCount)+" : Failed: "+str(int(totalCount)-successCount), "green")
        

    # Fetch a single URL
    def addSingle(self, onlyAudio):
        url = self.searchVar.get()
        self.updateStatus('Fetching video from YouTube...', "blue")
        if self.addUrl(onlyAudio, url) != False:
            self.updateStatus('Success!', "green")


    def addUrl(self, onlyAudio, url):

        urlFromQuery = False

        try:
            downloadable = Downloadable(url, onlyAudio)
        except Exception as e:
            print(e)
            if url=="" or url=="Enter a YouTube URL or Search Query":
                self.updateStatus("Enter a URL or Search Query", "red")
                return False
            else:
                try:
                    videosSearch = VideosSearch(url, limit = 1)
                    searchResultUrl = videosSearch.result()['result'][0]['link']
                    urlFromQuery = True
                    downloadable = Downloadable(searchResultUrl, onlyAudio)
                except:
                    self.updateStatus("Error fetching from YouTube", "red")
                    return False



        # If URL is already in list, flash the URL entry and notify the user

        urlRepeats = self.checkInDownloadables(downloadable)

        if (not self.allowRepeatsVar.get()) and urlRepeats > 0:

            if len(downloadable.name) < 25:
                statusString = downloadable.name
            else: 
                statusString = downloadable.name[:20] + "... "
            statusString += "(Audio)" if downloadable.onlyAudio else "(Video)"
            statusString += " is already in the list. Skipping"

            self.updateStatus(statusString, "orange")
            return False

        elif urlRepeats > 0:
            downloadable.name += f"({urlRepeats})"
            downloadable.displayName = downloadable.name + " --- " + ("Audio" if downloadable.onlyAudio else "Video")


        self.downloadables[downloadable.displayName] = downloadable

        # Count how many videos and songs are being downloaded and show in status frame

        if onlyAudio:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])+1))
        else:
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])+1))

        if self.addMdTagsVar.get():
            downloadable.generateTagListFromMetadata()
        
        if self.addTitleTagsVar.get():
            downloadable.generateTagListFromTitle()
        

        # Create text that represents URL in URL list
        self.mylist.insert(END, downloadable.displayName) 
        # Clear URL entry
        self.searchVar.set('')

        return downloadable


    def checkInDownloadables(self, downloadable):
        urlCount = 0
        for dlKey, dl in self.downloadables.items():
            if dl.url == downloadable.url and dl.onlyAudio == downloadable.onlyAudio:
                urlCount += 1
        return urlCount


    def updateStatus(self, message, color):
        self.statusVar.set(message)
        self.statusLabel['fg'] = color
        self.update()


    # Handles downloading of all contents in URL list
    def download(self):

        # Check if user entered any URLS
        if not len(self.downloadables):                                                                       
            self.updateStatus("No urls provided", "red")
            return

        directory = fd.askdirectory()

        # If exited out of directory chooser without picking location, warn user
        if not directory:                                                                               
            self.updateStatus("No directory chosen", "red")
            return
        
        self.updateStatus("Downloading...", "blue")

        # Download all added URLs, single and from playlist
        # TODO right now cut video doesnt get tags....

        for index, downloadable in enumerate(self.downloadables.values()):           

            # Update status frame                                                  
            self.updateStatus("Downloading...(" + str(index+1) + "/" + str( len(self.downloadables) ) + ")", "blue")       

            downloadable.download(directory)                                                                  
           

        # If option is set, clear every URL
        if self.deleteOnDownloadVar.get():
            self.deleteAll()

        # Notify user that download is complete
        self.updateStatus("Success! Downloaded into: " + directory, "green")
        
# Application entry-point
# Configure Tk object and start Tkinter loop
def main():
    root = Tk()
    try:
        root.state('zoomed') # windows
    except:
        root.attributes('-zoomed', True) # linux
    root['bg'] = BG
    root.geometry("1200x1200")
    root.title("YouTube Downloader")
    app = App(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()