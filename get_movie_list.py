import json, requests, re, time
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
# Disable chardet debug messages
import logging
logging.getLogger().setLevel(logging.WARNING)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Example:
# <li class="listitem poster-container" data-average-rating='3.45'>
# <div class="really-lazy-load poster film-poster film-poster-203520 no-poster linked-film-poster" 
# data-cache-busting-key="00000000" data-film-id="203520" 
# data-film-slug="/film/resurrection-of-a-corpse/" 
# data-image-height="105" data-image-width="70" data-linked="linked" 
# data-poster-url="/film/resurrection-of-a-corpse/image-150/" 
# data-show-menu="true" data-target-link="/film/resurrection-of-a-corpse/" 
# data-target-link-target=""> 
# <img alt="Resurrection of a Corpse" class="image" height="105" src="https://s.ltrbxd.com/static/img/empty-poster-70.8112b435.png" width="70"/> <span class="frame"><span class="frame-title"></span></span> </div>
# </li>

class FilmScraper:
    def __init__(self, language, page):
        self.language = language
        self.page = page
        self.url = self.get_url()

    def get_url(self):
        return 'https://letterboxd.com/films/ajax/language/{}/by/release-earliest/page/{}/'.format(self.language, self.page)

    def get_rating(self, item):
        try:
            rating = float(item['data-average-rating'])
        except:
            rating = None
        return rating

    def scrape_films(self):
        page = ''
        while page=='':
            try:
                response = requests.get(self.url, verify=False)
                break
            except:
                print('sleep')
                time.sleep(5)
                continue
        
        soup = BeautifulSoup(response.content, 'html.parser')
        film_div = soup.find_all('li', class_='listitem poster-container')
        film_lst = [movie.find('div', class_='linked-film-poster')['data-target-link'] for movie in film_div]
        rate_lst = [self.get_rating(movie) for movie in film_div]
        return film_lst, rate_lst

def get_language_count(keys):
    # keys = ['Japanese','Korean','Chinese','Cantonese']
    response = requests.get('https://letterboxd.com/countries/', verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')
    lan_lst = soup.find_all('a', class_='link')
    lan_name_lst = [lan.find('span',class_='name').text.strip() for lan in lan_lst]
    lan_count_lst = [lan.find('span',class_='count').text.strip() for lan in lan_lst]
    
    target_lans = {}
    for key in keys:
        lan_name_idx = lan_name_lst.index(key)
        target_lans[key] = int(re.sub(',','', lan_count_lst[lan_name_idx]))
    return target_lans

def get_all(language, target_lans):
    # language1: Japanese, Korean, Chinese, Cantonese
    film_lst, rate_lst = [], []
    end_page = int(target_lans[language]/72+2)
    pbar = tqdm(range(1, end_page))
    for page in pbar:
        pbar.set_description(f'Scraping page {page} of {end_page} pages')
        scraper = FilmScraper(language.lower(), page)
        temp_film_lst, temp_rate_lst = scraper.scrape_films()
        film_lst.extend(temp_film_lst)
        rate_lst.extend(temp_rate_lst)
    return film_lst, rate_lst