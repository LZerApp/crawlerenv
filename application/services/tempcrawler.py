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
def b_stripID(url, wantStrip):
    loc = url.find(wantStrip)
    length = len(wantStrip)
    return url[:loc]

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


def Quentina():
    shop_id = 242
    name = 'quentina'
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
        url = "https://www.quentina.com.tw/products?limit=50&offset=" + \
            str(offset)

        # 如果頁面超過(找不到)，直接印出completed然後break跳出迴圈
        try:
            chrome.get(url)
            print(url)
        except:
            break

        while(i < 51):
            chrome.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
            chrome.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
            chrome.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            try:
                title = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]/div[2]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]//a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/product/")
                pic_link = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]//img" % (i,)).get_attribute('src')
            except:
                print(title)
                i += 1
                if(i == 51):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]/div/div[2]" % (i,)).text
                sale_price = sale_price.strip('NT$ ')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]//span/s" % (i,)).text
                ori_price = ori_price.strip('NT$ ').split()
                ori_price = ori_price[0]
            except:
                sale_price = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]//s" % (i,)).text
                sale_price = sale_price.strip('NT$ ')
                ori_price = chrome.find_element_by_xpath(
                    "//div[@class='rmq-3ab81ca3'][%i]/div[4]/div[2]" % (i,)).text
                ori_price = ori_price.strip('NT$ ').split()
                ori_price = ori_price[0]

            i += 1
            if(i == 51):
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


def Secretacc():
    shop_id = 429
    name = 'secretacc'
    options = Options()                  # 啟動無頭模式
    # options.add_argument('--headless')   # 規避google bug
    # options.add_argument('--disable-gpu')
    # options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument("--remote-debugging-port=5566")
    options.headless = True
    chrome = webdriver.Chrome(
        executable_path='./chromedriver', options=options)

    p = 1
    df = pd.DataFrame()  # 暫存當頁資料，換頁時即整併到dfAll
    dfAll = pd.DataFrame()  # 存放所有資料
    close = 0
    while True:
        if (close == 1):
            chrome.quit()
            break
        i = 1
        url = "https://www.secretacc.com/?74f5e760-22bf-4b32-b9cd-1dd4093e350c="+str(p)+"%2Cselections"
        try:
            chrome.get(url)
            print(url)
        except:
            break

        while(i < 37):
            chrome.find_element("tag name", 'body').send_keys(Keys.PAGE_DOWN)
            chrome.find_element("tag name", 'body').send_keys(Keys.PAGE_DOWN)
            chrome.find_element("tag name", 'body').send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            try:
                title = chrome.find_element("xpath", "//div[@class='rmq-3ab81ca3'][%i]/div[3]" % (i,)).text
            except:
                close += 1
                break
            try:
                page_link = chrome.find_element(
                    "xpath", "//div[@class='rmq-3ab81ca3'][%i]//a[@href]" % (i,)).get_attribute('href')
                make_id = parse.urlsplit(page_link)
                page_id = make_id.path
                page_id = page_id.lstrip("/product/")
                pic_link = chrome.find_element(
                    "xpath", "//div[@class='rmq-3ab81ca3'][%i]//img" % (i,)).get_attribute('src')
            except:
                print(title)
                i += 1
                if(i == 37):
                    p += 1
                continue
            try:
                sale_price = chrome.find_element("xpath",
                                                 "//div[@class='rmq-3ab81ca3'][%i]/div[4]/div" % (i,)).text
            except:
                sale_price = chrome.find_element("xpath",
                                                 "//div[@class='rmq-3ab81ca3'][%i]/div[3]/div" % (i,)).text
            sale_price = sale_price.strip('NT$ ')
            sale_price = sale_price.strip('定價NT$ ')
            ori_price = ""

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
                if(switch == 1):
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
        if (size <= 5600):
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
        '23': Cici,  # 倒
        '27': Singular,
        '35': Jcjc,
        '36': Ccshop,
        '40': Greenpea,
        '55': Sweesa,
        '61': Pufii,  # json
        '80': Asobi,
        '87': Pattis,
        '123': Bonjour,
        '133': Amissa,
        '242': Quentina,  # lazy load V
        '429': Secretacc,  # lazy load
    }
    return crawlers.get(str(crawler_id))
