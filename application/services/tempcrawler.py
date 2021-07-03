from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import requests
import time
from datetime import datetime
import pandas as pd
from urllib import parse
from config import ENV_VARIABLE
from os.path import getsize

fold_path = "./crawler_data/"
page_Max = 100

def stripID(url, wantStrip):
    loc = url.find(wantStrip)
    length = len(wantStrip)
    return url[loc+length:]

def Kklee():
    shop_id = 13
    name = 'kklee'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.kklee.co/products?page=" + \
            str(p) + "&sort_by=&order_by=&limit=24"
        #
        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//a[%i]/div[@class='Product-info']/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-12 ProductList-list']/a[%i]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//a[%i]/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//a[%i]/div[@class='Product-info']/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = chrome.find_element_by_xpath(
                    "//a[%i]/div[@class='Product-info']/div[3]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//a[%i]/div[@class='Product-info']/div[2]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Wishbykorea():
    shop_id = 14
    name = 'wishbykorea'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if(close == 1):
            chrome.quit()
            break
        url = "https://www.wishbykorea.com/collection-727&pgno=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
            print(url)
        except:
            break

        time.sleep(1)
        i = 1
        while(i < 17):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='collection_item'][%i]/div/div/label" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='collection_item'][%i]/a[@href]" % (i,)).get_attribute('href')
                page_id = page_link.replace("https://www.wishbykorea.com/collection-view-", "").replace("&ca=727", "")
                find_href = chrome.find_element_by_xpath(
                    "//div[@class='collection_item'][%i]/a/div" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip('")')
            except:
                i += 1
                if(i == 17):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='collection_item'][%i]/div[@class='collection_item_info']/div[2]/label" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = ""
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='collection_item'][%i]/div[@class='collection_item_info']/div[2]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 17):
                        p += 1
                    continue

            if(sale_price == "0"):
                i += 1
                if(i == 17):
                    p += 1
                continue

            i += 1
            if(i == 17):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Aspeed():
    shop_id = 15
    name = 'aspeed'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if(close == 1):
            chrome.quit()
            break
        url = "https://www.aspeed.co/products?page=" + \
            str(p) + "&sort_by=&order_by=&limit=72"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break

        time.sleep(1)

        i = 1
        while(i < 73):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='product-item'][%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='product-item'][%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//div[@class='product-item'][%i]/product-item/a/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 73):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='product-item'][%i]/product-item/a/div[2]/div/div[2]/div[1]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='product-item'][%i]/product-item/a/div[2]/div/div[2]/div[2]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='product-item'][%i]/product-item/a/div[2]/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 73):
                        p += 1
                    continue
            i += 1
            if(i == 73):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Openlady():
    shop_id = 17
    name = 'openlady'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.openlady.tw/item.html?&id=157172&page=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 17):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[@class='item_block item_block_y'][%i]/div[@class='item_text']/p[@class='item_name']/a[@class='mymy_item_link']" % (i,)).text
                page_link = chrome.find_element_by_xpath(
                    "//li[@class='item_block item_block_y'][%i]/div[@class='item_text']/p[@class='item_name']/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("&id=", "")
            except:
                close += 1

                break
            try:
                pic_link = chrome.find_element_by_xpath(
                    "//li[@class='item_block item_block_y'][%i]/div[@class='item_img']/a[@class='mymy_item_link']/img[@src]" % (i,)).get_attribute("src")
            except:
                i += 1
                if(i == 17):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[@class='item_block item_block_y'][%i]/div[@class='item_text']/p[@class='item_amount']/span[2]" % (i,)).text
                sale_price = sale_price.strip('NT$ ')
                ori_price = chrome.find_element_by_xpath(
                    "//li[@class='item_block item_block_y'][%i]/div[@class='item_text']/p[@class='item_amount']/span[1]" % (i,)).text
                ori_price = ori_price.strip('NT$ ')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[@class='item_block item_block_y'][%i]/div[@class='item_text']/p[@class='item_amount']/span[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$ ')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 17):
                        p += 1
                    continue
            i += 1
            if(i == 17):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Azoom():
    shop_id = 20
    name = 'azoom'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if(close == 1):
            chrome.quit()
            break
        url = "https://www.aroom1988.com/categories/view-all?page=" + \
            str(p) + "&sort_by=&order_by=&limit=24"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break

        time.sleep(1)

        i = 1
        while(i < 24):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='product-item'][%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='product-item'][%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.strip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//div[@class='product-item'][%i]/product-item/a/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip('")')
            except:
                i += 1
                if(i == 24):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='product-item'][%i]/product-item/a/div[2]/div/div/div" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = ""
            except:
                i += 1
                if(i == 24):
                    p += 1
                continue

            i += 1
            if(i == 24):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Roxy():
    shop_id = 21
    name = 'roxy'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.roxytaiwan.com.tw/new-collection?p=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 65):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='product-container product-thumb'][%i]/div[@class='product-thumb-info']/p[@class='product-title']/a" % (i,)).text
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='product-container product-thumb'][%i]/div[@class='product-thumb-info']/p[@class='product-title']/a[@href]" % (i,)).get_attribute('href')
                page_id = stripID(page_link, "default=")
            except:
                close += 1
                break
            try:
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='product-container product-thumb'][%i]/div[@class='product-img']/a[@class='img-link']/picture[@class='main-picture']/img[@data-src]" % (i,)).get_attribute("data-src")

            except:
                i += 1
                if(i == 65):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='product-container product-thumb'][%i]//span[@class='special-price']//span[@class='price-dollars']" % (i,)).text
                sale_price = sale_price.replace('TWD', "")
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='product-container product-thumb'][%i]//span[@class='old-price']//span[@class='price-dollars']" % (i,)).text
                ori_price = ori_price.replace('TWD', "")

            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='product-container product-thumb'][%i]//span[@class='price-dollars']" % (i,)).text
                    sale_price = sale_price.replace('TWD', "")
                    ori_price = ""
                except:
                    i += 1
                    if(i == 65):
                        p += 1
                    continue

            i += 1
            if(i == 65):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Cici():
    shop_id = 23
    name = 'cici'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.cici2.tw/products?page=" + str(p)

        try:
            chrome.get(url)
        except:
            break

        i = 1
        while(i < 49):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div[1]/div" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 49):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div/div/div[2]/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 49):
                        p += 1
                    continue

            i += 1
            if(i == 49):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Amesoeur():
    shop_id = 25
    name = 'amesour'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.amesoeur.co/categories/%E5%85%A8%E9%83%A8%E5%95%86%E5%93%81?page=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//div/a[%i]/div[@class='Product-info']/div[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-12 ProductList-list']/a[%i]" % (i,)).get_attribute('href')
                page_id = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-12 ProductList-list']/a[%i]" % (i,)).get_attribute('product-id')

                find_href = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-12 ProductList-list']/a[%i]/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div/a[%i]/div[2]/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = chrome.find_element_by_xpath(
                    "//div/a[%i]/div[2]/div[3]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div/a[%i]/div[2]/div[2]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Singular():
    shop_id = 27
    name = 'singular'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        i = 1
        offset = (p-1) * 50
        url = "https://www.singular-official.com/products?limit=50&offset=" + \
            str(offset) + "&price=0%2C10000&sort=createdAt-desc"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)

        while(i < 51):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]/div[2]" % (i,)).text
            except:
                close += 1
                # print(i, "title")
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]//a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/product/")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]//img" % (i,)).get_attribute('src')
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]/div[3]/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$ ')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]/div[3]/div[1]/span/s" % (i,)).text
                ori_price = ori_price.strip('NT$ ')
                ori_price = ori_price.split()
                ori_price = ori_price[0]
            except:
                i += 1
                if(i == 51):
                    p += 1
                continue

            i += 1
            if(i == 51):
                p += 1
            chrome.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
            time.sleep(1)

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Folie():
    shop_id = 28
    name = 'folie'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.folief.com/products?page=" + \
            str(p) + "&sort_by=&order_by=&limit=24"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div[2]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Gmorning():
    shop_id = 30
    name = 'gmorning'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.gmorning.co/products?page=" + \
            str(p) + "&sort_by=&order_by=&limit=24"

        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div[2]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue
            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def July():
    shop_id = 31
    name = 'july'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.july2017.co/products?page=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div[1]/div" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div/div/div[2]/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Per():
    shop_id = 32
    name = 'per'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.perdot.com.tw/categories/all?page=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div[1]/div" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div/div/div[2]/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Cereal():
    shop_id = 33
    name = 'cereal'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 19
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    switch = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.cerealoutfit.com/product-tag/clothing/page/" + str(p) + "/"
        url2 = "https://www.cerealoutfit.com/product-category/accessories/page/" + str(p) + "/"
        if(switch == 0):
            try:
                chrome.get(url)
                print(url)
            except:
                break
        else:
            try:
                chrome.get(url2)
                print(url2)
            except:
                break
        time.sleep(1)
        try:
            chrome.find_element_by_xpath(
                "//button[@class='mfp-close']").click()
        except:
            pass
        
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@data-loop='%i']/h3/a" % (i,)).text
            except:
                if(switch==1):
                    close += 1
                else:
                    p = 1
                    switch += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@data-loop='%i']/div[1]/a[@href]" % (i,)).get_attribute('href')

                page_id = chrome.find_element_by_xpath(
                    "//div[@data-loop='%i']" % (i,)).get_attribute('126-id')

                pic_link = chrome.find_element_by_xpath(
                    "//div[@data-loop='%i']/div[1]/a/img" % (i,)).get_attribute('src')

            except:
                i += 1
                if(i == 25):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@data-loop='%i']//ins//bdi" % (i,)).text
                sale_price = sale_price.rstrip(' NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@data-loop='%i']//del//bdi" % (i,)).text
                ori_price = ori_price.rstrip(' NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@data-loop='%i']/div[2]//span[@class='woocommerce-Price-amount amount']" % (i,)).text
                    sale_price = sale_price.rstrip(' NT$')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue
            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Jcjc():
    shop_id = 35
    name = 'jcjc'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.jcjc-dailywear.com/collections/in-stock?limit=24&page=" + \
            str(p) + "&sort=featured"
        if(p > 4):
            break
        try:
            chrome.get(url)
            print(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='grid-uniform grid-link__container']/div[%i]/div/a/p[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='grid-uniform grid-link__container']/div[%i]/div/a[1][@href]" % (i,)).get_attribute('href')
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='grid-uniform grid-link__container']/div[%i]/div/span/a/img" % (i,)).get_attribute('src')
                page_id = pic_link[pic_link.find("i/")+2:pic_link.find(".j")]

            except:
                i += 1
                if(i == 25):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='grid-uniform grid-link__container']/div[%i]/div/a/p[2]/span" % (i,)).text
                sale_price = sale_price.strip('NT$ ')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='grid-uniform grid-link__container']/div[%i]/div/a/p[2]/s/span" % (i,)).text
                ori_price = ori_price.strip('NT$ ')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='grid-uniform grid-link__container']/div[%i]/div/a/p[2]/span" % (i,)).text
                    sale_price = sale_price.strip('NT$ ')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Ccshop():
    shop_id = 36
    name = 'ccshop'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.ccjshop.com/products?page=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[2]/ul/li[%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[1]/div" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = ""
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[%i]/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Iris():
    shop_id = 37
    name = 'iris'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.irisgarden.com.tw/products?page=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[@class='boxify-item product-item                           ng-isolate-scope'][%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[1]/div" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = ""
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[%i]/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Nook():
    shop_id = 39
    name = 'nook'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.nooknook.me/products?page=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div[1]/div" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div/div/div[2]/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Greenpea():
    shop_id = 40
    name = 'greenpea'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.greenpea-tw.com/products?page=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[2]/ul/li[%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[1]/div" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[3]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[2]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[%i]/a/div[2]/div/div[2]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Queen():
    shop_id = 42
    name = 'queen'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.queenshop.com.tw/zh-TW/QueenShop/ProductList?item1=01&item2=all&Page=" + \
            str(p) + "&View=4"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break

        i = 1
        while(i < 17):
            try:
                title = chrome.find_element_by_xpath(
                    "//ul[@class='items-list list-array-4']/li[%i]/a/p" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//ul[@class='items-list list-array-4']/li[%i]/a[@href]" % (i,)).get_attribute('href')
                page_id = stripID(page_link, "SaleID=")
                pic_link = chrome.find_element_by_xpath(
                    "//ul[@class='items-list list-array-4']/li[%i]/a/img[1]" % (i,)).get_attribute('data-src')
            except:
                i += 1
                if(i == 17):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//ul[@class='items-list list-array-4']/li[%i]/p[2]/span[2]" % (i,)).text
                sale_price = sale_price.strip('NT. ')
                ori_price = chrome.find_element_by_xpath(
                    "//ul[@class='items-list list-array-4']/li[%i]/p[2]/span[1]" % (i,)).text
                ori_price = ori_price.strip('NT. ')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//ul[@class='items-list list-array-4']/li[%i]/p[2]/span[1]" % (i,)).text
                    sale_price = sale_price.strip('NT. ')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 17):
                        p += 1
                    continue

            i += 1
            if(i == 17):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Cozyfee():
    shop_id = 48
    name = 'cozyfee'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.cozyfee.com/product.php?page=" + \
            str(p) + "&cid=55#prod_list"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 41):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/div[2]/a" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[%i]/div[2]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.lstrip("action=detail&pid=")
                pic_link = chrome.find_element_by_xpath(
                    "//li[%i]/div[1]/a/img[1]" % (i,)).get_attribute('data-original')
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/div[3]/span" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = ""
            except:
                i += 1
                if(i == 41):
                    p += 1
                continue

            i += 1
            if(i == 41):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)

    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Reishop():
    shop_id = 49
    name = 'reishop'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.reishop.com.tw/pdlist2.asp?item1=all&item2=&item3=&keyword=&ob=A&pagex=&pageno=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 31):
            try:
                title = chrome.find_element_by_xpath(
                    "//figcaption[%i]/a/span[2]/span[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//figcaption[%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.lstrip("yano=YA")
                page_id = page_id.replace("&color=", "")
                pic_link = chrome.find_element_by_xpath(
                    "//figcaption[%i]/a/span/img[1]" % (i,)).get_attribute('src')
                sale_price = chrome.find_element_by_xpath(
                    "//figcaption[%i]/a/span[2]/span[2]/span" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = ""
            except:
                i += 1
                if(i == 31):
                    p += 1
                continue

            i += 1
            if(i == 31):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)

    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Yourz():
    shop_id = 50
    name = 'yourz'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.yourz.com.tw/product/category/34/1/" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 13):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='pro_list'][%i]/div/table/tbody/tr/td/div/a" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='pro_list'][%i]/div/table/tbody/tr/td/div/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/product/detail/")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='pro_list'][%i]/div/a/img" % (i,)).get_attribute('src')
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='pro_list'][%i]/div[4]/p/font" % (i,)).text
                sale_price = sale_price.replace('VIP價：NT$ ', '')
                sale_price = sale_price.rstrip('元')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='pro_list'][%i]/div[4]/p/br" % (i,)).text
                ori_price = ori_price.replace('NT$ ', '')
                ori_price = ori_price.rstrip('元')
            except:
                i += 1
                if(i == 13):
                    p += 1
                continue

            i += 1
            if(i == 13):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Seoulmate():
    shop_id = 54
    name = 'seoulmate'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.seoulmate.com.tw/catalog.php?m=115&s=249&t=0&sort=&page=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 33):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/p[1]/a" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//ul/li[%i]/p[1]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("m=115&s=249&t=0&id=", "")
                pic_link = chrome.find_element_by_xpath(
                    "//ul/li[%i]/a/img[1]" % (i,)).get_attribute('src')
                if(pic_link == ""):
                    i += 1
                    if(i == 33):
                        p += 1
                    continue
            except:
                i += 1
                if(i == 33):
                    p += 1
                continue

            try:
                ori_price = chrome.find_element_by_xpath(
                    "//ul/li[%i]/p[3]/del" % (i,)).text
                ori_price = ori_price.strip('NT.')
                sale_price = chrome.find_element_by_xpath(
                    "//ul/li[%i]/p[3]" % (i,)).text
                sale_price = sale_price.strip('NT.')
                sale_price = sale_price.strip('NT.')
                locate = sale_price.find("NT.")
                sale_price = sale_price[locate+3:len(sale_price)]
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//ul/li[%i]/p[3]" % (i,)).text
                    sale_price = sale_price.strip('NT.')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 33):
                        p += 1
                    continue

            i += 1
            if(i == 33):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Sweesa():
    shop_id = 55
    name = 'sweesa'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.sweesa.com/Shop/itemList.aspx?&m=20&o=5&sa=1&smfp=" + \
            str(p)

        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 45):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[2]/a" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[2]/a" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("mNo1=", "")
                page_id = page_id.replace("&m=20", "")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]//a/img[@src]" % (i,)).get_attribute("src")
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[4]/span" % (i,)).text
                sale_price = sale_price.strip('TWD.')
                ori_price = ""
            except:
                i += 1
                if(i == 45):
                    p += 1
                continue

            i += 1
            if(i == 45):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Pazzo():
    shop_id = 56
    name = 'pazzo'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.pazzo.com.tw/recent?P=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 41):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/div[2]/p/a" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[%i]/div[2]/p/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.lstrip("c=")
                pic_link = chrome.find_element_by_xpath(
                    "//li[@class='item'][%i]/div[@class='item__images']/a/picture/img[@class='img-fluid']" % (i,)).get_attribute('src')

            except:
                i += 1
                if(i == 41):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/div[2]/p[2]/span[2]" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = chrome.find_element_by_xpath(
                    "//li[%i]/div[2]/p[2]/span[1]" % (i,)).text
                ori_price = ori_price.strip('NT.')
            except:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/div[2]/p[2]/span" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = ""

            i += 1
            if(i == 41):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Meierq():
    shop_id = 57
    name = 'meierq'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    page = 0
    prefix_urls = [
        "https://www.meierq.com/zh-tw/category/bottomclothing?P=",
        "https://www.meierq.com/zh-tw/category/jewelry?P=",
        "https://www.meierq.com/zh-tw/category/outerclothing?P=",
        "https://www.meierq.com/zh-tw/category/accessories?P=",
    ]
    for prefix in prefix_urls:
        page += 1
        for i in range(1, page_Max):
            url = f"{prefix}{i}"
            try:
                print(url)
                chrome.get(url)
                chrome.find_element_by_xpath("//div[@class='items__image']")
            except:
                print("find_element_by_xpath_break", page)
                if(page == 4):
                    chrome.quit()
                    print("break")
                    break
                break
            i = 1
            while(i < 41):
                try:
                    title = chrome.find_element_by_xpath(
                        "//li[%i]/div/p/a" % (i,)).text
                except:
                    break
                try:
                    page_link = chrome.find_element_by_xpath(
                        "//li[%i]/div/p/a[@href]" % (i,)).get_attribute('href')
                    page_id = stripID(page_link, "n/")
                    page_id = page_id[:page_id.find("?c")]
                    pic_link = chrome.find_element_by_xpath(
                        "//li[%i]/div/img" % (i,)).get_attribute('src')
                    try:
                        sale_price = chrome.find_element_by_xpath(
                            "//li[%i]/div/p/span[2]" % (i,)).text
                        sale_price = sale_price.strip('NT.')
                        ori_price = chrome.find_element_by_xpath(
                            "//li[%i]/div/p/span" % (i,)).text
                        ori_price = ori_price.strip('NT.')
                    except:
                        sale_price = chrome.find_element_by_xpath(
                            "//li[%i]/div/p/span" % (i,)).text
                        sale_price = sale_price.strip('NT.')
                        ori_price = ""
                except:
                    i += 1
                    if(i == 41):
                        p += 1
                    continue

                i += 1
                if(i == 41):
                    p += 1

                df = pd.DataFrame(
                    {
                        "title": [title],
                        "page_link": [page_link],
                        "page_id": [page_id],
                        "pic_link": [pic_link],
                        "ori_price": [ori_price],
                        "sale_price": [sale_price]
                    })

                dfAll = pd.concat([dfAll, df])
                dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Harper():
    shop_id = 58
    name = 'harper'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    while True:
        url = "https://www.harper.com.tw/Shop/itemList.aspx?&m=13&smfp=" + \
            str(p)
        if(p > 20):
            chrome.quit()
            break
        try:
            chrome.get(url)
        except:
            chrome.quit()
            break
        i = 1
        while(i < 80):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[2]/a" % (i,)).text
            except:
                p += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[2]/a" % (i,)).get_attribute('href')
                page_id = stripID(page_link, "cno=")
                page_id = page_id.replace("&m=13", "")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]//a/img[@src]" % (i,)).get_attribute("src")
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[4]/span" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = ""
            except:
                i += 1
                if(i == 79):
                    p += 1
                continue

            i += 1
            if(i == 79):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Lurehsu():
    shop_id = 59
    name = 'lurehsu'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.lurehsu.com/zh-TW/lure/productList?item1=00&item2=16&page=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        i = 1
        while(i < 28):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='grid-item'][%i]/a/div[2]/p" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='grid-item'][%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.lstrip("SaleID=")
                page_id = page_id[:page_id.find("&Color")]
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='grid-item'][%i]/a/div/img" % (i,)).get_attribute('src')
            except:
                i += 1
                if(i == 28):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='grid-item'][%i]/a/div[2]/div/p/span[2]" % (i,)).text
                sale_price = sale_price.strip('NTD.')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='grid-item'][%i]/a/div[2]/div/p/span[1]" % (i,)).text
                ori_price = ori_price.strip('NTD.')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='grid-item'][%i]/a/div[2]/div/p" % (i,)).text
                    sale_price = sale_price.strip('NTD.')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 28):
                        p += 1
                    continue

            i += 1
            if(i == 28):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Pufii():
    shop_id = 61
    name = 'pufii'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.pufii.com.tw/Shop/itemList.aspx?&m=6&smfp=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 37):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[3]" % (i,)).text

            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[1]/a" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("mNo1=P", "")
                page_id = page_id.replace("&m=6", "")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]//a/img[@src]" % (i,)).get_attribute("src")
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='itemListDiv'][%i]/div[@class='pricediv']/span[2]" % (i,)).text
                    sale_price = sale_price.strip('活動價NT')

                    ori_price = chrome.find_element_by_xpath(
                        "//div[@class='itemListDiv'][%i]/div[@class='pricediv']/span[1]" % (i,)).text
                    ori_price = ori_price.strip('NT')
                except:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='itemListDiv'][%i]/div[@class='pricediv']/span[1]" % (i,)).text
                    sale_price = sale_price.strip('NT')
                    ori_price = ""

            except:
                i += 1
                if(i == 37):
                    p += 1
                continue

            i += 1
            if(i == 37):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Mouggan():
    shop_id = 62
    name = 'mouggan'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.mouggan.com/zh-tw/category/ALL-ITEM?P=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        try:
            chrome.find_element_by_xpath(
                "//a[@class='close p-0']/i[@class='icon-popup-close']").click()

        except:
            pass
        i = 1
        while(i < 19):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[2]/div[%i]/div[2]/a" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[2]/div[%i]/div[2]/a[@href]" % (i,)).get_attribute('href')
                page_id = stripID(page_link, "c=")
                pic_link = chrome.find_element_by_xpath(
                    "//div[2]/div[%i]/div[1]/div/a/img" % (i,)).get_attribute('src')
            except:
                i += 1
                if(i == 19):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[2]/div[%i]/div[2]/div[1]/span[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//div[2]/div[%i]/div[2]/div[1]/span[1]" % (i,)).text
                ori_price = ori_price.strip('NT$')

            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[2]/div[%i]/div[2]/div[1]/span[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 19):
                        p += 1
                    continue

            i += 1
            if(i == 19):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Mercci():
    shop_id = 64
    name = 'mercci'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.mercci22.com/zh-tw/tag/HOTTEST?P=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        # chrome.find_element_by_xpath("//a[@class='close p-0']/i[@class='icon-popup-close']").click()
        i = 1
        while(i < 41):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/div[@class='items__info']/div[@class='pdname']/a" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[%i]/div[@class='items__info']/div[@class='pdname']/a[@href]" % (i,)).get_attribute('href')
                page_id = stripID(page_link, "c=")
                pic_link = chrome.find_element_by_xpath(
                    "//li[%i]/a[@class='items__image js-loaded']/img" % (i,)).get_attribute('src')
            except:
                i += 1
                if(i == 41):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/div[@class='items__info']/div[@class='price']" % (i,)).text
                sale_price = sale_price.strip('NT.')
                k = sale_price.find("NT.")
                sale_price = sale_price[k+3:len(sale_price)]
                ori_price = chrome.find_element_by_xpath(
                    "//li[%i]/div[@class='items__info']/div[@class='price']/span" % (i,)).text
                ori_price = ori_price.strip('NT.')

            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[%i]/div[@class='items__info']/p[@class='price']/span" % (i,)).text
                    sale_price = sale_price.strip('NT.')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 41):
                        p += 1
                    continue

            i += 1
            if(i == 41):
                p += 1

            if(sale_price == ""):
                continue

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Sivir():
    shop_id = 65
    name = 'sivir'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.sivir.com.tw/collections/new-all-%E6%89%80%E6%9C%89?page=" + \
            str(p)

        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='product col-lg-3 col-sm-4 col-6'][%i]/div[2]/a" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='product col-lg-3 col-sm-4 col-6'][%i]/div[2]/a[@href]" % (i,)).get_attribute('href')
                page_id = chrome.find_element_by_xpath(
                    "//div[@class='product col-lg-3 col-sm-4 col-6'][%i]/div[2]/a[@data-id]" % (i,)).get_attribute('data-id')
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='product col-lg-3 col-sm-4 col-6'][%i]/div[1]/a/img" % (i,)).get_attribute('data-src')
                pic_link = f"https:{pic_link}"
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='product col-lg-3 col-sm-4 col-6'][%i]/div[4]/span" % (i,)).text
                sale_price = sale_price.replace('NT$', '')
                ori_price = ""
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Nana():
    shop_id = 66
    name = 'nana'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.2nana.tw/product.php?page=" + \
            str(p) + "&cid=1#prod_list"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 75):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-6 col-sm-4 col-md-3'][%i]/div/div[2]/div[1]/a" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-6 col-sm-4 col-md-3'][%i]/div/div[1]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.lstrip("action=detail&pid=")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-6 col-sm-4 col-md-3'][%i]/div/div[1]/a/img" % (i,)).get_attribute('data-original')
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-6 col-sm-4 col-md-3'][%i]/div/div[2]/div[2]/span" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-6 col-sm-4 col-md-3'][%i]/div/div[2]/div[2]/del" % (i,)).text
                ori_price = ori_price.strip('NT.')
            except:
                i += 1
                if(i == 75):
                    p += 1
                continue

            i += 1
            if(i == 75):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Aachic():
    shop_id = 70
    name = 'aachic'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.aachic.com/categories/all-%E6%89%80%E6%9C%89%E5%95%86%E5%93%81?page=" + \
            str(p) + "&sort_by=&order_by=&limit=24"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//a[%i]/div[2]/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-12 ProductList-list']/a[%i][@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//a[%i]/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
                sale_price = chrome.find_element_by_xpath(
                    "//a[%i]/div[2]/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = chrome.find_element_by_xpath(
                    "//a[%i]/div[2]/div[3]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Lovso():
    shop_id = 71
    name = 'lovso'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.lovso.com.tw/Shop/itemList.aspx?m=8&o=0&sa=0&smfp=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 37):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[2]" % (i,)).text

            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[1]/center/a" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("mNo1=", "")
                page_id = page_id.replace("&m=8", "")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]//a/img[@src]" % (i,)).get_attribute("src")
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[4]" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[3]" % (i,)).text
                ori_price = ori_price.strip('NT.')
            except:
                i += 1
                if(i == 37):
                    p += 1
                continue

            i += 1
            if(i == 37):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Bowwow():
    shop_id = 72
    name = 'bowwow'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.bowwowkorea.com/products?page=" + \
            str(p) + "&sort_by=&order_by=&limit=48"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 49):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
                sale_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = ""
            except:
                i += 1
                if(i == 49):
                    p += 1
                continue

            i += 1
            if(i == 49):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Suitangtang():
    shop_id = 74
    name = 'suitangtang'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)
    i = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.suitangtang.com/Catalog/WOMAN"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        chrome.find_element_by_tag_name('body').send_keys(Keys.END)
        time.sleep(1)

        while(True):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='product-list'][%i]/div[@class='name']" % (i,)).text
                k = title.find("NT$")
                title = title[0:k-1]
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='product-list'][%i]/a[@href]" % (i,)).get_attribute('href')
                page_id = stripID(page_link, "/Product/")
                page_id = page_id[:page_id.find("?c=")]
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='product-list'][%i]/a/img" % (i,)).get_attribute('data-original')
            except:
                i += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='product-list'][%i]/div[2]/span" % (i,)).text
                sale_price = sale_price.strip('NT$')
                k = sale_price.find("NT$")
                sale_price = sale_price[k+3:len(sale_price)]
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='product-list'][%i]/div[2]/span/span" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='product-list'][%i]/div[2]/span" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    ori_price = ""
                except:
                    i += 1
                    continue

            i += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Chochobee():
    shop_id = 78
    name = 'chochobee'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.chochobee.com/catalog.php?m=40&s=0&t=0&sort=&page=" + \
            str(p)

        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//section/ul/li[%i]/span[2]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//section/ul/li[%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("m=40&s=0&t=0&id=", "")
                pic_link = chrome.find_element_by_xpath(
                    "//section/ul/li[%i]/a/div/img" % (i,)).get_attribute('src')
                sale_price = chrome.find_element_by_xpath(
                    "//section/ul/li[%i]/span[3]" % (i,)).text
                sale_price = sale_price.strip('NT.$')
                ori_price = ""
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Asobi():
    shop_id = 80
    name = 'asobi'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.asobi.com.tw/Shop/itemList.aspx?undefined&smfp=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 34):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[2]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[1]/a" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("mNo1=", "")
                page_id = page_id.replace("&&m=1&o=5&sa=1", "")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]//a/img[@src]" % (i,)).get_attribute("src")
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[3]/div/span" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = ""
            except:
                i += 1
                if(i == 34):
                    p += 1
                continue

            i += 1
            if(i == 34):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Kiyumi():
    shop_id = 81
    name = 'kiyumi'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)
    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    flag = 0
    while True:
        if (flag == 1):
            chrome.quit()
            break
        url = "https://www.kiyumishop.com/catalog.php?m=73&s=0&t=0&sort=&page=" + \
            str(p)
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//section/ul/li[%i]/span[2]" % (i,)).text
            except:
                flag += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//section/ul/li[%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("m=73&s=0&t=0&id=", "")
                pic_link = chrome.find_element_by_xpath(
                    "//section/ul/li[%i]/a/div/img" % (i,)).get_attribute('src')
                sale_price = chrome.find_element_by_xpath(
                    "//section/ul/li[%i]/span[3]" % (i,)).text
                sale_price = sale_price.strip('NT.$')
                ori_price = ""
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Genquo():
    shop_id = 82
    name = 'genquo'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)
    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    flag = 0
    while True:
        if (flag == 1):
            chrome.quit()
            break
        url = "https://www.genquo.com/zh-tw/category/women?P=" + str(p)
        print("處理頁面:", url)
        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        i = 1
        while(i < 37):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[@class='item'][%i]/div/p/a" % (i,)).text
            except:
                flag += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[@class='item'][%i]/div/p/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path + '?' + make_id.query
                page_id = page_id.lstrip("/zh-tw/market/n/")
                page_id = page_id[:page_id.find("?c=")]
                pic_link = chrome.find_element_by_xpath(
                    "//li[@class='item'][%i]/div/a/img" % (i,)).get_attribute('src')
            except:
                i += 1
                if(i == 37):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[@class='item'][%i]/div/p/span[1]" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = ""
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[@class='item'][%i]/div/p/span[2]" % (i,)).text
                    sale_price = sale_price.strip('NT.')
                    ori_price = chrome.find_element_by_xpath(
                        "//li[@class='item'][%i]/div/p/span[1]" % (i,)).text
                    ori_price = ori_price.strip('NT.')
                except:
                    i += 1
                    if(i == 37):
                        p += 1
                    continue

            i += 1
            if(i == 37):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Oolala():
    shop_id = 86
    name = 'oolala'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    flag = 0
    while True:
        if (flag == 1):
            chrome.quit()
            break
        url = "https://www.styleoolala.com/products?page=" + \
            str(p) + "&sort_by=&order_by=&limit=48"
        print("處理頁面:", url)
        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 49):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                flag += 1
                print(p, i)
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 49):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div[2]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 49):
                        p += 1
                    continue
            i += 1
            if(i == 49):
                p += 1

            if(sale_price == ""):
                continue

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Pattis():
    shop_id = 87
    name = 'pattis'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.i-pattis.com/catalog.php?m=1&s=21&t=0&sort=&page=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//section[@class='cataList']/ul/li[%i]/span[2]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//section[@class='cataList']/ul/li[%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("m=1&s=21&t=0&id=", "")
                pic_link = chrome.find_element_by_xpath(
                    "//li[%i]/a/img" % (i,)).get_attribute('src')
                sale_price = chrome.find_element_by_xpath(
                    "//ul/li[%i]/span[3]" % (i,)).text
                sale_price = sale_price.strip('NT.$')
                ori_price = chrome.find_element_by_xpath(
                    "//ul/li[%i]/del" % (i,)).text
                ori_price = ori_price.strip('NT.$')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Scheminggg():
    shop_id = 90
    name = 'scheminggg'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.scheminggg.com/productlist?page=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 37):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='columns']/div[%i]/a/p" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='columns']/div[%i]/a[1][@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.lstrip("/products?saleid=")
                page_id = page_id.rstrip("&colorid=")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='columns']/div[%i]/a/img" % (i,)).get_attribute('src')
                if (pic_link == ""):
                    i += 1
                    if(i == 37):
                        p += 1
                    continue
            except:
                i += 1
                if(i == 37):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='columns']/div[%i]/p[2]" % (i,)).text
                sale_price = sale_price.strip('NT. ')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='columns']/div[%i]/p[1]" % (i,)).text
                ori_price = ori_price.strip('NT. ')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='columns']/div[%i]/p[1]" % (i,)).text
                    sale_price = sale_price.strip('NT. ')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 37):
                        p += 1
                    continue
            i += 1
            if(i == 37):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Laconic():
    shop_id = 94
    name = 'laconic'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)
    i = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://laconic.waca.ec/product/all"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)

        while(True):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[@class=' item_block js_is_photo_style   '][%i]//h4" % (i,)).text
            except:
                close += 1
                # print(i, "title")
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[@class=' item_block js_is_photo_style   '][%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/product/detail/")
                find_href = chrome.find_element_by_xpath(
                    "//li[@class=' item_block js_is_photo_style   '][%i]//a/span" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.replace('url("', '')
                pic_link = pic_link.replace('")', '')
                sale_price = chrome.find_element_by_xpath(
                    "//li[@class=' item_block js_is_photo_style   '][%i]//li/span" % (i,)).text
                sale_price = sale_price.strip('$')
                ori_price = ""
            except:
                i += 1
                if(i % 10 == 1):
                    chrome.find_element_by_tag_name('body').send_keys(Keys.END)
                    time.sleep(1)
                    continue

            i += 1
            if(i % 10 == 1):
                chrome.find_element_by_tag_name('body').send_keys(Keys.END)
                time.sleep(1)

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Pixelcake():
    shop_id = 96
    name = 'pixelcake'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.pixelcake.com.tw/zh-tw/category/ALL?P=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        try:
            chrome.find_element_by_xpath(
                "//button[@class='aiq-2-w6Qa']").click()
            chrome.find_element_by_xpath(
                "//i[@class='icon-popup-close']").click()
        except:
            pass
        time.sleep(1)
        i = 1
        while(i < 17):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@id='category-item-wrap']//div[%i]/div[2]/a" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@id='category-item-wrap']/div[1]/div[%i]/div[1]/a[@href]" % (i,)).get_attribute('href')
                page_id = chrome.find_element_by_xpath(
                    "//div[@id='category-item-wrap']/div[1]/div[%i]/div[2]//div[@class='like-counter ']" % (i,)).get_attribute('data-custommarketid')
                pic_link = chrome.find_element_by_xpath(
                    "//div[%i]/div[1]/a/picture/img" % (i,)).get_attribute('src')
            except:
                i += 1
                if(i == 17):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@id='category-item-wrap']//div[%i]/div[2]/div[1]/span[1]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//div[%i]/div[5]/div[2]/div[1]/span[2]" % (i,)).text
                ori_price = ori_price.strip('NT$')

            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@id='category-item-wrap']//div[%i]/div[2]/div[1]/span[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 17):
                        p += 1
                    continue

            i += 1
            if(i == 17):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Miyuki():
    shop_id = 97
    name = 'miyuki'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.miyukiselect.com/zh-tw/category/ALL-ITEMS?P=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        try:
            chrome.find_element_by_xpath(
                "//button[@class='aiq-2-w6Qa']").click()
            chrome.find_element_by_xpath(
                "//i[@class='icon-popup-close']").click()
        except:
            pass
        time.sleep(1)
        i = 1
        while(i < 17):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@id='category-item-wrap']//div[%i]/div[2]/a" % (i,)).text
                if (title == ""):
                    i += 1
                    if(i == 17):
                        p += 1
                    continue
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@id='category-item-wrap']/div[1]/div[%i]/div[1]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.lstrip("c=")
                pic_link = chrome.find_element_by_xpath(
                    "//div[%i]/div[1]/a/picture/img" % (i,)).get_attribute('src')
            except:
                i += 1
                if(i == 17):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@id='category-item-wrap']//div[%i]/div[2]/div[1]/span[1]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@id='category-item-wrap']//div[%i]/div[2]/div[1]/span[2]" % (i,)).text
                ori_price = ori_price.strip('NT$')

            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@id='category-item-wrap']//div[%i]/div[2]/div[1]/span[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 17):
                        p += 1
                    continue

            i += 1
            if(i == 17):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Percha():
    shop_id = 99
    name = 'percha'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.percha.tw/Shop/itemList.aspx?m=7&p=14&smfp=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break

        i = 1
        while(i < 33):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[2]/a" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[1]/a" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("mNo1=", "")
                page_id = page_id.replace("&m=7&p=14", "")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]//a/img[@src]" % (i,)).get_attribute("src")
            except:
                i += 1
                if(i == 33):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[3]/span[2]" % (i,)).text
                sale_price = sale_price.strip('$')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[3]/span[1]" % (i,)).text
                ori_price = ori_price.strip('$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='itemListDiv'][%i]/div[3]/span[1]" % (i,)).text
                    sale_price = sale_price.strip('$')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 33):
                        p += 1
                    continue

            i += 1
            if(i == 33):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Mojp():
    shop_id = 102
    name = 'mojp'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    while True:

        url = "https://www.mojp.com.tw/product.php?page=" + \
            str(p) + "&cid=12#prod_list"
        print(url)
        if(p < 11):
            try:
                chrome.get(url)
            except:
                chrome.quit()
                break
        else:
            break

        time.sleep(1)
        i = 1
        while True:
            try:
                title = chrome.find_element_by_xpath(
                    "//div[1]/section[3]/div/div[1]/div[%i]/div/div[2]/div[1]/a" % (i,)).text
            except:
                p += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[1]/section[3]/div/div[1]/div[%i]/div/div[1]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.lstrip("action=detail&pid=")
                pic_link = chrome.find_element_by_xpath(
                    "//div[1]/section[3]/div/div[1]/div[%i]/div/div[1]/a/img[@src]" % (i,)).get_attribute('data-original')
            except:
                i += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[1]/section[3]/div/div[1]/div[%i]/div/div[2]/div[2]/span" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = chrome.find_element_by_xpath(
                    "//div[1]/section[3]/div/div[1]/div[%i]/div/div[2]/div[2]/del" % (i,)).text
                ori_price = ori_price.strip('NT.')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[1]/section[3]/div/div[1]/div[%i]/div/div[2]/div[@class='prod-price']" % (i,)).text
                    sale_price = sale_price.strip('NT.')
                    ori_price = ""
                except:
                    i += 1
                    continue

            i += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Pleats():
    shop_id = 104
    name = '92pleats'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.92pleats.com/products?page=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[2]/ul/li[%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                sale_price = sale_price.split()
                sale_price = sale_price[0]
                ori_price = ""
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Zebra():
    shop_id = 105
    name = 'zebra'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.zebracrossing.com.tw/Shop/itemList.aspx?&m=8&smfp=" + \
            str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 13):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[2]/a" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[1]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("mNo1=", "")
                page_id = page_id.replace("&m=8", "")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[1]/a/img" % (i,)).get_attribute("src")
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='itemListDiv'][%i]/div[3]/span" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = ""
            except:
                i += 1
                if(i == 13):
                    p += 1
                continue

            i += 1
            if(i == 13):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Mihara():
    shop_id = 107
    name = 'mihara'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.mihara.com.tw/product.php?page=" + \
            str(p) + "&cid=1#prod_list"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 81):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[1]/section[3]/div/div[1]/div[%i]/div/div[2]/div[1]/a" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[1]/section[3]/div/div[1]/div[%i]/div/div[1]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.lstrip("action=detail&pid=")
                pic_link = chrome.find_element_by_xpath(
                    "//div[1]/section[3]/div/div[1]/div[%i]/div/div[1]/a/img[@data-original]" % (i,)).get_attribute('data-original')
            except:
                i += 1
                if(i == 81):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[1]/section[3]/div/div[1]/div[%i]/div/div[2]/div[2]/span" % (i,)).text
                sale_price = sale_price.strip('NT.')
                ori_price = chrome.find_element_by_xpath(
                    "//div[1]/section[3]/div/div[1]/div[%i]/div/div[2]/div[2]/del" % (i,)).text
                ori_price = ori_price.strip('NT.')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[1]/section[3]/div/div[1]/div[%i]/div/div[2]/div[2]" % (i,)).text
                    sale_price = sale_price.strip('NT.')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 81):
                        p += 1
                    continue
            i += 1
            if(i == 81):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)

