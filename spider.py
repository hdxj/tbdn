import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
wait = WebDriverWait(browser,10)
browser.set_window_size(1400,900)


##
def search():
    try:
        browser.get('https://www.taobao.com/')
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#q')))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button')))
        input.send_keys('电脑')
        submit.click()
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total')))
        total = total.text
        total = re.compile('(\d+)').search(total).group()
        get_product()
        return int(total)
    except TimeoutException:
        return search()

def get_next_page(page_num):
    input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > input')))
    submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
    input.clear()
    input.send_keys(page_num)
    submit.click()
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_num)))
    get_product()

def get_product():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist > div > div')))
    html = browser.page_source
    items = BeautifulSoup(html,'lxml').find('div',class_='grid g-clearfix').find_all('div',class_="item J_MouserOnverReq ")
    for item in items:
        product = {
            'title':item.find('div',class_="row row-2 title").get_text().replace('\n','').strip(),
            'url':'https:'+item.find('div',class_="row row-2 title").find('a')['href'],
            'price':item.find('div',class_="price g_price g_price-highlight").get_text().replace('\n',''),
            'deal':item.find('div',class_="deal-cnt").get_text()[:-3],
            'shop_name':item.find('div',class_='shop').get_text().replace('\n',''),
            'location':item.find('div',class_='location').get_text()
        }
        save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储成功。',result)
    except Exception:
        print('存储失败',result)

def main():
    total = search()
    for i in range(2,total+1):
        get_next_page(i)
    browser.close()

if __name__ == '__main__':
    main()


