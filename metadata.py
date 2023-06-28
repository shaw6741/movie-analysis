import requests, time, re
from bs4 import BeautifulSoup
# Disable chardet debug messages
import logging
logging.getLogger().setLevel(logging.WARNING)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MovieMetadata:
    def __init__(self, url_short = None):
        self.film_url_short = url_short
        self.movie = self.film_url_short.split('/')[-2]
        self.headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
                'referer': 'https://google.com',
            }
        self.url = 'https://letterboxd.com/film/{}/'.format(self.movie)
        self.soup = self.get_soup()

    def get_soup(self):
        page = ''
        while page == '':
            try:
                r = requests.get(self.url, verify = False, headers = self.headers)
                break
            except:
                print("Connection refused by the server..")
                time.sleep(2)
                continue
        #r = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        return soup

    def get_header_desc(self):
        # header  + desc
        header_section = self.soup.find('section', id='featured-film-header')
        title = header_section.find('h1').text.strip() if header_section.find('h1') else None
        year = header_section.find('small').text.strip() if header_section.find('small') else None
        director = header_section.find('span').text.strip() if header_section.find('span') else None

        desc = self.soup.find('div', class_='review body-text -prose -hero prettify')
        desc = desc.find('div') if desc else None
        desc = desc.text.strip() if desc else None

        return title, year, director, desc

    def get_cast(self):
        cast = self.soup.find('div', class_='cast-list text-sluglist')
        if cast != None:
            cast = cast.find_all('a', class_='text-slug tooltip')
            if len(cast) == 0:
                cast = None
            else:
                cast = [ppl.text.strip() for ppl in cast]
        else:
            cast = None
        return cast

    def get_crew(self):
        crew_div = self.soup.find('div', id='tab-crew')
        if crew_div != None:
            crew_dic, current_key = {}, None
            for child in crew_div.children:
                if child.name == 'h3':
                    current_key = child.find('span', class_='crewrole -full').text.strip()
                    crew_dic[current_key] = []
                elif child.name == 'div' and child.has_attr('class') and 'text-sluglist' in child['class']:
                    names = [a.text.strip() for a in child.find_all('a', class_='text-slug')]
                    crew_dic[current_key].extend(names)
        else:
            crew_dic = None
        return crew_dic

    def get_details(self):
        details_div = self.soup.find('div', id='tab-details')
        if details_div != None:
            details_dic, current_key = {}, None
            for child in details_div.children:
                if child.name == 'h3':
                    current_key = child.find('span').text.strip()
                    details_dic[current_key] = []
                elif child.name == 'div' and child.has_attr('class') and 'text-sluglist' in child['class']:
                    names = [a.text.strip() for a in child.find_all('a', class_='text-slug')]
                    details_dic[current_key].extend(names)
                elif child.name == 'div' and child.has_attr('class') and 'text-indentedlist' in child['class']:
                    names = [a.text.strip() for a in child.find_all('p')]
                    details_dic[current_key].extend(names)
        else:
            details_dic = None
        return details_dic

    def get_genres(self):
        genres_div = self.soup.find('div', id='tab-genres')
        if genres_div != None:
            genres_dic, current_key = {}, None
            for child in genres_div.children:
                if child.name == 'h3':
                    current_key = child.find('span').text.strip()
                    genres_dic[current_key] = []
                elif child.name == 'div' and child.has_attr('class') and 'text-sluglist' in child['class']:
                    names = [a.text.strip() for a in child.find_all('a', class_='text-slug')]
                    genres_dic[current_key].extend(names)
        else:
            genres_dic = None
        return genres_dic

    def get_footer(self):
        try:
            footer = self.soup.find('p', class_='text-link text-footer')
            run_time = footer.text.strip().split('\xa0')[0] # in minutes
            imdb = footer.find('a', attrs={"data-track-action": "IMDb"})
            tmdb = footer.find('a', attrs={"data-track-action": "TMDb"})
            imdb = imdb['href'].split('/')[4] if imdb else None
            tmdb = tmdb['href'].split('/')[4] if tmdb else None
            return run_time, imdb, tmdb
        except:
            return None, None, None

    def get_stats(self):
        #movie = self.url.split('/')[-2]
        r = requests.get(f'https://letterboxd.com/esi/film/{self.movie}/stats/', verify=False, headers=self.headers)
        soup = BeautifulSoup(r.content, 'lxml', )

        watched_by = soup.find('a', {'class': 'has-icon icon-watched icon-16 tooltip'})
        listed_by = soup.find('a', {'class': 'has-icon icon-list icon-16 tooltip'})
        liked_by = soup.find('a', {'class': 'has-icon icon-like icon-liked icon-16 tooltip'})

        watched_by = watched_by.text if watched_by else None
        listed_by = listed_by.text if listed_by else None
        liked_by = liked_by.text if liked_by else None

        return watched_by, listed_by, liked_by

    def get_rate(self):
        url = 'https://letterboxd.com//csi/film/{}/rating-histogram/'.format(self.movie)
        r = requests.get(url, headers=self.headers, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        ratings = soup.find('span', class_='average-rating').find('a') if soup.find('span', class_='average-rating') else None
        if ratings:
            rating = ratings['title'].split(' ')[3]
            rated_by = ratings['title'].split(' ')[6].split('\xa0')[0]
        else:
            rating, rated_by = None, None
        return rating, rated_by

    def get_poster_link(self):
        element = self.soup.find('script', {'type' : 'application/ld+json'})
        if element:
            element = element.text.strip()
            poster_link = re.search(r'"image":"([^"]+)"', element)
            if poster_link:
                poster_link = poster_link.group(1)
            else:
                poster_link = None
        else:
            poster_link = None
        return poster_link

    def combine_all(self):
        try:
            title, year, director, desc = self.get_header_desc()
            cast, crew_dic = self.get_cast(), self.get_crew()
            details_dic, genres_dic = self.get_details(), self.get_genres()
            run_time, imdb_id, tmdb_id = self.get_footer()
            watched_by, listed_by, liked_by = self.get_stats()
            rating, rated_by = self.get_rate()
            poster_link = self.get_poster_link()

            def convert_to_number(value):
                if value != None:
                    try:
                        number = float(value)
                        return number
                    except ValueError:
                        return None
                else:
                    return None

            meta_dic = {
                'title': title,
                'year': convert_to_number(year),
                'director': director, 'desc': desc,
                'cast': cast}
            if crew_dic != None:
                meta_dic.update(crew_dic)
            if details_dic != None:
                meta_dic.update(details_dic)
            if genres_dic != None:
                meta_dic.update(genres_dic)
            meta_dic.update({
                'runtime': convert_to_number(run_time),
                'imdb_id': imdb_id,
                'tmdb_id': tmdb_id,
                'watched_by': watched_by,
                'listed_by': listed_by,
                'liked_by': liked_by,
                'rating': convert_to_number(rating),
                'rated_by': convert_to_number(rated_by),
                'poster': poster_link}
            )
        except:
            meta_dic = None
            print(self.movie, 'error')
        return meta_dic