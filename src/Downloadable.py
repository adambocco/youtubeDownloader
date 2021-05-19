# Author: Adam Bocco - github.com/adambocco
# YouTube Downloader 

# Make executable with: pyinstaller -F --add-data "./ffmpeg/*;./ffmpeg/" youtubeDownloader.py

import subprocess
import threading
import multiprocessing
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
from sanitize_filename import sanitize
import pygame


import ffmpeg

FFMPEG_PATH = "./ffmpeg/ffmpeg.exe"
FFPLAY_PATH = "./ffmpeg/ffplay.exe"
NUM_THREADS = 4

from helpers import formatSeconds, makeEllipsis

class Downloadable:
    metadataToTag = {'Artist':'Contributing Artists','Artists':'Contributing Artists', 'Title':'Title', 'Album' : 'Album', 'Song':'Title'}   

    previewClipVar = None
    previewThread = None
    previewFile = None
    previewDownloadable = None
    previewLabelVar = None


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


        self.streams = self.youtubeObject.streams.filter(file_extension="mp4")

        self.stream = self.streams.first()

        self.resolutionOptions = []
        self.resolutionToStream = {}

        for stream in self.youtubeObject.streams:
            if stream.resolution != None:
                if stream.resolution not in self.resolutionOptions:
                    self.resolutionOptions.append(stream.resolution)
                    self.resolutionToStream[stream.resolution] = stream
                elif not stream.is_dash and self.resolutionToStream[stream.resolution].is_dash:
                    self.resolutionToStream[stream.resolution] = stream
                elif (not (stream.is_dash and not self.resolutionToStream[stream.resolution].is_dash)) and stream.fps > self.resolutionToStream[stream.resolution].fps:
                    self.resolutionToStream[stream.resolution] = stream
        self.resolutionOptions.sort(reverse=True, key=lambda res: int(res[:len(res)-1]))

        # By default, get highest quality stream
        self.audioStream = self.streams.get_audio_only()
        self.videoStream = self.resolutionToStream[self.resolutionOptions[0]]
        for res in self.resolutionOptions:
            if not self.resolutionToStream[res].is_dash:
                self.videoStream = self.resolutionToStream[res]
                break

        if onlyAudio:
            self.stream = self.videoStream
        else:
            self.stream = self.videoStream

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


    def setStreamByResolution(self, stringVar):
        resolution = stringVar.get()
        self.stream = self.resolutionToStream[resolution]
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
        videoFile = self.stream.download(output_path=directory, filename=sanitize(self.displayName)+"tempVideo")
        downloadedFile = videoFile


        if self.stream.is_dash and not self.onlyAudio:

            audioFile = self.streams.get_audio_only().download(output_path=directory, filename=sanitize(self.displayName)+"tempAudio")

            mergedOutputPath = os.path.join(os.getcwd(), sanitize(self.displayName) + "tempMerge.mp4")
            downloadedFile = mergedOutputPath
            self.mergeAV(audioFile, videoFile, mergedOutputPath)
            os.remove(audioFile)
            os.remove(videoFile)


        extension = ".mp3" if self.onlyAudio else ".mp4"
        finalPath = os.path.join(directory, sanitize(self.name) + extension)


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

            if self.onlyAudio:
                clip.write_audiofile(finalPath, bitrate=bitrate)
                self.applyID3Tags(finalPath)
            else:
                clip.write_videofile(finalPath, threads=NUM_THREADS)   


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


    def mergeAV(self, audioPath, videoPath, outputPath):
        proc = subprocess.Popen([FFMPEG_PATH, "-i", videoPath, "-i", audioPath, outputPath])
        proc.wait()


    # From Masoud Rahimi on Stack Overflow - 
    # https://stackoverflow.com/questions/56370173/how-to-export-ffmpeg-into-my-python-program
    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)


    def previewClip(self, labelVar):
        Downloadable.previewLabelVar = labelVar
        stopPreview()

        labelVar.set("Playing:\n"+makeEllipsis(self.name,20))
        if self.onlyAudio:
            stream = self.stream
        else:
            stream = self.stream
            for res in self.resolutionOptions:
                if not self.resolutionToStream[res].is_dash:
                    stream = self.resolutionToStream[res]
                    break

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

        Downloadable.previewFile = os.path.join(os.getcwd(), "youtubeDownloaderPreviewFile.mp4")
        Downloadable.previewDownloadable = self
        Downloadable.previewThread = multiprocessing.Process(target=startPreview, args=(self.onlyAudio, stream, self.cut, low, high, newVolume))
        Downloadable.previewThread.start()
        

    def applyID3Tags(self, path):
        eyed3File = eyed3.load(path)

        if self.imgUrl == None:
            self.imgUrl = requestsGet(self.youtubeObject.thumbnail_url)
            

        eyed3File.tag.images.set(3, self.imgUrl.content, 'image/jpeg')

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


def startPreview(onlyAudio, stream, cut, low, high, volume):
    downloadedFile = stream.download(filename="youtubeDownloaderPreviewFile")

    clip = AudioFileClip(downloadedFile) if onlyAudio else VideoFileClip(downloadedFile) 

    if volume != 0:

        clip = clip.volumex(volume)

    if cut:
        clip = clip.subclip(low,high)

    clip.preview()
    clip.close()

    # See https://github.com/Zulko/moviepy/issues/575
    pygame.quit()
    os.remove(downloadedFile)



def stopPreview():
    Downloadable.previewLabelVar.set("Playing:\n")
    if Downloadable.previewThread != None:
        try:
            Downloadable.previewThread.terminate()
            Downloadable.previewThread.join()
        except:
            pass

        try:
            os.remove(Downloadable.previewFile)
        except:
            pass
    Downloadable.previewThread = None
    Downloadable.previewClipVar = None
    Downloadable.previewFile = None
    Downloadable.previewDownloadable = None