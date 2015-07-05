from requests import Session
from robobrowser import RoboBrowser
import cookielib
import pdb

session = Session()
session.verify = False # Skip SSL verification
cj = cookielib.MozillaCookieJar('cookies.txt')
cj.load()
browser = RoboBrowser(session=session)
## DVD Queue
browser.open('http://dvd.netflix.com/Queue?prioritized=true&qtype=DD', cookies = cj)
pdb.set_trace()
# get the form
queue_form = browser.get_form(class_='hasAwaitingRelease')
queue_submit = queue_form.submit_fields['updateQueue2']

predictions = []
skip_keys = ["authURL", "updateQueueBtn", "updateQueue1", "queueHeader", "updateQueue2"]
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

qbody = html.find("div", {"id" : "qbody"})
with open("qbody", "w") as f:
    f.write(qbody.prettify('utf-8'))

## use this code to go section by section if there are too many updates and it breaks netflix form
qtbls = form.find_all('table', {"class" : "qtbl"})
pdb.set_trace()
# for i, q in enumerate(qtbls[:-1]):
#     with open("qtbl{}".format(i + 1), "w") as f:
#         f.write(q.prettify("utf-8"))
