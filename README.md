# YouTube Downloader

This is a desktop application for downloading videos from YouTube. It supports several features:

* Download from a URL or YouTube query
* Fetch entire playlist or subsection of playlist
* Apply ID3 tags to audio files
    * Automatically apply tags from YouTube metadata and/or title
* Trim media
* Apply volume multiplier
* Preview changes before downloading


## Get Started:

### Install python3 dependencies:

```bash
python3 -m pip install -r requirements.txt
```

### Get *ffplay*:
**ffmpeg** includes **ffplay** which is used for previewing media modifications. Download the precompiled binaries for your system and add the **bin** folder to path.
- https://www.ffmpeg.org/download.html

### Run the script:

```bash
python3 youtubeDownloader.py
```


## Comments:
If the application doesn't support a feature you would like to see, please make an issue with a use case for it and I'd be happy to implement the change.