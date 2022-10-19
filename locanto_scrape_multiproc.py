from multiprocessing import Process, Queue, cpu_count
import requests as rq
from bs4 import BeautifulSoup, Tag

DEBUG = True
CAPTURE = False

LOCATION = 'yaounde'
OUTPUT = f'output/locanto_{LOCATION}_multiproc.csv'

BASE_URL = f'https://www.locanto.cm/Location-appartement/301/?query={LOCATION}'

def getPageUrl(page: int): return f'{BASE_URL}&page={page}'

_processes = []

def main():
    to_handle = page_count = get_page_count()
    cpuc = cpu_count()
    queue = Queue(100)

    for i in range(cpuc):
        payload = []

        while to_handle > 0:
            page = len(payload) * cpuc + i
            if page >= page_count: break

            payload.append(getPageUrl(page))
            to_handle -= 1

        if len(payload) == 0: break

        dprint(f'starting process {i} with {len(payload)} urls...')
        p = Process(target=batch_sniff_urls, args=(payload, queue), name=f'sniffer_{i}')
        p.start()
        _processes.append(p)

    out_p = Process(target=generate_output, args=(queue,), name=f'generator')
    out_p.start()

    for process in _processes:
        process.join()

    queue.put(None)
    out_p.join()

# ---------------------------------------------------------------------------------------------

def find_next_block(url: str):
    response = rq.get(url)
    if not response.ok: return 0

    bs = BeautifulSoup(response.text, 'lxml')
    pages = bs.select('div.paging a')

    has_next = (len(pages) > 2) and (pages[-2].text != pages[-2]['page'])
    next = ''
    if has_next:
        next = pages[-2]['href']
        dprint(f'next block at {next}')
    else: dprint('no next block found')

    return bs, has_next, next

def get_page_count() -> int:
    bs, has_next_block, next_url = find_next_block(BASE_URL)
    while has_next_block:
        bs, has_next_block, next_url = find_next_block(next_url)

    try:
        pages = bs.select('div.paging a')
        return int(pages[-2 if len(pages) > 1 else -1]['page'])
    except: return 0

def batch_sniff_urls(urls: list, queue: Queue):
    for url in urls:
        queue.put( sniff_url(url) )

def sniff_url(url: str) -> list:
    dprint(f'getting content at {url}...')

    response = rq.get(url)
    if CAPTURE:
        with open(f'./output/{LOCATION}_page{url.split("=")[-1]}.html', 'w') as f:
            f.write(response.text)

    if not response.ok: return []

    bs = BeautifulSoup(response.text, 'lxml')

    result = []
    extracted_count = 0
    for item in bs.select('div.entries > div.resultRow'):
        if not item.has_attr('id'): continue

        item = parse_item(item)
        if item is not None:
            result.append(item)
            extracted_count += 1

    dprint(f'extracted {extracted_count} announcements at {response.url}')

    return result

def parse_item(item: Tag) -> object:
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


def generate_output(queue: Queue):
    _announces = []

    while True:
        item = queue.get()
        if item is None: break

        dprint(f'adding {len(item)} announces...')
        _announces.extend(item)

    dprint(f'end of task => {len(_announces)} announces extracted')

    # output data
    import pandas as pd

    df = pd.DataFrame(_announces)
    if OUTPUT.endswith('.csv'):
        df.to_csv(OUTPUT, index=False)
    elif OUTPUT.endswith('.json'):
        df.to_json(OUTPUT)
    else: df.to_dict()

# ---------------------------------------------------------------------------------------------

def dprint(msg: str):
    if DEBUG: print(msg, flush=True)

def capture_page(url: str):
    response = rq.get(url)
    if not response.ok: return

    with open('./output/webpage.html', 'w') as f:
        f.write(response.text)

if __name__ == "__main__": main()
