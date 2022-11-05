from multiprocessing.pool import Pool
import requests as rq
from bs4 import BeautifulSoup

def check_proxy(row):
    try:
        row = BeautifulSoup(row, 'lxml')
        data = list(map(lambda d: d.text, row.find_all('td')))

        proxy = f'{data[0]}:{data[1]}'
        resp = rq.get('https://users.cs.cf.ac.uk/dave/PERL/node259.html', proxies={'http': proxy, 'https': proxy})

        return (data[0], data[1]) if resp.ok else None
    except: return None


def get_proxies():
    resp = rq.get('https://free-proxy-list.net/')
    if not resp.ok: return []

    bs = BeautifulSoup(resp.text, 'lxml')


    with Pool() as pool:
        result = pool.map(check_proxy, map(str, bs.select('div.fpl-list tbody tr')))
        result = [proxy for proxy in result if proxy is not None]

        return result


if __name__ == "__main__":
    result = get_proxies()
    print(len(result), 'proxies found', result)