def Oiiv():
    shop_id = 111
    name = 'ooiv'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.oiiv.co/products?page=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[@class='boxify-item product-item ng-isolate-scope'][%i]/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url(').rstrip(')"')

            except:
                i += 1
                if(i == 25):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[3]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//li[%i]/a/div[2]/div/div[2]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[%i]/a/div[2]/div/div[2]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue
            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Stayfoxy():
    shop_id = 113
    name = 'stayfoxy'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.stayfoxyshop.com/products?page=" + \
            str(p) + "&sort_by=&order_by=&limit=24"

        try:
            chrome.get(url)
        except:
            break

        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                page_link = page_link.strip('url("')
                page_id = chrome.find_element_by_xpath(
                    "//div[%i]/product-item" % (i,)).get_attribute('product-id')
                find_href = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                left = bg_url.find('https')
                right = bg_url.find('g")')
                pic_link = bg_url[left:right+1]

            except:
                i += 1
                if(i == 25):
                    p += 1
                continue
            try:
                presale_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                divide = presale_price.split(" ")
                sale_price = divide[0].strip('NT$')

                ori_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div[2]" % (i,)).text
                ori_price = ori_price.strip('NT$')

            except:
                try:
                    presale_price = chrome.find_element_by_xpath(
                        "//div[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                    divide = presale_price.split(" ")
                    sale_price = divide[0].strip('NT$')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    save(shop_id, name, dfAll)
    upload(shop_id, name)



def Righton():
    shop_id = 118
    name = 'righton'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    print("Start:", shop_id, name)
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://e.right-on.com.tw/categories/women?page=" + \
            str(p) + "&sort_by=&order_by=&limit=24"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue

            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//div[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                ori_price = ori_price.strip('NT$')
                ori_price = ori_price.split()
                ori_price = ori_price[0]
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    print("Finish:", shop_id, name)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Daf():
    shop_id = 120
    name = 'daf'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    print("Start:", shop_id, name)

    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.daf-shoes.com/product/list/all/" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='commoditys'][%i]/p[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='commoditys'][%i]/div/a[@href]" % (i,)).get_attribute('href')
                page_id = chrome.find_element_by_xpath(
                    "//div[@class='commoditys'][%i]/p[2]" % (i,)).get_attribute('id')
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='commoditys'][%i]/div/a/img" % (i,)).get_attribute('src')

            except:
                i += 1
                if(i == 25):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='commoditys'][%i]/p[2]/span[2]" % (i,)).text
                sale_price = sale_price.replace('NT$ ', '')
                sale_price = sale_price.replace('特價 ', '')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='commoditys'][%i]/p[2]/span[1]" % (i,)).text
                ori_price = ori_price.replace('NT$ ', '')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//div[@class='commoditys'][%i]/p[2]" % (i,)).text
                    sale_price = sale_price.replace('NT$ ', '')
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue
            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    print("Finish:", shop_id, name)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Sexyinshape():
    shop_id = 122
    name = 'sexyinshape'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    print("Start:", shop_id, name)

    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.sexyinshape.com/products?page=" + \
            str(p) + "&sort_by=&order_by=&limit=24"

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 25):
            try:
                title = chrome.find_element_by_xpath(
                    "//a[%i]/div[2]/div[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='col-xs-12 ProductList-list']/a[%i][@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//a[%i]/div[1]/div[1]" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                i += 1
                if(i == 25):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//a[%i]/div[2]/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//a[%i]/div[2]/div[3]" % (i,)).text
                ori_price = ori_price.strip('NT$')
                ori_price = ori_price.split()
                ori_price = ori_price[0]
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//a[%i]/div[2]/div[2]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    i += 1
                    if(i == 25):
                        p += 1
                    continue

            i += 1
            if(i == 25):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    print("Finish:", shop_id, name)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Bonjour():
    shop_id = 123
    name = 'bonjour'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', chrome_options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    print("Start:", shop_id, name)
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.bonjour.tw/Catalog.aspx?cid=40&p=" + str(p)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
        except:
            break
        time.sleep(1)
        i = 1
        while(i < 101):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/div/div[1]/a" % (i,)).text
            except:
                close += 1

                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[%i]/div/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.query
                page_id = page_id.replace("pid=", '')
                page_id = page_id[:page_id.find("&c=")]
                pic_link = chrome.find_element_by_xpath(
                    "//li[%i]/div/a/img" % (i,)).get_attribute('src')
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/div/div[3]" % (i,)).text
                sale_price = sale_price.replace('NT. $', '')
                ori_price = ""
            except:
                i += 1
                if(i == 101):
                    p += 1
                continue

            i += 1
            if(i == 101):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    print("Finish:", shop_id, name)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def Amissa():
    shop_id = 133
    name = 'amissa'
    options = Options()                  # 啟動無頭模式
    options.add_argument('--headless')   # 規避google bug
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--remote-debugging-port=5566")
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()   # 存放所有資料
    close = 0
    print("Start:", shop_id, name)
    while True:
        if (close == 1):
            chrome.quit()
            break
        url = "https://www.amissa.co/categories/%E6%89%80%E6%9C%89%E5%95%86%E5%93%81?page=" + str(p)

        try:
            chrome.get(url)
            print(url)
        except:
            break
        i = 1
        while(i < 73):
            try:
                title = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div[2]/div/div[1]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/products/")
                find_href = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div[1]/div" % (i,))
                bg_url = find_href.value_of_css_property('background-image')
                pic_link = bg_url.lstrip('url("').rstrip(')"')
            except:
                print(p, i, "1")
                i += 1
                if(i == 73):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div/div/div[2]/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$')
                ori_price = chrome.find_element_by_xpath(
                    "//li[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                ori_price = ori_price.strip('NT$')
            except:
                try:
                    sale_price = chrome.find_element_by_xpath(
                        "//li[%i]/product-item/a/div/div/div[2]/div[1]" % (i,)).text
                    sale_price = sale_price.strip('NT$')
                    sale_price = sale_price.split()
                    sale_price = sale_price[0]
                    ori_price = ""
                except:
                    print(p, i, "2")
                    i += 1
                    if(i == 73):
                        p += 1
                    continue

            i += 1
            if(i == 73):
                p += 1

            df = pd.DataFrame(
                {
                    "title": [title],
                    "page_link": [page_link],
                    "page_id": [page_id],
                    "pic_link": [pic_link],
                    "ori_price": [ori_price],
                    "sale_price": [sale_price]
                })

            dfAll = pd.concat([dfAll, df])
            dfAll = dfAll.reset_index(drop=True)
    print("Finish:", shop_id, name)
    save(shop_id, name, dfAll)
    upload(shop_id, name)


def save(shop_id, name, dfAll):
    filename = '_'.join(
        [str(shop_id), name, datetime.today().strftime("%Y%m%d")])
    dfAll.to_excel(fold_path + '/' + filename + ".xlsx")


def upload(shop_id, name):
    filename = '_'.join(
        [str(shop_id), name, datetime.today().strftime("%Y%m%d")])
    try:
        headers = {
            'authorization': ENV_VARIABLE['SERVER_TOKEN'],
            'cache-control': "no-cache",
        }
        url = f"{ENV_VARIABLE['SERVER_URL']}/api/import/product"
        files = {
            'file': (filename + '.xlsx', open(fold_path + filename + '.xlsx', 'rb')),
        }
        path = fold_path + filename + '.xlsx'
        size = getsize(path)
        if (size <= 6000):
            print(size)
        else:
            response = requests.post(verify=False, url=url, files=files,
                                     headers=headers)
            print(response.status_code)
            # os.remove(filename+'.xlsx')
    except Exception as e:
        print(e)

def get_tempcrawler(crawler_id):
    crawlers = {
        '13': Kklee,
        '14': Wishbykorea,
        '15': Aspeed,
        '17': Openlady,
        '20': Azoom,
        '21': Roxy,
        '23': Cici,
        '25': Amesoeur,
        '27': Singular,
        '28': Folie,
        # '30': Gmorning,
        '31': July,
        '32': Per,
        '35': Jcjc,
        '36': Ccshop,
        '37': Iris,
        '39': Nook,
        '40': Greenpea,
        '42': Queen,
        '48': Cozyfee,
        '49': Reishop,
        '50': Yourz,
        '54': Seoulmate,
        '55': Sweesa,
        '56': Pazzo,
        '57': Meierq,
        '58': Harper,
        '59': Lurehsu,
        '61': Pufii,
        '64': Mercci,
        '65': Sivir,
        '66': Nana,
        '70': Aachic,
        '71': Lovso,
        # '72': Bowwow,
        '74': Suitangtang,
        # '78': Chochobee,
        '80': Asobi,
        '81': Kiyumi,
        '82': Genquo,
        '86': Oolala,
        '87': Pattis,
        '90': Scheminggg,
        '94': Laconic,
        '96': Pixelcake,
        '97': Miyuki,
        '99': Percha,
        '102': Mojp,
        '104': Pleats,
        '105': Zebra,
        '107': Mihara,
        # '111': Oiiv,
        '113': Stayfoxy,
        '118': Righton,
        '120': Daf,
        '122': Sexyinshape,
        '123': Bonjour,
        '133': Amissa,
    }
    return crawlers.get(str(crawler_id))
