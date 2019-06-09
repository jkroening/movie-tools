from selenium import webdriver
from bs4 import BeautifulSoup
import re
import time

browser = webdriver.Chrome(
    '/Users/jonathan/Dropbox/Projects/Miscellaneous Scripts/chromedriver'
)

loginpage = 'https://movielens.org/login'
browser.get(loginpage)
inputs = browser.find_elements_by_tag_name('input')
inputs[0].send_keys('jkroening@gmail.com')
inputs[1].send_keys('C*8m8pKSj!3sekGFp^DP32')
submitbutton = browser.find_element_by_tag_name('button')
submitbutton.click()

time.sleep(5)


url = 'https://movielens.org/movies/168248'
browser.get(url)
inner = browser.execute_script("return document.body.innerHTML")

soup = BeautifulSoup(inner)
rating = soup.find('div', {'class': 'row movie-highlights'}).find(
    'div', {'class': 'ng-binding'}
).text
rating = re.findall("\d+\.\d+", rating)[0]
rating = float(rating)
