## This project is a standalone application to download YouTube videos and convert them to mp3 files. It allows single video and playlist downloads. Users can set the file names and mp3 ID3 tags. 

The 

## Software Dependencies:
### Python 3 
    - tkinter (GUI)
    - pytube (YouTube downloader) 

    - eyed3 (mp3 tagger)
    - moviepy (mp4->mp3 converter)

## Get Started:

### Quick-Start:

The '/dist' folder contains a single executable file to launch the application immediately.

### Install dependencies and run script 

```bash
python3 -m pip install -r requirements.txt
```
```bash
python3 dlyt.py
```


## Issues I Have Had:
### Numpy error: Try using numpy version 1.19.3 when creating the executable with pyinstaller

```bash
python3 -m pip install numpy==1.19.3
```

### PyTube error: Make sure most recent version of PyTube (10.5.3 as of 3/9/2021)
```bash
python3 -m pip install git+https://github.com/nficano/pytube
```