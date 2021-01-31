
import os, sys, time
from moviepy.editor import AudioFileClip
from moviepy.editor import VideoFileClip
import re
import pytube                           # install from git :: python3 -m pip install git+https://github.com/nficano/pytube.git
from tkinter import *
from tkinter import filedialog as fd
import eyed3
from PIL import Image, ImageTk
from io import BytesIO
import requests

bgColor = "#eeeeFa"

class App(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.urls = {}                                                                                              # Holds data from YouTube, references to widgets representing that data, and tags
        self['bg'] = bgColor
        self.tagOptions = ['Title', 'Contributing Artists', 'Album', 'Album Artist', 'Year', 'Track Number']        # Options for tags optionmenu
        self.mdToTag = {'Artist':'Contributing Artists','Artists':'Contributing Artists', 'Title':'Title', 'Album' : 'Album', 'Song':'Title'}                        # Maps youtube metadata to mp3 header tag name

        self.urlVar = StringVar()                                                                                   # textvariable for url entry
        self.urlVar.set("Enter the YouTube URL of a video or playlist") 
        self.nameChangeVar = StringVar() 
        self.urlListVar = [];                                                                           # textvariable for name change entry 
        self.listVar = Variable(value=self.urlListVar)                                                                                  # listvariable for urls added listbox
        self.audioCountVar = StringVar()                                                                                 # textvariable for count of songs added label
        self.audioCountVar.set('Audio: 0')
        self.videoCountVar = StringVar()                                                                                 # textvariable for count of songs added label
        self.videoCountVar.set('Video: 0')
        self.statusVar = StringVar()
        self.statusVar.set('')
        self.tagChangeVar = StringVar()                                                                             # textvariable for add mp3 tag entry
        self.tagChangeVar.set('Enter tag descriptor')
        self.tagVar = StringVar()                                                                                   # textvariable for dropdown list of songs
        self.tagVar.set(self.tagOptions[0])
        self.deleteOnDownloadVar = IntVar()
        self.deleteOnDownloadVar.set(0)
        self.playlistRangeVar = IntVar()
        self.playlistRangeVar.set(0)
        self.cutVar = IntVar()
        self.cutVar.set(0)
        self.addMdTagsVar = IntVar()
        self.addMdTagsVar.set(1)
        self.addTitleTagsVar = IntVar()
        self.addTitleTagsVar.set(1)
        self.playlistLowerRangeVar = StringVar()
        self.playlistLowerRangeVar.set('1')
        self.playlistUpperRangeVar = StringVar()
        self.playlistUpperRangeVar.set('10')
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
        self.previewUrlFrame = None
        self.previewUrl = None
        
        self.createWidgets()


    def createWidgets(self): 
        self.controlFrame = Frame(self, padx=10, pady=10, bg=bgColor, borderwidth=2, relief="groove", width=80)
        self.controlFrame.pack(expand=True, padx=5, pady=5)

        self.start = Button(self.controlFrame, text="Start Download", command=self.download, bg="#90be6d",width=15, height=3, padx=5, pady=7,font=('Arial', 12))
        self.start.grid(column=3, row=2, rowspan=2)


        self.deleteAllAudioBtn = Button(self.controlFrame, text="Delete All Audio", command=lambda:self.deleteAllAudio(), bg="red")
        self.deleteAllAudioBtn.grid(column=1, row=4, pady=3)

        self.deleteAllVideoBtn = Button(self.controlFrame, text="Delete All Video", command=lambda:self.deleteAllVideo(), bg="red")
        self.deleteAllVideoBtn.grid(column=2, row=4, pady=3)

        self.deleteOnDownload = Checkbutton(self.controlFrame, text="Delete after download", variable=self.deleteOnDownloadVar,bg=bgColor)
        self.deleteOnDownload.grid(column=3, row=4)


        self.addPlaylistBtn = Button(self.controlFrame, text="Playlist Audio", command= lambda : self.addPlaylist(False), bg="#f9c74f",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addPlaylistBtn.grid(column=1, row=3)
        

        self.addUrlBtn = Button(self.controlFrame, text="Single Audio", command=lambda : self.addUrl(False), bg="#ffe3b0",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addUrlBtn.grid(column=1, row=2)

        self.addPlaylistVideoBtn = Button(self.controlFrame, text="Playlist Video", command=lambda : self.addPlaylist(True), bg="#f3524c",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addPlaylistVideoBtn.grid(column=2, row=3)

        self.addUrlVideoBtn = Button(self.controlFrame, text="Single Video", command=lambda : self.addUrl(True), bg="#f3a29c",width=15,  padx=5, pady=5,font=('Arial', 12))
        self.addUrlVideoBtn.grid(column=2, row=2)


        self.statusFrame = Frame(self, padx=10, pady=10,bg=bgColor, borderwidth=2, relief="groove", width=80)
        self.statusFrame.pack(expand=True, padx=5, pady=5)

        self.audioCountLabel = Label(self.statusFrame, textvariable = self.audioCountVar, padx=10,font=('Arial', 12), bg=bgColor)
        self.audioCountLabel.grid(column=0, row=1)

        self.videoCountLabel = Label(self.statusFrame, textvariable = self.videoCountVar, padx=10,font=('Arial', 12), bg=bgColor)
        self.videoCountLabel.grid(column=1, row=1)

        self.statusLabel = Label(self.statusFrame, textvariable = self.statusVar, padx=10, font=('Arial', 12), bg=bgColor)
        self.statusLabel.grid(column=0,columnspan=2, row=2)


        self.optionsFrame1 = Frame(self.controlFrame, padx=5, pady=5, bg=bgColor, borderwidth=2, relief="groove")
        self.optionsFrame1.grid(padx=5, pady=5, row=1,rowspan=2, column=5, columnspan=3)

        self.playlistRangeLabel = Checkbutton(self.optionsFrame1, text="Playlist range", variable=self.playlistRangeVar,bg=bgColor)
        self.playlistRangeLabel.grid(column=1, columnspan=3, row=1)

        self.playlistLowerRange = Entry(self.optionsFrame1, textvariable=self.playlistLowerRangeVar, width=4)
        self.playlistLowerRange.grid(column=1, row=2)

        self.playlistRangeDashLabel = Label(self.optionsFrame1, text="-")
        self.playlistRangeDashLabel.grid(column=2, row=2)

        self.playlistUpperRange = Entry(self.optionsFrame1, textvariable=self.playlistUpperRangeVar, width=4)
        self.playlistUpperRange.grid(column=3, row=2)


        self.optionsFrame2 = Frame(self.controlFrame, padx=5, pady=5, bg=bgColor, borderwidth=2, relief="groove")
        self.optionsFrame2.grid(padx=5, pady=5, row=3,rowspan=2, column=5, columnspan=3)

        self.cutRangeLabel = Checkbutton(self.optionsFrame2, text="Cut song/video: ", variable=self.cutVar, bg=bgColor)
        self.cutRangeLabel.grid(column=1, columnspan=3, row=1)

        self.cutLowerRangeEntry = Entry(self.optionsFrame2, textvariable=self.cutLowerVar, width=4)
        self.cutLowerRangeEntry.grid(column=1, row=2)

        self.cutRangeDashLabel = Label(self.optionsFrame2, text="-")
        self.cutRangeDashLabel.grid(column=2, row=2)

        self.cutUpperRangeEntry = Entry(self.optionsFrame2, textvariable=self.cutUpperVar, width=4)
        self.cutUpperRangeEntry.grid(column=3, row=2)



        self.optionsFrame3 = Frame(self.controlFrame, padx=5, pady=5, bg=bgColor)
        self.optionsFrame3.grid(padx=5, pady=5, row=1, rowspan=5, column = 9, columnspan=3)

        self.addMdTags = Checkbutton(self.optionsFrame3, text="Add tags from\nYouTube metadata\n(Priority 1)", variable=self.addMdTagsVar, bg=bgColor)
        self.addMdTags.grid(column=1, columnspan=3, row=1,rowspan=2, pady=10)

        self.addTitleTags = Checkbutton(self.optionsFrame3, text="Add tags from title\nSplit on '-'\nEx) Artist - Song\n(Priority 2)", variable=self.addTitleTagsVar, bg=bgColor)
        self.addTitleTags.grid(column=1, columnspan=3, row=4,rowspan=2, pady=10)




        self.urlEntry = Entry(self.controlFrame, textvariable = self.urlVar,font=('Arial', 12), width=50)
        self.urlEntry.grid(column=1, row=1, columnspan=4, padx=5, pady=5)
        self.urlEntry.bind('<Button-1>',self.clearUrlEntry)                                             # Clear entry upon first click and after successful YouTube fetch

        self.scrollFrame = Frame(self, padx=5, pady=10, bg=bgColor)
        self.scrollFrame.pack()

        self.scroll_bar = Scrollbar(self.scrollFrame) 
        self.scroll_bar.pack(side=RIGHT, fill=Y) 

        self.mylist = Listbox(self.scrollFrame, yscrollcommand=self.scroll_bar.set, width= 120, listvariable=self.listVar, exportselection=False) 
        self.mylist.pack( side = LEFT, fill = BOTH ) 
        self.mylist.bind("<<ListboxSelect>>", self.showUrl)

        self.scroll_bar.config( command = self.mylist.yview ) 
        self.previewFrame = Frame(self, padx=10, pady=10, bg=bgColor)
        self.previewFrame.pack()

    def showUrl(self, ev):
        self.previewCutLowVar.set('0.00')
        self.previewCutHighVar.set('0.00')
        if self.previewUrlFrame != None:                                                # Destroy currently in preview frame
            self.previewUrlFrame.destroy()
            self.previewUrl = None
        try:
            selectedString = ev.widget.get(ev.widget.curselection()[0])
        except IndexError:
            return
        selectedUrl = selectedString.split(' ----- ')[0]                                # Get url of selected in listbox for self.urls key
        self.nameChangeVar.set(self.urls[selectedUrl]['name'])
        self.tagChangeVar.set('')
        formattedMetadata = ""                                                              # Display any metadata extracted from the url
        for i in [*self.urls[selectedUrl]['metadata']]:
            formattedMetadata += self.addLineBreaks(i + " : " + self.urls[selectedUrl]['metadata'][i]+"\n")

        urlFrame = Frame(self.previewFrame, padx=5, pady=5, bg=bgColor, borderwidth=2, relief="groove")                           # Pack url specific frame in preview frame
        urlFrame.pack(expand=True)

        urlName = Label(urlFrame, textvariable=self.nameChangeVar, bg=bgColor)
        urlName.grid(row=0, column=0, columnspan=10)

        urlLabel = Label(urlFrame, text=selectedUrl, font=('Helvetica', 12), bg=bgColor)
        urlLabel.grid(row=1, column=0,columnspan=10)

        urlDelete = Button(urlFrame, text="Delete",command=lambda:self.deleteUrl(selectedUrl), bg="#FF9999")
        urlDelete.grid(row=0, column=10)

        urlNameChangeEntry = Entry(urlFrame, textvariable = self.nameChangeVar, width=50, bg="#bbdddd")
        urlNameChangeEntry.grid(row=6, column=2)
        urlNameChangeEntry.bind('<Button-1>', self.clearNameEntry)

        urlChangeName = Button(urlFrame,text="Change Name", command=lambda:self.changeName(selectedUrl), bg="#99BBBB")
        urlChangeName.grid(row=6, column=3, columnspan=1)

        formattedInfo = ""
        if self.urls[selectedUrl]['cut']:
            formattedInfo += "Original Length: "+self.urls[selectedUrl]['length']+"\n"
            formattedInfo += "Cut Length: " + str(formatSeconds(self.urls[selectedUrl]['highCut']- self.urls[selectedUrl]['lowCut'])) + "\n"
            formattedInfo += "Cut Range: "+ formatSeconds(self.urls[selectedUrl]['lowCut']) + " - " + formatSeconds(self.urls[selectedUrl]['highCut'])
        else:
            formattedInfo += "Length: "+self.urls[selectedUrl]['length']

        urlInfoAndCutFrame = Frame(urlFrame, bg=bgColor, borderwidth=2, relief="groove")
        urlInfoAndCutFrame.grid(row=3, column=1)

        urlInfo = Label(urlInfoAndCutFrame, text=formattedInfo, bg=bgColor)
        urlInfo.grid(row=1, column=1)


        optionsFrame = Frame(urlInfoAndCutFrame, padx=5, pady=5, bg=bgColor, borderwidth=2, relief="groove")
        optionsFrame.grid(padx=5, pady=5, row=3,rowspan=2, column=5, columnspan=3)

        cutRangeBtn = Button(optionsFrame, text="Cut song/video: ",command= lambda:self.makeCutPreview(selectedUrl), bg=bgColor)
        cutRangeBtn.grid(column=1, columnspan=3, row=2)

        cutLowerRangeEntry = Entry(optionsFrame, textvariable=self.previewCutLowVar, width=4)
        cutLowerRangeEntry.grid(column=1, row=1)

        cutRangeDashLabel = Label(optionsFrame, text="-")
        cutRangeDashLabel.grid(column=2, row=1)

        cutUpperRangeEntry = Entry(optionsFrame, textvariable=self.previewCutHighVar, width=4)
        cutUpperRangeEntry.grid(column=3, row=1)

        
        urlMetadata = Label(urlFrame, text=formattedMetadata, bg=bgColor)
        urlMetadata.grid(row=3, column=2, columnspan=1)

        if not self.urls[selectedUrl]['includeVideo']:
            urlTags = Frame(urlFrame, padx=5, pady=5, bg=bgColor, borderwidth=2, relief="groove")
            urlTags.grid(row=8, column=2)

            urlTagsTitle = Label(urlTags, text="MP3 Metadata Tags: ",fg="#119911", bg=bgColor)
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

        imgUrl = requests.get(self.urls[selectedUrl]['yt'].thumbnail_url)
        img = Image.open(BytesIO(imgUrl.content))
        img = img.resize((160,90))
        render = ImageTk.PhotoImage(img)
        imageLabel = Label(urlFrame, image=render, width=160, height=90, bg=bgColor)
        imageLabel.grid(row=3,rowspan=2,column=3,columnspan=5)
        imageLabel.image = render

        self.urls[selectedUrl]['urlLabel'] = urlLabel                               # Assign references to the widgets in preview frame to url dict entry
        self.urls[selectedUrl]['urlDelete'] = urlDelete
        self.urls[selectedUrl]['urlInfo'] = urlInfo
        self.urls[selectedUrl]['urlFrame'] = urlFrame
        self.previewUrlFrame = urlFrame
        self.previewUrl = selectedUrl
    
    def deleteUrl(self, url):
        self.urls[url]['urlFrame'].destroy()                                        # or self.previewUrlFrame.destroy()
        self.previewUrl = None
        self.mylist.delete(self.mylist.curselection()[0])
        if self.urls[url]['includeVideo']:
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])-1))     # Decrement count by 1
        else:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])-1))     # Decrement count by 1
        del self.urls[url]

    def makeCutPreview(self, url):
        lowArr = self.previewCutLowVar.get().split('.')
        highArr = self.previewCutHighVar.get().split('.')
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
        except:
            print("errrrrorrr")
            self.statusVar.set('Invalid cut range, length of video is '+str(formatSeconds(self.urls[url]['lengthInSeconds'])))
            self.statusLabel['fg'] = "red"
            return
        if high > int(self.urls[url]['lengthInSeconds']) or high-low < 0:
            self.statusVar.set('Invalid cut range, length of video is '+str(formatSeconds(self.urls[url]['lengthInSeconds'])))
            self.statusLabel['fg'] = "red"
            return
        self.urls[url]['cut'] = True
        self.urls[url]['lowCut'] = low
        self.urls[url]['highCut'] = high
        formattedInfo = ''
        formattedInfo += "Original Length: "+self.urls[url]['length']+"\n"
        formattedInfo += "Cut Length: " + str(formatSeconds(high- low)) + "\n"
        formattedInfo += "Cut Range: "+ formatSeconds(low) + " - " + formatSeconds(high)
        self.urls[url]['urlInfo']['text'] = formattedInfo


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
            print("errrrrorrr")
            return False
        if high > int(seconds) or high-low < 0:
            self.statusVar.set('Invalid cut range, length of video is '+str(formatSeconds(int(seconds))))
            self.statusLabel['fg'] = "red"
            return False
        return [low, high]


    def changeName(self, url):
        newName = self.nameChangeVar.get()
        self.mylist.delete(self.mylist.curselection()[0])
        self.urls[url]['name'] = newName
        mediaTag = None
        if self.urls[url]['includeVideo']:
            mediaTag = '(Video)'
        else:
            mediaTag = '(Audio)'
        self.mylist.insert(END, url+" ----- "+newName+" "+mediaTag) 
        self.nameChangeVar.set(newName)
        self.mylist.selection_set('end') 
        self.clearNameChangeEntryNextClick = True

    def addLineBreaks(self, string):                                                # Helper function for displaying metadata
        retList = string
        for i in range(1,int(len(string)/50)+1):
            retList = retList[:i*50] + '\n' + retList[i*50:]
        return retList

    def deleteAllAudio(self):
        for i in [*self.urls]:
            if not self.urls[i]['includeVideo']:
                if i == self.previewUrl:
                    self.urls[i]['urlFrame'].destroy()                                        # or self.previewUrlFrame.destroy()
                    self.previewUrl = None
                self.audioCountVar.set('Audio: 0')
                urlsInList = self.listVar.get()
                for k,j in enumerate(urlsInList):
                    listUrl = j.split("-----")[0].strip()
                    print(listUrl)
                    if listUrl == i:
                        self.mylist.delete(k)
                del self.urls[i]

    def deleteAllVideo(self):
        for i in [*self.urls]:
            if self.urls[i]['includeVideo']:
                if i == self.previewUrl:
                    self.urls[i]['urlFrame'].destroy()                                        # or self.previewUrlFrame.destroy()
                    self.previewUrl = None
                self.videoCountVar.set('Video: 0')
                urlsInList = self.listVar.get()
                for k,j in enumerate(urlsInList):
                    listUrl = j.split("-----")[0].strip()
                    if listUrl == i:
                        self.mylist.delete(k)
                del self.urls[i]


    def addTag(self, url):
        self.clearTagEntryNextClick = True
        tagKey = self.tagVar.get()
        tagValue = self.tagChangeVar.get()
        print(self.urls[url]['tagList'])
        for n in self.urls[url]['tagList']:
            print("N: ",n)
            if n[0] == tagKey:
                self.urls[url]['tagList'].remove(n)
                n[2].destroy()
        tagDeleteButton = Button(self.urls[url]['urlTags'], text="X "+tagKey+" : "+tagValue,bg="#77cc55")
        tagDeleteButton.pack(side=BOTTOM)
        data={"tagKey": tagKey, "tagValue": tagValue, 'url':url}
        tagDeleteButton.bind("<Button-1>", lambda event, arg=data: self.deleteTag(event, arg))

        self.urls[url]['tagList'].append([tagKey,tagValue, tagDeleteButton])
    
    def deleteTag(self, ev, arg):
        print("DELETING TAG")
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

    def addPlaylist(self, includeVideo):
        inputPlaylist = self.urlVar.get()
        if self.cutVar.get():
                self.statusVar.set("Can't cut playlist, click URLs in list to modify")
                self.statusLabel['fg'] = "red"
                return
        try:
            playlistUrls = pytube.Playlist(inputPlaylist).video_urls
        except KeyError:
            print("No response from YouTube")
            self.statusVar.set('Failed to fetch playlist')
            self.statusLabel['fg'] = "red"
            return
        totalCount = 0
        successCount = 0
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
            for b in [*self.urls]:                                              # If url is already in list, flash the entry widget
                if b == j:
                    self.statusVar.set('...video is already in list')
                    self.statusLabel['fg'] = "red"
                    self.urlVar.set("URL " + j + " already entered")
                    self.update()
                    self.clearUrlEntryNextClick = True
                    repeated = True
                    continue
            if repeated:
                totalCount+=1
                continue
            self.statusVar.set('Succeeded: '+str(successCount) + "/" + str(len(playlistUrls)) +" : Failed: "+str(totalCount-successCount) +"/" + str(len(playlistUrls)))
            self.statusLabel['fg'] = "blue"
            self.update()
            totalCount+=1
            yt = None
            try:
                yt = pytube.YouTube(j)
            except (pytube.exceptions.VideoUnavailable, pytube.exceptions.RegexMatchError):
                print('Video is unavailable at:::'+j)
                continue
            except pytube.exceptions.VideoPrivate:
                print('Video is private at:::'+j)
                continue
            except KeyError:
                print('Video has been deleted at:::'+j)
                continue
            stream = yt.streams.filter(only_audio=(not includeVideo)).first()
            md = ''
            tl = []
            alreadyAddedTitleTags = False
            try:
                md = [*yt.metadata][0]
                for g in [*md]:
                    print("Is " + g + " in : ", [*self.mdToTag])
                    if g in [*self.mdToTag]:
                        tl.append([self.mdToTag[g], md[g]])
                        print([self.mdToTag[g], md[g]])
            except IndexError:
                print('no metadata')
                if len(yt.title.split('-')) >1 and self.addTitleTagsVar.get():
                    tl.append(['Title', yt.title.split('-')[1]])
                    tl.append(['Contributing Artists',yt.title.split('-')[0]])
                    alreadyAddedTitleTags = True
                pass
            # if self.addTitleTagsVar.get() and not alreadyAddedTitleTags and len(yt.title.split('-')) > 1:
            #     tl.append(['Title', yt.title.split('-')[1]])
            #     tl.append(['Contributing Artists',yt.title.split('-')[0]])
            self.urls[j] = {'includeVideo':includeVideo, 'yt':yt,'stream': stream, 'name':yt.title, 'length':formatSeconds(yt.length),'lengthInSeconds': yt.length, 'tagList':tl, 'metadata':md, 'cut':False}
            mediaTag = None
            if includeVideo:
                self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])+1))
                mediaTag = '(Video)'
            else:
                self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])+1))
                mediaTag = '(Audio)'
            self.mylist.insert(END, j+" ----- "+stream.default_filename[:-4]+" "+mediaTag)
                
            successCount+=1
        self.clearUrlEntryNextClick = True
        self.statusVar.set('Done! : Succeeded: '+str(successCount)+" : Failed: "+str(totalCount-successCount))
        self.statusLabel['fg'] = "green"
        self.update()
        

    def addUrl(self, includeVideo):
        if self.playlistRangeVar.get():
            self.statusVar.set("Can't apply playlist range to single URL")
            self.statusLabel['fg'] = "red"
            self.update()
            return
        self.statusVar.set('Fetching video from YouTube...')
        self.statusLabel['fg'] = "blue"
        self.update()
        inputUrl = self.urlVar.get()
        exists = False
        for i in [*self.urls]:                                              # If url is already in list, flash the entry widget
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
        yt=None
        try:
            yt = pytube.YouTube(inputUrl)
        except (pytube.exceptions.VideoUnavailable, pytube.exceptions.RegexMatchError) as e:
            print(e.args)
            self.statusVar.set('Failed to fetch video')
            self.statusLabel['fg'] = "red"
            return
        except pytube.exceptions.VideoPrivate:
            print('Video is private at:::'+j)
            return
        except KeyError:
            print('Video has been deleted at:::'+j)
            return
        stream = yt.streams.filter(only_audio=(not includeVideo)).first()
        md = ''
        tl = []
        alreadyAddedTitleTags = False
        if self.addMdTags:
            try:
                md = [*yt.metadata][0]
                for g in [*md]:
                    if g in [*self.mdToTag]:
                        tl.append([self.mdToTag[g], md[g]])
            except IndexError:
                print('no metadata')
                if len(yt.title.split('-')) >1 and self.addTitleTagsVar.get():
                    tl.append(['Title', yt.title.split('-')[1]])
                    tl.append(['Contributing Artists',yt.title.split('-')[0]])
                    alreadyAddedTitleTags = True
                pass
        # if self.addTitleTagsVar.get() and not alreadyAddedTitleTags and len(yt.title.split('-')) > 1:
        #     tl.append(['Title', yt.title.split('-')[1]])
        #     tl.append(['Contributing Artists',yt.title.split('-')[0]])
        cutRange = False
        if self.cutVar.get():
            cutRange = self.makeCut(inputUrl, yt.length)
            if not cutRange:
                return
        self.statusVar.set('Success!')
        self.statusLabel['fg'] = "green"
        self.clearUrlEntryNextClick = True
        self.urls[inputUrl] = {'includeVideo':includeVideo, 'yt': yt, 'stream': stream, 'name':stream.default_filename[:-4], 'length':formatSeconds(yt.length),'lengthInSeconds': yt.length, 'tagList':tl, 'metadata':md, 'cut':False}
        mediaTag = None
        if includeVideo:
            self.videoCountVar.set('Video: '+str(int(self.videoCountVar.get().split()[1])+1))
            mediaTag = "(Video)"
        else:
            self.audioCountVar.set('Audio: '+str(int(self.audioCountVar.get().split()[1])+1))
            mediaTag = "(Audio)"
        self.mylist.insert(END, inputUrl+" ----- "+stream.default_filename[:-4]+" "+mediaTag) 
        self.urlVar.set('')
        if cutRange:
            self.urls[inputUrl]['cut'] = True
            self.urls[inputUrl]['lowCut'] = cutRange[0]
            self.urls[inputUrl]['highCut'] = cutRange[1]


    def download(self):
        if not len([*self.urls]):
            self.statusVar.set('No urls provided')
            self.statusLabel['fg'] = "red"
            self.update()
            return
        self.statusVar.set('Downloading...')
        self.statusLabel['fg'] = "blue"
        self.update()
        vidNames = []
        directory = fd.askdirectory()
        if not directory:
            self.statusVar.set('No directory chosen')
            self.statusLabel['fg'] = "red"
            return
        for k,u in enumerate([*self.urls]):
            self.statusVar.set('Downloading...('+str(k+1)+"/"+str(len([*self.urls]))+")")
            self.statusLabel['fg'] = "blue"
            self.update()
            if self.urls[u]['includeVideo']:
                if self.urls[u]['cut']:
                    fileName = self.urls[u]['name']+'.mp4'
                    self.urls[u]['stream'].download(output_path=directory, filename='tempCut')
                    tempPath = os.path.join(directory, 'tempCut.mp4')                                   # Moviepy would only write first second of video if path name had spaces
                    low = self.urls[u]['lowCut']
                    high = self.urls[u]['highCut']
                    finalPath=os.path.join(directory, self.urls[u]['name']+'.mp4')
                    y = VideoFileClip(tempPath)
                    y=y.subclip(low,high)
                    y.write_videofile(finalPath)                                                        # Save as final path name
                    y.close()
                    os.remove(tempPath)
                continue
            dlReturn = self.urls[u]['stream'].download(output_path=directory, filename=self.urls[u]['name'])
            print("CREATING SONG")
            print("DL Title", dlReturn.title())
            fn = self.urls[u]['name']+'.mp4'
            full_path = os.path.join(directory, fn)
            output_path = dlReturn[:-1]+"3"
            clip = AudioFileClip(dlReturn)   
            if self.urls[u]['cut']:
                low = self.urls[u]['lowCut']
                high = self.urls[u]['highCut']
                clip = clip.subclip(low,high)
            clip.write_audiofile(output_path,bitrate="320k")
            clip.close()
            os.remove(dlReturn)
            if len(self.urls[u]['tagList']) != 0:                           # Try to match metadata with mp3 tags to add to output files
                newAudioFile = eyed3.load(output_path)
                print(output_path)
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
        if self.deleteOnDownloadVar.get():
            self.urls = {}
            self.mylist.delete('0', 'end')
            self.audioCountVar.set('Audio: 0')
            self.videoCountVar.set('Video: 0')
            if self.previewUrlFrame != None:                                                # Destroy currently in preview frame
                self.previewUrlFrame.destroy()
                self.previewUrl = None
        self.statusVar.set('Success! Downloaded into: '+directory)
        self.statusLabel['fg'] = "green"
        

def formatSeconds(seconds): 
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

def main():
    root = Tk()
    root['bg'] = bgColor
    root.geometry("1200x1200")
    root.title("YouTube Downloader")
    app = App(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
