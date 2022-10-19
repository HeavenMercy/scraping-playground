from playwright.sync_api import sync_playwright

# skip the challenge: div.cp-challenge button.secondary-action-new

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()

        page.goto('https://www.linkedin.com')

        uname = input('[username]: ')
        passwd = input('[password]: ')

        page.fill('input[name="session_key"]', uname)
        page.fill('input[name="session_password"]', passwd)
        page.keyboard.press('Enter')

        page.wait_for_timeout(3000)
        if page.is_visible('input[name="pin"]'):
            pin = input('enter the pin received: ')
            page.fill('input[name="pin"]', pin)
            page.keyboard.press('Enter')

        page.wait_for_timeout(3000)
        if page.is_visible('div.cp-challenge'):
            page.click('div.cp-challenge button.secondary-action-new')


        page.wait_for_timeout(20000)



if __name__ == "__main__": main()