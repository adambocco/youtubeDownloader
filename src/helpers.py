def formatSeconds(seconds): 
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

 # Helper function for displaying metadata
def addLineBreaks(string):                                               
    retList = string
    for i in range(1,int(len(string)/50)+1):
        retList = retList[:i*50] + '\n' + retList[i*50:]
    return retList

def HMStoSeconds(HMS):
    hms = HMS.split(":")
    h = int(hms[0])
    m = int(hms[1])
    s = int(hms[2])
    return (h*3600) + (m*60) + s


def makeEllipsis(string, max):
    if len(string) > max:
        return string[:max] + "..."
    else:
        return string