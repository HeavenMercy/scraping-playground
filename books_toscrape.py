import requests as rq
from bs4 import BeautifulSoup, Tag

import pandas as pd

urls = ['http://books.toscrape.com']

def main():
    resp = rq.get(urls.pop())
    base_url = '/'.join(resp.url.split('/')[0:-1])

    print(f"scraping url '{resp.url}'...")
    bs = BeautifulSoup(resp.text, 'lxml')

    books = []
    for cat in bs.select('.side_categories ul ul > li a'):
        books += get_books(cat['href'], base_url)

    return books


def get_books(cat_url: str, base_url: str):
    resp = rq.get(f"{base_url}/{cat_url}")

    bs = BeautifulSoup(resp.text, 'lxml')
    category = bs.select_one('.page-header h1').text.strip()

    print(f"inspecting categorie '{category}'...")

    books = []
    for article in bs.select('.page_inner .row ol li'):
        book = parse_book(article.select_one('a')['href'], base_url, category=category)
        if book is not None: books.append( book )

    return books


ratings = ['zero', 'one', 'two', 'three', 'four', 'five']

def parse_book(book: Tag, base_url: str, category: str):
    try:
        resp = rq.get(f"{base_url}/catalogue/{book.replace('../', '')}")
        bs = BeautifulSoup(resp.text, 'lxml')

        cover = bs.select_one('.product_page #product_gallery img')['src']
        cover = f"{base_url}/{cover.replace('../', '')}"

        title = bs.select_one('.product_page h1').text.strip()
        description = bs.select_one('.product_page #product_description + p').text.replace('...more', '').strip()

        data = {'Cover': cover, 'Title': title, 'Description': description, 'Category': category}
        for d in bs.select('.product_page table tr'):
            data[d.select_one('th').text.strip()] = d.select_one('td').text.strip()

        print(f"data extracted for '{title}'...")
        return data
    except Exception as e:
        print(e)
        return None


if __name__ == "__main__":
    pd.DataFrame(main()).to_csv('output/books.csv')

