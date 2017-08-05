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
## "savedQueueItems" and copy that outerHTML into saved_queue.html.
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


parser = argparse.ArgumentParser()
parser.add_argument("--streaming", help = "only display movies that are available to stream",
                    action = "store_true")
args = parser.parse_args()

## load database
try:
    with open("databases/movies_db.json", "r") as f:
        movies_in = json.load(f)
        out_movies = pd.DataFrame(movies_in)
except:
    out_movies = pd.DataFrame({
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
        , 'rt_score' : []
    })

## whether canistream.it should be checked for existing DB entries to update streams
if args.streaming:
    streaming = True
    ## subset out_movies
    out_movies = out_movies.loc[[True if x != [] else False for x in out_movies.streams.values], ]
else:
    streaming = False
    print("To show only the movies that are available to stream, enter '--streaming' as a command line argument.\n")

complete_genres = np.unique([x for y in out_movies.genres.values for x in y]).tolist()

sorted_movies = []
while len(sorted_movies) == 0:
    print("\nOf the following genres...\n{}".format([str(g) for g in complete_genres]))
    genre_in = raw_input("Which genre(s) do you want to watch? (Enter up to 2, separated by a comma; or 'All'): ")

    out_movies.rating = [round(o, 1) if isinstance(o, float) else np.nan for o in out_movies.rating.values]
    if genre_in.lower() == 'all':
        sorted_movies = out_movies.sort_values(['rating', 'rt_score'], ascending = [False, False])
    else:
        genres_in = [g.strip() for g in genre_in.split(",")]

        genre1_idx = [True if genres_in[0].lower() in k else False for k in [[j.lower() for j in i] for i in out_movies.genres.values]]
        if len(genres_in) > 1:
            genre2_idx = [True if genres_in[1].lower() in k else False for k in [[j.lower() for j in i] for i in out_movies.genres.values]]
            genre_idx = np.array(genre1_idx) * np.array(genre2_idx)
        else:
            genre_idx = genre1_idx

        movies_genred = out_movies.loc[genre_idx, ]
        sorted_movies = movies_genred.sort_values(['rating', 'rt_score'], ascending = [False, False])

    print("\n{}\n".format(sorted_movies[['title', 'rating', 'rt_score', 'year', 'runtime', 'genres', 'streams', 'tagline']].to_string()))

while True:
    user_in = raw_input("Enter the row index number of movie you want to know more about: (or q to quit)  ")
    if user_in.lower() == 'q':
        break
    tl = sorted_movies.ix[int(user_in), 'tagline']
    if tl is None or not len(tl): tl = 'No tagline.'
    runtime = sorted_movies.ix[int(user_in), 'runtime']
    if runtime is None or str(runtime) == "NaN": runtime = "???"
    streams = sorted_movies.ix[int(user_in), 'streams']
    if not len(streams): streams = 'Not available to stream.'
    rt_score = sorted_movies.ix[int(user_in), 'rt_score']
    if rt_score != 'NaN': rt_score = int(rt_score)
    print("\n{}".format(sorted_movies.ix[int(user_in), 'title']))
    print("\n{}".format(tl))
    print("\n{}".format(sorted_movies.ix[int(user_in), 'overview']))
    print("\n{}".format(int(sorted_movies.ix[int(user_in), 'year'])))
    print("\n{} mins".format(runtime))
    print("\n{} stars".format(round(sorted_movies.ix[int(user_in), 'rating'], 1)))
    print("\n{}%").format(rt_score)
    print("\n{}".format(sorted_movies.ix[int(user_in), 'genres']))
    print("\n{}\n".format(streams))
