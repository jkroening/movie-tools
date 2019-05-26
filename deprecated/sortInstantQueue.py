from requests import Session
from robobrowser import RoboBrowser
import cookielib
import pdb

session = Session()
session.verify = False # Skip SSL verification
cj = cookielib.MozillaCookieJar('cookies.txt')
cj.load()
browser = RoboBrowser(session=session)
## Instant Queue
browser.open("http://www.netflix.com/MyList", cookies = cj)

# get the form
queue_form = browser.get_form(id='MainQueueForm')
# queue_submit = queue_form.submit_fields['evoSubmit']

predictions = []
skip_keys = ["queueHeader"]
for key in queue_form.keys():
    if key in skip_keys:
        continue
    if 'OP' in key:
        continue
    spans = browser.find_all("input", {"name" : key })[0].findAllNext("span")
    for s in spans:
        if s is not None:
            for c in s['class']:
                if 'sbmf-' in c:
                    predicted_rating = c.strip("sbmf-")
                    if key not in (item[0] for item in predictions):
                        predictions.append((key, predicted_rating))

sorted_preds = sorted(predictions, key=lambda x: float(x[1]), reverse=True)

# for i in xrange(len(sorted_preds)):
#     in_arg = 
#     in_target
#     queue_form[sorted_preds[i][0]].value = i
# ## form submit not actually working here, it doesn't seem to take
# browser.submit_form(queue_form, queue_submit)

html = browser.parsed
for idx, tpl in enumerate(sorted_preds):
    key, value = tpl
    html.find("input", {"name" : key })['value'] = idx + 1

form = html.find("form", {"id" : "MainQueueForm"})

qbody = html.find("tbody", {"id" : "qbody"})
with open("qbody", "w") as f:
    f.write(qbody.prettify('utf-8'))
