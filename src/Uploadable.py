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



FFMPEG_PATH = "./ffmpeg/ffmpeg.exe"
FFPLAY_PATH = "./ffmpeg/ffplay.exe"
NUM_THREADS = 4

from helpers import formatSeconds, makeEllipsis, sanitizeFilename

class Uploadable:  

    previewClipVar = None
    previewThread = None

    previewDownloadable = None
    previewLabelVar = None


    def __init__(self, filePath, onlyAudio):

        self.cut = False
        self.lowCut = 0
        self.highCut = self.length

        self.length = self.youtubeObject["duration"]
        self.name = self.youtubeObject["title"]

        # Display name is the key for [youtubeDownloader::downloadables]
        self.displayName = self.name + " --- " + ("Audio" if self.onlyAudio else "Video")

        self.extension = ".mp3" if self.onlyAudio else ".mp4"

        if onlyAudio