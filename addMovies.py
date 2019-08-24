################################################################################
## takes a DB of movies and adds new movies to the database using the MovieLens
## ID. the script collects TMDB and JustWatch information. if you pass the flag
## --update
##
## to use, you need a The Movie Database API key and a MovieLens account. if you
## want to be able to update your MovieLens rating you need to use selenium and
## have a webdriver installed and the path to it specified in config.txt
################################################################################

import csv
from unidecode import unidecode
import pandas as pd
import tmdbsimple as tmdb
import requests
from justwatch import JustWatch
from rotten_tomatoes_client import RottenTomatoesClient
from selenium import webdriver
from bs4 import BeautifulSoup
import re
import time
import numpy as np
import json
import shutil
import argparse
import warnings
import pdb

warnings.simplefilter(action = 'ignore', category = FutureWarning)

def parseTMDB(r):
    tmdb_id = float(r['id'])
    mov = tmdb.Movies(tmdb_id).info()
    year = float(mov['release_date'].split("-")[0]) if len(mov['release_date'].split("-")[0]) > 0 else np.nan
    genres = mov['genres'] if mov['genres'] is not None else []
    imdb_id = str(mov['imdb_id']) if mov['imdb_id'] is not None else None
    overview = unidecode(mov['overview']) if mov['overview'] is not None else None
    tagline = unidecode(mov['tagline']) if mov['tagline'] is not None else None
    lang = mov['original_language'] if mov['original_language'] is not None else None
    runtime = float(mov['runtime']) if mov['runtime'] is not None else np.nan
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
                sel = input(
                    "Matching '{}' with TMDB '{}' ({})... OK? [y or n] ".format(title, tmdb_title, r['id'])
                ).lower()
            if sel == 'y':
                tmdb_id, year, overview, tagline, runtime, gs, imdb_id = parseTMDB(r)
                break
            else:
                print("Trying again...")

    if sel != 'y':
        print("Unable to find match in TMDB for '{}'".format(title))
        tmdb_title = None
        tmdb_id = tryFloat(input("What is the TMDB ID?  "), get = True)
        year = tryFloat(input("What is the year?  "), get = True)
        overview = input("What is the overview?  ")
        tagline = input("What is the tagline?  ")
        runtime = tryFloat(input("What is the runtime?  "), get = True)
        genres = input("What are the genres? (separated by commas)  ")
        gs = [x.strip() for x in genres.split(',')]
        imdb_id = input("What is the IMDB ID?  ")
    else:
        print("* MATCHED TMDB")
    return tmdb_id, year, overview, tagline, runtime, gs, imdb_id, tmdb_title

def parseScore(scores, prov = 'tomato:meter'):
    if len(scores):
        rt_scores = [x for x in scores if prov in x['provider_type']]
        if len(rt_scores):
            return(float(rt_scores[0]['value']))
        else:
            return np.nan
    else:
        return np.nan

def parseGenres(gs, jw_genres):
    if not not gs and not not jw_genres:
        out = [g['translation'] for g in jw_genres if g['id'] in gs]
        return out
    else:
        return []

def getProviders():
    with open("config/providers.json", "r") as f:
        providers = json.load(f)
    jw = JustWatch(country = "US")
    provider_details = jw.get_providers()
    for provider in provider_details:
        providers[str(provider['id'])] = provider
    with open("config/providers.json", "w") as f:
        json.dump(providers, f)
    return providers

providers = getProviders()

provider_map = {'Netflix Instant' : 'Netflix',
                'Amazon Prime' : 'Amazon',
                'Amazon Instant Video' : 'Amazon',
                'Amazon Prime Instant Video' : 'Amazon',
                'HBO Now' : 'HBO',
                'HBO Go' : 'HBO'}

my_providers = ['Netflix', 'Syfy', 'Smithsonian Channel', 'The CW', 'HBO',
                'NBC', 'Amazon', 'CBS', 'ABC', 'FXNow', 'Tubi TV', 'Crackle',
                'Hulu', 'AMC', 'PlayStation', 'Showtime', 'Epix', 'Yahoo View']

def parseStreams(streams):
    ss = []
    if not not streams:
        for s in streams:
            if any(x in s['monetization_type'] for x in ['flatrate', 'flat_rate', 'free']):
                prov = providers[str(s['provider_id'])]
                name = prov['clear_name']
                if name in provider_map:
                    short_name = provider_map[name]
                else:
                    short_name = name
                if short_name in my_providers:
                    ss.append(short_name)
    return list(set(ss))

