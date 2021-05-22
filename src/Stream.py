

class Stream:

    def __init__(self, stream):

        if stream["ext"] != "mp4" and stream["fps"] != None:
            raise Exception

        self.stream = stream

        self.bitrate = stream["tbr"]
        self.url = stream["url"]

        if "container" not in stream or stream["container"] == None:
            self.mediaType = "AV"
        elif stream["fps"] == None:

            self.mediaType = "A"
        else:
            self.mediaType = "V"

        self.resolution = stream["height"]
        self.fps = stream["fps"]
        self.ext = stream["ext"]


    def __str__(self):
        if self.mediaType == "A":
            return "Audio Stream: Ext: " + self.ext 
        elif self.mediaType == "AV":
            return "Video Stream: Ext: " +self.ext + " Resolution: " + str(self.resolution) + " FPS: " + str(self.fps)
        else:
            return "Video ONLY Stream: Ext: " + self.ext + " Resolution: " + str(self.resolution) + " FPS: " + str(self.fps)
