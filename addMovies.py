################################################################################
## takes a DB of movies in a queue and the html block of movies from a Netflix
## queue, collects streaming information and metadata about the movies and
## provides an interface for a user to pick a movie to watch.
##
## to use you need a The Movie Database API key and to place an html block from
## your Netflix DVD queue in a file called queue_body.html. the block of interest
## can be copied in Chrome by choosing "Inspect Element" over your DVD queue
## (https://dvd.netflix.com/Queue), selecting the div with id "activeQueueItems"
## and right-clicking to select copy outerHTML. then paste that into queue_body.
## if you would also like to include in movies from the Saved section of your
## Netflix queue (movies that aren't released yet on Netflix DVD but may be
## available on streaming services) then follow the same procedure above, but for
## "savedQueueItems" and copy that outerHTML into saved_queue.html. Use the flag
## --saved to process movies from the Saved section of your DVD queue. The same
## procedure applies to movies in your "My List" (streaming queue) that you
## would like to add, instead you will select the div with class "rowList" using
## Chrome's "Inspect Element" feature on https://www.netflix.com/browse/my-list
## and right-clicking to select copy the outerHTML and pasting that into
## my_list.html. Be sure to use the flag --mylist to process these movies.
##
## after the first pass through your queue a DB of the entries and info will be
## saved to movies_db.json. from that point forward you can choose to update the
## streaming information in your DB by passing "update" as a command line arg.
## and if you add or remove movies from your queue you will want to re-copy the
## html block into queue_body.html as instructed above.
################################################################################

import csv
import sys
import os
import re
from unidecode import unidecode
from bs4 import BeautifulSoup
import pandas as pd
import tmdbsimple as tmdb
import requests
from functools import partial
import numpy as np
import json
import shutil
import argparse
import pdb

def search(movie):
    try:
        r = requests.get('http://www.canistream.it/services/search',
            params={'movieName': movie},
            headers={
                'User-Agent':
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36'
                    '(KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36'})
        if hasattr(r, 'json'):
            try:
                req = r.json()
                return(req)
            except:
                return None
        else:
            return None
    except:
        print sys.exc_info()[0]
        return None

def movie(movie_id, media_type):
    try:
        r = requests.get('http://www.canistream.it/services/query',
            params={'movieId': movie_id,
                    'attributes': '1',
                    'mediaType': media_type},
            headers={
                'User-Agent':
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36'
                    '(KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36'})
        if hasattr(r, 'json'):
            try:
                req = r.json()
                return(req)
            except:
                return None
        else:
            return None
    except:
        print sys.exc_info()[0]
        return None


def parseTMDB(r):
    tmdb_id = int(r['id'])
    mov = tmdb.Movies(tmdb_id).info()
    year = int(mov['release_date'].split("-")[0]) if len(mov['release_date'].split("-")[0]) > 0 else None
    genres = mov['genres'] if mov['genres'] is not None else []
    imdb_id = str(mov['imdb_id']) if mov['imdb_id'] is not None else None
    overview = unidecode(mov['overview']) if mov['overview'] is not None else None
    tagline = unidecode(mov['tagline']) if mov['tagline'] is not None else None
    lang = mov['original_language'] if mov['original_language'] is not None else None
    runtime = mov['runtime'] if mov['runtime'] is not None else None
    gs = [str(g['name']) for g in genres]
    if lang != 'en' and 'Foreign' not in gs:
        gs.append(str('Foreign'))
    return tmdb_id, year, overview, tagline, runtime, gs, imdb_id

def findTMDB(title, imdb_id = None):
    page = 1
    sel = 'n'
    tmdb_id = None
    year = None
    overview = None
    runtime = None
    tagline = None
    gs = []
    tmdb_title = None
    if imdb_id is not None:
        res = tmdb.Find(imdb_id).info(external_source = 'imdb_id')['movie_results']
        if len(res) > 0:
            tmdb_id, year, overview, tagline, runtime, gs, imdb_id = parseTMDB(res[0])
            tmdb_title = None
            sel = 'y'
    while sel != 'y' and page <= 5:
        res = tmdb.Search().movie(query = title, page = page)
        page += 1
        if len(res['results']) == 0: break
        for r in res['results']:
            tmdb_title = unidecode(r['title']).replace(',', '')
            if tmdb_title.lower() == title.lower():
                sel = 'y'
            elif title.lower() in tmdb_title.lower() or tmdb_title.lower() in title.lower():
                sel = raw_input(
                    "Matching '{}' with TMDB '{}' ({})... OK? [y or n] ".format(title, tmdb_title, r['id'])
                ).lower()
            if sel == 'y':
                tmdb_id, year, overview, tagline, runtime, gs, imdb_id = parseTMDB(r)
                break
            else:
                print("Trying again...")

    if sel != 'y':
        print("Unable to find match in TMDB for '{}'".format(title))
        print("Genres won't be available.")
        user_genres = raw_input("Enter genres separated by commas if you want to include manually: ")
        gs = [x.strip() for x in user_genres.split(',')]
        tmdb_title = None
    else:
        print("* MATCHED TMDB")
    return tmdb_id, year, overview, tagline, runtime, gs, imdb_id, tmdb_title