def parseJustWatch(mov):
    jw_id = tryFloat(mov['id'], get = True)
    year = tryFloat(mov['original_release_year'], get = True) if 'original_release_year' in mov.keys() else np.nan
    desc = unidecode(mov['short_description']) if 'short_description' in mov.keys() else None
    runtime = tryFloat(mov['runtime'], get = True) if 'runtime' in mov.keys() else np.nan
    rt_score = parseScore(mov['scoring']) if 'scoring' in mov.keys() else np.nan
    streams = parseStreams(mov['offers']) if 'offers' in mov.keys() else []
    return jw_id, year, desc, runtime, rt_score, streams

def findJustWatch(title, jw = None, jw_genres = None, imdb_id = None, tmdb_id = None):
    if jw == None:
        jw = JustWatch(country = 'US')
    if jw_genres is None:
        jw_genres = jw.get_genres()
    sel = 'n'
    jw_id = np.nan
    year = np.nan
    desc = None
    runtime = np.nan
    rt_score = np.nan
    gs = []
    streams = []
    jw_title = None
    res = jw.search_for_item(query = title)
    while sel != 'y' and res['total_results'] > 0:
        for r in res['items']:
            if 'scoring' in r:
                provs = pd.DataFrame(r['scoring'])
                if (imdb_id != None and len(provs.value[provs.provider_type == 'imdb:id'].values) != 0):
                    if provs.value[provs.provider_type == 'imdb:id'].values != imdb_id:
                        next
                if (tmdb_id != None and len(provs.value[provs.provider_type == 'tmdb:id'].values) != 0):
                    if provs.value[provs.provider_type == 'tmdb:id'].values != tmdb_id:
                        next
                jw_title = unidecode(r['title']).replace(',', '')
                if jw_title.lower() == title.lower():
                    sel = 'y'
                elif title.lower() in jw_title.lower() or jw_title.lower() in title.lower():
                    sel = input(
                        "Matching '{}' with JustWatch '{}' ({})... OK? [y or n] ".format(title, jw_title, r['id'])
                    ).lower()
                if sel == 'y':
                    jw_id, year, desc, runtime, rt_score, streams = parseJustWatch(r)
                    break
                else:
                    print("Trying again...")
        break
    if sel != 'y':
        print("Unable to find match in JustWatch for '{}'".format(title))
        jw_id = tryFloat(input("What is the JustWatch ID?  "), get = True)
        if jw_id == '':
            jw_id = np.nan
        rt_score = tryFloat(input("What is the Rotten Tomatoes score?  "), get = True)
        if rt_score == '':
            rt_score = np.nan
        user_streams = input("On which services is it streaming? (separated by commas)  ")
        if user_streams != '':
            streams = [x.strip() for x in user_streams.split(',')]
        jw_title = None
    else:
        print("* MATCHED JustWatch")

    ## get genres
    if not np.isnan(jw_id):
        full_res = jw.get_title(title_id = int(jw_id))
        gs = parseGenres(full_res['genre_ids'], jw_genres) if 'genre_ids' in full_res.keys() else []

    return jw_id, year, desc, runtime, rt_score, gs, streams, jw_title

def getJustWatch(title, jw_id, jw = None):
    if jw == None:
        jw = JustWatch(country = 'US')
    sel = 'n'
    ## JustWatch breaks if you bombard it too much, so use a VPN
    while True:
        try:
            res = jw.get_title(title_id = int(jw_id))
        except Exception as e:
            if e.response.status_code == 500:
                print("No match found for this JustWatch ID {}.".format(jw_id))
                return jw_id, rt_score, streams
            print(e.response.status_code)
            print("JustWatch not reached. Try again...")
            print("** Rate Limit was likely exceeded. Please use VPN. **")
        else:
            print("* MATCHED JustWatch")
            break
    jw_id, year, desc, runtime, rt_score, streams = parseJustWatch(res)
    return jw_id, rt_score, streams

def findRTScore(title):
    res = RottenTomatoesClient.search(term = title, limit = 5)
    for r in res['movies']:
        print("{} -- {} -- {}% -- {}".format(r['name'], tryInt(r['year'], get = True),
                                             tryInt(r.get('meterScore'), get = True), r['subline'] + r['url']))
        approval = input("Does this look like a match? [y or n]  ")
        if approval == 'y':
            return tryInt(r['meterScore'], get = True)
        else:
            continue
    print("Unable to find match in Rotten Tomatoes for '{}'".format(title))
    return None

def tryFloat(x, get = False):
    try:
        float(x)
    except:
        if get:
            return str(x)
        else:
            return False
    if get:
        return float(x)
    else:
        return True

def tryInt(x, get = False):
    try:
        int(x)
    except:
        if get:
            return str(x)
        else:
            return False
    if get:
        return int(x)
    else:
        return True

## load api key for TMDB
with open("config/config.csv") as f:
    reader = csv.reader(f)
    config = {}
    for row in reader:
        config[row[0]] = row[1]

tmdb.API_KEY = config['TMDB_API_KEY']

