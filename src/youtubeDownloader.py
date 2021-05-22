import os
import sys
import string
from tkinter import *
from tkinter import filedialog as fd
from tkinter import scrolledtext
from eyed3 import load as eyed3Load
from PIL import Image, ImageTk
from io import BytesIO
from requests import get as requestsGet
from Downloadable import Downloadable, stopPreview
from tkSliderWidget import Slider
from youtubesearchpython import VideosSearch
from urllib.error import HTTPError
import youtube_dl
import threading
import re

from helpers import formatSeconds, addLineBreaks, HMStoSeconds, makeEllipsis, breakLines, sanitizeFilename


BG="#ffffff"

COLOR_TOP_FRAME = "#9bafcc"
COLOR_OPTIONS_FRAME = "#d1d7e0"
COLOR_OPTIONS_ENTRY = "#edf3fc"
COLOR_OPTIONS_OPTION = "#dfdcf0"

COLOR_LOWER_FRAME = "#9bafcc"
COLOR_MANIP_FRAME = "#d1d7e0"
COLOR_MANIP_ENTRY = "#edf3fc"
COLOR_MANIP_BUTTON = "#afcce0"

COLOR_DELETE = "#feaeae"
COLOR_DISABLED = "#dddddd"
COLOR_DOWNLOAD = "#90be6d"
COLOR_FETCH = "#f9c74f"

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
        self.downloadedCount = 0

        self.fetchLock = False
        self.downloadLock = False

        self.tryAgainButton = None

        # textvariable for url entry
        self.searchVar = StringVar()                                                                                  
        self.searchVar.set("Enter a YouTube URL or Search Query")

        self.onlyAudioVar = BooleanVar()
        self.onlyAudioVar.set(False)
        
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

        self.previewLabelVar = StringVar()
        self.previewLabelVar.set("Playing:\n")

        # text variable for holding application status (ALL user notifications pop up here)
        self.statusVar = StringVar()
        self.statusVar.set('')

        # textvariable for dropdown list of songs
        self.tagChangeVar = StringVar()                                                                            
        self.tagChangeVar.set('Enter tag descriptor')

        # textvariable for holding currently selected metadata tag
        self.tagVar = StringVar()                                                                                   
        self.tagVar.set(ID3_TAG_OPTIONS[0])

        self.resolutionVar = StringVar()

        # integer variable for volume slider
        self.volumeVar = IntVar()
        self.volumeVar.set(1)

        # boolvariables for checkbox options
        self.deleteOnDownloadVar = BooleanVar()
        self.deleteOnDownloadVar.set(False)

        self.allowRepeatsVar = BooleanVar()
        self.allowRepeatsVar.set(True)

        self.triesVar = IntVar()
        self.triesVar.set(3)

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
        self.cutLowerVarH.set('0')
        self.cutLowerVarM = StringVar()
        self.cutLowerVarM.set('0')
        self.cutLowerVarS = StringVar()
        self.cutLowerVarS.set('0')

        self.cutUpperVarH = StringVar()
        self.cutUpperVarH.set('0')
        self.cutUpperVarM = StringVar()
        self.cutUpperVarM.set('0')
        self.cutUpperVarS = StringVar()
        self.cutUpperVarS.set('0')

        self.previewCutLowVarH = StringVar()
        self.previewCutLowVarH.set('0')
        self.previewCutLowVarM = StringVar()
        self.previewCutLowVarM.set('0')
        self.previewCutLowVarS = StringVar()
        self.previewCutLowVarS.set('0')

        self.previewCutHighVarH = StringVar()
        self.previewCutHighVarH.set('0')
        self.previewCutHighVarM = StringVar()
        self.previewCutHighVarM.set('0')
        self.previewCutHighVarS = StringVar()
        self.previewCutHighVarS.set('0')

        self.addCutAsNewSongVar = StringVar()
        self.addCutAsNewSongVar.set("Name of Copy")

        self.specificOnlyAudioVar = BooleanVar()
        self.specificOnlyAudioVar.set(False)
 

        self.clearSearchEntryNextClick = True
        self.clearTagEntryNextClick = True

        # holds URL and data for currently selected video/song
        self.previewDownloadableFrame = None
        self.previewDownloadable = None
        
        self.createWidgets()


    def createWidgets(self): 

        # Top frame widgets for adding Downloadables, downloading and other options
        self.controlFrame = Frame(self, padx=10, pady=10, bg=COLOR_TOP_FRAME, borderwidth=2, relief="groove", width=80)
        self.controlFrame.pack(expand=True, padx=5, pady=5)

        self.searchEntry = Entry(self.controlFrame, textvariable = self.searchVar,font=FONT_MD, width=60, bg=COLOR_OPTIONS_ENTRY)
        self.searchEntry.grid(row=1, column=0, columnspan=10, padx=5, pady=5)
        self.searchEntry.bind("<Button-1>",self.clearSearchEntry)
        self.searchEntry.bind("<Return>", self.handleFetchEvent)   

        self.fetchOnlyAudioCheckbox = Checkbutton(self.controlFrame, text="Only\nAudio", variable=self.onlyAudioVar, bg=COLOR_OPTIONS_FRAME, borderwidth=1, relief="groove")
        self.fetchOnlyAudioCheckbox.grid(row=1, rowspan=2, column=10)     

        self.fetchButton = Button(self.controlFrame, text="Add", command= lambda : self.fetch(), bg=COLOR_FETCH,width=10, font=FONT_MD)
        self.fetchButton.grid(row=1, column=11, padx=5, pady=5)

        # Top right frame for controlling playlist range to be retrieved
        self.optionsFrame = Frame(self.controlFrame, padx=5, pady=5, bg=COLOR_OPTIONS_FRAME, borderwidth=2, relief="groove")
        self.optionsFrame.grid(padx=5, pady=5, row=3, rowspan=10, column=0, columnspan=12)

        self.playlistRangeFrame = Frame(self.optionsFrame, bg=COLOR_OPTIONS_OPTION, borderwidth=1, relief="groove")
        self.playlistRangeFrame.grid(column=1, row=0)

        self.playlistRangeCheckbox = Checkbutton(self.playlistRangeFrame, text="Playlist range", variable=self.playlistRangeVar, bg=COLOR_OPTIONS_OPTION)
        self.playlistRangeCheckbox.grid(column=0, columnspan=6, row=1)

        self.playlistLowerRange = Entry(self.playlistRangeFrame, textvariable=self.playlistLowerRangeVar, width=4, bg=COLOR_OPTIONS_ENTRY)
        self.playlistLowerRange.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        self.playlistRangeDashLabel = Label(self.playlistRangeFrame, text="-", bg=COLOR_OPTIONS_OPTION)
        self.playlistRangeDashLabel.grid(row=2, column=2, columnspan = 2)

        self.playlistUpperRange = Entry(self.playlistRangeFrame, textvariable=self.playlistUpperRangeVar, width=4, bg=COLOR_OPTIONS_ENTRY)
        self.playlistUpperRange.grid(row=2, column=4, columnspan=2, padx=5, pady=5)

        self.allowRepeatsCheckbox = Checkbutton(self.optionsFrame, text="Allow Repeats", variable=self.allowRepeatsVar,bg=COLOR_OPTIONS_OPTION, borderwidth=1, relief="groove")
        self.allowRepeatsCheckbox.grid(column=2, row=0, padx=10, pady=10)

        self.keepTryingFrame = Frame(self.optionsFrame, bg=COLOR_OPTIONS_OPTION, borderwidth=1, relief="groove")
        self.keepTryingFrame.grid(row=0, column=3, padx=5, pady=5)

        self.keepTryingLabel =Label(self.keepTryingFrame, text="Attempts to Fetch\nFrom YouTube\nBefore Skipping", bg=COLOR_OPTIONS_OPTION)
        self.keepTryingLabel.pack(side=LEFT)

        self.keepTryingEntry = Entry(self.keepTryingFrame, textvariable = self.triesVar, width=5, validate="key", validatecommand=self.vcmdInt, bg=COLOR_OPTIONS_ENTRY)
        self.keepTryingEntry.pack(side=LEFT, padx=5, pady=5)
        self.keepTryingEntry.bind("<FocusOut>", self.applyTries)

        self.middleFrame = Frame(self, bg=BG)
        self.middleFrame.pack(expand=True)

        # Frame below URL input, displays status of URL retrieval success, errors, and download progress
        self.statusFrame = Frame(self.middleFrame, padx=5, pady=5,bg=COLOR_MANIP_ENTRY, borderwidth=2, relief="groove", width=80)
        self.statusFrame.pack(side=LEFT)

        self.audioCountLabel = Label(self.statusFrame, textvariable = self.audioCountVar, padx=10,font=FONT_MD, bg=COLOR_MANIP_ENTRY)
        self.audioCountLabel.grid(column=0, row=1)

        self.videoCountLabel = Label(self.statusFrame, textvariable = self.videoCountVar, padx=10,font=FONT_MD, bg=COLOR_MANIP_ENTRY)
        self.videoCountLabel.grid(column=1, row=1)

        self.statusLabel = Label(self.statusFrame, textvariable = self.statusVar, padx=10, font=FONT_LG, bg=COLOR_MANIP_ENTRY)
        self.statusLabel.grid(column=0,columnspan=2, row=2)

        self.deleteAllAudioBtn = Button(self.statusFrame, text="Delete All Audio", command=lambda:self.deleteAllMedia("audio"), bg=COLOR_DELETE)
        self.deleteAllAudioBtn.grid(column=0, columnspan=3, row=3, pady=2)

        self.deleteAllVideoBtn = Button(self.statusFrame, text="Delete All Video", command=lambda:self.deleteAllMedia("video"), bg=COLOR_DELETE)
        self.deleteAllVideoBtn.grid(column=0, columnspan=3, row=4, pady=2)

        # Middle frame/scrollbox for holding URLs retrieved and ready to be customized or downloaded

        self.downloadablesListFrame = Frame(self.middleFrame, padx=5, pady=10, bg="#ffffff")
        self.downloadablesListFrame.pack(side=LEFT)

        self.scrollFrame = Frame(self.downloadablesListFrame, padx=5, pady=10, bg="#ffffff")
        self.scrollFrame.grid(column=1, row=2, columnspan=10)

        self.scroll_barY = Scrollbar(self.scrollFrame) 
        self.scroll_barY.pack(side=RIGHT, fill=Y) 

        self.scroll_barX = Scrollbar(self.scrollFrame, orient=HORIZONTAL) 
        self.scroll_barX.pack(side=BOTTOM, fill=X) 

        self.mylist = Listbox(self.scrollFrame, yscrollcommand=self.scroll_barY.set, xscrollcommand=self.scroll_barX.set, width= 70, listvariable=self.downloadableListVar, exportselection=False, bg=COLOR_MANIP_ENTRY) 
        self.mylist.pack( side = LEFT, fill = BOTH ) 
        self.mylist.bind("<<ListboxSelect>>", self.showDownloadable)

        self.scroll_barY.config( command = self.mylist.yview ) 
        self.scroll_barX.config( command = self.mylist.xview ) 

        self.previewFrame = Frame(self, padx=10, pady=10, bg=COLOR_LOWER_FRAME)
        self.previewFrame.pack()

        # Start Download Frame
        self.startDownloadFrame = Frame(self.middleFrame, borderwidth=2, relief="groove", width=25, bg=COLOR_MANIP_ENTRY)
        self.startDownloadFrame.pack(side=LEFT)

        self.startDownloadButton = Button(self.startDownloadFrame, text="Start\nDownload", command=self.download, bg=COLOR_DOWNLOAD,width=10, font=FONT_MD)
        self.startDownloadButton.grid( row=2, rowspan=4, column=10, columnspan=2, padx=5, pady=5)

        self.deleteOnDownloadCheckbutton = Checkbutton(self.startDownloadFrame, text="Clear List\nAfter Downloading", variable=self.deleteOnDownloadVar, bg=COLOR_MANIP_ENTRY, highlightthickness=0)
        self.deleteOnDownloadCheckbutton.grid(row=6, rowspan=2, column=10, columnspan=2, padx=5, pady=5)


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
            newTries = 1
        if newTries < 1:
            newTries = 1
        self.triesVar.set(newTries)

    # Shows all data retrieved from youtube and options to customize before downloading
    # Loads into preview frame (bottom frame)
    # Binds to 'self.mylist'
    def showDownloadable(self, ev):                                                             

         # Destroy currently in preview frame to show currently selecte done
        if self.previewDownloadableFrame != None:                                               
            self.previewDownloadableFrame.destroy()
            self.previewDownloadable = None

        # Get downloadable display name from listbox

        try:
            downloadableKey = self.mylist.get(self.mylist.curselection()[0])
        except IndexError:
            return
        
        self.downloadable = self.downloadables[downloadableKey]
                       
        # Reset entry variables
        self.nameChangeVar.set(self.downloadable.name)
        self.tagChangeVar.set('')


        self.downloadableFrame = Frame(self.previewFrame, padx=5, pady=5, bg=COLOR_LOWER_FRAME, borderwidth=2, relief="groove")                             
        self.downloadableFrame.pack(expand=True)

        self.downloadableNameLabel = Label(self.downloadableFrame, text=makeEllipsis(self.downloadable.name, 50), bg=COLOR_LOWER_FRAME, font=FONT_XL)                                                      
        self.downloadableNameLabel.grid(row=0, column=0, columnspan=3)

        deleteDownloadableButton = Button(self.downloadableFrame, text="Delete",command=self.deleteDownloadable, bg=COLOR_DELETE)
        deleteDownloadableButton.grid(row=0, column=6)

        self.specificOnlyAudioVar.set(self.downloadable.onlyAudio)
        setOnlyAudioCheckbox = Checkbutton(self.downloadableFrame, text="Only\nAudio", variable=self.specificOnlyAudioVar, bg=COLOR_MANIP_ENTRY, command=self.changeMediaType, borderwidth=2, relief="groove")
        setOnlyAudioCheckbox.grid(row=1, column=6)

        downloadableNameChangeEntry = Entry(self.downloadableFrame, textvariable = self.nameChangeVar, width=50, bg=COLOR_MANIP_ENTRY, font=("Helvetica", 16))
        downloadableNameChangeEntry.grid(row=1, column=1, columnspan=2)

        downloadableChangeNameButton = Button(self.downloadableFrame,text="Change Name", command=self.changeName, bg=COLOR_MANIP_BUTTON, height=2)
        downloadableChangeNameButton.grid(row=1, column=3, columnspan=1, padx=5)

        mediaManipulationFrame = Frame(self.downloadableFrame, bg=COLOR_LOWER_FRAME)
        mediaManipulationFrame.grid(row=4,column=0,columnspan=20)

        cutFrame = Frame(self.downloadableFrame, bg=COLOR_LOWER_FRAME, borderwidth=2, relief="groove")
        cutFrame.grid(row=3, column=1)

        optionsFrame = Frame(mediaManipulationFrame, padx=5, pady=5, bg=COLOR_MANIP_FRAME, borderwidth=2, relief="groove")
        optionsFrame.grid(row=0, column=0, padx=10, pady=10)

        cutLabel = Label(optionsFrame, text="Cut Media:", font=("Helvetica",16), bg=COLOR_MANIP_FRAME)
        cutLabel.grid(row=0, column=1, columnspan=5, pady=3)



        # <----- CUT SLIDER FOR BOTH LOW-CUT AND HIGH-CUT----->
        self.cutSlider = Slider(optionsFrame, width = 400, height = 60, min_val = 0, max_val = self.downloadable.length, init_lis = [self.downloadable.lowCut, self.downloadable.highCut], show_value = True, bg_color=COLOR_MANIP_FRAME,
                             lowHMSVars=[self.previewCutLowVarH,  self.previewCutLowVarM,  self.previewCutLowVarS],
                             highHMSVars=[self.previewCutHighVarH,  self.previewCutHighVarM,  self.previewCutHighVarS])
        self.cutSlider.grid(column=1, columnspan=20, row=3)
        self.cutSlider.bind("<ButtonRelease-1>", self.makeCut)

        

        # <----- CUT TEXT INPUTS AND LABELS (H[____] M[____] S[____] --TO-- H[____] M[____] S[____]) ----->


        labelH = Label(optionsFrame, text="H", bg=COLOR_MANIP_FRAME)
        labelH.grid(row=1, column=1)
        lowH = Entry(optionsFrame, textvariable = self.previewCutLowVarH, width=5, bg=COLOR_MANIP_ENTRY)
        lowH.grid(row=1, column=2, padx=2, pady=2)
        lowH.bind("<FocusOut>", self.handleCutEntry)
        lowH.bind("<Return>", self.handleCutEntry)
        
        labelM = Label(optionsFrame, text="M", bg=COLOR_MANIP_FRAME)
        labelM.grid(row=1, column=3)
        lowM = Entry(optionsFrame, textvariable = self.previewCutLowVarM, width=5, bg=COLOR_MANIP_ENTRY)
        lowM.grid(row=1, column=4, padx=2, pady=2)
        lowH.bind("<FocusOut>", self.handleCutEntry)
        lowM.bind("<Return>", self.handleCutEntry)

        labelS = Label(optionsFrame, text="S", bg=COLOR_MANIP_FRAME)
        labelS.grid(row=1, column=5)
        lowS = Entry(optionsFrame, textvariable = self.previewCutLowVarS, width=5, bg=COLOR_MANIP_ENTRY)
        lowS.grid(row=1, column=6, padx=2, pady=2)
        lowS.bind("<FocusOut>", self.handleCutEntry)
        lowS.bind("<Return>", self.handleCutEntry)

        labelTo = Label(optionsFrame, text="--TO--", bg=COLOR_MANIP_FRAME)
        labelTo.grid(row=1, column=7, padx=4, pady=2)

        labelH = Label(optionsFrame, text="H", bg=COLOR_MANIP_FRAME)
        labelH.grid(row=1, column=8)
        highH = Entry(optionsFrame, textvariable = self.previewCutHighVarH, width=5, bg=COLOR_MANIP_ENTRY)
        highH.grid(row=1, column=9, padx=2, pady=2)
        highH.bind("<FocusOut>", self.handleCutEntry)
        highH.bind("<Return>", self.handleCutEntry)

        labelM = Label(optionsFrame, text="M", bg=COLOR_MANIP_FRAME)
        labelM.grid(row=1, column=10)
        highM = Entry(optionsFrame, textvariable = self.previewCutHighVarM, width=5, bg=COLOR_MANIP_ENTRY)
        highM.grid(row=1, column=11, padx=2, pady=2)
        highM.bind("<FocusOut>", self.handleCutEntry)
        highM.bind("<Return>", self.handleCutEntry)

        labelS = Label(optionsFrame, text="S", bg=COLOR_MANIP_FRAME)
        labelS.grid(row=1, column=12)
        highS = Entry(optionsFrame, textvariable = self.previewCutHighVarS, width=5, bg=COLOR_MANIP_ENTRY)
        highS.grid(row=1, column=13, padx=2, pady=2)
        highS.bind("<FocusOut>", self.handleCutEntry)
        highS.bind("<Return>", self.handleCutEntry)

        if self.downloadable.cut:
            formattedCutInfo = self.formatCutInfo(self.downloadable.lowCut, self.downloadable.highCut, self.downloadable.length)
        else:
            formattedCutInfo = "Length: " + self.downloadable.getLengthString()

        self.cutInfo = Label(optionsFrame, text=formattedCutInfo, bg=COLOR_MANIP_FRAME)
        self.cutInfo.grid(row=4, column=6, columnspan=10, pady=5, padx=5)

        addCutAsNewSongEntry = Entry(optionsFrame, textvariable=self.addCutAsNewSongVar, bg=COLOR_MANIP_ENTRY)
        addCutAsNewSongEntry.grid(row=4, column=1, columnspan=6)
        addCutAsNewSongEntry.bind("<Button-1>", self.clearAddCutAsNewSongEntry)

        addCutAsNewSongButton = Button(optionsFrame, text="Copy Cut", font=FONT_MD, command=self.addCutAsNewSong)
        addCutAsNewSongButton.grid(row=5, column=1, columnspan=6)

        # Add metadata tags if downloading audio only
        # TODO: Add support for adding tags to .mp4
        
        if self.downloadable.onlyAudio:

            metadataTagsFrame = Frame(mediaManipulationFrame, borderwidth=2, relief="groove", bg=COLOR_MANIP_FRAME)
            metadataTagsFrame.grid(row=0, column=1, padx=10, pady=2)

            metadataLabel = Label(metadataTagsFrame, text="Format ID3 Tags:", font=("Helvetica",16), bg=COLOR_MANIP_FRAME)
            metadataLabel.grid(row=0, column=1, pady=2)


            self.tagsFrame = Frame(metadataTagsFrame, padx=5, pady=5, bg=COLOR_MANIP_FRAME)
            self.tagsFrame.grid(row=3, column=1, columnspan=10, padx=5, pady=5)

            tagsTitle = Label(self.tagsFrame, text="Tags: ", font=("Helvetica",14), bg=COLOR_MANIP_FRAME)
            tagsTitle.pack(side=LEFT)

            for tagKey in [*self.downloadable.tags]:       
                if self.downloadable.tags[tagKey] != "":                                  # Load any tags previously selected
                    tagDeleteFrame = Frame(self.tagsFrame, borderwidth=2, relief="groove", bg=COLOR_MANIP_FRAME)
                    tagDeleteFrame.pack(side=BOTTOM)
                    tagDeleteButton = Button(tagDeleteFrame, text="X",bg=COLOR_DELETE)
                    tagDeleteButton.pack(side=LEFT)
                    tagsTitle = Label(tagDeleteFrame, text=tagKey+" : ", font=("Helvetica", 10, "bold"), bg=COLOR_MANIP_FRAME)
                    tagsTitle.pack(side=LEFT)
                    tagsValue = Label(tagDeleteFrame, text=self.downloadable.tags[tagKey], bg=COLOR_MANIP_FRAME)
                    tagsValue.pack(side=LEFT)
                    self.downloadable.tagIds[tagKey] = tagDeleteFrame
                    self.downloadable.tagIds[tagKey+"Label"] = tagsTitle
                    tagDeleteButton.bind("<Button-1>", lambda event, arg=tagKey: self.deleteTag(event, arg))
                
            tagSelect = OptionMenu(metadataTagsFrame, self.tagVar, *ID3_TAG_OPTIONS)
            tagSelect.grid(row=1, column=1, columnspan=5,padx=3)
            tagSelect.config(width=40, bg=COLOR_MANIP_ENTRY)

            tagEntry = Entry(metadataTagsFrame, textvariable = self.tagChangeVar, width=40, bg=COLOR_MANIP_ENTRY)
            tagEntry.grid(row=2, column=1, columnspan=3, padx=10, pady=5)
            tagEntry.bind('<Button-1>', self.clearTagEntry)

            addTag = Button(metadataTagsFrame, text="Add Tag",command=self.addTag, bg=COLOR_MANIP_ENTRY)
            addTag.grid(row=2, column=4, columnspan=1, padx=5, pady=5)

        else:
            videoManipulationFrame = Frame(mediaManipulationFrame, borderwidth=2, relief="groove", bg=COLOR_MANIP_FRAME)
            videoManipulationFrame.grid(row=0, column=1, padx=10, pady=2)

            videoManipulationLabel = Label(videoManipulationFrame, text="MP4 Resolution:", font=("Helvetica",16), bg=COLOR_MANIP_FRAME)
            videoManipulationLabel.grid(row=0, column=1, pady=2)
            
            self.resolutionVar.set(self.downloadable.stream.resolution)

            try:
                self.resolutionVar.v_delete("w", self.resolutionVar.trace_id)
            except:
                pass

            self.resolutionVar.trace_id = self.resolutionVar.trace("w", lambda *args:self.downloadable.setStreamByResolution(self.resolutionVar))

            resolutionSelect = OptionMenu(videoManipulationFrame, self.resolutionVar, *list(self.downloadable.resolutionToStream.keys()))
            resolutionSelect.grid(row=1, column=1, columnspan=5,padx=3, pady=5)
            resolutionSelect.config(bg=COLOR_MANIP_ENTRY)




        self.volumeVar.set(self.downloadable.volumeMultiplier)

        volumeMultiplierFrame = Frame(mediaManipulationFrame, bg=COLOR_MANIP_FRAME, borderwidth=2, relief="groove")
        volumeMultiplierFrame.grid(row=0, column=3)

        volumeSliderLabel = Label(volumeMultiplierFrame, text="Volume Adjust:",font=("Helvetica",16), bg=COLOR_MANIP_FRAME)
        volumeSliderLabel.grid(row=0, column=0)

        volumeSlider = Scale(volumeMultiplierFrame, variable=self.volumeVar, from_=100, to=-100, length=150, bg=COLOR_MANIP_FRAME, bd=0, highlightthickness=0, relief='ridge')
        volumeSlider.grid(row=2, column=0, padx=3, pady=3)
        volumeSlider.bind("<ButtonRelease-1>",  self.applyVolumeMultiplier)

        volumeEntry = Entry(volumeMultiplierFrame, width=4, textvariable = self.volumeVar, bg=COLOR_MANIP_ENTRY)
        volumeEntry.grid(row=1, column=0, padx=2, pady=2)
        volumeEntry.bind("<KeyRelease>", self.applyVolumeMultiplier)


        if self.downloadable.imgUrl == None:
            self.downloadable.imgUrl = requestsGet(self.downloadable.youtubeObject.thumbnail_url)
            
        img = Image.open(BytesIO(requestsGet(self.downloadable.imgUrl).content))
        img = img.resize((160,90))
        render = ImageTk.PhotoImage(img)
        imageLabel = Label(self.downloadableFrame, image=render, width=160, height=90, bg=COLOR_LOWER_FRAME)
        imageLabel.grid(row=0,rowspan=2,column=5)
        imageLabel.image = render

        previewControlFrame= Frame(mediaManipulationFrame, bg=COLOR_LOWER_FRAME, borderwidth=1, relief="groove")
        previewControlFrame.grid(row=2, column=0, padx=5, pady=5)

        videoPreviewButton = Button(previewControlFrame, text="Preview "+("Audio" if self.downloadable.onlyAudio else "Video") ,command=self.previewClip, bg=COLOR_MANIP_BUTTON)
        videoPreviewButton.grid(row=0, column=0, padx=5, pady=5)

        self.previewLabel = Label(previewControlFrame, textvariable=self.previewLabelVar, bg=COLOR_LOWER_FRAME)
        self.previewLabel.grid(row=0, column=1, padx=3, pady=3)

        stopPreviewButton = Button(previewControlFrame, text="Stop Preview", command=self.stopPreview, bg=COLOR_MANIP_BUTTON)
        stopPreviewButton.grid(row=0, column=2, padx=5, pady=5)

        showMetadataButton = Button(mediaManipulationFrame, text="Show Metadata", command=self.showMetadata, bg=COLOR_MANIP_BUTTON)
        showMetadataButton.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

        # Assign references to the widgets in preview frame to url dict entry                          
        self.previewDownloadableFrame = self.downloadableFrame
        self.previewDownloadable = self.downloadable.displayName


    def previewClip(self):
        self.previewLabelVar.set("Loading...\n")
        self.update()
        self.downloadable.previewClip(self.previewLabelVar)
        Downloadable.previewDownloadable = self.downloadable
        self.previewLabelVar.set("Playing:\n"+makeEllipsis(Downloadable.previewDownloadable.name,20))


    def stopPreview(self):
        stopPreview()
        Downloadable.previewDownloadable = None
        self.previewLabelVar.set("Playing:\n")


    def showMetadata(self):
        metadataWindow = Toplevel(self.master)
        metadataWindow.title("YouTube Metadata")
        metadataWindow.geometry("400x400")

        text_area = scrolledtext.ScrolledText(metadataWindow, wrap=WORD, font=FONT_SM)

        formattedMetadata = ""

        for k,v in self.downloadable.youtubeObject.items():
            if k in ["requested_formats", "formats", "thumbnails"]:
                continue
            formattedMetadata += "<------------------------------------------------------------>\n" 

            formattedMetadata += k + ":\n " + str(v) + "\n\n"

        text_area.insert(INSERT,formattedMetadata)
        text_area.pack()


    def changeMediaType(self):
        onlyAudio = self.specificOnlyAudioVar.get()

        oldKey = self.downloadable.displayName

        newKey = self.downloadable.name + " --- " + ("Audio" if onlyAudio else "Video")

        if newKey in self.downloadables.keys():
            self.specificOnlyAudioVar.set(not onlyAudio)
            return

        self.downloadable.setOnlyAudio(onlyAudio)
        self.downloadableFrame.destroy()       

        self.mylist.delete(self.mylist.curselection()[0])
        self.downloadables[self.downloadable.displayName] = self.downloadables.pop(oldKey)
        self.previewDownloadable = self.downloadable.displayName

        self.mylist.insert(END, self.downloadable.displayName) 
        self.mylist.selection_set(END) 

        if onlyAudio:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])+1))
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])-1))
        else:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])-1))
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])+1))

        self.showDownloadable(None)


    def clearAddCutAsNewSongEntry(self, ev):
        self.addCutAsNewSongVar.set("")

    def addCutAsNewSong(self):
        newName = self.addCutAsNewSongVar.get()
        newDisplayName = newName + " --- " + ("Audio" if self.downloadable.onlyAudio else "Video")
        if newDisplayName in self.downloadables.keys():
            self.addCutAsNewSongVar.set("Name Taken")
            return
        if newName in ["", "Name of Copy", "Enter a Name", "Name Taken"]:
            self.addCutAsNewSongVar.set("Enter a Name")
            return

        newDownloadable = Downloadable(self.downloadable.youtubeObject, self.downloadable.onlyAudio)
        newDownloadable.name = newName
        newDownloadable.displayName = newDisplayName
        newDownloadable.changeCut(self.downloadable.lowCut, self.downloadable.highCut)
        self.downloadables[newDisplayName] = newDownloadable
        self.mylist.insert(END, newDisplayName) 
        if self.downloadable.onlyAudio:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])+1))
        else:
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])+1))
        self.addCutAsNewSongVar.set("")
        

    def handleCutEntry(self, ev):
        self.cutSlider.moveBar()


    def applyVolumeMultiplier(self, event):
        self.downloadable.volumeMultiplier = int(self.volumeVar.get())


    def deleteDownloadable(self):
        downloadableKey = self.downloadable.displayName
        self.downloadableFrame.destroy()                                       
        self.previewDownloadable = None
        self.mylist.delete(self.mylist.curselection()[0])
        if self.downloadable.onlyAudio:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])-1))     
        else:
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])-1))   

        del self.downloadables[downloadableKey]

        self.setDefaultListSelection()


    def formatCutInfo(self, low, high, length):
        formattedInfo = ""
        formattedInfo += "Original Length: " + formatSeconds(length) +"\n"
        formattedInfo += "Cut Length: " + formatSeconds(high - low) + "\n"
        formattedInfo += "Cut Range: "+ formatSeconds(low) + " - " + formatSeconds(high)
        return formattedInfo


    # Handles cutting in URL preview frame after fetching
    # When user makes a cut on a song or video, calculate and save new range
    def makeCut(self, event):
        low, high = self.cutSlider.getValues()
        low = int(low)
        high = int(high)
        if self.downloadable.changeCut(low, high):
            self.cutInfo['text'] = self.formatCutInfo(low, high, self.downloadable.length)
        else:
            self.cutInfo['text'] = "Length: " + formatSeconds(self.downloadable.length) +"\n"

    # Handle changing name 
    def changeName(self):
        oldKey = self.downloadable.displayName
        newName = self.nameChangeVar.get()
        newDisplayName = newName + " --- " + ("Audio" if self.downloadable.onlyAudio else "Video")
        if newDisplayName in self.downloadables.keys():
            self.nameChangeVar.set("Name Taken")
            return

        self.downloadableNameLabel.config(text=makeEllipsis(newName,50))
        self.mylist.delete(self.mylist.curselection()[0])
        self.downloadable.name = newName
        self.downloadable.displayName =  newDisplayName
        self.downloadables[self.downloadable.displayName] = self.downloadables.pop(oldKey)
        self.previewDownloadable = self.downloadable.displayName

        # Update media tag at the end of URL in list view
        self.mylist.insert(END, self.downloadable.displayName) 
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
                    self.downloadableFrame.destroy()                                     
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

        self.setDefaultListSelection()


    # Manually add a metadata tag
    def addTag(self):
        self.clearTagEntryNextClick = True
        tagKey = self.tagVar.get()
        tagValue = self.tagChangeVar.get()
        if tagValue in ["","Enter a Tag"]:
            self.tagChangeVar.set("Enter a Tag")
            return

        tagText = tagKey+" : "+tagValue

        if self.downloadable.tags[tagKey] == "":
        # Add new tag and event handlers
            tagDeleteFrame = Frame(self.tagsFrame, borderwidth=2, relief="groove", bg=COLOR_MANIP_FRAME)
            tagDeleteFrame.pack(side=BOTTOM)
            tagDeleteButton = Button(tagDeleteFrame, text="X",bg=COLOR_DELETE)
            tagDeleteButton.pack(side=LEFT)
            tagsTitle = Label(tagDeleteFrame, text=tagText, bg=COLOR_MANIP_FRAME)
            tagsTitle.pack(side=LEFT)
            self.downloadable.tagIds[tagKey] = tagDeleteFrame
            self.downloadable.tagIds[tagKey+"Label"] = tagsTitle
            tagDeleteButton.bind("<Button-1>", lambda event, arg=tagKey: self.deleteTag(event, arg))

        else:
            self.downloadable.tagIds[tagKey+"Label"].config(text=tagText)
        self.update()
        self.downloadable.tags[tagKey] = tagValue
    


    def deleteTag(self, ev, tagKey):
        ev.widget.destroy()
        self.downloadable.tags[tagKey] = ""
        self.downloadable.tagIds[tagKey].destroy()
        self.downloadable.tagIds[tagKey] = None

    def clearSearchEntry(self, ev):
        if self.clearSearchEntryNextClick:
            self.clearSearchEntryNextClick = False
            self.searchVar.set('')
    
    def clearTagEntry(self, ev):
        if self.clearTagEntryNextClick:
            self.clearTagEntryNextClick = False
            self.tagChangeVar.set('')
        

    def handleFetchEvent(self, event):
        self.fetch()


    def fetch(self):

        userInput = self.searchVar.get()
        onlyAudio = self.onlyAudioVar.get()

        if userInput=="" or userInput=="Enter a YouTube URL or Search Query":
            self.updateStatus("Enter a URL or Search Query", "red")
            return False

        if self.fetchLock:
            print("Can't fetch because currently fetching")
            return
        self.setLocked(True)

        self.updateStatus("Fetching...", "blue")
        threading.Thread(target = self.fetchThreaded, args=(userInput, onlyAudio)).start()


    def fetchThreaded(self, userInput, onlyAudio):
        youtubeObjects = self.getYoutubeObjects(userInput)
        if len(youtubeObjects) < 1:
            self.updateStatus("Failed to Add\n" + makeEllipsis(userInput,25), "red")
        else: 
            for ytObj in youtubeObjects:
                newDownloadable = Downloadable(ytObj, onlyAudio)
                self.addSingleUrl(newDownloadable)

        self.setLocked(False)


    def addSingleUrl(self, downloadable):
        onlyAudio = self.onlyAudioVar.get()

        urlRepeats = self.checkInDownloadables(downloadable)

        if (not self.allowRepeatsVar.get()) and urlRepeats > 0:

            statusString = makeEllipsis(downloadable.name, 18)
            statusString += "(Audio)" if downloadable.onlyAudio else "(Video)"
            statusString += " already in list.\nSkipping"

            self.updateStatus(statusString, "orange")
            return False

        elif urlRepeats > 0:
            downloadable.name += f"({urlRepeats})"
            downloadable.displayName = downloadable.name + " --- " + ("Audio" if downloadable.onlyAudio else "Video")


        self.downloadables[downloadable.displayName] = downloadable


        if onlyAudio:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])+1))
        else:
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])+1))

        self.mylist.insert(END, downloadable.displayName) 

        self.setDefaultListSelection()

        # Clear URL entry
        self.searchVar.set('')
        self.updateStatus("Success!", "green")
        return True

    def setDefaultListSelection(self):
        if len(self.mylist.curselection()) < 1:
            self.mylist.selection_set(END)
            self.showDownloadable(None)

    def checkInDownloadables(self, downloadable):
        urlCount = 0
        for dlKey, dl in self.downloadables.items():
            if dl.url == downloadable.url and dl.onlyAudio == downloadable.onlyAudio:
                urlCount += 1
        return urlCount


    def updateStatus(self, message, color):
        try:
            self.tryAgainButton.destroy()
        except:
            pass
        self.tryAgainButton = None
        self.statusVar.set(message)
        self.statusLabel['fg'] = color
        self.update()


    # Handles downloading of all contents in URL list

    def download(self):
        if self.downloadLock:
            print("Downloading locked because currently downloading")
            return
        self.setLocked(True)
        threading.Thread(target=self.downloadThreaded).start()

    def downloadThreaded(self):

        numDownloadables = len(self.downloadables)
        # Check if user entered any URLS
        if not numDownloadables:                                                                       
            self.updateStatus("No urls provided", "red")
            return

        directory = fd.askdirectory()

        # If exited out of directory chooser without picking location, warn user
        if not directory:                                                                               
            self.updateStatus("No directory chosen", "red")
            return
        
        self.updateStatus("Downloading...", "blue")

        threadList = []

        for index, downloadable in enumerate(self.downloadables.values()):           
            thread = threading.Thread(target=downloadable.download, args=(directory,))
            threadList.append(thread)
            thread.start()                                                         
        
        for index, thread in enumerate(threadList):
            thread.join()
            self.updateStatus("Downloading...(" + str(index+1) + "/" + str( numDownloadables ) + ")", "blue")

        # If option is set, clear every URL
        if self.deleteOnDownloadVar.get():
            self.deleteAll()

        # Notify user that download is complete
        self.setLocked(False)
        self.updateStatus("Success! Downloaded into:\n" + (directory if len(directory) <25 else directory[:12] + "..." + directory[len(directory)-12:]), "green")

    def setLocked(self, locked):
        self.downloadLock = locked
        self.fetchLock = locked
        if locked:
            self.startDownloadButton.config(bg=COLOR_DISABLED)
            self.fetchButton.config(bg=COLOR_DISABLED)

            self.startDownloadButton["state"] = "disabled"
            self.fetchButton["state"] = "disabled"

        else:
            self.startDownloadButton.config(bg=COLOR_DOWNLOAD)
            self.fetchButton.config(bg=COLOR_FETCH)
            
            self.startDownloadButton["state"] = "normal"
            self.fetchButton["state"] = "normal"



    def pollForPreview(self):

        if Downloadable.previewThread == None or Downloadable.previewThread.is_alive() == False:
            self.previewLabelVar.set("Playing:\n")
        self.after(2000, self.pollForPreview)

    def getYoutubeObjects(self, url):
        youtubeObjects = []

        with youtube_dl.YoutubeDL({'quiet':True, "noplaylist":True, "age_limit":3,
                                    "logger": self.MyLogger(self)})as ydl:
            try:
                result = ydl.extract_info \
                (url,
                download=False) #We just want to extract the info
                if 'entries' in result:
                    # Can be a playlist or a list of videos
                    video = result['entries']

                    #loops entries to grab each video_url
                    for i, item in enumerate(video):
                        video = result['entries'][i]
                        youtubeObjects.append(video)

                else:
                    youtubeObjects.append(result)

            except Exception as e1:
                print("E1: ",e1)
                try:
                    videosSearch = VideosSearch(url, limit = 1)
                    searchResultUrl = videosSearch.result()['result'][0]['link']
                    result = ydl.extract_info \
                        (searchResultUrl,
                        download=False) 
                    youtubeObjects.append(result)
                except Exception as e2:
                    print("Failed to fetch: ",e2)
                    pass

        return youtubeObjects

    class MyLogger(object):

        def __init__(self, outer):
            self.outer = outer
        def debug(self, msg):
            x = re.search("Downloading video [0-9]+ of [0-9]+", msg)
            if x != None:
                nums = re.findall("[0-9]+", msg)

                self.outer.updateStatus("Fetching "+str(nums[0])+"/"+str(nums[1]), "blue")
                

        def warning(self, msg):
            print("WARNING: ",msg)

        def error(self, msg):
            print("ERROR: ",msg)


# Application entry-point
# Configure Tk object and start Tkinter loop
def main():
    root = Tk()
    root['bg'] = BG
    root.geometry("1200x1200")
    root.title("YouTube Downloader")
    app = App(master=root)
    app.pollForPreview()
    app.mainloop()


if __name__ == '__main__':
    main()