import re
import unicodecsv as csv
from bs4 import BeautifulSoup

with open('input/letterboxd.html') as lb:
    lbsoup = BeautifulSoup(lb, 'html.parser')
## with open('input/movielens.html') as ml:
##     mlsoup = BeautifulSoup(ml, 'html.parser')
with open('input/movielens.txt') as mt: ## copy/paste version
    mtsoup = BeautifulSoup(mt, 'lxml')

lbdivs = lbsoup.find_all('div', attrs = {'data-film-name': True})
lbdict = {}
lbtxts = []
for div in lbdivs:
    lbtxts.append(div['data-film-name'])
    year = None
    if 'data-film-release-year' in div.attrs:
        year = div['data-film-release-year']
    else:
        imga = div.findNext('img').findNext('a')
        if 'data-original-title' in imga.attrs:
            match = re.search(r"\((\d+)\)$", imga['data-original-title'])
            if match.group(1).isdigit():
                year = match.group(1)
    lbdict[div['data-film-id']] = {
        'title': div['data-film-name'],
        'year': year
    }

## mlpees = mlsoup.find_all('p', 'title')
## mltxts = [p.text for p in mlpees]

mltxts = [
    re.search(r'(?<=poster for ).*', a).group(0)
    for a in mtsoup.find('p').text.splitlines()
    if re.search(r'(?<=poster for ).*', a) is not None
]

intersect = [mov for mov in mltxts if mov.lower() in [vid.lower() for vid in lbtxts]]

print('\n')
with open('output/whattowatch.csv', 'wb') as csvfile:
    csvwriter = csv.writer(
        csvfile, quotechar = '"', delimiter = ',', escapechar = '\\'
    )
    csvwriter.writerow(['Title', 'Year'])
    for sect in intersect:
        print(sect)
        ## simply take the last item in case of multiple matches
        out = [[i, x['year']] for i, x in lbdict.items() if x['title'] == sect][-1]
        ## handle duplicate titles by removing
        del lbdict[out[0]]
        csvwriter.writerow([sect, out[1]])
print('\n')