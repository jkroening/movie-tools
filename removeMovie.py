import sys
import json
import pandas as pd
import numpy as np
import pdb

with open("movies_db.json", "r") as f:
    movies_in = json.load(f)
    movies_db = pd.DataFrame(movies_in)

## remove by title
in_one = raw_input("What's the name of the movie to remove? ")
title_idx = [in_one.lower() in t.lower() for t in movies_db.title.values]

if sum(title_idx) == 0:
    print("\nNo matches found.")
    sys.exit()

print("\n{}".format(movies_db.loc[title_idx, ['title', 'rating', 'year', 'runtime', 'genres', 'streams', 'tagline']].to_string()))

if len(movies_db.loc[title_idx, ]) > 1:
    in_two = int(raw_input("\nWhich one? (Enter index of row) "))
    if isinstance(in_two, int):
        print("\n{}".format(movies_db.loc[in_two, ['title', 'rating', 'year', 'runtime', 'genres', 'streams', 'tagline']].to_string()))
    else:
        print("Please enter a valid row number index next time. Exiting...")
        sys.exit()
else:
    in_two = movies_db.loc[title_idx, ].index[0]
in_three = raw_input("\nThis one? (y or n) ")

if in_three == 'y' and isinstance(in_two, int):
    movies_db = movies_db.loc[movies_db.index != in_two, ]
    with open('movies_db.json', 'w') as outfile:
        json.dump(movies_db.T.to_dict().values(), outfile)
else:
    print("\nOK. Try again.")