parser = argparse.ArgumentParser()
parser.add_argument(
    "--updatestreaming",
    help = "update streaming status and rotten tomatoes score of movies already in database",
    action = "store_true"
)
parser.add_argument(
    "--updateratings",
    help = "update Movie Lens ratings of movies already in database",
    action = "store_true"
)
args = parser.parse_args()

if args.updatestreaming:
    updatestreaming = True
else:
    updatestreaming = False
    print("To update the streaming status and rotten tomatoes scores of existing movies, enter '--updatestreaming' as a command line argument.")
if args.updateratings:
    updateratings = True
else:
    updateratings = False
    print("To update the predicted ratings of existing movies, enter '--updateratings' as a command line argument.")

## backup database file
shutil.copyfile('databases/movies_db.json', 'databases/backup/movies_db.json')

## load database
try:
    with open("databases/movies_db.json", "r") as f:
        movies_in = json.load(f)
        movies_db = pd.DataFrame(movies_in)
except:
    movies_db = pd.DataFrame({
          'movielens_id' : []
        , 'netflix_id' : []
        , 'tmdb_id' : []
        , 'imdb_id' : []
        , 'title' : []
        , 'rating' : []
        , 'netflix_rating' : []
        , 'genres' : []
        , 'netflix_instant' : []
        , 'streams' : []
        , 'year' : []
        , 'runtime' : []
        , 'overview' : []
        , 'tagline' : []
        , 'jw_id' : []
        , 'rt_score' : []
    })

## JustWatch genre list
jw = JustWatch(country = "US")
full_genres = jw.get_genres()

## accept new movies
keepgoing = False
add_movies = input("\nDo you want to add movies to the database? [y or n]  ")
if add_movies == 'y':
    keepgoing = True
while keepgoing:
    netflix_id = None ## no dependence on netflix IDs anymore
    netflix_rating = None ## not using netflix as rating basis anymore
    new_title = input("\nWhat is the name of the movie to add?  ")
    new_id = tryFloat(input("What is the MovieLens ID of the movie?  "), get = True)
    new_rating = tryFloat(input("What is the MovieLens predicted rating for the movie?  "), get = True)
    avg_rating = tryFloat(input("What is the MovieLens average rating for the movie?  "), get = True)
    num_rating = tryFloat(input("What is the MovieLens number of ratings for the movie?  "), get = True)

    ## check if the movie is already in the DB
    if new_id != '' and len(movies_db[(movies_db.movielens_id == new_id)]):
        print('This movie seems to already exist in the DB. Skipping...')
        keepgoing = input("\nAdd another movie? [y or n]  ")
        if keepgoing == 'n':
            keepgoing = False
        continue

    ## find TMDB
    tmdb_id, year, overview, tagline, runtime, genres, imdb_id, title = findTMDB(new_title)
    print(title, " -- ", tryInt(year, get = True), " -- ", tagline, " -- ", genres)
    print(overview)
    approval = input("Does this look like a match? [y or n]  ")
    if approval == 'n':
        title = new_title
        tmdb_id = tryFloat(input("What is the TMDB ID?  "), get = True)
        if tmdb_id == '':
            tmdb_id = np.nan
        year = tryFloat(input("What is the year?  "), get = True)
        overview = input("What is the overview?  ")
        tagline = input("What is the tagline?  ")
        runtime = tryFloat(input("What is the runtime?  "), get = True)
        genres = input("What are the genres? (separated by commas)  ")
        genres = [x.strip() for x in genres.split(',')]
        imdb_id = tryFloat(input("What is the IMDB ID?  "), get = True)
        if imdb_id == '':
            imdb_id = np.nan

    ## find JustWatch
    jw_id, jw_year, desc, jw_runtime, rts, jw_genres, streams, jw_title = findJustWatch(title, jw, full_genres)
    if not np.isnan(jw_id):
        print("{} -- {} -- {}% -- {}".format(jw_title, tryInt(jw_year, get = True),
                                             tryInt(rts, get = True), jw_genres))
        print(desc)
        approval = input("Does this look like a match? [y or n]  ")
        if approval == 'n':
            jw_id = tryFloat(input("What is the JustWatch ID?  "), get = True)
            if jw_id == '':
                jw_id = np.nan
            rts = tryFloat(input("What is the Rotten Tomatoes score?  "), get = True)
            if rts == '':
                rts = np.nan
            user_streams = input("On which services is it streaming? (separated by commas)  ")
            if user_streams != '':
                streams = [x.strip() for x in user_streams.split(',')]

    ## get RT Score directly
    rt_score = findRTScore(title)
    if rt_score is None:
        rt_score = rts ## use JustWatch RT Score, which is usually out of date

    ## clean up streams
    if streams is None or not any(streams):
        streams = []
    netflix_instant = False
    if 'Netflix' in streams:
        netflix_instant = True
    ## clean up genres
    gs = genres + list(set(jw_genres) - set(genres))
    if 'Comedy' in gs:
        user_in = input("Is {} in the 'Stand-Up' genre? [y or n]  ".format(title))
        if user_in == 'y':
            gs.append('Stand-Up')
    if gs is None or not any(gs):
        gs = []

    movies_db = movies_db.append({
        'movielens_id' : new_id
        , 'netflix_id' : netflix_id
        , 'tmdb_id' : tmdb_id
        , 'imdb_id' : imdb_id
        , 'title' : new_title
        , 'rating' : new_rating
        , 'netflix_rating' : netflix_rating
        , 'genres' : gs
        , 'netflix_instant' : netflix_instant
        , 'streams' : streams
        , 'year' : year
        , 'runtime' : runtime
        , 'overview' : overview
        , 'tagline' : tagline
        , 'jw_id' : jw_id
        , 'rt_score' : rt_score
        , 'numratings' : num_rating
        , 'avgrating' : avg_rating
    }, ignore_index = True)

    print("{} added.".format(new_title))
    keepgoing = input("\nAdd another movie? [y or n]  ")
    if keepgoing == 'n':
        keepgoing = False

