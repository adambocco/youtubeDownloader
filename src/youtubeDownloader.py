import os
from moviepy.editor import AudioFileClip, VideoFileClip
import pytube                           # install from git :: python3 -m pip install git+https://github.com/nficano/pytube.git
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

class App(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.bg = BG
        self.config(bg=self.bg)

        # Holds data from YouTube, references to widgets representing that data, and tags

        self.downloadables = {}

        # Options for tags optionmenu
        self.tagOptions = ['Title', 'Contributing Artists', 'Album', 'Album Artist', 'Year', 'Track Number']        
        # Maps youtube metadata to mp3 header tag name
        self.mdToTag = {'Artist':'Contributing Artists','Artists':'Contributing Artists', 'Title':'Title', 'Album' : 'Album', 'Song':'Title'}   

        # textvariable for url entry
        self.urlVar = StringVar()                                                                                  
        self.urlVar.set("Enter a YouTube URL or Search Query")
        
        # textvariable for name change entry 
        self.nameChangeVar = StringVar() 
        self.urlListVar = [];                                                                                       

        # listvariable for fetched urls added to listbox
        self.listVar = Variable(value=self.urlListVar)         

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
        self.tagVar.set(self.tagOptions[0])

        # boolvariables for checkbox options
        self.deleteOnDownloadVar = BooleanVar()
        self.deleteOnDownloadVar.set(False)
        self.playlistRangeVar = BooleanVar()
        self.playlistRangeVar.set(False)
        self.cutVar = BooleanVar()
        self.cutVar.set(False)
        self.addMdTagsVar = BooleanVar()
        self.addMdTagsVar.set(True)
        self.addTitleTagsVar = BooleanVar()
        self.addTitleTagsVar.set(True)

        # textvaraibles for holding range of videos in playlist to download, only active when [self.playlistRangeVar] is true
        # 1-indexed, lower and upper range is inclusive
        self.playlistLowerRangeVar = StringVar()
        self.playlistLowerRangeVar.set('1')
        self.playlistUpperRangeVar = StringVar()
        self.playlistUpperRangeVar.set('10')

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
 

        self.clearUrlEntryNextClick = True
        self.clearTagEntryNextClick = True

        # holds URL and data for currently selected video/song
        self.previewUrlFrame = None
        self.previewUrl = None
        
        self.createWidgets()


    def createWidgets(self): 

        # Top frame widgets for adding URLs and downloading and other options
        self.controlFrame = Frame(self, padx=10, pady=10, bg=self.bg, borderwidth=2, relief="groove", width=80)
        self.controlFrame.pack(expand=True, padx=5, pady=5)

        self.urlEntry = Entry(self.controlFrame, textvariable = self.urlVar,font=('Arial', 12), width=50)
        self.urlEntry.grid(column=1, row=1, columnspan=4, padx=5, pady=5)
        self.urlEntry.bind('<Button-1>',self.clearUrlEntry)                                             

        self.start = Button(self.controlFrame, text="Start Download", command=self.download, bg="#90be6d",width=15, height=3, padx=5, pady=7,font=('Arial', 12))
        self.start.grid(column=3, row=2, rowspan=2)

        self.deleteOnDownload = Checkbutton(self.controlFrame, text="Delete after download", variable=self.deleteOnDownloadVar,bg=self.bg)
        self.deleteOnDownload.grid(column=3, row=4)

        self.addPlaylistBtn = Button(self.controlFrame, text="Playlist Audio", command= lambda : self.addPlaylist(False), bg="#f9c74f",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addPlaylistBtn.grid(column=1, row=3)
        
        self.addUrlBtn = Button(self.controlFrame, text="Single Audio", command=lambda : self.addSingleUrl(True), bg="#ffe3b0",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addUrlBtn.grid(column=1, row=2)

        self.addPlaylistVideoBtn = Button(self.controlFrame, text="Playlist Video", command=lambda : self.addPlaylist(True), bg="#f3524c",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addPlaylistVideoBtn.grid(column=2, row=3)

        self.addUrlVideoBtn = Button(self.controlFrame, text="Single Video", command=lambda : self.addSingleUrl(False), bg="#f3a29c",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addUrlVideoBtn.grid(column=2, row=2)

        # Frame below URL input, displays status of URL retrieval success, errors, and download progress
        self.statusFrame = Frame(self, padx=10, pady=10,bg=self.bg, borderwidth=2, relief="groove", width=80)
        self.statusFrame.pack(expand=True, padx=5, pady=5)

        self.audioCountLabel = Label(self.statusFrame, textvariable = self.audioCountVar, padx=10,font=('Arial', 12), bg=self.bg)
        self.audioCountLabel.grid(column=0, row=1)

        self.videoCountLabel = Label(self.statusFrame, textvariable = self.videoCountVar, padx=10,font=('Arial', 12), bg=self.bg)
        self.videoCountLabel.grid(column=1, row=1)

        self.statusLabel = Label(self.statusFrame, textvariable = self.statusVar, padx=10, font=('Arial', 12), bg=self.bg)
        self.statusLabel.grid(column=0,columnspan=2, row=2)

        self.deleteAllAudioBtn = Button(self.statusFrame, text="Delete All Audio", command=lambda:self.deleteAll("audio"), bg="#feaeae")
        self.deleteAllAudioBtn.grid(column=2, row=1, pady=2)

        self.deleteAllVideoBtn = Button(self.statusFrame, text="Delete All Video", command=lambda:self.deleteAll("video"), bg="#feaeae")
        self.deleteAllVideoBtn.grid(column=2, row=2, pady=2)

        # Top right frame for controlling playlist range to be retrieved
        self.optionsFrame1 = Frame(self.controlFrame, padx=5, pady=5, bg=self.bg, borderwidth=2, relief="groove")
        self.optionsFrame1.grid(padx=5, pady=5, row=1,rowspan=2, column=5, columnspan=3)

        self.playlistRangeLabel = Checkbutton(self.optionsFrame1, text="Playlist range", variable=self.playlistRangeVar,bg=self.bg)
        self.playlistRangeLabel.grid(column=1, columnspan=3, row=1)

        self.playlistLowerRange = Entry(self.optionsFrame1, textvariable=self.playlistLowerRangeVar, width=4)
        self.playlistLowerRange.grid(column=1, row=2)

        self.playlistRangeDashLabel = Label(self.optionsFrame1, text="-")
        self.playlistRangeDashLabel.grid(column=2, row=2)

        self.playlistUpperRange = Entry(self.optionsFrame1, textvariable=self.playlistUpperRangeVar, width=4)
        self.playlistUpperRange.grid(column=3, row=2)

        # Top right frame for the program to add any found default metadata tags
        self.optionsFrame3 = Frame(self.controlFrame, padx=5, pady=5, bg=self.bg)
        self.optionsFrame3.grid(padx=5, pady=5, row=1, rowspan=5, column = 9, columnspan=3)

        self.addMdTags = Checkbutton(self.optionsFrame3, text="Add tags from\nYouTube metadata\n(Priority 1)", variable=self.addMdTagsVar, bg=self.bg)
        self.addMdTags.grid(column=1, columnspan=3, row=1,rowspan=2, pady=10)

        self.addTitleTags = Checkbutton(self.optionsFrame3, text="Add tags from title\nSplit on '-'\nEx) Artist - Song\n(Priority 2)", variable=self.addTitleTagsVar, bg=self.bg)
        self.addTitleTags.grid(column=1, columnspan=3, row=4,rowspan=2, pady=10)

        # Middle frame/scrollbox for holding URLs retrieved and ready to be customized or downloaded

        self.downloadablesListFrame = Frame(self, padx=5, pady=10, bg=self.bg)
        self.downloadablesListFrame.pack()

        self.scrollFrame = Frame(self.downloadablesListFrame, padx=5, pady=10, bg=self.bg)
        self.scrollFrame.grid(column=1, row=2, columnspan=10)

        self.scroll_bar = Scrollbar(self.scrollFrame) 
        self.scroll_bar.pack(side=RIGHT, fill=Y) 

        self.mylist = Listbox(self.scrollFrame, yscrollcommand=self.scroll_bar.set, width= 120, listvariable=self.listVar, exportselection=False) 
        self.mylist.pack( side = LEFT, fill = BOTH ) 
        self.mylist.bind("<<ListboxSelect>>", self.showUrl)

        self.scroll_bar.config( command = self.mylist.yview ) 
        self.previewFrame = Frame(self, padx=10, pady=10, bg=self.bg)
        self.previewFrame.pack()


    # Shows all data retrieved from youtube and options to customize before downloading
    # Loads into preview frame (bottom frame)
    # Binds to 'self.mylist'
    def showUrl(self, ev):                                                             

         # Destroy currently in preview frame to show currently selecte done
        if self.previewUrlFrame != None:                                               
            self.previewUrlFrame.destroy()
            self.previewUrl = None

        try:
            downloadableKey = ev.widget.get(ev.widget.curselection()[0])
        # handle error from user clicking in empty list box
        except IndexError:
            return
        
        downloadable = self.downloadables[downloadableKey]
        # Gets url of selected item in listbox

        selectedUrl = downloadable.url                             
        self.nameChangeVar.set(downloadable.name)
        self.tagChangeVar.set('')

        # Configure GUI to show preview of URL content, including customization options
        # Pack URL frame into in preview frame
        urlFrame = Frame(self.previewFrame, padx=5, pady=5, bg=self.bg, borderwidth=2, relief="groove")                             
        urlFrame.pack(expand=True)

        # Components for showing current name 
        # Represents name of downloaded file minus the extension
        urlName = Label(urlFrame, text=downloadable.name, bg=self.bg, font=('Helvetica', 22))                                                      
        urlName.grid(row=0, column=0, columnspan=3)

        urlDelete = Button(urlFrame, text="Delete",command=lambda:self.deleteUrl(downloadableKey), bg="#FF9999")
        urlDelete.grid(row=0, column=6)

        urlNameChangeEntry = Entry(urlFrame, textvariable = self.nameChangeVar, width=50, bg="#bbdddd", font=("Helvetica", 16))
        urlNameChangeEntry.grid(row=1, column=1, columnspan=2)

        urlChangeName = Button(urlFrame,text="Change Name", command=lambda:self.changeName(downloadable, urlName), bg="#99BBBB", height=2)
        urlChangeName.grid(row=1, column=3, columnspan=1, padx=5)

        # Pack cut text info
        lowerFrame = Frame(urlFrame, bg=self.bg, borderwidth=2, relief="groove")
        lowerFrame.grid(row=4,column=0,columnspan=20)

        urlInfoAndCutFrame = Frame(urlFrame, bg=self.bg, borderwidth=2, relief="groove")
        urlInfoAndCutFrame.grid(row=3, column=1)

        optionsFrame = Frame(lowerFrame, padx=5, pady=5, bg=self.bg, borderwidth=2, relief="groove")
        optionsFrame.grid(row=0, column=0, padx=10)

        cutLabel = Label(optionsFrame, text="Cut Media:", font=("Helvetica",16), bg=self.bg)
        cutLabel.grid(row=0, column=1, columnspan=5, pady=3)

        # <----- CUT TEXT INPUTS AND LABELS (H[____] M[____] S[____] --TO-- H[____] M[____] S[____]) ----->
        labelH = Label(optionsFrame, text="H", bg=self.bg)
        labelH.grid(row=1, column=1)
        lowH = Entry(optionsFrame, textvariable = self.previewCutLowVarH, width=5, bg="#DDFFAA", )
        lowH.grid(row=1, column=2, padx=2, pady=2)
        
        labelM = Label(optionsFrame, text="M", bg=self.bg)
        labelM.grid(row=1, column=3)
        lowM = Entry(optionsFrame, textvariable = self.previewCutLowVarM, width=5, bg="#DDFFAA", )
        lowM.grid(row=1, column=4, padx=2, pady=2)

        labelS = Label(optionsFrame, text="S", bg=self.bg)
        labelS.grid(row=1, column=5)
        lowS = Entry(optionsFrame, textvariable = self.previewCutLowVarS, width=5, bg="#DDFFAA", )
        lowS.grid(row=1, column=6, padx=2, pady=2)

        labelTo = Label(optionsFrame, text="--TO--", bg=self.bg)
        labelTo.grid(row=1, column=7, padx=4, pady=2)

        labelH = Label(optionsFrame, text="H", bg=self.bg)
        labelH.grid(row=1, column=8)
        highH = Entry(optionsFrame, textvariable = self.previewCutHighVarH, width=5, bg="#DDFFAA", )
        highH.grid(row=1, column=9, padx=2, pady=2)

        labelM = Label(optionsFrame, text="M", bg=self.bg)
        labelM.grid(row=1, column=10)
        highM = Entry(optionsFrame, textvariable = self.previewCutHighVarM, width=5, bg="#DDFFAA", )
        highM.grid(row=1, column=11, padx=2, pady=2)

        labelS = Label(optionsFrame, text="S", bg=self.bg)
        labelS.grid(row=1, column=12)
        highS = Entry(optionsFrame, textvariable = self.previewCutHighVarS, width=5, bg="#DDFFAA", )
        highS.grid(row=1, column=13, padx=2, pady=2)

        # <----- CUT SLIDER FOR BOTH LOW-CUT AND HIGH-CUT----->
        cutSlider = Slider(optionsFrame, width = 400, height = 60, min_val = 0, max_val = downloadable.length, init_lis = [downloadable.lowCut, downloadable.highCut], show_value = True,
                             lowHMSVars=[self.previewCutLowVarH,  self.previewCutLowVarM,  self.previewCutLowVarS],
                             highHMSVars=[self.previewCutHighVarH,  self.previewCutHighVarM,  self.previewCutHighVarS])
        cutSlider.grid(column=1, columnspan=20, row=3)

        # <----- BUTTON TO APPLY H:M:S INPUT TO SLIDER ----->
        applyCutInputBtn = Button(optionsFrame, 
                                text="Apply to Slider",
                                command=lambda:cutSlider.moveBar(
                                self.previewCutLowVarH, self.previewCutLowVarM, self.previewCutLowVarS,
                                self.previewCutHighVarH, self.previewCutHighVarM, self.previewCutHighVarS), 
                                bg=self.bg)
        applyCutInputBtn.grid(column=1, columnspan=15, row=2, pady=3)

        cutRangeBtn = Button(optionsFrame, text="Make Cut",command= lambda:self.makeCut(downloadable, cutSlider), font=("Helvetica", 14), bg="#e9f9a9")
        cutRangeBtn.grid(column=1, columnspan=5, row=4, pady=5)

        formattedInfo = ""
        if downloadable.cut:
            formattedInfo += "Original Length: "+downloadable.getLengthString()+"\n"
            formattedInfo += "Cut Length: " + formatSeconds(downloadable.highCut - downloadable.lowCut) + "\n"
            formattedInfo += "Cut Range: "+ formatSeconds(downloadable.lowCut) + " - " + formatSeconds(downloadable.highCut)
        else:
            formattedInfo += "Length: " + downloadable.getLengthString()

        urlInfo = Label(optionsFrame, text=formattedInfo, bg=self.bg)
        urlInfo.grid(row=4, column=6, columnspan=10)

        # Add metadata tags if downloading audio only
        # TODO: Add support for adding tags to .mp4
        metadataTagsFrame = Frame(lowerFrame, borderwidth=2, relief="groove", bg=self.bg)
        metadataTagsFrame.grid(row=0, column=1, padx=10, pady=2)

        metadataLabel = Label(metadataTagsFrame, text="Format ID3 Tags:", font=("Helvetica",16), bg=self.bg)
        metadataLabel.grid(row=0, column=1, pady=2)

        if downloadable.onlyAudio:
            urlTags = Frame(metadataTagsFrame, padx=5, pady=5, bg=self.bg, borderwidth=2, relief="groove")
            urlTags.grid(row=3, column=1, columnspan=10, padx=5, pady=5)

            urlTagsTitle = Label(urlTags, text="MP3 Metadata Tags: ",fg="#119911", bg=self.bg)
            urlTagsTitle.pack(side=LEFT)

            for tag in [*downloadable.tags]:       
                if downloadable.tags[tag] != "":                                  # Load any tags previously selected
                    tagDeleteButton = Button(urlTags, text="X "+tag+" : "+downloadable.tags[tag],bg="#77cc55")
                    tagDeleteButton.pack(side=BOTTOM)
                    downloadable.tagIds[tag] = tagDeleteButton
                    data={"tagKey": tag, "tagValue": downloadable.tags[tag], 'downloadableKey':downloadable.displayName}
                    tagDeleteButton.bind("<Button-1>", lambda event, arg=data: self.deleteTag(event, arg))

                

            tagSelect = OptionMenu(metadataTagsFrame, self.tagVar, *self.tagOptions)
            tagSelect.grid(row=1, column=1, columnspan=5,padx=3)
            tagSelect.config(width=40, bg="#DDFFAA")

            tagEntry = Entry(metadataTagsFrame, textvariable = self.tagChangeVar, width=40, bg="#DDFFAA")
            tagEntry.grid(row=2, column=1, columnspan=3, padx=10, pady=5)
            tagEntry.bind('<Button-1>', self.clearTagEntry)

            addTag = Button(metadataTagsFrame, text="Add Tag",command=lambda:self.addTag(downloadable.displayName), bg="#DDFFAA")
            addTag.grid(row=2, column=4, columnspan=1, padx=5, pady=5)

            downloadable.widgetIds["urlTags"] = urlTags

        imgUrl = requestsGet(downloadable.youtubeObject.thumbnail_url)
        img = Image.open(BytesIO(imgUrl.content))
        img = img.resize((160,90))
        render = ImageTk.PhotoImage(img)
        imageLabel = Label(urlFrame, image=render, width=160, height=90, bg=self.bg)
        imageLabel.grid(row=0,rowspan=2,column=5)
        imageLabel.image = render

        
        # formattedMetadata = ""                                                              
        # for i in [*downloadable.metadata]:
        #     formattedMetadata += addLineBreaks(i + " : " +downloadable.metadata[i]+"\n")

        # urlMetadata = Label(urlFrame, text=formattedMetadata, bg=self.bg)
        # urlMetadata.grid(row=3, column=3, columnspan=1)

        # Assign references to the widgets in preview frame to url dict entry                          
        downloadable.widgetIds["urlDelete"] = urlDelete
        downloadable.widgetIds["urlInfo"] = urlInfo
        downloadable.widgetIds["urlFrame"] = urlFrame
        self.previewUrlFrame = urlFrame
        self.previewUrl = downloadable.displayName
    
    def deleteUrl(self, downloadableKey):
        downloadable = self.downloadables[downloadableKey]
        downloadable.widgetIds["urlFrame"].destroy()                                       
        self.previewUrl = None
        self.mylist.delete(self.mylist.curselection()[0])
        if downloadable.onlyAudio:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])-1))     
        else:
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])-1))   

        del self.downloadables[downloadableKey]

    # Handles cutting in URL preview frame after fetching
    # When user makes a cut on a song or video, calculate and save new range
    def makeCut(self, downloadable, slider):
        low, high = slider.getValues()
        print(low," : ",high)
        low = int(low)
        high = int(high)
        if downloadable.changeCut(low, high):
            formattedInfo = ''
            formattedInfo += "Original Length: " + formatSeconds(downloadable.length) +"\n"
            formattedInfo += "Cut Length: " + formatSeconds(high - low) + "\n"
            formattedInfo += "Cut Range: "+ formatSeconds(low) + " - " + formatSeconds(high)
            downloadable.widgetIds['urlInfo']['text'] = formattedInfo
        else:
            downloadable.widgetIds['urlInfo']['text'] = "Length: " + formatSeconds(downloadable.length) +"\n"

    # Handle changing name 
    def changeName(self, downloadable, nameLabel):
        newName = self.nameChangeVar.get()
        nameLabel.config(text=newName)
        self.mylist.delete(self.mylist.curselection()[0])
        downloadable.name = newName
        downloadable.displayName =  newName + " --- " + ("Audio" if downloadable.onlyAudio else "Video")
        # Update media tag at the end of URL in list view
        self.mylist.insert(END, downloadable.displayName) 
        self.mylist.selection_set('end') 


    def deleteAll(self):
        self.downloadables = {}
        self.mylist.delete('0', 'end')
        self.audioCountVar.set('Audio: 0')
        self.videoCountVar.set('Video: 0')
        if self.previewUrlFrame != None: 
            self.previewUrlFrame.destroy()
            self.previewUrl = None

    # Delete all fetched audio URLs
    def deleteAll(self, mediaType):
        isAudio = True if mediaType == "audio" else False
        deleteList = []
        for downloadableKey, downloadable in self.downloadables.items():
            if not(downloadable.onlyAudio ^ isAudio):
                if downloadableKey == self.previewUrl:
                    downloadable.widgetIds["urlFrame"].destroy()    
                    downloadable.widgetIds                                    
                    self.previewUrl = None
                if isAudio:
                    self.audioCountVar.set('Audio: 0')
                else:
                    self.videoCountVar.set('Video: 0') 
                downloadableKeysList = self.listVar.get()
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

        tagText = "X "+tagKey+" : "+tagValue

        if downloadable.tags[tagKey] == "":
        # Add new tag and event handlers
            tagDeleteButton = Button(downloadable.widgetIds["urlTags"], text=tagText,bg="#77cc55")
            tagDeleteButton.pack(side=BOTTOM)
            downloadable.tagIds[tagKey] = tagDeleteButton
            data={"tagKey": tagKey, "tagValue": tagValue, "downloadableKey": downloadable.displayName}
            tagDeleteButton.bind("<Button-1>", lambda event, arg=data: self.deleteTag(event, arg))
        else:
            downloadable.tagIds[tagKey].config(text=tagText)
        self.update()
        downloadable.tags[tagKey] = tagValue
    
    # < ---------- On click event handlers ---------- >

    def deleteTag(self, ev, arg):
        downloadable = self.downloadables[arg["downloadableKey"]]
        ev.widget.destroy()
        downloadable.tags[arg["tagKey"]] = ""
        downloadable.tagIds[arg["tagKey"]].destroy()
        downloadable.tagIds[arg["tagKey"]] = None

    def clearUrlEntry(self, ev):
        self.urlEntry['bg'] = "white" 
        if self.clearUrlEntryNextClick:
            self.clearUrlEntryNextClick = False
            self.urlVar.set('')
    
    def clearTagEntry(self, ev):
        if self.clearTagEntryNextClick:
            self.clearTagEntryNextClick = False
            self.tagChangeVar.set('')

    # < ---------- On click event handlers ---------- >

    # Fetch entire playlist from single URL
    def addPlaylist(self, includeVideo):
        inputPlaylist = self.urlVar.get()

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
            downloadable = self.addUrl(includeVideo, url)
            if (not downloadable):
                continue

            # Update status to user
            self.updateStatus("Succeeded: "+str(successCount) + "/" + str(len(playlistUrls)) +" : Total: "+totalCount, "blue")
            
            # Add to successful fetch out of totalCount
            successCount+=1

        # When all URLs in playlist have been processed, 
        self.clearUrlEntryNextClick = True
        self.updateStatus('Done! : Succeeded: '+str(successCount)+" : Failed: "+str(int(totalCount)-successCount), "green")
        
    # Fetch a single URL
    def addSingleUrl(self, onlyAudio):
        url = self.urlVar.get()
        self.addUrl(onlyAudio, url)

    def addUrl(self, onlyAudio, url):

        # update status frame
        self.updateStatus('Fetching video from YouTube...', "blue")

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
                    print(searchResultUrl)
                    downloadable = Downloadable(searchResultUrl, onlyAudio)
                except:
                    self.updateStatus("Error fetching from YouTube", "red")
                    return False

        # If URL is already in list, flash the URL entry and notify the user

        if downloadable.displayName in [*self.downloadables]:                                          
            self.updateStatus("URL is already in list", "red")
            return False

        # URL successfully fetched, make URL dictionary and notify user
        self.updateStatus('Success!', "green")

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
        self.urlVar.set('')

        return downloadable



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
            self.statusVar.set('No directory chosen')
            self.statusLabel['fg'] = "red"
            return
        
        self.updateStatus("Downloading...", "blue")

        vidNames = []
        # Download all added URLs, single and from playlist
        # TODO right now cut video doesnt get tags....

        index = 1
        for downloadableKey, downloadable in self.downloadables.items():           

            # Update status frame                                                  
            self.updateStatus("Downloading...(" + str(index) + "/" + str( len(self.downloadables) ) + ")", "blue")       
            index += 1        

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
    root['bg'] = BG
    root.geometry("1200x1200")
    root.title("YouTube Downloader")
    app = App(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()