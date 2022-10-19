from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)

        page = browser.new_page()
        page.goto('https://shoppable-campaign-demo.netlify.app/#/')
        page.is_visible('div#productListing')

        content = page.inner_html('div#productListing')
        browser.close()

        result = scrape_content( content )
        if len(result) == 0: return

        df = pd.DataFrame(result)
        df.to_csv('./output/commerce_js_ng.csv', index=False)


def scrape_content(html: str) -> list:
    bs = BeautifulSoup(html, 'lxml')
    result = []

    for product in bs.select('div.product-item-container div.card > div.row'):
        try:
            body = product.find('div', {'class': 'card-body'})
            form = product.find('div', {'class': 'form-group'})

            result.append({
                'name': body.find('h3').text,
                'description': body.find('div', {'class': 'card-text'}).text,
                'image': product.find_all('img')[-1]['src'],
                'price': float(form.find('label').text[1:]),
                'options': ', '.join(map(lambda o: o.text.strip(), form.find_all('option')[1:])),
            })
        except: continue

    return result


if __name__ == "__main__": main()