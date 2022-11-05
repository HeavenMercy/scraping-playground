import requests as rq
from bs4 import BeautifulSoup, Tag

import pandas as pd

urls = ['http://books.toscrape.com']

def main():
    articles = []

    while len(urls) > 0:
        req = rq.get(urls.pop(), proxies={'http': '64.225.97.57:8080', 'https': '64.225.97.57:8080'})
        base_url = '/'.join(req.url.split('/')[0:-1])

        print(f'scraping {req.url}...')
        bs = BeautifulSoup(req.text, 'lxml')

        for article in bs.find_all('article'):
            article = parse_article(article, base_url)
            if article == None: continue

            print(f'found {article}...')
            articles.append(article)

        next = bs.select('li.next a')
        if next:
            next = next[0]['href']
            urls.insert(0, F"{base_url}/{next}")
        else: print('no next page found!')

    df = pd.DataFrame(articles)
    df.to_csv('./output/books.csv')


ratings = ['zero', 'one', 'two', 'three', 'four', 'five']

def parse_article(article: Tag, base_url: str):
    try:
        img = article.select('div.image_container > a > img.thumbnail')[0]
        rating = article.find('p', {'class': 'star-rating'})
        title = article.select('h3 a')[0]
        price = article.find('div', {'class': 'product_price'})

        return {
            'title': title['title'],
            'cover_url': f"{base_url}/{img['src']}",
            'price': price.find('p', {'class': 'price_color'}).text,
            'rating': ratings.index(rating['class'][-1].lower()),
            'link': f"{base_url}/{title['href']}",
            'available': (price.find('i', {'class': 'icon-ok'}) != None)
        }
    except:
        return None

if __name__ == "__main__": main()
