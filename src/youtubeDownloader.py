import os
from moviepy.editor import AudioFileClip, VideoFileClip
import pytube                           # install from git :: python3 -m pip install git+https://github.com/nficano/pytube.git
from tkinter import *
from tkinter import filedialog as fd
from eyed3 import load as eyed3Load
from PIL import Image, ImageTk
from io import BytesIO
from requests import get as requestsGet

from helpers import formatSeconds, addLineBreaks

class App(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.bg = "#eeeeFa"

        # Holds data from YouTube, references to widgets representing that data, and tags
        self.urls = {} 

        # Options for tags optionmenu
        self.tagOptions = ['Title', 'Contributing Artists', 'Album', 'Album Artist', 'Year', 'Track Number']        
        # Maps youtube metadata to mp3 header tag name
        self.mdToTag = {'Artist':'Contributing Artists','Artists':'Contributing Artists', 'Title':'Title', 'Album' : 'Album', 'Song':'Title'}   

        # textvariable for url entry
        self.urlVar = StringVar()                                                                                  
        self.urlVar.set("Enter the YouTube URL of a video or playlist")
        
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
        self.cutLowerVar = StringVar()
        self.cutLowerVar.set('0.00')
        self.cutUpperVar = StringVar()
        self.cutUpperVar.set('0.00')
        self.previewCutLowVar = StringVar()
        self.previewCutLowVar.set('0.00')
        self.previewCutHighVar = StringVar()
        self.previewCutHighVar.set('0.00')
 

        self.clearUrlEntryNextClick = True
        self.clearNameChangeEntryNextClick = True
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

        self.deleteAllAudioBtn = Button(self.controlFrame, text="Delete All Audio", command=lambda:self.deleteAllAudio(), bg="red")
        self.deleteAllAudioBtn.grid(column=1, row=4, pady=3)

        self.deleteAllVideoBtn = Button(self.controlFrame, text="Delete All Video", command=lambda:self.deleteAllVideo(), bg="red")
        self.deleteAllVideoBtn.grid(column=2, row=4, pady=3)

        self.deleteOnDownload = Checkbutton(self.controlFrame, text="Delete after download", variable=self.deleteOnDownloadVar,bg=self.bg)
        self.deleteOnDownload.grid(column=3, row=4)

        self.addPlaylistBtn = Button(self.controlFrame, text="Playlist Audio", command= lambda : self.addPlaylist(False), bg="#f9c74f",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addPlaylistBtn.grid(column=1, row=3)
        
        self.addUrlBtn = Button(self.controlFrame, text="Single Audio", command=lambda : self.addUrl(False), bg="#ffe3b0",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addUrlBtn.grid(column=1, row=2)

        self.addPlaylistVideoBtn = Button(self.controlFrame, text="Playlist Video", command=lambda : self.addPlaylist(True), bg="#f3524c",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addPlaylistVideoBtn.grid(column=2, row=3)

        self.addUrlVideoBtn = Button(self.controlFrame, text="Single Video", command=lambda : self.addUrl(True), bg="#f3a29c",width=15,  padx=5, pady=5,font=('Arial', 12))
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

        # Top right frame for cutting song or video
        self.optionsFrame2 = Frame(self.controlFrame, padx=5, pady=5, bg=self.bg, borderwidth=2, relief="groove")
        self.optionsFrame2.grid(padx=5, pady=5, row=3,rowspan=2, column=5, columnspan=3)

        self.cutRangeLabel = Checkbutton(self.optionsFrame2, text="Cut song/video: ", variable=self.cutVar, bg=self.bg)
        self.cutRangeLabel.grid(column=1, columnspan=3, row=1)

        self.cutLowerRangeEntry = Entry(self.optionsFrame2, textvariable=self.cutLowerVar, width=4)
        self.cutLowerRangeEntry.grid(column=1, row=2)

        self.cutRangeDashLabel = Label(self.optionsFrame2, text="-")
        self.cutRangeDashLabel.grid(column=2, row=2)

        self.cutUpperRangeEntry = Entry(self.optionsFrame2, textvariable=self.cutUpperVar, width=4)
        self.cutUpperRangeEntry.grid(column=3, row=2)

        # Top right frame for the program to add any found default metadata tags
        self.optionsFrame3 = Frame(self.controlFrame, padx=5, pady=5, bg=self.bg)
        self.optionsFrame3.grid(padx=5, pady=5, row=1, rowspan=5, column = 9, columnspan=3)

        self.addMdTags = Checkbutton(self.optionsFrame3, text="Add tags from\nYouTube metadata\n(Priority 1)", variable=self.addMdTagsVar, bg=self.bg)
        self.addMdTags.grid(column=1, columnspan=3, row=1,rowspan=2, pady=10)

        self.addTitleTags = Checkbutton(self.optionsFrame3, text="Add tags from title\nSplit on '-'\nEx) Artist - Song\n(Priority 2)", variable=self.addTitleTagsVar, bg=self.bg)
        self.addTitleTags.grid(column=1, columnspan=3, row=4,rowspan=2, pady=10)

        # Middle frame/scrollbox for holding URLs retrieved and ready to be customized or downloaded
        self.scrollFrame = Frame(self, padx=5, pady=10, bg=self.bg)
        self.scrollFrame.pack()

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
        self.previewCutLowVar.set('0.00')
        self.previewCutHighVar.set('0.00')

         # Destroy currently in preview frame to show currently selecte done
        if self.previewUrlFrame != None:                                               
            self.previewUrlFrame.destroy()
            self.previewUrl = None

        try:
            selectedString = ev.widget.get(ev.widget.curselection()[0])
        # handle error from user clicking in empty list box
        except IndexError:
            return
        
        # Gets url of selected item in listbox
        selectedUrl = selectedString.split(' ----- ')[0]                                
        self.nameChangeVar.set(self.urls[selectedUrl]['name'])
        self.tagChangeVar.set('')

        # Display any metadata extracted from the url
        formattedMetadata = ""                                                              
        for i in [*self.urls[selectedUrl]['metadata']]:
            formattedMetadata += addLineBreaks(i + " : " + self.urls[selectedUrl]['metadata'][i]+"\n")

        urlMetadata = Label(urlFrame, text=formattedMetadata, bg=self.bg)
        urlMetadata.grid(row=3, column=2, columnspan=1)

        # Configure GUI to show preview of URL content, including customization options
        # Pack URL frame into in preview frame
        urlFrame = Frame(self.previewFrame, padx=5, pady=5, bg=self.bg, borderwidth=2, relief="groove")                             
        urlFrame.pack(expand=True)

        urlLabel = Label(urlFrame, text=selectedUrl, font=('Helvetica', 12), bg=self.bg)
        urlLabel.grid(row=1, column=0,columnspan=10)

        # Components for showing current name 
        # Represents name of downloaded file minus the extension
        urlName = Label(urlFrame, textvariable=self.nameChangeVar, bg=self.bg)                                                      
        urlName.grid(row=0, column=0, columnspan=10)

        urlDelete = Button(urlFrame, text="Delete",command=lambda:self.deleteUrl(selectedUrl), bg="#FF9999")
        urlDelete.grid(row=0, column=10)

        urlNameChangeEntry = Entry(urlFrame, textvariable = self.nameChangeVar, width=50, bg="#bbdddd")
        urlNameChangeEntry.grid(row=6, column=2)
        urlNameChangeEntry.bind('<Button-1>', self.clearNameEntry)

        urlChangeName = Button(urlFrame,text="Change Name", command=lambda:self.changeName(selectedUrl), bg="#99BBBB")
        urlChangeName.grid(row=6, column=3, columnspan=1)

        # If a video was cut before being fetched, load that info
        # Otherwise, just show media length until user decides to cut
        formattedInfo = ""
        if self.urls[selectedUrl]['cut']:
            formattedInfo += "Original Length: "+self.urls[selectedUrl]['length']+"\n"
            formattedInfo += "Cut Length: " + str(formatSeconds(self.urls[selectedUrl]['highCut']- self.urls[selectedUrl]['lowCut'])) + "\n"
            formattedInfo += "Cut Range: "+ formatSeconds(self.urls[selectedUrl]['lowCut']) + " - " + formatSeconds(self.urls[selectedUrl]['highCut'])
        else:
            formattedInfo += "Length: "+self.urls[selectedUrl]['length']

        # Pack cut text info
        urlInfoAndCutFrame = Frame(urlFrame, bg=self.bg, borderwidth=2, relief="groove")
        urlInfoAndCutFrame.grid(row=3, column=1)

        urlInfo = Label(urlInfoAndCutFrame, text=formattedInfo, bg=self.bg)
        urlInfo.grid(row=1, column=1)

        optionsFrame = Frame(urlInfoAndCutFrame, padx=5, pady=5, bg=self.bg, borderwidth=2, relief="groove")
        optionsFrame.grid(padx=5, pady=5, row=3,rowspan=2, column=5, columnspan=3)

        # Pack cutting tools (range and button)
        cutRangeBtn = Button(optionsFrame, text="Cut song/video: ",command= lambda:self.makeCutPreview(selectedUrl), bg=self.bg)
        cutRangeBtn.grid(column=1, columnspan=3, row=2)

        cutLowerRangeEntry = Entry(optionsFrame, textvariable=self.previewCutLowVar, width=4)
        cutLowerRangeEntry.grid(column=1, row=1)

        cutRangeDashLabel = Label(optionsFrame, text="-")
        cutRangeDashLabel.grid(column=2, row=1)

        cutUpperRangeEntry = Entry(optionsFrame, textvariable=self.previewCutHighVar, width=4)
        cutUpperRangeEntry.grid(column=3, row=1)

        # Add metadata tags if downloading audio only
        # TODO: Add support for adding tags to .mp4
        if not self.urls[selectedUrl]['includeVideo']:
            urlTags = Frame(urlFrame, padx=5, pady=5, bg=self.bg, borderwidth=2, relief="groove")
            urlTags.grid(row=8, column=2)

            urlTagsTitle = Label(urlTags, text="MP3 Metadata Tags: ",fg="#119911", bg=self.bg)
            urlTagsTitle.pack(side=LEFT)

            for k in self.urls[selectedUrl]['tagList']:                                         # Load any tags previously selected
                tagDeleteButton = Button(urlTags, text="X "+k[0]+" : "+k[1],bg="#77cc55")
                tagDeleteButton.pack(side=BOTTOM)
                data={"tagKey": k[0], "tagValue": k[1], 'url':selectedUrl}
                tagDeleteButton.bind("<Button-1>", lambda event, arg=data: self.deleteTag(event, arg))
                if len(k) < 3:
                    k.append(tagDeleteButton)
                else:
                    k[2] = tagDeleteButton
                print(k)

            tagSelect = OptionMenu(urlFrame, self.tagVar, *self.tagOptions)
            tagSelect.grid(row=7, column=1, columnspan=1)
            tagSelect.config(width=40, bg="#DDFFAA")

            tagEntry = Entry(urlFrame, textvariable = self.tagChangeVar, width=40, bg="#DDFFAA")
            tagEntry.grid(row=7, column=2, columnspan=1)
            tagEntry.bind('<Button-1>', self.clearTagEntry)

            addTag = Button(urlFrame, text="Add Tag",command=lambda:self.addTag(selectedUrl), bg="#DDFFAA")
            addTag.grid(row=7, column=3, columnspan=1)

            self.urls[selectedUrl]['urlTags'] = urlTags

        imgUrl = requestsGet(self.urls[selectedUrl]['yt'].thumbnail_url)
        img = Image.open(BytesIO(imgUrl.content))
        img = img.resize((160,90))
        render = ImageTk.PhotoImage(img)
        imageLabel = Label(urlFrame, image=render, width=160, height=90, bg=self.bg)
        imageLabel.grid(row=3,rowspan=2,column=3,columnspan=5)
        imageLabel.image = render

        # Assign references to the widgets in preview frame to url dict entry
        self.urls[selectedUrl]['urlLabel'] = urlLabel                               
        self.urls[selectedUrl]['urlDelete'] = urlDelete
        self.urls[selectedUrl]['urlInfo'] = urlInfo
        self.urls[selectedUrl]['urlFrame'] = urlFrame
        self.previewUrlFrame = urlFrame
        self.previewUrl = selectedUrl
    
    def deleteUrl(self, url):
        self.urls[url]['urlFrame'].destroy()                                       
        self.previewUrl = None
        self.mylist.delete(self.mylist.curselection()[0])
        if self.urls[url]['includeVideo']:
            # Decrement fetched videos count by 1
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])-1))     
        else:
            # Decrement fetched songs count by 1
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])-1))     
        del self.urls[url]

    # Handles cutting in URL preview frame after fetching
    # When user makes a cut on a song or video, calculate and save new range
    def makeCutPreview(self, url):

        # cut in seconds, minutes.seconds, or hours.minutes.seconds
        lowArr = self.previewCutLowVar.get().split('.')
        highArr = self.previewCutHighVar.get().split('.')
        low=0
        high=0
        try:
            # Calculate cut range based on input format
            if len(lowArr) ==1 and len(highArr) == 1 and int(lowArr[0]) > 0 and int(lowArr[0]) < int(highArr[0]):
                low = int(lowArr[0])
                high = int(highArr[0])
            elif len(lowArr) ==2 and len(highArr) == 2:
                low = int(lowArr[0])*60 + int(lowArr[1])
                high = int(highArr[0])*60 + int(highArr[1])
            elif len(lowArr) ==3 and len(highArr) == 3:
                low = int(lowArr[0])*3600 + int(lowArr[1])*60 + int(lowArr[2])
                high = int(highArr[0])*3600 +int(highArr[1])*60 + int(highArr[2])
            else:
                self.staturVar.set('Invalid cut. Acceptable formats: sec, min.sec, or hour.min.sec')
                self.statusLabel['fg'] = "red"
                self.update()
        except:
            self.statusVar.set('Invalid cut range, length of video is '+str(formatSeconds(self.urls[url]['lengthInSeconds'])))
            self.statusLabel['fg'] = "red"
            return
        if high > int(self.urls[url]['lengthInSeconds']) or high-low < 0:
            self.statusVar.set('Invalid cut range, length of video is '+str(formatSeconds(self.urls[url]['lengthInSeconds'])))
            self.statusLabel['fg'] = "red"
            return

        # Update variables and user view of current cut
        self.urls[url]['cut'] = True
        self.urls[url]['lowCut'] = low
        self.urls[url]['highCut'] = high
        formattedInfo = ''
        formattedInfo += "Original Length: "+self.urls[url]['length']+"\n"
        formattedInfo += "Cut Length: " + str(formatSeconds(high- low)) + "\n"
        formattedInfo += "Cut Range: "+ formatSeconds(low) + " - " + formatSeconds(high)
        self.urls[url]['urlInfo']['text'] = formattedInfo

    # Handles cutting before fetching URL
    def makeCut(self, url, seconds):
        lowArr = self.cutLowerVar.get().split('.')
        highArr = self.cutUpperVar.get().split('.')
        low=0
        high=0
        try:
            if len(lowArr) ==1 and len(highArr) == 1 and int(lowArr[0]) > 0 and int(lowArr[0]) < int(highArr[0]):
                low = int(lowArr[0])
                high = int(highArr[0])
            elif len(lowArr) ==2 and len(highArr) == 2:
                low = int(lowArr[0])*60 + int(lowArr[1])
                high = int(highArr[0])*60 + int(highArr[1])
            elif len(lowArr) ==3 and len(highArr) == 3:
                low = int(lowArr[0])*3600 + int(lowArr[1])*60 + int(lowArr[2])
                high = int(highArr[0])*3600 +int(highArr[1])*60 + int(highArr[2])
            else:
                self.staturVar.set('Invalid cut. Acceptable formats: sec, min.sec, or hour.min.sec')
                self.statusLabel['fg'] = "red"
                self.update()
                return False
        except:
            self.staturVar.set('Invalid cut. Acceptable formats: sec, min.sec, or hour.min.sec')
            self.statusLabel['fg'] = "red"
            self.update()
            return False
        if high > int(seconds) or high-low < 0:
            self.statusVar.set('Invalid cut range, length of video is '+str(formatSeconds(int(seconds))))
            self.statusLabel['fg'] = "red"
            return False
        return [low, high]

    # Handle changing name 
    def changeName(self, url):
        newName = self.nameChangeVar.get()
        self.mylist.delete(self.mylist.curselection()[0])
        self.urls[url]['name'] = newName
        mediaTag = None

        # Update media tag at the end of URL in list view
        if self.urls[url]['includeVideo']:
            mediaTag = '(Video)'
        else:
            mediaTag = '(Audio)'
        self.mylist.insert(END, url+" ----- "+newName+" "+mediaTag) 
        self.nameChangeVar.set(newName)
        self.mylist.selection_set('end') 

        self.clearNameChangeEntryNextClick = True

    # Delete all fetched audio URLs
    def deleteAllAudio(self):
        for i in [*self.urls]:
            if not self.urls[i]['includeVideo']:
                if i == self.previewUrl:
                    self.urls[i]['urlFrame'].destroy()                                        
                    self.previewUrl = None
                self.audioCountVar.set('Audio: 0')
                urlsInList = self.listVar.get()
                for k,j in enumerate(urlsInList):
                    listUrl = j.split("-----")[0].strip()
                    print(listUrl)
                    if listUrl == i:
                        self.mylist.delete(k)
                del self.urls[i]

    # Delete all fetch video URLs
    def deleteAllVideo(self):
        for i in [*self.urls]:
            if self.urls[i]['includeVideo']:
                if i == self.previewUrl:
                    self.urls[i]['urlFrame'].destroy()                                        
                    self.previewUrl = None
                self.videoCountVar.set('Video: 0')
                urlsInList = self.listVar.get()
                for k,j in enumerate(urlsInList):
                    listUrl = j.split("-----")[0].strip()
                    if listUrl == i:
                        self.mylist.delete(k)
                del self.urls[i]

    # Manually add a metadata tag
    def addTag(self, url):
        self.clearTagEntryNextClick = True
        tagKey = self.tagVar.get()
        tagValue = self.tagChangeVar.get()

        # If tag already exists, delete it
        for n in self.urls[url]['tagList']:
            if n[0] == tagKey:
                self.urls[url]['tagList'].remove(n)
                n[2].destroy()

        # Add new tag and event handlers
        tagDeleteButton = Button(self.urls[url]['urlTags'], text="X "+tagKey+" : "+tagValue,bg="#77cc55")
        tagDeleteButton.pack(side=BOTTOM)
        data={"tagKey": tagKey, "tagValue": tagValue, 'url':url}
        tagDeleteButton.bind("<Button-1>", lambda event, arg=data: self.deleteTag(event, arg))

        self.urls[url]['tagList'].append([tagKey,tagValue, tagDeleteButton])
    
    # < ---------- On click event handlers ---------- >
    def deleteTag(self, ev, arg):
        for m in self.urls[arg['url']]['tagList']:
            if m[0] == arg['tagKey']:
                ev.widget.destroy()
                self.urls[arg['url']]['tagList'].remove(m)

    def clearUrlEntry(self, ev):
        self.urlEntry['bg'] = "white" 
        if self.clearUrlEntryNextClick:
            self.clearUrlEntryNextClick = False
            self.urlVar.set('')
    
    def clearTagEntry(self, ev):
        if self.clearTagEntryNextClick:
            self.clearTagEntryNextClick = False
            self.tagChangeVar.set('')

    def clearNameEntry(self, ev):
        if self.clearNameChangeEntryNextClick:
            self.clearNameChangeEntryNextClick = False
            self.nameChangeVar.set('')
    # < ---------- On click event handlers ---------- >

    # Fetch entire playlist from single URL
    def addPlaylist(self, includeVideo):
        inputPlaylist = self.urlVar.get()
        if self.cutVar.get():
                self.statusVar.set("Can't cut playlist, individually click URLs in list to modify")
                self.statusLabel['fg'] = "Orange"
        try:
            playlistUrls = pytube.Playlist(inputPlaylist).video_urls
        except KeyError:
            self.statusVar.set('Failed to fetch playlist')
            self.statusLabel['fg'] = "red"
            return

        # Some URLs may fail to load
        totalCount = 0
        successCount = 0

        # If user specified a playlist range, check if it is valid, and if so, shorten [playlistUrls] accordingly
        if self.playlistRangeVar.get():
            try:
                if (int(self.playlistLowerRangeVar.get()) < 1) or (int(self.playlistUpperRangeVar.get())>len(playlistUrls)):
                    raise IndexError
                playlistUrls = playlistUrls[int(self.playlistLowerRangeVar.get())-1:int(self.playlistUpperRangeVar.get())]
            except IndexError:
                self.statusVar.set('Playlist out of range (In playlist: '+str(len(playlistUrls))+")")
                self.statusLabel['fg'] = "red"
                return
            except (TypeError, ValueError):
                self.statusVar.set('Invalid range (In playlist: '+str(len(playlistUrls))+")")
                self.statusLabel['fg'] = "red"
                return


        for j in playlistUrls:
            repeated = False

            # Check if single URL of playlist is already in list
            for b in [*self.urls]:                                              
                if b == j:
                    self.statusVar.set('Video is already in list')
                    self.statusLabel['fg'] = "red"
                    self.urlVar.set("URL " + j + " already entered")
                    self.update()
                    self.clearUrlEntryNextClick = True
                    repeated = True
                    continue
            
            # If a URL from playlist is already in list, add to totalCount (but not successCount) and continue to next URL
            if repeated:
                totalCount+=1
                continue

            # Update status to user
            self.statusVar.set('Succeeded: '+str(successCount) + "/" + str(len(playlistUrls)) +" : Failed: "+str(totalCount-successCount) +"/" + str(len(playlistUrls)))
            self.statusLabel['fg'] = "blue"
            self.update()

            totalCount+=1

            # Attempt to get this single URL from YouTube
            yt = None
            try:
                yt = pytube.YouTube(j)
            except (pytube.exceptions.VideoUnavailable, pytube.exceptions.RegexMatchError,
                    pytube.exceptions.VideoPrivate, KeyError):
                continue

            # Get first stream of video or audio
            stream = yt.streams.filter(only_audio=(not includeVideo)).first()

            # Metadata
            md = ''

            # List to hold dynamically added ID3 tags
            tagList = []
            alreadyAddedTitleTags = False
            try:
                md = [*yt.metadata][0]
                for g in [*md]:
                    if g in [*self.mdToTag]:
                        tagList.append([self.mdToTag[g], md[g]])


            # No metadata gotten from YouTube
            # If the user selected to also try adding metadata from the title, do that if the title format is correct
            except IndexError:
                if len(yt.title.split('-')) >1 and self.addTitleTagsVar.get():
                    tagList.append(['Title', yt.title.split('-')[1]])
                    tagList.append(['Contributing Artists',yt.title.split('-')[0]])
                    alreadyAddedTitleTags = True
                pass

            # Create URL dictionary
            self.urls[j] = {'includeVideo':includeVideo, 'yt':yt,'stream': stream, 'name':yt.title, 'length':formatSeconds(yt.length),'lengthInSeconds': yt.length, 'tagList':tagList, 'metadata':md, 'cut':False}
            
            mediaTag = None

            # Count how many videos and songs are being downloaded and show in status frame
            if includeVideo:
                self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])+1))
                mediaTag = '(Video)'
            else:
                self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])+1))
                mediaTag = '(Audio)'
            # Create text that represents URL in URL list
            self.mylist.insert(END, j+" ----- "+stream.default_filename[:-4]+" "+mediaTag)
                
            # Add to successful fetch out of totalCount
            successCount+=1

        # When all URLs in playlist have been processed, 
        self.clearUrlEntryNextClick = True
        self.statusVar.set('Done! : Succeeded: '+str(successCount)+" : Failed: "+str(totalCount-successCount))
        self.statusLabel['fg'] = "green"
        self.update()
        
    # Fetch a single URL
    def addUrl(self, includeVideo):
        # warn user that options may not be applied
        if self.playlistRangeVar.get():
            self.statusVar.set("Can't apply playlist range to single URL")
            self.statusLabel['fg'] = "orange"
            self.update()

        # update status frame
        self.statusVar.set('Fetching video from YouTube...')
        self.statusLabel['fg'] = "blue"
        self.update()

        # Get URL from input
        inputUrl = self.urlVar.get()

        # If URL is already in list, flash the URL entry and notify the user
        exists = False
        for i in [*self.urls]:                                          
            if i == inputUrl:
                self.urlVar.set("Already entered")
                self.statusVar.set('Video is already in list')
                self.statusLabel['fg'] = "red"
                self.update()
                def e():
                    self.urlEntry['bg'] = "#ffbbbb"
                def f():
                    self.urlEntry['bg'] = "white"
                for i in range(1,10):
                    if i%2 != 0:
                        self.after(100*i, e)
                    else:
                        self.after(100*i, f)
                return

        # Attempt to get this single URL from YouTube
        yt=None        
        try:
            yt = pytube.YouTube(inputUrl)
        except (pytube.exceptions.VideoUnavailable, pytube.exceptions.RegexMatchError,
                pytube.exceptions.VideoPrivate, KeyError) as e:

            self.statusVar.set('Failed to fetch video')
            self.statusLabel['fg'] = "red"
            return

        # Get first stream of video or audio
        stream = yt.streams.filter(only_audio=(not includeVideo)).first()

        # Metadata
        md = ''

        # List to hold dynamically added ID3 tags
        tagList = []

        alreadyAddedTitleTags = False
        # If user selected options to add ID3 tags from metadata, check 
        if self.addMdTags:
            try:
                md = [*yt.metadata][0]
                for g in [*md]:
                    if g in [*self.mdToTag]:
                        tl.append([self.mdToTag[g], md[g]])
            except IndexError:
                if len(yt.title.split('-')) >1 and self.addTitleTagsVar.get():
                    tl.append(['Title', yt.title.split('-')[1]])
                    tl.append(['Contributing Artists',yt.title.split('-')[0]])
                    alreadyAddedTitleTags = True
                pass

        # If user specified a cut, try or notify user that cut failed and stop
        cutRange = False
        if self.cutVar.get():
            cutRange = self.makeCut(inputUrl, yt.length)
            if not cutRange:
                self.statusVar.set("Cut range is invalid")
                self.statusLabel['fg'] = "red"
                self.update()
                return

        # URL successfully fetched, make URL dictionary and notify user
        self.statusVar.set('Success!')
        self.statusLabel['fg'] = "green"
        self.clearUrlEntryNextClick = True
        self.urls[inputUrl] = {'includeVideo':includeVideo, 'yt': yt, 'stream': stream, 'name':stream.default_filename[:-4], 'length':formatSeconds(yt.length),'lengthInSeconds': yt.length, 'tagList':tl, 'metadata':md, 'cut':False}
        
        # Count how many videos and songs are being downloaded and show in status frame
        mediaTag = None
        if includeVideo:
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])+1))
            mediaTag = "(Video)"
        else:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])+1))
            mediaTag = "(Audio)"

        # Create text that represents URL in URL list
        self.mylist.insert(END, inputUrl+" ----- "+stream.default_filename[:-4]+" "+mediaTag) 
        # Clear URL entry
        self.urlVar.set('')

        # Add cut range data to URL dictionary if a cutRange was specified
        if cutRange:
            self.urls[inputUrl]['cut'] = True
            self.urls[inputUrl]['lowCut'] = cutRange[0]
            self.urls[inputUrl]['highCut'] = cutRange[1]

    # Handles downloading of all contents in URL list
    def download(self):

        # Check if user entered any URLS
        if not len([*self.urls]):                                                                       
            self.statusVar.set('No urls provided')
            self.statusLabel['fg'] = "red"
            self.update()
            return

        # Update status frame
        self.statusVar.set('Downloading...')                                                            
        self.statusLabel['fg'] = "blue"
        self.update()

        directory = fd.askdirectory()
        # If exited out of directory chooser without picking location, warn user
        if not directory:                                                                               
            self.statusVar.set('No directory chosen')
            self.statusLabel['fg'] = "red"
            return

        vidNames = []
        # Download all added URLs, single and from playlist
        # TODO right now cut video doesnt get tags....
        for k,u in enumerate([*self.urls]):           

            # Update status frame                                                  
            self.statusVar.set('Downloading...('+str(k+1)+"/"+str(len([*self.urls]))+")")               
            self.statusLabel['fg'] = "blue"
            self.update()       

            # If URL is video and needs to be cut                                                                       
            if self.urls[u]['includeVideo'] and self.urls[u]['cut']:
    
                # Download the temporary video before cut
                self.urls[u]['stream'].download(output_path=directory, filename='tempCut')      
    
                # Create path for temporary and final files
                fileName = self.urls[u]['name']+'.mp4'
                tempPath = os.path.join(directory, 'tempCut.mp4')                                   
                finalPath = os.path.join(directory, fileName)

                # Create MoviePy video object from YouTube downloaded video
                y = VideoFileClip(tempPath)

                # Clip the video
                low = self.urls[u]['lowCut']
                high = self.urls[u]['highCut']
                y = y.subclip(low,high)

                # Save as final path name
                y.write_videofile(finalPath)          

                # Close the object and remove the temporary file                                              
                y.close()
                os.remove(tempPath)
                continue

            # If URL is audio
            dlReturn = self.urls[u]['stream'].download(output_path=directory, filename=self.urls[u]['name'])
            
            # Can just continue here because cut video is handled above and downloading direct
            # from YouTube already gives us video file
            if self.urls[u]['includeVideo']:     
                continue

            # Format path name for '.mp3'
            fn = self.urls[u]['name']+'.mp4'
            full_path = os.path.join(directory, fn)
            output_path = dlReturn[:-1]+"3"

            # Create MoviePy audio object
            clip = AudioFileClip(dlReturn)   

            # Cut video if range is selected
            if self.urls[u]['cut']:
                low = self.urls[u]['lowCut']
                high = self.urls[u]['highCut']
                clip = clip.subclip(low,high)

            # Write out final audio file with correct bitrate and remove temporary download
            clip.write_audiofile(output_path,bitrate="320k")
            clip.close()
            os.remove(dlReturn)

            # Try to match metadata with mp3 tags to add to output files
            if len(self.urls[u]['tagList']) != 0:                           
                newAudioFile = eyed3Load(output_path)

                for g in self.urls[u]['tagList']:
                    if g[0] == 'Title':
                        newAudioFile.tag.title = g[1]
                    elif g[0] == 'Contributing Artists':
                        newAudioFile.tag.artist = g[1]
                    elif g[0] == 'Album Artist':
                        newAudioFile.tag.album_artist = g[1]
                    elif g[0] == "Track Number":
                        newAudioFile.tag.track_num = g[1]
                    elif g[0] == "Year":
                        newAudioFile.tag.year = g[1]
                    elif g[0] == "Album":
                        newAudioFile.tag.album = g[1]
                newAudioFile.tag.save()

        # If option is set, clear every URL
        if self.deleteOnDownloadVar.get():
            self.urls = {}
            self.mylist.delete('0', 'end')
            self.audioCountVar.set('Audio: 0')
            self.videoCountVar.set('Video: 0')
            if self.previewUrlFrame != None:                                                # Destroy currently in preview frame
                self.previewUrlFrame.destroy()
                self.previewUrl = None

        # Notify user that download is complete
        self.statusVar.set('Success! Downloaded into: '+directory)
        self.statusLabel['fg'] = "green"
        
# Application entry-point
# Configure Tk object and start Tkinter loop
def main():
    root = Tk()
    root['bg'] = "#eeeeFa"
    root.geometry("1200x1200")
    root.title("YouTube Downloader")
    app = App(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()