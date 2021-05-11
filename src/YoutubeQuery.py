from youtubesearchpython import VideosSearch

videosSearch = VideosSearch('', limit = 1)

print(videosSearch.result()['result'][0]['link'])