import requests as rq
from bs4 import BeautifulSoup, Tag

import pandas as pd

DEBUG = True
LOCATION = 'obili'
OUTPUT = f'output/locanto_{LOCATION}.csv'

url_queue = [f'https://www.locanto.cm/Location-appartement/301/?query={LOCATION}']

def main():
    result = []

    while len(url_queue) > 0:
        response = rq.get(url_queue.pop(0))
        if not response.ok: continue

        bs = BeautifulSoup(response.text, 'lxml')

        extracted_count = 0
        for item in bs.select('div.entries > div.resultRow'):
            if not item.has_attr('id'): continue

            item = parse_item(item)
            if item is not None:
                result.append(item)
                extracted_count += 1

        dprint(f'extracted {extracted_count} announcements from {response.url}')

        fetch_next_page(bs)

    dprint(f'end of task => {len(result)} announces extracted')

    # output
    df = pd.DataFrame(result)
    if OUTPUT.endswith('.csv'):
        df.to_csv(OUTPUT, index=False)
    elif OUTPUT.endswith('.json'):
        df.to_json(OUTPUT, index=False)
    else: df.to_dict()


def parse_item(item: Tag):
    try:
        description = item.find('div', {'class': 'resultMain'})

        image = item.select_one('div.resultImage img')
        image = image['data-src'] if image is not None else ''

        price = description.select_one('div.bp_ad__second_header')
        price = int(price.text.split()[0].replace(',', '')) if price is not None else 0

        return {
            'title': description.select_one('div.textHeader h3').find(text=True, recursive=False).strip(),
            'description_part': description.select_one('div.textDesc').text.strip(),
            'price': price,
            'link': description.select_one('div.textHeader a')['href'],
            'image_url': image,
        }
    except Exception as e:
        print(e)
        return None

def fetch_next_page(bs: BeautifulSoup):
    paging = bs.select('div.paging a')

    if len(paging) > 1:
        next_page = paging[-1]

        next_found = False
        if next_page['page'] != next_page.get_text().strip():
            for page in paging[:-1]:
                if page['page'] == next_page['page']:
                    next_found = True
                    break

        if next_found:
            dprint(f"adding {next_page['href']} to queue...")
            url_queue.append(next_page['href'])

def dprint(msg: str):
    if DEBUG: print(msg)

if __name__ == "__main__": main()