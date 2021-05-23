# Author: Adam Bocco - github.com/adambocco
# YouTube Downloader


# Make executable with: pyinstaller -F --add-data "./ffmpeg/*;./ffmpeg/" youtubeDownloader.py
import signal
import multiprocessing
import subprocess
import os
import sys
from moviepy.editor import AudioFileClip, VideoFileClip
from requests import get as requestsGet
import youtube_dl
from tkinter import *
from tkinter import filedialog as fd
import eyed3
from PIL import Image, ImageTk
from io import BytesIO
from requests import get as requestsGet
from tkSliderWidget import Slider
from urllib.error import HTTPError
import pygame

from Stream import Stream


FFMPEG_PATH = "./ffmpeg/ffmpeg.exe"
FFPLAY_PATH = "./ffmpeg/ffplay.exe"
NUM_THREADS = 4

from helpers import formatSeconds, makeEllipsis, sanitizeFilename

class Downloadable:
    metadataToTag = {'Artist':'Contributing Artists','Artists':'Contributing Artists', 'Title':'Title', 'Album' : 'Album', 'Song':'Title'}   

    previewClipVar = None
    previewThread = None

    previewDownloadable = None
    previewLabelVar = None


    def __init__(self, youtubeObject, onlyAudio):

        self.youtubeObject = youtubeObject

        self.onlyAudio = onlyAudio

        self.url = "https://www.youtube.com/watch?v="+youtubeObject['id']

        self.audioOnlyPostProcessor = { 
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }

        self.ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist":True,

        }

        self.imgUrl = self.youtubeObject['thumbnail'] 

        self.allStreams = []
        self.streams = []

        self.audioStream = None
        self.videoStreams = []

        self.resolutionToStream = {}

        for stream in self.youtubeObject["formats"]:

            try:
                newStream = Stream(stream)
                self.allStreams.append(newStream)
                if newStream.mediaType == "A" and newStream.ext == "m4a":
                    if self.audioStream != None:
                        if newStream.stream["tbr"] > self.audioStream.stream["tbr"]:
                            self.audioStream = newStream 

                    self.audioStream = newStream
                    self.streams.append(newStream)

                elif newStream.mediaType == "V" and newStream.resolution not in self.resolutionToStream.keys():
                    self.resolutionToStream[newStream.resolution] = newStream
                    self.streams.append(newStream)
                
                elif newStream.mediaType == "AV":
                    if newStream.resolution in self.resolutionToStream.keys():
                        self.streams.remove(self.resolutionToStream[newStream.resolution])
                    self.streams.append(newStream)

                    self.resolutionToStream[newStream.resolution] = newStream

            except Exception as e:
                pass
            
        self.videoStreams = self.resolutionToStream.values()

        if onlyAudio:
            self.stream = self.audioStream
        else:
            self.stream = None
            for videoStream in self.videoStreams:
                if videoStream.mediaType == "AV":
                    if self.stream == None or self.stream.resolution < videoStream.resolution:
                        self.stream = videoStream
            if self.stream == None:
                self.stream = self.videoStreams[0]

        self.videoStream = self.stream
        self.previewStream = self.stream


        self.length = self.youtubeObject["duration"]
        self.name = self.youtubeObject["title"]

        # Display name is the key for [youtubeDownloader::downloadables]
        self.displayName = self.name + " --- " + ("Audio" if self.onlyAudio else "Video")

        self.cut = False
        self.lowCut = 0
        self.highCut = self.length

        self.tags = {}

        if "track" in self.youtubeObject:
            self.tags["Track Number"] = self.youtubeObject["track"]
        else:
            self.tags["Track Number"] = ""

        if "year" in self.youtubeObject:
            self.tags["Year"] = self.youtubeObject["year"]
        else:
            self.tags["Year"] = ""

        if "album" in self.youtubeObject:
            self.tags["Album"] = self.youtubeObject["album"]
        else:
             self.tags["Album"] = ""

        if "album_artist" in self.youtubeObject:
            self.tags["Album Artist"] = self.youtubeObject["album_artist"]
        else:
            self.tags["Album Artist"] = ""

        if "artist" in self.youtubeObject:
            self.tags["Contributing Artists"] = self.youtubeObject["artist"]
        else:
            self.tags["Contributing Artists"] = ""

        if "track" in self.youtubeObject:
            self.tags["Title"] = self.youtubeObject["track"]
        else:
            self.tags["Title"] = ""



        self.tagIds = {"Title" : None,
                    "Contributing Artists" : None,
                    "Album" : None,
                    "Album Artist" : None,
                    "Year" : None,
                    "Track Number" : None}

        self.volumeMultiplier = 0


    def setStreamByResolution(self, stringVar):
        resolution = stringVar.get()
        self.stream = self.resolutionToStream[int(resolution)]
        self.videoStream = self.stream


    def setOnlyAudio(self, onlyAudio):
        self.onlyAudio = onlyAudio
        self.displayName = self.name + " --- " + ("Audio" if onlyAudio else "Video")
        if onlyAudio:
            self.stream = self.audioStream
        else:
            self.stream = self.videoStream

    def getLengthString(self):
        return formatSeconds(self.length)


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
        url = self.stream.url
        extension = ".mp3" if self.onlyAudio else ".mp4"
        finalPath = os.path.join(directory, sanitizeFilename(self.name) + extension)

        clip = AudioFileClip(url) if self.onlyAudio else VideoFileClip(url)

        if self.stream.mediaType == "V":
            audioClip = AudioFileClip(self.audioStream.url)
            
            clip = clip.set_audio(audioClip)


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

            if self.onlyAudio:
                clip.write_audiofile(finalPath, bitrate=bitrate)
                self.applyID3Tags(finalPath)
            else:
                clip.write_videofile(finalPath, threads=NUM_THREADS)   


            clip.close()


        elif self.onlyAudio:

            clip.write_audiofile(finalPath, bitrate=bitrate)

            clip.close()

            self.applyID3Tags(finalPath)

        else:
        
            clip.write_videofile(finalPath, threads=NUM_THREADS) 
            clip.close()
        try:
            clip.close()
        except:
            pass
        return finalPath


    def previewClip(self, labelVar, ffmpegOrMoviepy):
        Downloadable.previewLabelVar = labelVar
        stopPreview()

        labelVar.set("Playing:\n"+makeEllipsis(self.name,20))

        newVolume = 0
        if self.volumeMultiplier != 0:
            newVolume = (1+self.volumeMultiplier/100)**2 if self.volumeMultiplier < 0 else self.volumeMultiplier/5

        low=0
        high=0
        if self.cut:
            # Clip the video
            low = self.lowCut
            high = self.highCut
            if low < 0:
                low = 0
            if high > self.length:
                high = self.length

        Downloadable.previewDownloadable = self
        url = self.stream.url if self.onlyAudio else self.previewStream.url
        if ffmpegOrMoviepy == "ffmpeg":
            cmd = "ffplay "
            if self.cut:
                cmd += "-ss " + str(low)
                cmd += " -t " + str(high) + " "
            cmd += "-loglevel error "
            cmd += self.stream.url
            Downloadable.previewThread = subprocess.Popen(cmd)
        elif ffmpegOrMoviepy == "moviepy":
            Downloadable.previewThread = multiprocessing.Process(target=startPreview, args=(self.onlyAudio, url, self.cut, low, high, newVolume))
            Downloadable.previewThread.start()

    def applyID3Tags(self, path):
        eyed3File = eyed3.load(path)

        if self.imgUrl == None:
            self.imgUrl = requestsGet(self.youtubeObject.thumbnail_url)

        eyed3File.tag.images.set(3, requestsGet(self.imgUrl).content, 'image/jpeg')

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


def startPreview(onlyAudio, url, cut, low, high, volume):

    clip = None
    if onlyAudio:
        clip = AudioFileClip(url) 
    else:
        clip = VideoFileClip(url) 

    if volume != 0:

        clip = clip.volumex(volume)

    if cut:
        clip = clip.subclip(low,high)
    print("PREVIEWING WITH MOVIEPY")
    clip.preview()
    clip.close()

    # See https://github.com/Zulko/moviepy/issues/575
    pygame.quit()


def stopPreview():
    Downloadable.previewLabelVar.set("Playing:\n")
    if Downloadable.previewThread != None:
        print("Preview thread trying to stop: ", Downloadable.previewThread)
    # try:
        Downloadable.previewThread.terminate()
        Downloadable.previewThread.kill()
        # os.kill(Downloadable.previewThread.pid, signal.SIGTERM)
        os.kill(Downloadable.previewThread.pid, 0)
        os.system("taskkill  /F /pid "+str(Downloadable.previewThread.pid))

        # except Exception as e:
        #     print("Error killing preview: ", e)
        #     pass

    Downloadable.previewThread = None
    Downloadable.previewClipVar = None
    Downloadable.previewDownloadable = None