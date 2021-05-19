import pytube

x = pytube.YouTube("https://www.youtube.com/watch?v=K1QICrgxTjA")

print(vars(x.streams[0]).keys())

for i in x.streams:
    print("\n\n")
    print(i.bitrate," : ",i.resolution," : ",i.mime_type)