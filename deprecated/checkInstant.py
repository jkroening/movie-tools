################################################################################
## Takes your DVD queue and tells you which movies are available to stream that
## aren't in you streaming queue.
##
## Place an html block from your Netflix DVD queue in a file called
## queue_body.html. the block of interest can be copied in Chrome by choosing
## "Inspect Element" over your DVD queue (https://dvd.netflix.com/Queue),
## selecting the div where id="sortable" and aria-label="Active queue list"
## and right-clicking to select copy outerHTML. then paste that into queue_body.
## if you would also like to check the movies in the Saved section of your
## Netflix queue (movies that aren't released yet on Netflix DVD but may be
## available on streaming services) then follow the same procedure above, but for
## "savedListQueue" and copy that outerHTML into saved_queue.html. Use the flag
## --saved to process movies from the Saved section of your DVD queue.
## The same procedure applies to movies in your "My List" (streaming queue) that
## you would like to add, instead you will select the div with class "rowList"
## using Chrome's "Inspect Element" feature on
## https://www.netflix.com/browse/my-list and right-clicking to select copy the
## outerHTML and pasting that into my_list.html.
################################################################################


import pdb
import argparse
from bs4 import BeautifulSoup
from unidecode import unidecode


def findQueuePlays(soup, lst = []):
    for mov in soup.find_all('li', {'class' : 'queue-item'}):
        m = [m for m in mov.strings]
        m = [x.replace(',', '') for x in m]
        if 'Play' in m:
            lst.append(unidecode(m[4]).replace("&", "and").strip())
    return(lst)

def findSavedPlays(soup, lst = []):
    for mov in soup.find_all('li'):
        m = [m for m in mov.strings]
        m = [x.replace(',', '') for x in m]
        if 'Play' in m:
            lst.append(unidecode(m[2]).replace("&", "and").strip())
    return(lst)

def getMyListTitles(soup, lst = []):
    for mov in soup.find_all('div', {'class' : 'title'}):
        ## skip if TV show
        if 'Season' in mov.findNext('span', {'class', 'duration'}).text:
            continue
        m = [m for m in mov.strings]
        m = [x.replace(',', '') for x in m]
        for s in unidecode(m[0]).replace("&", "and").strip().split(": "):
            lst.append(s.strip().lower())
    return(lst)

def getGalleryTitles(soup, lst = []):
    for mov in soup.find_all('div', {'class' : 'video-preload-title-label'}):
        m = [m for m in mov.strings]
        m = [x.replace(',', '') for x in m]
        for s in unidecode(m[0]).replace("&", "and").strip().split(": "):
            lst.append(s.strip().lower())
    return(lst)

parser = argparse.ArgumentParser()
parser.add_argument("--saved", help = "also check movies in saved queue",
                    action = "store_true")
parser.add_argument("--asgallery",
                    help = "check streaming queue as gallery, not as list",
                    action = "store_true")
args = parser.parse_args()


## load netflix queue
with open("input/queue_body.html", "r") as f:
    queue = BeautifulSoup(f, 'html.parser')

plays = []
plays = findQueuePlays(queue, plays)

if args.saved:
    with open("input/saved_queue.html", "r") as f:
        saved = BeautifulSoup(f, 'html.parser')
    plays = findSavedPlays(saved, plays)
else:
    print("\nSaved queue will not be checked. To check saved queue as well use command line arg --saved.")

with open("input/my_list.html", "r") as f:
    mylist = BeautifulSoup(f, 'html.parser', from_encoding = 'utf-8')
with open("input/my_gallery.html", "r") as f:
    gallery = BeautifulSoup(f, 'html.parser', from_encoding = 'utf-8')

if not args.asgallery:
    instant = getMyListTitles(mylist)
else:
    instant = getGalleryTitles(gallery)

## get only what's not in my list but is in DVD and saved queues
## not the reverse
missing = []
for p in plays:
    if p.lower() not in instant:
        if not any([i in instant for i in p.lower().split(": ")]):
            missing.append(p)

print("\nAdd these movies to your My List queue for streaming:\n")
for m in missing:
    print m
print("\n")
