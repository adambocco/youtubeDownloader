import subprocess
import threading
import os
import sys
from moviepy.editor import AudioFileClip, VideoFileClip
import pytube                           # install from git :: python3 -m pip install git+https://github.com/nficano/pytube.git
from tkinter import *
from tkinter import filedialog as fd
import eyed3
from PIL import Image, ImageTk
from io import BytesIO
from requests import get as requestsGet
from tkSliderWidget import Slider
from urllib.error import HTTPError


from helpers import formatSeconds

class Downloadable:
    metadataToTag = {'Artist':'Contributing Artists','Artists':'Contributing Artists', 'Title':'Title', 'Album' : 'Album', 'Song':'Title'}   

      
    def __init__(self, url, onlyAudio, youtubeObject=None):
        self.url = url
        self.onlyAudio = onlyAudio

        self.imgUrl = None

        if youtubeObject != None:
            self.youtubeObject = youtubeObject
        else:
            try:
                print("Fetching URL: ", url)
                self.youtubeObject = pytube.YouTube(url)
            except (pytube.exceptions.VideoUnavailable, pytube.exceptions.RegexMatchError,
                    pytube.exceptions.VideoPrivate, KeyError, HTTPError) as e:
                raise e


        self.stream = self.youtubeObject.streams.filter().first()
        self.length = self.youtubeObject.length
        self.name = self.youtubeObject.title

        # Display name is the key for [youtubeDownloader::downloadables]
        self.displayName = self.name + " --- " + ("Audio" if self.onlyAudio else "Video")

        self.cut = False
        self.lowCut = 0
        self.highCut = self.length

        if len([*self.youtubeObject.metadata]) > 0:
            self.metadata = [*self.youtubeObject.metadata][0]
            if len([*self.metadata]) > 1:
                self.allMetadata = [*self.youtubeObject.metadata]
            else:
                self.allMetadata = []
        else:
            self.metadata = []
            self.allMetadata = []

        self.tags = {"Title" : "",
                    "Contributing Artists" : "",
                    "Album" : "",
                    "Album Artist" : "",
                    "Year" : "",
                    "Track Number" : ""}
        self.tagIds = {"Title" : None,
                    "Contributing Artists" : None,
                    "Album" : None,
                    "Album Artist" : None,
                    "Year" : None,
                    "Track Number" : None}

        self.volumeMultiplier = 0

    def setOnlyAudio(self, onlyAudio):
        self.onlyAudio = onlyAudio
        self.displayName = self.name + " --- " + ("Audio" if onlyAudio else "Video")


    def makeCut(self, low, high):
        if low > self.length or high > self.length or low < 0 or high < 0:
            return
        self.low = low
        self.high = high

    def getLengthString(self):
        return formatSeconds(self.length)

    def generateTagListFromMetadata(self):
        for tagKey in [*self.metadata]:
            if tagKey in [*Downloadable.metadataToTag]:
                self.tags[Downloadable.metadataToTag[tagKey]] = self.metadata[tagKey]

    def generateTagListFromTitle(self):
        if len(self.name.split('-')) > 1:
            self.tags["Contributing Artists"] = self.name.split('-')[0]
            self.tags["Title"] = self.name.split('-')[1]

    def changeCut(self, low, high):
        if low == 0 and high == self.length:
            self.cut = False
            self.lowCut = 0
            self.highCut = self.length
            return False
        else:
            self.cut = True
            self.lowCut = low
            self.highCut = high
            return True

    def download(self, directory):
        bitrate = str(int(self.stream.bitrate/1000)) + "k"
        downloadedFile = self.stream.download(output_path=directory, filename='tempVid')
        extension = ".mp3" if self.onlyAudio else ".mp4"
        finalPath = os.path.join(directory, self.name.replace(" ", "_") + extension)

        tempPath = os.path.join(directory, 'tempVid.mp4')

        # Create MoviePy video object from YouTube downloaded video
        clip = AudioFileClip(downloadedFile) if self.onlyAudio else VideoFileClip(downloadedFile)

        if self.volumeMultiplier != 0:
            newVolume = (1+self.volumeMultiplier/100)**2 if self.volumeMultiplier < 0 else self.volumeMultiplier/5

            clip = clip.volumex(newVolume)

        if self.cut:

            # Clip the video
            low = self.lowCut
            high = self.highCut
            if low < 0:
                low = 0
            if high > clip.end:
                high = clip.end
            clip = clip.subclip(low,high)

            # Save as final path name

            if (self.onlyAudio):

                clip.write_audiofile(finalPath, bitrate=bitrate)
            else:
                clip.write_videofile(finalPath, bitrate=bitrate)   


            clip.close()
            os.remove(downloadedFile)

        elif self.onlyAudio:

            clip.write_audiofile(finalPath, bitrate=bitrate)


            clip.close()
            os.remove(downloadedFile)

            self.applyID3Tags(finalPath)

        else:
            
            clip.close()
            os.rename(downloadedFile, finalPath)
        return finalPath

    # From Masoud Rahimi on Stack Overflow - 
    # https://stackoverflow.com/questions/56370173/how-to-export-ffmpeg-into-my-python-program
    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)



    def previewClip(self):
        path = self.download("./")

        ffplay_path = "./ffmpeg/ffplay.exe"

        previewThread = popenAndCall(lambda:os.remove(path), [self.resource_path(ffplay_path), path])



    def applyID3Tags(self, path):
        eyed3File = eyed3.load(path)

        if self.imgUrl == None:
            self.imgUrl = requestsGet(self.youtubeObject.thumbnail_url)
            
        eyed3File.tag.images.set(3, BytesIO(self.imgUrl.content).getvalue(), 'image/jpeg')

        eyed3File.tag.title=self.tags["Title"]
        eyed3File.tag.artist=self.tags["Contributing Artists"]
        eyed3File.tag.album=self.tags["Album"]
        eyed3File.tag.album_artist=self.tags["Album Artist"]
        eyed3File.tag.year=self.tags["Year"]

        try: 
            eyed3File.tag.track_num = int(self.tags["Track Number"])
        except ValueError:
            pass
    
        eyed3File.tag.save()
        eyed3File.tag.save(version=eyed3.id3.ID3_V2_3)


# From sagar on Semicolon World 
# https://www.semicolonworld.com/question/56553/python-subprocess-callback-when-cmd-exits
def popenAndCall(onExit, popenArgs):

    def runInThread(onExit, popenArgs):
        proc = subprocess.Popen(popenArgs)
        proc.wait()
        onExit()
        return
    thread = threading.Thread(target=runInThread, args=(onExit, popenArgs))
    thread.start()
    # returns immediately after the thread starts
    return thread