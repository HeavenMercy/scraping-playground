from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from bs4 import BeautifulSoup



driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def wait_for_element_by(by: tuple):
    return WebDriverWait(driver, 10).until(EC.element_to_be_clickable(by))

# ---------------------------------------------------------------------------------------------------------------

driver.get('https://shoppable-campaign-demo.netlify.app/#/')

wait_for_element_by((By.CSS_SELECTOR, 'div#productListing'))

bs = BeautifulSoup(driver.page_source, 'lxml')

driver.quit()


# ---------------------------------------------------------------------------------------------------------------

products = []

for product in bs.select('div.product-item-container div.card > div.row'):
    description = product.select_one('div:nth-child(3) div.card-body')
    form = description.find('div', {'class': 'form-group'})

    products.append({
        'title': description.find('h3', {'class': 'card-title'}).text,
        'description': description.find('div', {'class': 'card-text'}).text,
        'price': float( form.find('label').text[1:] ),
        'options': list(map(lambda o: o.text.strip(), form.select('select option')[1:])),
        'image': product.select_one('img')['src']
    })

import pandas as pd

df = pd.DataFrame(products)
df.to_csv('output/commerce_js.csv', index=True)

