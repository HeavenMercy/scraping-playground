from multiprocessing import Process, Queue
from playwright.sync_api import sync_playwright

from bs4 import BeautifulSoup

_processes = []

def main():
    queue = Queue()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://demo.opencart.com/admin')
        page.fill('input[name="username"]', 'demo')
        page.fill('input[name="password"]', 'demo')
        page.click('button[type="submit"]')

        try:
            page.click('button.btn-close[data-bs-dismiss="modal"]')
        except: pass

        page.click('li#menu-catalog > a')
        page.click('li#menu-catalog ul > li:nth-child(2) > a')

        while True:
            process = Process(target=scrape_page, args=(page.inner_html('div#product'), queue))
            process.start()
            _processes.append(process)

            next_page = page.query_selector('li.page-item.active + li > a')
            if next_page == None: break

            next_page.click()
            next_page.wait_for_element_state('hidden')

        g = Process(target=generate_output, args=(queue,))
        g.start()

        for process in _processes:
            process.join()

        queue.put(None)
        g.join()

def generate_output(queue: Queue):
    output = []
    while True:
        product = queue.get()
        if product == None: break

        output.append(product)

    import pandas as pd

    df = pd.DataFrame(output)
    df.to_csv('output/opencart.csv', index=False)

def scrape_page(html: str, queue: Queue):
    bs = BeautifulSoup(html, 'lxml')
    for product in bs.select('table tr')[1:]:
        main_part = product.select_one('td:nth-child(3)').text.split('\n\n')

        prices = product.select_one('td:nth-child(5)').text.split('\n\n')

        queue.put({
            'name': main_part[0].strip(),
            'enabled': ((len(main_part) > 1) and (main_part[-1].strip().lower() == 'enabled')),
            'price': prices[-1].strip(),
            'old_price': (prices[0].strip() if len(prices) > 1 else None),
            'quantity': product.select_one('td:nth-child(6)').text.strip(),
        })



if __name__ == "__main__": main()