streaming = partial(movie, media_type='streaming')
rental = partial(movie, media_type='rental')
purchase = partial(movie, media_type='purchase')
dvd = partial(movie, media_type='dvd')
xfinity = partial(movie, media_type='xfinity')

def getStreams(cisi_id):
    streams = streaming(cisi_id)
    ss = []
    if streams is not None and len(streams) > 0:
        for k, v in streams.items():
            stream = str(v['friendlyName'])
            if stream != 'Youtube Free': ## Youtube Free isn't free...
                ss.append(stream)
    return ss

def parseCISI(title, tmdb_title = None):
    movs = search(title)
    mov = None
    mov_id = None
    imdb_id = None
    year = None
    ss = []
    sel = 'n'
    if movs is not None and len(movs) > 0:
        for m in movs:
            cisi_title = unidecode(m['title']).replace(',', '')
            if cisi_title.lower() == title.lower():
                sel = 'y'
                break
            elif title.lower() in cisi_title.lower() or cisi_title.lower() in title.lower():
                sel = raw_input(
                    "Matching '{}' with canistream.it '{}' ({})... OK? [y or n] ".format(
                        title
                        , cisi_title
                        , m['_id']
                    )
                ).lower()
                if sel == 'y':
                    break
            print("Trying again...")
    elif tmdb_title is not None:
        movs = search(tmdb_title)
        sel = 'n'
        if movs is not None and len(movs) > 0:
            for m in movs:
                cisi_title = unidecode(m['title'].decode('utf-8'))
                if cisi_title.lower() == tmdb_title.lower():
                    sel = 'y'
                    break
                elif tmdb_title.lower() in cisi_title.lower() or cisi_title.lower() in tmdb_title.lower():
                    sel = raw_input(
                        "Matching TMDB '{}' with canistream.it '{}' ({})... OK? [y or n] ".format(
                            tmdb_title
                            , cisi_title
                            , m['_id']
                        )
                    ).lower()
                    if sel == 'y':
                        break
                    else:
                        print("Trying again...")
    if sel == 'y':
        mov = m
        mov_id = str(m['_id'])
        year = int(m['year'])
        if 'imdb' in m['links'].keys():
            imdb_id = str(m['links']['imdb'].split("/")[-2])
    else:
        print("Unable to find match in canistream.it for '{}'".format(title))
    if mov is not None:
        ss = getStreams(mov_id)
        print("* MATCHED canistream.it")
    elif tmdb_title is not None:
        print("Streaming availability won't be available.")
    return mov_id, year, ss, imdb_id

