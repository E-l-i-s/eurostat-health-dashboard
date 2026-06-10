from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        print('Taking screenshot of Dashboard 1...')
        page.goto('http://127.0.0.1:5000/')
        page.wait_for_timeout(3000) # Wait for charts/data to load
        page.screenshot(path='c:/Users/elisa/Desktop/KEMV-Final/Capstone3/screenshots/dashboard1_working.png')
        
        print('Taking screenshot of Dashboard 2...')
        page.goto('http://127.0.0.1:5000/analytics')
        page.wait_for_timeout(3000)
        page.screenshot(path='c:/Users/elisa/Desktop/KEMV-Final/Capstone3/screenshots/dashboard2_working.png')
        
        print('Interacting with Dashboard 1 filter...')
        page.goto('http://127.0.0.1:5000/')
        page.wait_for_timeout(2000)
        page.select_option('select#wave-select', '2014')
        page.wait_for_timeout(2000)
        page.screenshot(path='c:/Users/elisa/Desktop/KEMV-Final/Capstone3/screenshots/dashboard1_filtered.png')
        
        browser.close()

if __name__ == '__main__':
    run()
