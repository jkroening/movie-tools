from justwatch import JustWatch
import numpy as np
import pandas as pd
from unidecode import unidecode


def siftJustWatch(title, jw = None):
    if jw == None:
        jw = JustWatch(country = 'US')
    sel = 'n'
    jw_title = None
    res = jw.search_for_item(query = title)
    for r in res['items']:
        if 'scoring' in r:
            jw_title = unidecode(r['title']).replace(',', '')
            print(r['id'])
            print(r['title'])
            print(r['original_release_year'])
            if 'short_description' in r.keys():
                print(unidecode(r['short_description']))
            sel = input(
                "Matching '{}' with '{}' ({})... OK? [y or n] ".format(
                    title, jw_title, r['id']
                )
            ).lower()
        if sel == 'y':
            jw_id = r['id']
            break
    if sel != 'y':
        print("Unable to find match in JustWatch for '{}'".format(title))
    else:
        print("JustWatch ID is {}".format(int(jw_id)))

inp = input("What is the title of the film? ")
siftJustWatch(inp)