def processMovies(soup, movies_db, update_streams = True):
    movies = []
    for mov in soup.find_all('div', {'class' : 'queue-item'}):
        m = [m for m in mov.strings]
        m = [x.replace(',', '') for x in m]

        ## netflix block
        title = unidecode(m[1]).strip()
        if 'future release' in m or 'Future release' in m:
            print("Skipping '{}' because it's a Future release.".format(title))
            continue
        if 'Play' in m:
            netflix_instant = True
        else:
            netflix_instant = False
        rating = float([s for s in m if tryFloat(s)][1].encode('utf-8'))
        netflix_id = int(mov.get('data-movie-id'))
        ## update rating and streams if already in the database, then skip to next movie
        if not movies_db.empty:
            cond1 = any(float(netflix_id) == movies_db.netflix_id.values)
            cond2 = any(int(netflix_id) == movies_db.netflix_id.values)
            if cond1 or cond2:
                ## if movie has already been rated, remove from DB, assume it's been watched
                if mov.find('div', {'class' : 'maskRated'}) is not None:
                    movies_db = movies.db[movies_db.netflix_id != int(netflix_id)]
                    print("Skipping '{}' because it has already been watched and rated.".format(title))
                else:
                    idx = movies_db[movies_db.netflix_id == netflix_id].index[0]
                    movies_db.loc[idx, 'rating'] = rating
                    movies_db.loc[idx, 'netflix_instant'] = netflix_instant
                    prev_streams = movies_db.loc[idx, 'streams']
                    if netflix_instant and 'Netflix Instant' not in prev_streams:
                        prev_streams.append(str('Netflix Instant'))
                    movies_db = movies_db.set_value(idx, 'streams', prev_streams)
                    cisi_id = movies_db.loc[idx, 'canistreamit_id']
                    if update_streams and cisi_id is not None:
                        new_streams = getStreams(cisi_id)
                        all_streams = prev_streams.append(new_streams)
                        if all_streams is None:
                            all_streams = []
                        movies_db = movies_db.set_value(idx, 'streams', all_streams)
                continue
        if mov.find('div', {'class' : 'maskRated'}) is not None:
            print("Skipping '{}' because it has already been watched and rated.".format(title))
            continue

        print("\n{}".format(title))
        user_in = raw_input("\nAdd '{}' to the database? [y or n] ".format(title))
        if user_in != 'y':
            print("Skipping...")
            continue

        cisi_id, year, runtime, imdb_id, tmdb_id, overview, tagline, tmdb_title = (None,) * 8
        ss, gs = ([],) * 2

        ## canistreamit block
        cisi_id, cisi_year, ss, imdb_id = parseCISI(title)

        ## tmdb block
        tmdb_id, tmdb_year, overview, tagline, runtime, gs, imdb_id, tmdb_title = findTMDB(title, imdb_id)

        ## try canistreamit again if it failed the first time
        if cisi_id is None and tmdb_title is not None:
            cisi_id, cisi_year, ss, imdb_id = parseCISI(title, tmdb_title)
        if netflix_instant and 'Netflix Instant' not in ss:
            ss.append(str('Netflix Instant'))

        ## get year, prefer CISI
        year = cisi_year if cisi_year is not None else tmdb_year

        ## just to be sure
        if ss is None:
            ss = []

        movies.append({
            'netflix_id' : netflix_id
            , 'tmdb_id' : tmdb_id
            , 'canistreamit_id' : cisi_id
            , 'imdb_id' : imdb_id
            , 'title' : title
            , 'rating' : rating
            , 'genres' : gs
            , 'netflix_instant' : netflix_instant
            , 'streams' : ss
            , 'year' : year
            , 'runtime' : runtime
            , 'overview' : overview
            , 'tagline' : tagline
        })
        with open('new_movies.json', 'w') as outfile:
            json.dump(movies, outfile)

    return movies, movies_db

def processMyList(soup, movies_db):
    movies = []
    for mov in soup.find_all('div', {'class' : 'title'}):
        ## skip if TV show
        if 'Season' in mov.findNext('span', {'class', 'duration'}).text:
            continue

        m = [m for m in mov.strings]
        m = [x.replace(',', '') for x in m]

        ## netflix block
        title = unidecode(m[0]).strip()
        netflix_instant = True
        spans = mov.findNext('div').find_all('span', {'class', 'match-score'})
        if len(spans) < 1:
            rating = None
        else:
            rating = float(spans[0].text.split("% ")[0])
        ## old code from before Netflix changed streaming from star ratings to match percentages
        # spans = mov.findNext('div').find_all('span', {'class', 'star'})
        # sbplaceholder = [i for i, item in enumerate(spans) if re.search('sb-placeholder', item['class'][1])]
        # if len(sbplaceholder):
        #     base = sbplaceholder[0] - 1
        # else:
        #     base = 5.0
        # percent = [s for s in spans if re.search('percent', s['class'][2])]
        # if len(percent):
        #     decimal = float(filter(str.isdigit, str([s for s in spans if re.search('percent', s['class'][2])][0]['class'][2]))) / 100
        # else:
        #     decimal = 0
        # rating = base + decimal
        netflix_id = int(mov.find('a')['href'].split('/')[-1])
        ## update netflix instant stream status and rating if already in the database, then skip to next movie
        if not movies_db.empty:
            cond1 = any(float(netflix_id) == movies_db.netflix_id.values)
            cond2 = any(int(netflix_id) == movies_db.netflix_id.values)
            if cond1 or cond2:
                idx = movies_db[movies_db.netflix_id == netflix_id].index[0]
                if rating is not None:
                    movies_db.loc[idx, 'rating'] = rating
                movies_db.loc[idx, 'netflix_instant'] = netflix_instant
                prev_streams = movies_db.loc[idx, 'streams']
                if netflix_instant and 'Netflix Instant' not in prev_streams:
                    prev_streams.append(str('Netflix Instant'))
                movies_db = movies_db.set_value(idx, 'streams', prev_streams)
                continue

        print("\n{}".format(title))
        user_in = raw_input("\nAdd '{}' to the database? [y or n] ".format(title))
        if user_in != 'y':
            print("Skipping...")
            continue

        cisi_id, year, runtime, imdb_id, tmdb_id, overview, tagline, tmdb_title = (None,) * 8
        ss, gs = ([],) * 2

        ## canistreamit block
        cisi_id, cisi_year, ss, imdb_id = parseCISI(title)

        ## tmdb block
        tmdb_id, tmdb_year, overview, tagline, runtime, gs, imdb_id, tmdb_title = findTMDB(title, imdb_id)

        ## try canistreamit again if it failed the first time
        if cisi_id is None and tmdb_title is not None:
            cisi_id, cisi_year, ss, imdb_id = parseCISI(title, tmdb_title)
        if netflix_instant and 'Netflix Instant' not in ss:
            ss.append(str('Netflix Instant'))

        ## get year, prefer CISI
        year = cisi_year if cisi_year is not None else tmdb_year
        if year is None:
            year = int(mov.findNext('div', {'class', 'year'}).text)

        ## just to be sure
        if ss is None:
            ss = []

        if 'Comedy' in gs:
            user_in = raw_input("\nAdd 'Stand-Up' to genres? [y or n]")
            if user_in == 'y':
                gs.append('Stand-Up')

        movies.append({
            'netflix_id' : netflix_id
            , 'tmdb_id' : tmdb_id
            , 'canistreamit_id' : cisi_id
            , 'imdb_id' : imdb_id
            , 'title' : title
            , 'rating' : rating
            , 'genres' : gs
            , 'netflix_instant' : netflix_instant
            , 'streams' : ss
            , 'year' : year
            , 'runtime' : runtime
            , 'overview' : overview
            , 'tagline' : tagline
        })
        with open('new_movies.json', 'w') as outfile:
            json.dump(movies, outfile)

    return movies, movies_db

