

import os, sys, time
import moviepy 
from moviepy.editor import AudioFileClip
import re
import pytube                           # install from git :: python3 -m pip install git+https://github.com/nficano/pytube.git
from tkinter import *
from tkinter import filedialog as fd
import eyed3


class App(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.urls = {}                                                                                              # Holds data from YouTube, references to widgets representing that data, and tags
        self.urlVar = StringVar()                                                                                   # textvariable for url entry
        self.urlVar.set("Enter the YouTube URL of a video or playlist") 
        self.nameChangeVar = StringVar()                                                                            # textvariable for name change entry 
        self.listVar = StringVar()                                                                                  # listvariable for urls added listbox
        self.countVar = StringVar()                                                                                 # textvariable for count of songs added label
        self.countVar.set('Count: 0')
        self.tagChangeVar = StringVar()                                                                             # textvariable for add mp3 tag entry
        self.tagVar = StringVar()                                                                                   # textvariable for dropdown list of songs
        self.tagOptions = ['Title', 'Contributing Artists', 'Album', 'Album Artist', 'Year', 'Track Number']        # Options for tags optionmenu
        self.tagVar.set(self.tagOptions[0])
        self.clearUrlEntryNextClick = True
        self.clearNameChangeEntryNextClick = True
        self.previewUrlFrame = None
        self.mdToTag = {'Artist':'Contributing Artists', 'Title':'Title', 'Album' : 'Album'}                        # Maps youtube metadata to mp3 header tag name
        self.createWidgets()


    def createWidgets(self): 
        self.controlFrame = Frame(self, padx=10, pady=10)
        self.controlFrame.pack(expand=True)

        self.start = Button(self.controlFrame, text="Start Download", command=self.download, bg="#aaf0bb",  padx=10, pady=10)
        self.start.pack(side=RIGHT)

        self.addPlaylist = Button(self.controlFrame, text="Add Playlist", command=self.addPlaylist, bg="#c498f0",  padx=10, pady=10)
        self.addPlaylist.pack(side=RIGHT)

        self.addUrl = Button(self.controlFrame, text="Add Video", command=self.addUrl, bg="#a4b8f0",  padx=10, pady=10)
        self.addUrl.pack(side=RIGHT)

        self.countLabel = Label(self.controlFrame, textvariable = self.countVar)
        self.countLabel.pack(side=BOTTOM)

        self.urlEntry = Entry(self.controlFrame, textvariable = self.urlVar, width=100)
        self.urlEntry.pack()
        self.urlEntry.bind('<Button-1>',self.clearUrlEntry)                                             # Clear entry upon first click and after successful YouTube fetch

        self.scrollFrame = Frame(self, padx=5, pady=10)
        self.scrollFrame.pack()

        self.scroll_bar = Scrollbar(self.scrollFrame) 
        self.scroll_bar.pack(side=RIGHT, fill=Y) 

        self.mylist = Listbox(self.scrollFrame, yscrollcommand=self.scroll_bar.set, width= 150, listvariable=self.listVar, exportselection=False) 
        self.mylist.pack( side = LEFT, fill = BOTH ) 
        self.mylist.bind("<<ListboxSelect>>", self.showUrl)

        self.scroll_bar.config( command = self.mylist.yview ) 
        self.previewFrame = Frame(self, padx=10, pady=10)
        self.previewFrame.pack()

    def showUrl(self, ev):
        if self.previewUrlFrame != None:                                                # Destroy currently in preview frame
            self.previewUrlFrame.destroy()
        selectedString = ev.widget.get(ev.widget.curselection()[0])
        selectedUrl = selectedString.split(' ----- ')[0]                                # Get url of selected in listbox for self.urls key
        self.nameChangeVar.set(self.urls[selectedUrl]['name'])
        self.tagChangeVar.set('')
        formattedMetadata = ""                                                              # Display any metadata extracted from the url
        for i in [*self.urls[selectedUrl]['metadata']]:
            formattedMetadata += self.addLineBreaks(i + " : " + self.urls[selectedUrl]['metadata'][i]+"\n")

        urlFrame = Frame(self.previewFrame, padx=10, pady=10)                           # Pack url specific frame in preview frame
        urlFrame.pack(expand=True)

        urlLabel = Label(urlFrame, text=selectedUrl, font=('Helvetica', 12))
        urlLabel.grid(row=0, column=0,columnspan=10)

        urlDelete = Button(urlFrame, text="Delete",command=lambda:self.deleteUrl(selectedUrl), bg="#FF9999")
        urlDelete.grid(row=0, column=10)

        urlNameChangeEntry = Entry(urlFrame, textvariable = self.nameChangeVar, width=50, bg="#bbdddd")
        urlNameChangeEntry.grid(row=1, column=1)

        urlChangeName = Button(urlFrame,text="Change Name", command=lambda:self.changeName(selectedUrl), bg="#99BBBB")
        urlChangeName.grid(row=1, column=2, columnspan=1)

        urlLength = Label(urlFrame, text="Length: "+self.urls[selectedUrl]['length'])
        urlLength.grid(row=3, column=1, columnspan=1)
        
        urlMetadata = Label(urlFrame, text=formattedMetadata)
        urlMetadata.grid(row=4, column=1, columnspan=1)

        urlTags = Frame(urlFrame, padx=5, pady=5)
        urlTags.grid(row=4, column=2)

        urlTagsTitle = Label(urlTags, text="MP3 Metadata Tags: ",fg="#119911")
        urlTagsTitle.pack(side=LEFT)

        for k in self.urls[selectedUrl]['tagList']:                                         # Load any tags previously selected
            tagDeleteButton = Button(urlTags, text="X "+k[0]+" : "+k[1],bg="#77cc55")
            tagDeleteButton.pack(side=BOTTOM)

        tagSelect = OptionMenu(urlFrame, self.tagVar, *self.tagOptions)
        tagSelect.grid(row=5, column=1, columnspan=1)
        tagSelect.config(width=40, bg="#DDFFAA")

        tagEntry = Entry(urlFrame, textvariable = self.tagChangeVar, width=40, bg="#DDFFAA")
        tagEntry.grid(row=5, column=2, columnspan=1)

        addTag = Button(urlFrame, text="Add Tag",command=lambda:self.addTag(selectedUrl), bg="#DDFFAA")
        addTag.grid(row=5, column=3, columnspan=1)

        self.urls[selectedUrl]['urlLabel'] = urlLabel                               # Assign references to the widgets in preview frame to url dict entry
        self.urls[selectedUrl]['urlDelete'] = urlDelete
        self.urls[selectedUrl]['urlLength'] = urlLength
        self.urls[selectedUrl]['urlTags'] = urlTags
        self.urls[selectedUrl]['urlFrame'] = urlFrame
        self.previewUrlFrame = urlFrame
    
    def deleteUrl(self, url):
        self.urls[url]['urlFrame'].destroy()                                        # or self.previewUrlFrame.destroy()
        del self.urls[url]
        self.mylist.delete(self.mylist.curselection()[0])
        self.countVar.set('Count: '+str(int(self.countVar.get().split()[1])-1))     # Decrement count by 1

    def changeName(self, url):
        newName = self.nameChangeVar.get()
        self.mylist.delete(self.mylist.curselection()[0])
        self.urls[url]['name'] = newName
        self.mylist.insert(END, url+" ----- "+newName) 
        self.nameChangeVar.set(newName)
        self.mylist.selection_set('end') 
        self.clearNameChangeEntryNextClick = True

    def addLineBreaks(self, string):                                                # Helper function for displaying metadata
        retList = string
        for i in range(1,int(len(string)/20)+1):
            retList = retList[:i*20] + '\n' + retList[i*20:]
        return retList

    def addTag(self, url):
        tagKey = self.tagVar.get()
        tagValue = self.tagChangeVar.get()
        print(self.urls[url]['tagList'])
        for n in self.urls[url]['tagList']:
            if n[0] == tagKey:
                self.deleteTag(url, tagKey)
        tagDeleteButton = Button(self.urls[url]['urlTags'], text="X "+tagKey+" : "+tagValue, bg="#77cc55", command=lambda:self.deleteTag(url, tagKey))
        tagDeleteButton.pack(side=BOTTOM)
        self.urls[url]['tagList'].append([tagKey,tagValue, tagDeleteButton])
    
    def deleteTag(self, url, tagKey):
        for m in self.urls[url]['tagList']:
            if m[0] == tagKey:
                m[2].destroy()
                self.urls[url]['tagList'].remove(m)

    def clearUrlEntry(self, ev):
        self.urlEntry['bg'] = "white" 
        if self.clearUrlEntryNextClick:
            self.clearUrlEntryNextClick = False
            self.urlVar.set('')

    def clearNameEntry(self, ev):
        if self.clearNameChangeEntryNextClick:
            self.clearNameChangeEntryNextClick = False
            self.nameChangeVar.set('')

    def addPlaylist(self):
        inputPlaylist = self.urlVar.get()
        playlistUrls = pytube.Playlist(inputPlaylist).video_urls
        
        for j in playlistUrls:
            try:
                yt = pytube.YouTube(j)
            except pytube.exceptions.VideoUnavailable:
                print('Video is unavailable at:::'+j)
                continue
            stream = yt.streams.filter(only_audio="True").first()
            md = ''
            try:
                md = [*yt.metadata][0]
            except IndexError:
                print('no metadata')
                pass
            self.urls[j] = {'stream': stream, 'name':stream.default_filename[:-4], 'length':formatSeconds(yt.length), 'tagList':[], 'metadata':md}
            self.mylist.insert(END, j+" ----- "+stream.default_filename[:-4]) 
            self.countVar.set('Count: '+str(int(self.countVar.get().split()[1])+1))
        self.clearUrlEntryNextClick = True

    def addUrl(self):
        inputUrl = self.urlVar.get()
        exists = False
        for i in [*self.urls]:                                              # If url is already in list, flash the entry widget
            if i == inputUrl:
                self.urlVar.set("Already entered") 
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
        try:
            yt = pytube.YouTube(inputUrl)
        except pytube.exceptions.VideoUnavailable:
            print("Video is unavilable at:::"+inputUrl)
            pass
            # TODO alert the user
        if len(yt.streams)==0: 
            print("NO STREAMS AVAILABLE") # TODO alert the user
        stream = yt.streams.filter(only_audio="True").first()
        md = ''
        tl = []
        try:
            md = [*yt.metadata][0]
            for g in [*md]:
                if g in [*self.mdToTag]:
                    tl.append([self.mdToTag[g], md[g]])
                    print([self.mdToTag[g], md[g]])
        except IndexError:
           print('no metadata')
           pass
        self.clearUrlEntryNextClick = True
        self.urls[inputUrl] = {'stream': stream, 'name':stream.default_filename[:-4], 'length':formatSeconds(yt.length), 'tagList':tl, 'metadata':md}
        self.mylist.insert(END, inputUrl+" ----- "+stream.default_filename[:-4]) 
        self.urlVar.set('')
        self.countVar.set('Count: '+str(int(self.countVar.get().split()[1])+1))


    def download(self):
        vidNames = []
        directory = fd.askdirectory()
        for u in [*self.urls]:
            self.urls[u]['stream'].download(output_path=directory, filename=self.urls[u]['name'])
            fn = self.urls[u]['name']+'.mp4'
            full_path = os.path.join(directory, fn)
            output_path = os.path.join(directory, os.path.splitext(fn)[0] + '.mp3')
            clip = moviepy.editor.AudioFileClip(full_path)   
            clip.write_audiofile(output_path)
            os.remove(os.path.join(directory, fn))
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
        

def formatSeconds(seconds): 
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

def main():
    root = Tk()
    app = App(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
