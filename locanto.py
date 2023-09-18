from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = 'https://www.locanto.cm/Immobilier/R/?type=rent'


def extract_content(url: str):
    if not url: return []

    result = []

    # extracting content
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()

        next_url = url

        while True:
            try:
                page.goto(next_url)

                content = page.inner_html('.main_content')
                bs = BeautifulSoup(content, 'lxml')

                result.append(tag for tag in bs.select('.resultRow .textHeader a'))

                next = bs.select('.paging a')[-1]

                if 'Suivant' not in next.text: break

                next_url = next['href']
                print('next...', end=', ')
            except Exception as e:
                print(e)
                break

    return result

if __name__ == '__main__':
    extract_content(url)


