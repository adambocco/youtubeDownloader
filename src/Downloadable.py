
import os
from moviepy.editor import AudioFileClip, VideoFileClip
import pytube                           # install from git :: python3 -m pip install git+https://github.com/nficano/pytube.git
from tkinter import *
from tkinter import filedialog as fd
from eyed3 import load as eyed3Load
from PIL import Image, ImageTk
from io import BytesIO
from requests import get as requestsGet
from tkSliderWidget import Slider



from helpers import formatSeconds

class Downloadable:
    metadataToTag = {'Artist':'Contributing Artists','Artists':'Contributing Artists', 'Title':'Title', 'Album' : 'Album', 'Song':'Title'}   

      
    def __init__(self, url, onlyAudio):
        self.url = url
        self.onlyAudio = onlyAudio

        self.widgetIds = {}

        try:
            print("Fetching URL: ", url)
            self.youtubeObject = pytube.YouTube(url)
        except (pytube.exceptions.VideoUnavailable, pytube.exceptions.RegexMatchError,
                pytube.exceptions.VideoPrivate, KeyError) as e:
            print(e)
            raise Exception

        self.youtubeObject = pytube.YouTube(url)
        self.stream = self.youtubeObject.streams.filter().first()
        self.length = self.youtubeObject.length
        self.name = self.youtubeObject.title
        self.displayName = self.name + " --- " + ("Audio" if self.onlyAudio else "Video")

        self.cut = False
        self.lowCut = 0
        self.highCut = self.length

        if len([*self.youtubeObject.metadata]) > 0:
            self.metadata = [*self.youtubeObject.metadata][0]
        else:
            self.metadata = []

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
        
    def makeCut(self, low, high):
        if low > self.length or high > self.length or low < 0 or high < 0:
            return
        self.low = low
        self.high = high

    def setOnlyAudio(self, onlyAudio):
        self.stream = self.youtubeObject.streams.filter(only_audio=(onlyAudio)).first()

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
            print("NEWVOLUME: ",newVolume)

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

            newAudioFile = eyed3Load(finalPath)

            for tagKey, tagValue in self.tags.items():
                if (tagValue == ""):
                    continue
                if tagKey == 'Title':
                    newAudioFile.tag.title = tagValue
                elif tagKey == 'Contributing Artists':
                    newAudioFile.tag.artist = tagValue
                elif tagKey == 'Album Artist':
                    newAudioFile.tag.album_artist = tagValue
                elif tagKey == "Track Number":
                    try:
                        v = int(tagValue)
                    except:
                        continue
                    newAudioFile.tag.track_num = v
                elif tagKey == "Year":
                    newAudioFile.tag.year = tagValue
                elif tagKey == "Album":
                    newAudioFile.tag.album = tagValue
            newAudioFile.tag.save()
        else:
            
            clip.close()
            os.rename(downloadedFile, finalPath)
        return finalPath

    def previewClip(self):
        path = self.download("./")
        os.system("ffplay.exe " + path)
        os.remove(path)

