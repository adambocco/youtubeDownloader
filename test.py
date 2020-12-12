from moviepy.editor import VideoFileClip
import pytube
import os
d=os.getcwd()
x = pytube.YouTube('https://www.youtube.com/watch?v=cHWs3c3YNs4')

x.streams.first().download(filename="test", output_path="C:/Users/User/Desktop/youtubedownloader/")

y = VideoFileClip('./test.mp4')
y=y.subclip(0,30)
y.write_videofile('./testout.mp4')