def tryFloat(x):
    try:
        float(x)
    except:
        return False
    return True

## load api key for TMDB
with open("config/config.csv", "U") as f:
    reader = csv.reader(f)
    config = {}
    for row in reader:
        config[row[0]] = row[1]

tmdb.API_KEY = config['TMDB_API_KEY']

parser = argparse.ArgumentParser()
parser.add_argument("--update", help = "update streaming status of movies already in database",
                    action = "store_true")
parser.add_argument("--saved", help = "also process movies in saved queue",
                    action = "store_true")
parser.add_argument("--mylist", help = "also process movies from my list (streaming queue)",
                    action = "store_true")
args = parser.parse_args()

## whether canistream.it should be checked for existing DB entries to update
if args.update:
    update_streams = True
else:
    update_streams = False
    print("To update the streaming status of existing movies, enter '--update' as a command line argument.\n")

## backup database file
shutil.copyfile('databases/movies_db.json', 'databases/backup/movies_db.json')

## load database
try:
    with open("databases/movies_db.json", "r") as f:
        movies_in = json.load(f)
        movies_db = pd.DataFrame(movies_in)
except:
    movies_db = pd.DataFrame({
        'netflix_id' : []
        , 'rating' : []
        , 'title' : []
        , 'canistreamit_id' : []
        , 'tmdb_id' : []
        , 'imdb_id' : []
        , 'genres' : []
        , 'streams' : []
        , 'netflix_instant' : []
        , 'runtime' : []
        , 'year' : []
        , 'overview' : []
        , 'tagline' : []
    })

## load netflix queue
with open("input/queue_body.html", "r") as f:
    soup = BeautifulSoup(f, 'html.parser')

genres = tmdb.Genres().list()['genres']
alt_genres = [{'id' : 10769, 'name' : 'Foreign'}]

print("Processing Active queue...")
movies, movies_db = processMovies(soup, movies_db, update_streams)

if args.saved:
    with open("input/saved_queue.html", "r") as f:
        soup = BeautifulSoup(f, 'html.parser')
    print("\nProcessing Saved queue...")
    saved_movies, movies_db = processMovies(soup, movies_db, update_streams)
else:
    saved_movies = None
    print("\nSaved queue will not be processed. To process saved queue as well use command line arg --saved.")
if args.mylist:
    with open("input/my_list.html", "r") as f:
        soup = BeautifulSoup(f, 'html.parser')
    print("\nProcessing My List (streaming queue)...")
    mylist_movies, movies_db = processMyList(soup, movies_db)
else:
    mylist_movies = None
    print("\nMy List (streaming queue) will not be processed. To process My List as well use command line arg --mylist.")

## combine new movies with previous DB
## save updated combined DB
new_movies = pd.DataFrame(movies)
out_movies = movies_db.append(new_movies, ignore_index = True)
if saved_movies is not None:
    saved_movies = pd.DataFrame(saved_movies)
    out_movies = out_movies.append(saved_movies, ignore_index = True)
if mylist_movies is not None:
    mylist_movies = pd.DataFrame(mylist_movies)
    out_movies = out_movies.append(mylist_movies, ignore_index = True)

with open('databases/movies_db.json', 'w') as outfile:
    json.dump(out_movies.T.to_dict().values(), outfile)

try:
    os.remove('new_movies.json')
except OSError:
    pass
