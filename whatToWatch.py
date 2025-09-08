import re
import unicodecsv as csv
from datetime import datetime
from bs4 import BeautifulSoup
import pdb

def extractYear(title):
    current_year = datetime.now().year
    matches = list(re.finditer(r'\((\d{4})\)', title))
    for match in reversed(matches):
        year = int(match.group(1))
        if 1880 <= year <= current_year:
            start, end = match.span()
            cleaned_title = (title[:start] + title[end:]).strip()
            cleaned_title = re.sub(r'\s{2,}', ' ', cleaned_title)
            return cleaned_title, year
    return title, None

with open('input/letterboxd.html') as lb:
    lbsoup = BeautifulSoup(lb, 'html.parser')
## with open('input/movielens.html') as ml:
##     mlsoup = BeautifulSoup(ml, 'html.parser')
with open('input/movielens.txt') as mt: ## copy/paste version
    mtsoup = BeautifulSoup(mt, 'lxml')

lbdivs = lbsoup.find_all('div', attrs = {'data-item-name': True})
lbdict = {}
lbtxts = []
for div in lbdivs:
    name, year = extractYear(div['data-item-name'])
    lbtxts.append(name)
    if not year:
        imga = div.findNext('img').findNext('a')
        if 'data-original-title' in imga.attrs:
            match = re.search(r"\((\d+)\)$", imga['data-original-title'])
            if match is None:
               match = re.search(r"\((\d+)\)", imga['data-original-title'])
            if match.group(1).isdigit():
                year = match.group(1)
    lbdict[div['data-film-id']] = {
        'title': name,
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
        entry = [[i, x['year']] for i, x in lbdict.items() if x['title'] == sect]
        if len(entry):
            ## simply take the last item in case of multiple matches
            out = [[i, x['year']] for i, x in lbdict.items() if x['title'] == sect][-1]
            ## handle duplicate titles by removing
            del lbdict[out[0]]
            csvwriter.writerow([sect, out[1]])
print('\n')