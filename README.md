### This project is a standalone application to download YouTube videos and convert them to mp3 files. It allows single video and playlist downloads. Users can set the file names and mp3 ID3 tags. 

## Software Dependencies:
## Python 3 
###    - tkinter (GUI)
###    - pytube (YouTube downloader) 

###    - eyed3 (mp3 tagger)
###    - moviepy (mp4->mp3 converter)

## Get Started:
```bash
python3 -m pip install -r requirements.txt
```
```bash
python3 dlyt.py
```


## Issues I Have Had:
### Numpy error: Try using numpy version 1.19.3

```bash
python3 -m pip install numpy==1.19.3
```

### Pytube error: Make sure most recent version (10.1.0 as of 12/9/2020)
```bash
python3 -m pip install git+https://github.com/nficano/pytube
```