if updatestreaming:
    print("\nUpdating database with streaming availability and latest RT scores...\n")
    for idx, row in movies_db.iterrows():
        title = movies_db.loc[idx, 'title']
        print(title)
        jw_id = movies_db.loc[idx, 'jw_id']
        prev_rt_score = movies_db.loc[idx, 'rt_score']
        if not not jw_id and isinstance(jw_id, float) and not np.isnan(jw_id):
            jw_id, rt_score, streams = getJustWatch(title, jw_id, jw)
            if not np.isnan(rt_score):
                movies_db.at[idx, 'rt_score'] = rt_score
            if any(streams):
                curr_streams = [s for s in streams if s in my_providers]
                streams = list(set(curr_streams))
                movies_db.at[idx, 'streams'] = streams
            else:
                movies_db.at[idx, 'streams'] = []
        else:
            print("No JustWatch ID for {}.".format(title))

        print("{}% -- {}".format(tryInt(rt_score, get = True), streams))

if updateratings:
    print("\nUpdating database with latest predicted ratings...\n")
    browser = webdriver.Chrome(config['WEBDRIVER_PATH'])

    ## login
    loginpage = 'https://movielens.org/login'
    browser.get(loginpage)
    inputs = browser.find_elements_by_tag_name('input')
    inputs[0].send_keys(config['MOVIELENS_UN'])
    inputs[1].send_keys(config['MOVIELENS_PW'])
    submitbutton = browser.find_element_by_tag_name('button')
    submitbutton.click()

    time.sleep(3)
    ## loop through movies in DB
    for idx, row in movies_db.iterrows():
        print(movies_db.loc[idx, 'title'])
        print('Previous rating: {}'.format(
            tryFloat(movies_db.loc[idx, 'rating'], get = True)
        ))
        movielens_id = tryFloat(movies_db.loc[idx, 'movielens_id'], get = True)
        if movielens_id != '' and not np.isnan(movielens_id):
            url = 'https://movielens.org/movies/' + str(tryInt(movielens_id, get = True))
            while True:
                try:
                    browser.get(url)
                    time.sleep(0.5)
                    inner = browser.execute_script("return document.body.innerHTML")
                    soup = BeautifulSoup(inner, features="lxml")
                    ## predicted rating
                    rating = soup.find(
                        'div', {'class': 'movie-details-heading'}
                    ).findNext('div').text
                    rating = re.findall("\d+\.\d+", rating)[0]
                    rating = float(rating)
                    print('Updated rating: {}'.format(rating))
                    ## number of ratings
                    numratings = soup.findAll(
                        'div', {'class': 'movie-details-heading'}
                    )[1].text
                    numratings = tryInt(
                        numratings.split('Average of ')[1].split(' ')[0].replace(',', ''),
                        get = True
                    )
                    ## average rating
                    avgrating = soup.findAll(
                        'div', {'class': 'movie-details-heading'}
                    )[1].findNext('div').text
                    avgrating = re.findall("\d+\.\d+", avgrating)[0]
                    avgrating = float(avgrating)

                    ## update
                    movies_db.at[idx, 'rating'] = rating
                    movies_db.at[idx, 'numratings'] = numratings
                    movies_db.at[idx, 'avgrating'] = avgrating
                except:
                    print("MovieLens not reached. Try again...")
                    print("** Rate Limit was likely exceeded. Please use VPN. **")
                else:
                    break

movies_db.reset_index(inplace = True, drop = True)
with open('databases/movies_db.json', 'w') as outfile:
    json.dump(list(movies_db.T.to_dict().values()), outfile)
