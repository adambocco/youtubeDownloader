def formatSeconds(seconds): 
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)


def formatCutInfo(low, high, length):
    formattedInfo = ""
    formattedInfo += "Original Length: " + formatSeconds(length) +"\n"
    formattedInfo += "Cut Length: " + formatSeconds(high - low) + "\n"
    formattedInfo += "Cut Range: "+ formatSeconds(low) + " - " + formatSeconds(high)
    return formattedInfo

# Handles cutting in URL preview frame after fetching
# When user makes a cut on a song or video, calculate and save new range
def makeCut(event, dlAndSlider):
    downloadable = dlAndSlider[0]
    slider = dlAndSlider[1]
    low, high = slider.getValues()
    low = int(low)
    high = int(high)
    if downloadable.changeCut(low, high):
        downloadable.widgetIds['urlInfo']['text'] = formatCutInfo(low, high, downloadable.length)
    else:
        downloadable.widgetIds['urlInfo']['text'] = "Length: " + formatSeconds(downloadable.length) +"\n"