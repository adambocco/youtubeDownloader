def formatSeconds(seconds): 
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

def addLineBreaks(string):                                                # Helper function for displaying metadata
    retList = string
    for i in range(1,int(len(string)/50)+1):
        retList = retList[:i*50] + '\n' + retList[i*50:]
    return retList