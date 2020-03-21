import sys
import shutil
import json
import pandas as pd
import numpy as np
import pdb

with open("databases/movies_db.json", "r") as f:
    movies_in = json.load(f)
    movies_db = pd.DataFrame(movies_in)

## backup database
shutil.copyfile('databases/movies_db.json', 'databases/backup/movies_db.json')

## remove by title
in_one = input("What's the name of the movie to remove? ")
title_idx = [in_one.lower() in t.lower() for t in movies_db.title.values]

if sum(title_idx) == 0:
    print("\nNo matches found.")
    sys.exit()

print("\n{}".format(movies_db.loc[title_idx, ['title', 'rating', 'year', 'runtime', 'genres', 'streams', 'tagline']].to_string()))

if len(movies_db.loc[title_idx, ]) > 1:
    in_two = int(input("\nWhich one? (Enter index of row) "))
    if isinstance(in_two, int):
        print("\n{}".format(movies_db[[
            'title', 'rating', 'year', 'runtime', 'genres', 'streams', 'tagline'
        ]].loc[in_two, ]))
    else:
        print("Please enter a valid row number index next time. Exiting...")
        sys.exit()
else:
    in_two = int(movies_db.loc[title_idx, ].index[0])
in_three = input("\nThis one? (y or n) ")

if in_three == 'y' and isinstance(in_two, int):
    movies_db = movies_db.loc[movies_db.index != in_two, ]
    with open('databases/movies_db.json', 'w') as outfile:
        json.dump(list(movies_db.T.to_dict().values()), outfile)
else:
    print("\nOK. Try again.")
