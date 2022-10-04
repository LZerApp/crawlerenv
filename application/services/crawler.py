import re
import json
from collections import namedtuple
from datetime import datetime
from typing import ItemsView, Pattern
import requests
import csv
from bs4 import BeautifulSoup, FeatureNotFound
from openpyxl import Workbook
from base64 import b64decode
from gzip import decompress
from requests import cookies
from requests.sessions import session
from config import ENV_VARIABLE
from urllib import parse
from urllib.request import urlopen
import time
import os
from requests_html import HTMLSession
import base64


fold_path = "./crawler_data"
page_Max = 150

def stripID(url, wantStrip):
    loc = url.find(wantStrip)
    length = len(wantStrip)
    return url[loc+length:]
def b_stripID(url, wantStrip):
    loc = url.find(wantStrip)
    length = len(wantStrip)
    return url[:loc]


# Product = namedtuple('Product', ['title', 'url', 'page_id', 'image_url', 'original_price', 'sale_price'])
Product = namedtuple(
    "Product", ["title", "page_link", "page_id",
                "pic_link", "ori_price", "sale_price"]
)


class BaseCrawler(object):
    headers = {
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml,*/*",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,la;q=0.json,ja;q=0.4",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
        "cache-control": "no-cache",
    }

    def __init__(self):
        self.result = []

    def fetch(self):
        pass

    def parse(self):
        pass

    def extract(self):
        pass

    def store(self):
        pass

    def save(self):
        name = "_".join(
            [str(self.id), self.name, datetime.today().strftime("%Y%m%d")]
        )

        filename = f"{fold_path}/{name}.csv"

        with open(filename, 'w', newline='') as save_file:
            file_writer = csv.writer(save_file)
            file_writer.writerow(Product._fields)
            for product in self.result:
                if product:
                    file_writer.writerow(product)

        # with open(f"{fold_path}/{filename}.csv", 'wb') as out:
        #     csv_out = csv.writer(out)
        #     csv_out.writerow(Product._fields)
        #     for row in self.result:
        #         csv_out.writerow(row)

        # book = Workbook()
        # sheet = book.active
        # sheet.append()
        # for product in self.result:
        #     if product:
        #         sheet.append([*product])
        # book.save(f"{fold_path}/{filename}.xlsx")

    def upload(self):
        filename = "_".join(
            [str(self.id), self.name, datetime.today().strftime("%Y%m%d")]
        )
        try:
            headers = {
                **self.headers,
                "authorization": ENV_VARIABLE["SERVER_TOKEN"],
            }
            url = f"{ENV_VARIABLE['SERVER_URL']}/api/import/product"
            files = {
                "file": (
                    filename + ".csv",
                    open(f"{fold_path}/{filename}.csv", "rb"),
                ),
            }
            if os.stat(f"{fold_path}/{filename}.csv").st_size <= 60:
                print("File is empty")
            else:
                response = requests.post(
                    verify=False, url=url, files=files, headers=headers
                )
                print(response.status_code)
        except Exception as e:
            print(e)

    def manual_upload(self):
        filename = "_".join(
            [str(self.id), self.name, datetime.today().strftime("%Y%m%d")]
        )
        print(filename)
        try:
            headers = {
                **self.headers,
                "authorization": "Bearer qdm24nwuJqIP9ptuaNTwZL56t5KcpCdCdnERGRHA",
            }
            url = f"https://www.curvedata.tw/api/import/product"
            files = {
                "file": (
                    filename + ".csv",
                    open(f"{fold_path}/{filename}.csv", "rb"),
                ),
            }
            if os.stat(f"{fold_path}/{filename}.csv").st_size <= 60:
                print("File is empty")
            else:
                response = requests.post(
                    verify=False, url=url, files=files, headers=headers
                )
                print(response.status_code)
        except Exception as e:
            print(e)

    def get_price(
        self,
        raw_text,
        pattern="(-?(?:0|[1-9]\d{0,2}(?:,?\d+)*)(?:\.\d+)?)",
        remove_comma=True,
    ):
        if remove_comma:
            return re.search(pattern, raw_text).group(0).replace(",", "")
        return re.search(pattern, raw_text).group(0)


# 000_ExampleCrawler()
# class ExampleCrawler(BaseCrawler):
#     id = 0
#     name = "example"
#     base_url = "http://www.example.com"

#     def parse(self):
#         url = f"{self.base_url}/"
#         response = requests.request("GET", url, headers=self.headers)
#         soup = BeautifulSoup(response.text, features="html.parser")
#         items = soup.find("div", {"class": "example"}).find_all(
#             "div", {"class": "subexample"}
#         )

#         self.result.extend([self.parse_product(item) for item in items])

#     def parse_product(self, item):
#         title = ""
#         link_id = ""
#         link = ""
#         image_url = ""
#         original_price = ""
#         sale_price = ""
#         return Product(title, link, link_id, image_url, original_price, sale_price)


# 001_GracegiftCrawler()
class GracegiftCrawler(BaseCrawler):
    id = 1
    name = "gracegift"
    base_url = "https://www.gracegift.com.tw"

    def parse(self):
        url = f"{self.base_url}/product/category"
        payload = {"ajax": "true", "cid": "239", "size": "99999", "page": "1"}
        response = requests.request(
            "POST", url, headers=self.headers, data=payload)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = soup.find_all("li", {"class": "SaleItem"})
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "productName"}).find(
            "a").text.strip()
        link_id = item.find("a").get("href")
        link = self.base_url + link_id
        link_id = b_stripID(link_id, "/cid/")
        link_id = stripID(link_id, "/pmc/")
        image_url = item.find("img").get("src")
        original_price = (
            self.get_price(item.find("div", {"class": "OrPrice"}).text)
            if item.find("div", {"class": "OrPrice"})
            else ""
        )
        sale_price = self.get_price(item.find("div", {"class": "Price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 002_LegustCrawler()
class LegustCrawler(BaseCrawler):
    id = 2
    name = "legust"
    base_url = "https://www.gusta.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            # print(items)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title text-primary-color"}
        ).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        if (title == "滿額贈，訂單滿1699即贈。"):
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            try:
                original_price = ""
                sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
            except:
                return
        return Product(title, link, link_id, image_url, original_price, sale_price)

class AachicCrawler(BaseCrawler):
    id = 70
    name = "aachic"
    base_url = "https://www.aachic.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all-%E6%89%80%E6%9C%89%E5%95%86%E5%93%81?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title"}
        ).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image m-fill"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class MuminCrawler(BaseCrawler):
    id = 198
    name = "mumin"
    base_url = "https://www.mumin0517.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return
        title = item.find(
            "div", {"class": "title text-primary-color"}
        ).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("background-image:url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class PleatsCrawler(BaseCrawler):
    id = 104
    name = "92pleats"
    base_url = "https://www.92pleats.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all-items-1?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        original_price = ""
        sale_price = self.get_price(item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
        if (len(sale_price) == 1):
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class Me30Crawler(BaseCrawler):
    id = 391
    name = "me30"
    base_url = "https://www.me-30.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all-product?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        original_price = ""
        try:
            sale_price = self.get_price(item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
        except:
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
            except:
                pass
        if (len(sale_price) == 1):
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class XuaccCrawler(BaseCrawler):
    id = 441
    name = "xuacc"
    base_url = "https://www.xuacc.co"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            try:
                original_price = ""
                sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next('div').text)
            except:
                print(title)
                return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class AspeedCrawler(BaseCrawler):
    id = 15
    name = "aspeed"
    base_url = "https://www.aspeed.co"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title text-primary-color"}
        ).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        original_price = ""
        sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class SeoulmateCrawler(BaseCrawler):
    id = 54
    name = "seoulmate"
    base_url = "https://www.seoulmate.com.tw"
    prefix_urls = [
        "/catalog.php?m=123&page=",
        "/catalog.php?m=136&page=",
        "/catalog.php?m=137&page=",
        "/catalog.php?m=143&page=",
        "/catalog.php?m=144&page=",
        "/catalog.php?m=290&page=",
        "/catalog.php?m=231&page=",
        "/catalog.php?m=370&page=",
        "/catalog.php?m=358&page=",
        "/catalog.php?m=242&page=",
        "/catalog.php?m=115&page=",
    ]

    def parse(self):
        for prefix in self.prefix_urls:
            for i in range(1, page_Max):
                urls = [f"{self.base_url}{prefix}{i}"]
                for url in urls:
                    print(url)
                    response = requests.get(url, headers=self.headers)
                    soup = BeautifulSoup(response.text, features="html.parser")
                    try:
                        items = soup.find(
                            "section", {"class": "cataList cataList-align-left cataList-4x"}).find_all("li")
                        if not items:
                            print(url, "break")
                            break
                    except:
                        break
                    self.result.extend([self.parse_product(item) for item in items])
                else:
                    continue
                break

    def parse_product(self, item):
        if item.find("a", {"class": "cataList_gif proImg soldout"}):
            return

        title = item.find(
            "p", {"class": "info"}
        ).text.strip()
        link = item.find("a").get("href")
        link_id = stripID(link, "id=")
        link = f"{self.base_url}/{link}"
        image_url = item.find("img").get("src")
        if (item.find("del", {"class": "proprice"})):
            original_price = self.get_price(item.find("del", {"class": "proprice"}).text)
            sale_price = self.get_price(item.find("p", {"class": "price"}).contents[1])
        else:
            original_price = ""
            sale_price = self.get_price(item.find("p", {"class": "price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class ChochobeeCrawler(BaseCrawler):
    id = 78
    name = "chochobee"
    base_url = "https://www.chochobee.com/"

    def parse(self):
        urls = [
            f"{self.base_url}catalog.php?m=40&s=0&t=0&sort=&page={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("section", {"class": "cataList"}).find_all("li")
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("a", {"class": "cataList_gif proImg soldout"}):
            return

        title = item.find(
            "span", {"class": "info"}
        ).text.strip()
        link = item.find("a").get("href")
        link_id = stripID(link, "id=")
        link = f"{self.base_url}/{link}"
        image_url = item.find("img").get("src")
        if (item.find("del", {"class": "proprice"})):
            original_price = self.get_price(item.find("del", {"class": "proprice"}).text)
            sale_price = self.get_price(item.find("span", {"class": "price"}).contents[1])
        else:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class AzoomCrawler(BaseCrawler):
    id = 20
    name = "azoom"
    base_url = "https://www.aroom1988.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/view-all?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title text-primary-color"}
        ).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class FolieCrawler(BaseCrawler):
    id = 28
    name = "folie"
    base_url = "https://www.folief.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title text-primary-color"}
        ).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class CoochadCrawler(BaseCrawler):
    id = 234
    name = "coochadstore"
    base_url = "https://www.coochadstore.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find("div", {"class": "Product-title Label mix-primary-text"}).text
        link = item.get("href")
        link_id = item.get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            print(title)
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            original_price = ""
            try:
                sale_price = self.get_price(item.find("div", {"class": "Label-price sl-price"}).text)
            except:
                sale_price = self.get_price(
                    item.find("div", {"class": "Label-price sl-price primary-color-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)

class StayfoxyCrawler(BaseCrawler):
    id = 113
    name = "stayfoxy"
    base_url = "https://www.stayfoxyshop.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title text-primary-color"}
        ).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class RightonCrawler(BaseCrawler):
    id = 118
    name = "righton"
    base_url = "https://e.right-on.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/women?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title text-primary-color"}
        ).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class AllgenderCrawler(BaseCrawler):
    id = 337
    name = "allgender"
    base_url = "https://www.allgender.co"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return
        title = item.find(
            "div", {"class": "title text-primary-color"}
        ).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
            except:
                sale_price = self.get_price(
                    item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
            original_price = ""
        return Product(title, link, link_id, image_url, original_price, sale_price)


class DeerwCrawler(BaseCrawler):
    id = 295
    name = "deerw"
    base_url = "https://www.deerw.net"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("product-item")
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title text-primary-color title-container ellipsis"}
        ).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class SexyinshapeCrawler(BaseCrawler):
    id = 122
    name = "sexyinshape"
    base_url = "https://www.sexyinshape.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "Product-title Label mix-primary-text"}).text
        link = item.get("href")
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                      "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            try:
                original_price = ""
                sale_price = self.get_price(item.find("div", {"class": "Label-price sl-price"}).text)
            except:
                original_price = ""
                sale_price = self.get_price(
                    item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class YsquareCrawler(BaseCrawler):
    id = 306
    name = "ysquare"
    base_url = "https://www.ysquare.co"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "Product-title Label mix-primary-text"}).text
        link = item.get("href")
        link_id = item.get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            try:
                original_price = ""
                sale_price = self.get_price(item.find("div", {"class": "Label-price sl-price"}).text)
            except:
                original_price = ""
                sale_price = self.get_price(
                    item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class AriaspaceCrawler(BaseCrawler):
    id = 278
    name = "ariaspace"
    base_url = "https://www.aria-space.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "Product-title Label mix-primary-text"}).text
        link = item.get("href")
        link_id = item.get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            try:
                original_price = ""
                sale_price = self.get_price(item.find("div", {"class": "Label-price sl-price"}).text)
            except:
                original_price = ""
                sale_price = self.get_price(
                    item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class KkleeCrawler(BaseCrawler):
    id = 13
    name = "kklee"
    base_url = "https://www.kklee.co"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "Label-title"}).text
        link = item.get("href")
        link_id = item.get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale tertiary-color-price"}).text)
        except:
            try:
                original_price = ""
                sale_price = self.get_price(item.find("div", {"class": "Label-price sl-price"}).text)
            except:
                original_price = ""
                sale_price = self.get_price(
                    item.find("div", {"class": "Label-price sl-price is-sale tertiary-color-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class AmesoeurCrawler(BaseCrawler):
    id = 25
    name = "amesoeur"
    base_url = "https://www.amesoeur.co"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/%E5%85%A8%E9%83%A8%E5%95%86%E5%93%81?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            if(item.find("div", {"class": "global-primary dark-primary price sl-price"})):
                sale_price = self.get_price(
                    item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
            else:
                sale_price = self.get_price(
                    item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)

class OolalaCrawler(BaseCrawler):
    id = 86
    name = "oolala"
    base_url = "https://www.styleoolala.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title"}).text
        link = item.find("a").get("href")
        link_id = stripID(link, "products/")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price tertiary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class DesireCrawler(BaseCrawler):
    id = 223
    name = "desire"
    base_url = "https://www.desireshop.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class ChiehCrawler(BaseCrawler):
    id = 248
    name = "chieh"
    base_url = "https://www.chieh.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.get("href")
        link_id = stripID(link, "products/")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price tertiary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class WondershopCrawler(BaseCrawler):
    id = 417
    name = "wondershop"
    base_url = "https://www.wondershop.me"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price tertiary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class Menu12Crawler(BaseCrawler):
    id = 442
    name = "12menu"
    base_url = "https://12menu.shoplineapp.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price tertiary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class ChangeuCrawler(BaseCrawler):
    id = 250
    name = "changeu"
    base_url = "https://www.changeu.me"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("div", {"class": "sold-out-item"})):
            return
        title = item.find("div", {"class": "Label-title"}).text
        link = item.get("href")
        link_id = stripID(link, "products/")
        image_url = (
            item.find("div", {
                "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "Label-price sl-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class NinetwonineCrawler(BaseCrawler):
    id = 384
    name = "929"
    base_url = "https://www.929.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("div", {"class": "sold-out-item"})):
            return
        title = item.find("div", {"class": "Product-title Label mix-primary-text"}).text
        link = item.get("href")
        link_id = stripID(link, "products/")
        image_url = (
            item.find("div", {
                "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "Label-price sl-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class PimgoCrawler(BaseCrawler):
    id = 341
    name = "pimgo"
    base_url = "https://www.pimgo.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all-items?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("div", {"class": "sold-out-item"})):
            return
        title = item.find("div", {"class": "Product-title Label mix-primary-text"}).text
        link = item.get("href")
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)

class GirlsdiaryCrawler(BaseCrawler):
    id = 439
    name = "girlsdiary"
    base_url = "https://www.girlsdiarykorea.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("div", {"class": "sold-out-item"})):
            return
        title = item.find("div", {"class": "Product-title Label mix-primary-text"}).text
        link = item.get("href")
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            original_price = ""
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "Label-price sl-price"}).text)
            except:
                sale_price = self.get_price(
                    item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class Seaaa1Crawler(BaseCrawler):
    id = 297
    name = "seaaa1"
    base_url = "https://www.seaaa1.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("div", {"class": "sold-out-item"})):
            return
        title = item.find("div", {"class": "Product-title Label mix-primary-text"}).text
        link = item.get("href")
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            original_price = ""
            try:
                sale_price = self.get_price(item.find("div", {"class": "Label-price sl-price"}).text)
            except:
                try:
                    sale_price = self.get_price(
                        item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
                except:
                    print(item)
                    return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class KiiwioCrawler(BaseCrawler):
    id = 240
    name = "kiiwio"
    base_url = "https://www.kiiwio.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all-product?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("div", {"class": "sold-out-item"})):
            return
        title = item.find("div", {"class": "Product-title Label mix-primary-text"}).text
        link = item.get("href")
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "Label-price sl-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)

class ReallifeCrawler(BaseCrawler):
    id = 225
    name = "reallife"
    base_url = "https://www.real-life.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = stripID(link, "products/")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class LstylestudioCrawler(BaseCrawler):
    id = 300
    name = "lstylestudio"
    base_url = "https://www.lstylestudio.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class MandoCrawler(BaseCrawler):
    id = 401
    name = "mando"
    base_url = "https://www.mando-shop.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        print(item)
        title = item.find("div", {"class": "title"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class OhherCrawler(BaseCrawler):
    id = 238
    name = "ohher"
    base_url = "https://www.ohher.co"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image m-fill"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next('div').text)

        return Product(title, link, link_id, image_url, original_price, sale_price)

class ShaxiCrawler(BaseCrawler):
    id = 22
    name = "shaxi"
    base_url = "https://www.shaxi.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("li", {"class": "boxify-item product-item"})
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):

        title = item.find("div", {"class": "title text-primary-color title-container ellipsis"}).text.strip()
        link = item.find("a").get("href")
        link = f"https://www.shaxi.tw{link}"
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            if(item.find("div", {"class": "global-primary dark-primary price"})):
                sale_price = self.get_price(item.find("div", {"class": "global-primary dark-primary price"}).text)
            else:
                sale_price = self.get_price(item.find("div", {"class": "price-sale price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class PerCrawler(BaseCrawler):
    id = 32
    name = "per"
    base_url = "https://www.perdot.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all?page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("li", {"class": "boxify-item product-item"})
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})):
            return

        title = item.find("div", {"class": "title text-primary-color title-container ellipsis"}).text.strip()
        link = item.find("a").get("href")
        link = f"https://www.perdot.com.tw{link}"
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            if(item.find("div", {"class": "global-primary dark-primary price"})):
                sale_price = self.get_price(item.find("div", {"class": "global-primary dark-primary price"}).text)
            else:
                sale_price = self.get_price(item.find("div", {"class": "price-sale price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class JulyCrawler(BaseCrawler):
    id = 31
    name = "july"
    base_url = "https://www.july2017.co"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/shop-all?limit=72&page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("li", {"class": "boxify-item product-item"})
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})) or (item.find("div", {"class": "available-time-item"})):
            return
        title = item.find("div", {"class": "title text-primary-color title-container ellipsis"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            if(item.find("div", {"class": "global-primary dark-primary price"})):
                sale_price = self.get_price(item.find("div", {"class": "global-primary dark-primary price"}).text)
            else:
                sale_price = self.get_price(item.find("div", {"class": "price-sale price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class IrisCrawler(BaseCrawler):
    id = 37
    name = "iris"
    base_url = "https://www.irisgarden.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/products?limit=72&page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all(
                "li", {"class": "boxify-item product-item"})
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})) or (item.find("div", {"class": "available-time-item"})):
            return
        title = item.find(
            "div", {"class": "title text-primary-color title-container ellipsis force-text-align-"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.find("a").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        original_price = ""
        try:
            sale_price = self.get_price(item.find("div", {"class": "global-primary dark-primary price"}).text)
        except:
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "global-primary dark-primary price force-text-align-"}).text)
            except:
                sale_price = self.get_price(
                    item.find("div", {"class": "price-sale price force-text-align-"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class OmostudioCrawler(BaseCrawler):
    id = 405
    name = "omostudio"
    base_url = "https://www.omostudio.co"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all(
                "li", {"class": "boxify-item product-item"})
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})) or (item.find("div", {"class": "available-time-item"})):
            return
        title = item.find(
            "div", {"class": "title text-primary-color title-container ellipsis force-text-align-"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.find("a").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        original_price = ""
        try:
            sale_price = self.get_price(item.find("div", {"class": "global-primary dark-primary price"}).text)
        except:
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "global-primary dark-primary price force-text-align-"}).text)
            except:
                sale_price = self.get_price(
                    item.find("div", {"class": "price-sale price force-text-align-"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class TennyshopCrawler(BaseCrawler):
    id = 185
    name = "tennyshop"
    base_url = "https://www.tennyshop.co"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all(
                "li", {"class": "boxify-item product-item"})
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})) or (item.find("div", {"class": "available-time-item"})):
            return
        title = item.find(
            "div", {"class": "title text-primary-color title-container ellipsis"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            # if(item.find("div", {"class": "global-primary dark-primary price"})):
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "quick-cart-price"}).text)
            except:
                print(title)
                return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class LeatherCrawler(BaseCrawler):
    id = 196
    name = "leather"
    base_url = "https://www.30leather.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/products?limit=72&page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all(
                "li", {"class": "boxify-item product-item"})
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})) or (item.find("div", {"class": "available-time-item"})):
            return
        title = item.find(
            "div", {"class": "title text-primary-color title-container ellipsis force-text-align-"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.find("a").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed force-text-align-"}).text)
            sale_price = self.get_price(item.find("div", {"class": "price-sale price force-text-align-"}).text)
        except:
            original_price = ""
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "global-primary dark-primary price force-text-align-"}).text)
            except:
                try:
                    sale_price = self.get_price(
                        item.find("div", {"class": "price-sale price force-text-align-"}).text)
                except:
                    print(item.find("div", {"class": "info-box-inner-wrapper"}))
                    return
        if len(sale_price) >= 6:
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)

class NookCrawler(BaseCrawler):
    id = 39
    name = "nook"
    base_url = "https://www.nooknook.me"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})):
            return

        title = item.find("div", {"class": "title text-primary-color"}).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            if(item.find("div", {"class": "global-primary dark-primary price sl-price"})):
                sale_price = self.get_price(
                    item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
            else:
                sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class OurstudioCrawler(BaseCrawler):
    id = 302
    name = "ourstudio"
    base_url = "https://www.our-studio.me"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("product-item")
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})):
            return

        title = item.find("div", {"class": "title text-primary-color title-container ellipsis"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            # if(item.find("div", {"class": "global-primary dark-primary price"})):
            sale_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price"}).text)
            # else:
            #     sale_price = self.get_price(item.find("div", {"class": "price-sale price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class HoukoreaCrawler(BaseCrawler):
    id = 388
    name = "houkorea"
    base_url = "https://www.houkorea.co/"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("product-item")
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})):
            return

        title = item.find("div", {"class": "title text-primary-color title-container ellipsis"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            # if(item.find("div", {"class": "global-primary dark-primary price"})):
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "quick-cart-price"}).text)
            except:
                return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class FashionforyesCrawler(BaseCrawler):
    id = 415
    name = "fashionforyes"
    base_url = "https://www.fashionforyes.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("product-item")
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})):
            return

        title = item.find("div", {"class": "title text-primary-color title-container ellipsis"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            # if(item.find("div", {"class": "global-primary dark-primary price"})):
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "quick-cart-price"}).text)
            except:
                return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class RosirosCrawler(BaseCrawler):
    id = 390
    name = "rosiros"
    base_url = "https://rosirosofficial.shoplineapp.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?limit=72&page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("product-item")
            if not items:
                print(url, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})):
            return

        title = item.find("div", {"class": "title text-primary-color title-container ellipsis"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            # if(item.find("div", {"class": "global-primary dark-primary price"})):
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "quick-cart-price"}).text)
            except:
                return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class OliviaCrawler(BaseCrawler):
    id = 313
    name = "olivia"
    base_url = "https://www.olivia.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image m-fill"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class MypopcornCrawler(BaseCrawler):
    id = 186
    name = "mypopcorn"
    base_url = "https://www.mypopcorn.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class HealerCrawler(BaseCrawler):
    id = 190
    name = "healer"
    base_url = "https://www.healer.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/%E6%89%80%E6%9C%89%E5%95%86%E5%93%81?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image m-fill"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class PeachanCrawler(BaseCrawler):
    id = 406
    name = "peachan"
    base_url = "https://peachan0201449.shoplineapp.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class WhomforCrawler(BaseCrawler):
    id = 431
    name = "whomfor"
    base_url = "https://www.whomfor.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})):
            return
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class AormoreCrawler(BaseCrawler):
    id = 272
    name = "aormore"
    base_url = "https://www.aormore.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})):
            return
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class XwysiblingsCrawler(BaseCrawler):
    id = 435
    name = "xwysiblings"
    base_url = "https://www.xwysiblings.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/women?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})):
            return
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class RoshopCrawler(BaseCrawler):
    id = 46
    name = "roshop"
    base_url = "https://www.roshop.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "sold-out-item"})):
            return
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        image_url = (
            item.find("div", {
                "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )

        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "quick-cart-price"}).find_next("div").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class YourzCrawler(BaseCrawler):
    id = 50
    name = "yourz"
    base_url = "https://www.yourz.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/product/category/0/{i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "c-product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("h3").text
        link = f"{self.base_url}/{item.find('a').get('href')}"
        link_id = item.find("div", {"class": "c-product-item-top-like"}).get("data-idx")
        image_url = f"{self.base_url}/{item.find('img').get('src')}"
        original_price = ""
        sale_price = self.get_price(item.find("span", {"class": "c-product-item-vip-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class Closet152Crawler(BaseCrawler):
    id = 440
    name = "152closet"
    base_url = "https://www.152closet.com"

    def parse(self):
        urls = [
            f"{self.base_url}/shop?page={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("li", {"data-hook": "product-list-grid-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("span", {'data-hook': 'product-item-out-of-stock'}):
            return
        title = item.find("h3").text
        link = item.find('a').get('href')
        link_id = stripID(link, "product-page/")
        image_url = item.find("div", {"data-hook": "ImageUiTpaWrapperDataHook.Wrapper_1"}
                              ).find('img').get('src').replace('147', '720')

        try:
            original_price = self.get_price(
                item.find("span", {"data-hook": "product-item-price-before-discount"}).text)
            sale_price = self.get_price(
                item.find("span", {"data-hook": "product-item-price-to-pay"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("span", {"data-hook": "product-item-price-to-pay"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 004_AjpeaceCrawler()
class AjpeaceCrawler(BaseCrawler):
    id = 4
    name = "ajpease"
    base_url = "https://www.ajpeace.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/index.php?app=search&cate_id=all&order=g.first_shelves_date%20desc&page={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            if (soup.find("div", {"id": "goods-list"})):
                items = soup.find("div", {"id": "goods-list"}).find_all(
                    "div", {"class": "col-sm-4 col-xs-6"}
                )
            else:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("h5").text.strip()
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        link_id = stripID(link_id, "id=")
        image_url = item.find("img").get("src")
        original_price = (
            self.get_price(item.find("span", {"class": "deltxt"}).text)
            if item.find("span", {"class": "deltxt"})
            else ""
        )
        sale_price = self.get_price(item.find("span", {"class": None}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 092_BisouCrawler()
class BisouCrawler(BaseCrawler):
    id = 92
    name = "bisou"
    base_url = "https://www.cn.bisoubisoustore.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?page={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            if (soup.find("div", {"class": "product-list"})):
                items = soup.find("div", {"class": "product-list"}).find_all("div",
                                                                             {"class": "product-block detail-mode-permanent"})
            else:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title"}).text
        link_id = item.get("data-product-id")
        link = item.find('a').get('href')
        link = f"{self.base_url}{link}"
        image_url = item.find("img").get("src")
        image_url = f"https:{image_url}"
        original_price = ""
        sale_price = self.get_price(item.find("span", {"class": "price"}).text)
        sale_price = sale_price.replace(".00", "")
        return Product(title, link, link_id, image_url, original_price, sale_price)

class WishbykoreaCrawler(BaseCrawler):
    id = 14
    name = "wishbykorea"
    base_url = "https://www.wishbykorea.com"
    first_url = "https://www.wishbykorea.com/collection-727&pgno=1"

    def parse(self):
        # 先找到最後一頁的頁碼
        response = requests.request("GET", self.first_url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        last_page = soup.find("a", {"class": "collection_page last"}).get("href")
        # print(last_page)
        last_page = stripID(last_page, "no=")
        # print(last_page)
        last_page = int(last_page)
        print(last_page)
        urls = [
            f"{self.base_url}/collection-727&pgno={i}"
            for i in range(1, last_page+1)
        ]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "collection_item"})

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "collection_item_namecht"}).text
        link = item.find('a').get('href')
        link_id = link.replace("collection-view-", "")
        link_id = b_stripID(link_id, "&ca=")
        link = f"{self.base_url}/{link}"
        image_url = item.find('div', {'class': 'collection_item_image1'}
                              ).get('style').split('background-image:url(.')[1].replace(');', "")
        image_url = f"{self.base_url}{image_url}"
        original_price = ""
        sale_price = self.get_price(item.find("div", {"class": "collection_item_outprice _PRICE"}).text)
        if(len(sale_price) > 5):
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)

# 115_GracechowCrawler()
class GracechowCrawler(BaseCrawler):
    id = 115
    name = "gracechow"
    base_url = "https://www.gracechowtw.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all-item?page={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            if (soup.find("div", {"class": "product product_tag"})):
                items = soup.find("div", {"class": "products_content"}).find_all(
                    "div", {"class": "product product_tag"})
            else:
                break

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a").get("data-name")
        link_id = item.get("product_id")
        link = item.find('a').get('href')
        link = f"{self.base_url}{link}"
        image_url = item.find("img").get("data-src")
        image_url = f"https:{image_url}"
        original_price = ""
        sale_price = self.get_price(item.find("a").get("data-price"))
        sale_price = sale_price.replace(".0", "")
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 005_MajormadeCrawler()
class MajormadeCrawler(BaseCrawler):
    id = 5
    name = "majormade"
    base_url = "https://www.major-made.com"

    def parse(self):
        url = f"{self.base_url}/Shop/itemList.aspx?m=14&smfp=0"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = list(
            json.loads(
                soup.find("div", {"id": "ctl00_ContentPlaceHolder1_ilItems"})
                .find("script")
                .findNext("script")
                .string.replace(" var itemListJson = '", "")
                .replace("';", "")
            )["Data"]["StItem"].values()
        )
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        title = item["mername"]
        link_id = f"mNo1={item['merNo1']}&cno={item['orderNum']}"
        link = f"{self.base_url}/Shop/itemDetail.aspx?{link_id}"
        link_id = stripID(link_id, "mNo1=")
        link_id = link_id[:link_id.find("&cno")]
        image_url = f"http://{item['photosmpath'].replace('//', '')}"
        original_price = item["originalPrice"]
        sale_price = item["price"]
        return Product(title, link, link_id, image_url, original_price, sale_price)

class PufiiCrawler(BaseCrawler):
    id = 61
    name = "pufii"
    base_url = "https://www.pufii.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/Shop/itemList.aspx?&m=6&smfp={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            print(url)
            items = list(
                json.loads(
                    soup.find("div", {"id": "ctl00_ContentPlaceHolder1_ilItems"})
                    .find("script")
                    .findNext("script")
                    .string.replace(" var itemListJson = '", "")
                    .replace("';", "")
                    .replace('\\', "")
                )["Data"]["StItem"].values()
            )
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        title = item["mername"]
        link_id = item["cno"]
        link = f"{self.base_url}/Shop/itemDetail.aspx?mNo1={item['merNo1']}&cno={item['cno']}"
        image_url = item['photosmpath']
        if (image_url == ""):
            try:
                image_url = item['PhotoSm']
            except:
                try:
                    image_url = item['Photo']
                except:
                    print(title)
                    return
        original_price = item["originalPrice"]
        sale_price = item["price"]
        if (original_price == sale_price or int(original_price) == 0):
            original_price = ""
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 052_ApplestarryCrawler()
class ApplestarryCrawler(BaseCrawler):
    id = 52
    name = "applestarry"
    base_url = "https://www.applestarry.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/Shop/itemList.aspx?m=1&smfp={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = list(
                json.loads(
                    soup.find("div", {"id": "ctl00_ContentPlaceHolder1_ilItems"})
                    .find("script")
                    .findNext("script")
                    .string.replace(" var itemListJson = '", "")
                    .replace("';", "")
                )["Data"]["StItem"].values()
            )
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item["mername"]
        link_id = item["idno"]
        link = f"{self.base_url}/Shop/itemDetail.aspx?mNo1={item['merNo1']}&cno={item['ordernum']}"
        image_url = item['photosmpath']
        original_price = item["originalPrice"]
        sale_price = item["price"]
        return Product(title, link, link_id, image_url, original_price, sale_price)

class HarperCrawler(BaseCrawler):
    id = 58
    name = "harper"
    base_url = "https://www.harper.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/Shop/itemList.aspx?m=13&smfp={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            print(url)
            items = list(
                json.loads(
                    soup.find("div", {"id": "ctl00_ContentPlaceHolder1_ilItems"})
                    .find("script")
                    .findNext("script")
                    .string.replace(" var itemListJson = '", "")
                    .replace("';", "")
                    .replace('\\', "")
                )["Data"]["StItem"].values()
            )
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        title = item["mername"]
        link_id = item["cno"]
        link = f"{self.base_url}/Shop/itemDetail.aspx?mNo1={item['merNo1']}&cno={item['cno']}"
        image_url = item['photosmpath']
        if (image_url == ""):
            try:
                image_url = item['PhotoSm']
            except:
                try:
                    image_url = item['Photo']
                except:
                    print(title)
                    return
        original_price = item["originalPrice"]
        sale_price = item["price"]
        if (original_price == sale_price or int(original_price) == 0):
            original_price = ""
        return Product(title, link, link_id, image_url, original_price, sale_price)


class PerchaCrawler(BaseCrawler):
    id = 99
    name = "percha"
    base_url = "https://www.percha.tw"

    def parse(self):
        url = f"{self.base_url}/Shop/itemList.aspx?m=7&smfp=0"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = list(
            json.loads(
                soup.find("div", {"id": "ctl00_ContentPlaceHolder1_ilItems"})
                .find("script")
                .findNext("script")
                .string.replace(" var itemListJson = '", "")
                .replace("';", "")
            )["Data"]["StItem"].values()
        )
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item["mername"]
        pre_link = f"mNo1={item['merNo1']}&m=7"
        link = f"{self.base_url}/Shop/itemDetail.aspx?{pre_link}"
        link_id = item["merNo1"]
        image_url = item["photosmpath"]
        original_price = item["originalPrice"]
        sale_price = item["price"]
        return Product(title, link, link_id, image_url, original_price, sale_price)


class LalalatwCrawler(BaseCrawler):
    id = 266
    name = "lalalatw"
    base_url = "https://www.lalalatw.com"

    def parse(self):
        urls = [f"{self.base_url}/Shop/itemList.aspx?m=5&smfp={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            raw_string = soup.find("div", {"id": "ctl00_ContentPlaceHolder1_ilItems"}).find(
                "script").findNext("script").string.replace(" var itemListJson = '", "").replace("';", "")
            decoded_json = decompress(b64decode(raw_string[5:])).decode("utf-8")
            items = list(json.loads(decoded_json)["Valuse"]["Data"]["Data"]["StItem"].values())
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item["MerName"]
        pre_link = f"mNo1={item['MerNo1']}&m=5"
        link = f"{self.base_url}/Shop/itemDetail.aspx?{pre_link}"
        link_id = item["MerNo1"]
        image_url = item["PhotoSm"]
        original_price = item["OriginalPrice"]
        original_price = str(original_price).replace(".0", "")
        if original_price == "0":
            original_price = ""
        sale_price = item["Price"]
        sale_price = str(sale_price).replace(".0", "")
        if original_price == sale_price:
            original_price = ""
        return Product(title, link, link_id, image_url, original_price, sale_price)

class ZebraCrawler(BaseCrawler):
    id = 105
    name = "zebracrossing"
    base_url = "https://www.zebracrossing.com.tw"

    def parse(self):
        url = f"{self.base_url}/Shop/itemList.aspx?&m=8&smfp=0"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = list(
            json.loads(
                soup.find("div", {"id": "ctl00_ContentPlaceHolder1_ilItems"})
                .find("script")
                .findNext("script")
                .string.replace("var itemListJson = '", "")
                .replace("';", "")
                .replace('img src=\\\\"https', "img src=\\\\'https")
                .replace('jpg\\\\">', "jpg\\\\'>")
            )["Data"]["StItem"].values()
        )
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item["mername"]
        pre_link = f"mNo1={item['merNo1']}&m=8"
        link = f"{self.base_url}/Shop/itemDetail.aspx?{pre_link}"
        link_id = item["merNo1"]
        image_url = item["photosmpath"]
        original_price = item["originalPrice"]
        sale_price = item["price"]
        return Product(title, link, link_id, image_url, original_price, sale_price)

# 007_BasicCrawler()
class BasicCrawler(BaseCrawler):
    id = 7
    name = "basic"
    base_url = "https://www.basic.tw"

    def parse(self):
        url = f"{self.base_url}/productlist?page=all"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = soup.find("div", {"class": "pdlist_wrap"}).find_all(
            "div",
            {
                "class": "column is-half-mobile is-one-third-tablet is-one-quarter-widescreen pdbox"
            },
        )

        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "pdbox_name"}).text.strip()
        link_id = item.find("a").find_next_sibling("a").get("href")
        link = f"{self.base_url}/{link_id}"
        image_url = item.find("img").get("src")
        link_id = stripID(link_id, "saleid=")
        original_price = (
            self.get_price(
                item.find("span", {"class": "pdbox_price-origin"}).text)
            if item.find("span", {"class": "pdbox_price-origin"})
            else ""
        )
        sale_price = (
            self.get_price(
                item.find("span", {"class": "pdbox_price-sale"}).text)
            if item.find("span", {"class": "pdbox_price-sale"})
            else self.get_price(item.find("span", {"class": "pdbox_price"}).text)
        )
        return Product(title, link, link_id, image_url, original_price, sale_price)

class SchemingggCrawler(BaseCrawler):
    id = 90
    name = "scheminggg"
    base_url = "https://www.scheminggg.com"

    def parse(self):
        urls = [f"{self.base_url}/productlist?page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("div", {"class": "pdlist_wrap"}).find_all(
                "div",
                {
                    "class": "column is-half-mobile is-one-third-tablet is-one-quarter-widescreen pdbox"
                },
            )
            if not items:
                print("break")
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "pdbox_name"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        image_url = item.find("img").get("src")
        link_id = stripID(link_id, "saleid=")
        original_price = (
            self.get_price(
                item.find("p", {"class": "pdbox_price-origin"}).text)
            if item.find("p", {"class": "pdbox_price-origin"})
            else ""
        )
        sale_price = (
            self.get_price(
                item.find("p", {"class": "pdbox_price-sale"}).text)
            if item.find("p", {"class": "pdbox_price-sale"})
            else self.get_price(item.find("p", {"class": "pdbox_price"}).text)
        )
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 008_AirspaceCrawler()
class AirspaceCrawler(BaseCrawler):
    id = 8
    name = "airspace"
    base_url = "https://www.airspaceonline.com"

    def parse(self):
        get_max_page = "https://www.airspaceonline.com/PDList.asp?color=&keyword=&pp1=all&pp2=&pp3=&newpd=&ob=A&pageno=300"
        response = requests.request("GET", get_max_page, headers=self.headers, verify=False)
        soup = BeautifulSoup(response.text, features="html.parser")
        max_page = soup.find("div", {"class": "pdpager"}).find("font").text
        max_page = int(max_page)
        print(max_page)
        urls = [
            f"{self.base_url}/PDList.asp?pp1=all&pp2=&pp3=&newpd=&ob=A&pageno={i}" for i in range(1, max_page+1)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers, verify=False)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("div", {"id": "item"}).find_all("li")
            print(url)
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "pdtext"}).find("a").text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        link_id = stripID(link_id, "yano=")
        link_id = link_id[:link_id.find("&yacolor")]
        image_url = item.find("img").get("src")
        original_price = ""
        sale_price = self.get_price(item.find("p", {"class": "pdprice"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 112_VeryyouCrawler()
class VeryyouCrawler(BaseCrawler):
    id = 112
    name = "veryyou"
    base_url = "https://www.veryyou.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/PDList2.asp?item=all&ob=D3&pageno={i}" for i in range(1, 10)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("figure", {"class": "p-item"})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        link_id = stripID(link_id, "yano=")
        link_id = link_id[:link_id.find("&color")]
        image_url = item.find("img").get("data-src")
        try:
            original_price = self.get_price(item.find("span", {"class": "retail"}).text)
            sale_price = self.get_price(item.find("span", {"class": "on-sale"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "retail"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class GotobuyCrawler(BaseCrawler):
    id = 342
    name = "gotobuy"
    base_url = "https://www.gotobuy.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/PDList2.asp?item=all&ob=D3&pageno={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "pdBox"})
            print(url)
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "pdBox_name"}).contents[0]
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        link_id = stripID(link_id, "yano=")
        image_url = item.find("img").get("src")
        try:
            original_price = self.get_price(item.find("span", {"class": "pd_originalPrice"}).text)
            sale_price = self.get_price(item.find("span", {"class": "pd_salePrice"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("p", {"class": "pdBox_price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class AfadCrawler(BaseCrawler):
    id = 239
    name = "afad"
    base_url = "https://www.afad.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/PDList2.asp?item=all&ob=D3&pageno={i}" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "pdbox"})
            if len(items) < 30:
                if flag == True:
                    print("break")
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "pdbox_name"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        pattern = "no=(.+)&"
        link_id = re.search(pattern, link).group(1)
        image_url = item.find("img").get("src")
        try:
            original_price = self.get_price(item.find("p", {"class": "pdbox_price-origin"}).text)
            sale_price = self.get_price(item.find("p", {"class": "pdbox_price-sale"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("p", {"class": "pdbox_price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 108_EyescreamCrawler()
class EyecreamCrawler(BaseCrawler):
    id = 108
    name = "eyescream"
    base_url = "https://www.eyescream.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/PDList2.asp?item=all&ob=D3&pageno={i}" for i in range(1, 15)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("figure", {"class": "p-item col-lg-3 col-md-4 col-xs-6 wow fadeInUp animated"})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        link_id = stripID(link_id, "yano=")
        link_id = link_id[:link_id.find("&color")]
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find("span", {"class": "retail"}).text)
            sale_price = self.get_price(item.find("span", {"class": "on-sale"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "retail"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class ReishopCrawler(BaseCrawler):
    id = 49
    name = "reishop"
    base_url = "https://www.reishop.com.tw"

    def parse(self):
        temp_url = "https://www.reishop.com.tw/pdlist2.asp?item1=all&item2=&item3=&keyword=&ob=A&pagex=&pageno=100"
        response = requests.request("GET", temp_url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        max_page = soup.find("a", {"class": "pg_link active"}).text
        max_page = int(max_page)
        print(max_page)
        urls = [
            f"{self.base_url}/pdlist2.asp?item1=all&item2=&item3=&keyword=&ob=A&pagex=&pageno={i}" for i in range(1, max_page + 1)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("figcaption", {"class": "pd_list"})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a").get("title")
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        link_id = stripID(link_id, "yano=")
        link_id = link_id[:link_id.find("&color")]
        image_url = item.find("img").get("src")
        original_price = ""
        sale_price = self.get_price(item.find("span", {"class": "pd_saleprice"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

# 009_YocoCrawler()
class YocoCrawler(BaseCrawler):
    id = 9
    name = "Yoco"
    base_url = "https://www.yoco.com.tw"
    payload = {
        "pmmNo": "Topic56",
        "PageSize": "32",
        "SortCol": "pm_sdate",
        "SortType": "desc",
    }

    def get_cookies(self):
        url = f"{self.base_url}/Product/Category/Topic56/"
        cookies = requests.request("GET", url, headers=self.headers).cookies
        return cookies

    def get_discount_ratio(self, raw_text, pattern="(\d+%)"):
        discount_off = re.search(pattern, raw_text).group(0).replace("%", "")
        return 1 - int(discount_off) / 100

    def get_original_price(self, raw_text):
        sale_price = float(self.get_price(raw_text))
        discount_ratio = float(self.get_discount_ratio(raw_text))
        return int(sale_price / discount_ratio)

    def parse(self):
        url = f"{self.base_url}/AjaxProduct/GetProductCategoryListHtml"
        for page_index in range(1, 17):
            cookies = self.get_cookies()
            response = requests.request(
                "POST",
                url,
                headers={**self.headers, "X-Requested-With": "XMLHttpRequest"},
                data={**self.payload, "PageIndex": page_index},
                cookies=cookies,
            )
            soup = BeautifulSoup(
                json.loads(response.text)["html"], features="html.parser"
            )
            items = soup.find_all("li", {"class": "product-cate_item"})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("span", {"class": "cate-name"}).text.strip()
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        image_url = (
            item.find("img").get("data-original")
            if item.find("img").get("data-original")
            else item.find("img").get("src")
        )
        original_price = self.get_original_price(
            item.find("span", {"class": "price_discount"}).text
        )
        sale_price = self.get_price(
            item.find("span", {"class": "price_discount"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 076_MiustarCrawler()
class MiustarCrawler(BaseCrawler):
    id = 76
    name = "miustar"
    base_url = "https://www.miu-star.com.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 1317, "categoryId": 43374,
                 "fetchCount": 20000, "orderBy": "Curator", "isShowCurator": True, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(20):
            start = 200 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 125_MiniqueenCrawler()
class MiniqueenCrawler(BaseCrawler):
    id = 125
    name = "miniqueen"
    base_url = "https://www.miniqueen.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 1426, "categoryId": 0, "fetchCount": 200,
                 "orderBy": "", "isShowCurator": False, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(10):
            start = 200 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")
        return Product(title, link, link_id, image_url, original_price, sale_price)

# 130_BaibeautyCrawler()
class BaibeautyCrawler(BaseCrawler):
    id = 130
    name = "baibeauty"
    base_url = "https://www.baibeauty.com/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 576, "categoryId": 275337, "fetchCount": 200,
                 "orderBy": "", "isShowCurator": True, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(10):
            start = 200 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 136_DaimaCrawler()
class DaimaCrawler(BaseCrawler):
    id = 136
    name = "daima"
    base_url = "https://www.daima.asia/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 488, "categoryId": 0, "fetchCount": 200,
                 "orderBy": "", "isShowCurator": False, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(20):
            start = 200 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 138_MiakiCrawler()
class MiakiCrawler(BaseCrawler):
    id = 138
    name = "miaki"
    base_url = "https://www.miaki.com.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 385, "categoryId": 0, "fetchCount": 200,
                 "orderBy": "", "isShowCurator": False, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(20):
            start = 200 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 爬取多個頁面
# 024_InshopCrawler()
class InshopCrawler(BaseCrawler):
    id = 24
    name = "inshop"
    base_url = "https://www.inshop.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 6300, "startIndex": 0, "fetchCount": 200,
                 "orderBy": "", "isShowCurator": True, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        categoryids = ["115047", "247685", "115050", "247684", "181353", "115051", "181287", "115052"]
        for categoryid in categoryids:
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "categoryId": int(categoryid)}},
            )
            # print(response.text)
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 爬取多個頁面
# 139_VinaclosetCrawler()
class VinaclosetCrawler(BaseCrawler):
    id = 139
    name = "vinacloset"
    base_url = "https://www.vinacloset.com.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 1962, "fetchCount": 200, "orderBy": "", "isShowCurator": True, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        categoryids = ["228637", "228646", "322505", "322505", "228639"]
        for categoryid in categoryids:
            print(categoryid)
            for i in range(20):
                start = 200 * i
                response = requests.request(
                    "POST",
                    url,
                    headers=self.headers,
                    json={'query': self.query, 'variables': {**self.variables, "categoryId": int(categoryid), "startIndex": start}},)
                items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
                if not items:
                    break
                self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        original_price = ""
        sale_price = item.get("suggestPrice")

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 爬取多個頁面
# 103_GoddessCrawler()
class GoddessCrawler(BaseCrawler):
    id = 103
    name = "goddess"
    base_url = "https://www.goddess-shop.com/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 2332, "fetchCount": 200, "orderBy": "Curator", "isShowCurator": True, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        categoryids = ["296022", "167645", "295988", "295998", "295975"]
        for categoryid in categoryids:
            for i in range(20):
                start = 200 * i
                response = requests.request(
                    "POST",
                    url,
                    headers=self.headers,
                    json={'query': self.query, 'variables': {**self.variables,
                                                             "categoryId": int(categoryid), "startIndex": start}},
                )
                items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
                if not items:
                    break
                self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 041_RainbowCrawler()
class RainbowCrawler(BaseCrawler):
    id = 41
    name = "rainbow"
    base_url = "https://www.rainbow-shop.com.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 688, "categoryId": 0, "fetchCount": 200,
                 "orderBy": "", "isShowCurator": False, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(20):
            start = 200 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 043_NeedCrawler()
class NeedCrawler(BaseCrawler):
    id = 43
    name = "need"
    base_url = "https://www.need.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 1649, "categoryId": 183137, "fetchCount": 200,
                 "orderBy": "", "isShowCurator": True, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(20):
            start = 200 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 079_BasezooCrawler()
class BasezooCrawler(BaseCrawler):
    id = 79
    name = "basezoo"
    base_url = "https://www.basezoo.com.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 31928, "categoryId": 0, "fetchCount": 200,
                 "orderBy": "", "isShowCurator": False, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(20):
            start = 200 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 095_LulusCrawler()
class LulusCrawler(BaseCrawler):
    id = 95
    name = "lulus"
    base_url = "https://www.lulus.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 2190, "categoryId": 0, "fetchCount": 200,
                 "orderBy": "", "isShowCurator": False, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(20):
            start = 200 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 109_CandyboxCrawler()
class CandyboxCrawler(BaseCrawler):
    id = 109
    name = "candybox"
    base_url = "https://candybox.com.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 14, "categoryId": 98162, "fetchCount": 200,
                 "orderBy": "", "isShowCurator": True, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(20):
            start = 200 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"
        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")
        return Product(title, link, link_id, image_url, original_price, sale_price)


class CorbanCrawler(BaseCrawler):
    id = 29
    name = "corban"
    base_url = "https://www.corban.tw/SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                    __typename
                }
            totalSize
            shopCategoryId
            shopCategoryName
            statusDef
            listModeDef
            orderByDef
            dataSource
            __typename
            }
            __typename
        }
    }
"""

    variables = {"shopId": 40995, "categoryId": 382947, "fetchCount": 100,
                 "orderBy": "", "isShowCurator": True, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(20):
            start = 100 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"

        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")
        return Product(title, link, link_id, image_url, original_price, sale_price)


class MaaCrawler(BaseCrawler):
    id = 389
    name = "maa"
    base_url = "https://www.2maa.com.tw//SalePage/Index/"  # 要記得改
    query = """
    query cms_shopCategory($shopId: Int!, $categoryId: Int!, $startIndex: Int!, $fetchCount: Int!, $orderBy: String, $isShowCurator: Boolean, $locationId: Int) {
        shopCategory(shopId: $shopId, categoryId: $categoryId) {
            salePageList(startIndex: $startIndex, maxCount: $fetchCount, orderBy: $orderBy, isCuratorable: $isShowCurator, locationId: $locationId) {
                salePageList {
                    salePageId
                    title
                    picUrl
                    price
                    suggestPrice
                }
            }
        }
    }
"""

    variables = {"shopId": 325, "categoryId": 0, "fetchCount": 100, "isShowCurator": True, "locationId": 0}

    def parse(self):
        url = "https://fts-api.91app.com/pythia-cdn/graphql"
        for i in range(20):
            start = 100 * i
            response = requests.request(
                "POST",
                url,
                headers=self.headers,
                json={'query': self.query, 'variables': {**self.variables, "startIndex": start}},
            )
            items = json.loads(response.text)["data"]["shopCategory"]["salePageList"]["salePageList"]
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link_id = item.get("salePageId")
        link = f"{self.base_url}{link_id}"
        image_url = f"https:{item.get('picUrl')}"

        if(item.get("price") == item.get("suggestPrice")):
            original_price = ""
            sale_price = item.get("price")
        else:
            original_price = item.get("suggestPrice")
            sale_price = item.get("price")
        return Product(title, link, link_id, image_url, original_price, sale_price)


class EvermoreCrawler(BaseCrawler):
    id = 155
    name = "evermore"
    base_url = "https://www.love-evermore.com/product/"  # 要記得改
    query = """query getProducts($search: searchInputObjectType)
{
      computeProductList(search: $search) {
              data {
                        id
                              title {
                                          zh_TW

                                                    }
                                                                                                                       variants {


                                                                                                                                          listPrice

                                                                                                                                                          totalPrice

                                                                                                                                                                        }
                                                                                                                                                                              coverImage {

                                                                                                                                                                                                  scaledSrc {
                                                                                                                                                                                                                                                                                                 w1920

                                                                                                                                                                                                                                                                                                                            }

                                                                                                                                                                                                                                                                                                                                          }

                                                                                                                                                                                                                                                                                                                                }

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        }
}
"""

    variables = {"search": {"size": 500, "from": 0, "filter": {"and": [{"type": "exact", "field": "status", "query": "1"}], "or": [
    ]}, "sort": [{"field": "createdAt", "order": "desc"}], "showVariants": True, "showMainFile": True}}

    def parse(self):
        url = "https://www.love-evermore.com/api/graphql"
        for offset in range(0, 2000, 500):
            try:
                print(offset)
                self.variables["search"]["from"] = offset
                response = requests.request(
                    "POST",
                    url,
                    headers=self.headers,
                    json={'query': self.query, 'variables': {**self.variables}},
                )
                items = json.loads(response.text)["data"]["computeProductList"]["data"]
                self.result.extend([self.parse_product(item) for item in items])

            except:
                print(offset)
                break

    def parse_product(self, item):

        title = item['title']['zh_TW']
        link_id = item['id']
        link = f"{self.base_url}{link_id}"
        image_url = item['coverImage']['scaledSrc']['w1920']

        price = item["variants"]
        original_price = price[0]["listPrice"]
        sale_price = price[0]["totalPrice"]
        return Product(title, link, link_id, image_url, original_price, sale_price)


class Nora38Crawler(BaseCrawler):
    id = 444
    name = "nora38"
    base_url = "https://www.nora38.com/product/"  # 要記得改
    query = """query getProducts($search: searchInputObjectType)
{
      computeProductList(search: $search) {
              data {
                        id
                              title {
                                          zh_TW

                                                    }
                                                                                                                       variants {


                                                                                                                                          listPrice

                                                                                                                                                          totalPrice

                                                                                                                                                                        }
                                                                                                                                                                              coverImage {

                                                                                                                                                                                                  scaledSrc {
                                                                                                                                                                                                                                                                                                 w1920

                                                                                                                                                                                                                                                                                                                            }

                                                                                                                                                                                                                                                                                                                                          }

                                                                                                                                                                                                                                                                                                                                }

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        }
}
"""

    variables = {"search": {"size": 500, "from": 0, "filter": {"and": [{"type": "exact", "field": "status", "query": "1"}], "or": [
    ]}, "sort": [{"field": "createdAt", "order": "desc"}], "showVariants": True, "showMainFile": True}}

    def parse(self):
        url = "https://www.nora38.com/api/graphql"
        for offset in range(0, 2000, 500):
            try:
                print(offset)
                self.variables["search"]["from"] = offset
                response = requests.request(
                    "POST",
                    url,
                    headers=self.headers,
                    json={'query': self.query, 'variables': {**self.variables}},
                )
                items = json.loads(response.text)["data"]["computeProductList"]["data"]
                self.result.extend([self.parse_product(item) for item in items])

            except:
                print(offset)
                break

    def parse_product(self, item):

        title = item['title']['zh_TW']
        link_id = item['id']
        link = f"{self.base_url}{link_id}"
        image_url = item['coverImage']['scaledSrc']['w1920']
        price = item["variants"]
        original_price = price[0]["listPrice"]
        if original_price == 0:
            original_price = ""
        sale_price = price[0]["totalPrice"]
        return Product(title, link, link_id, image_url, original_price, sale_price)


class MiashiCrawler(BaseCrawler):
    id = 414
    name = "miashi"
    base_url = "https://www.miashi.com.tw/product/"  # 要記得改
    query = """query getProducts($search: searchInputObjectType)
{
      computeProductList(search: $search) {
              data {
                        id
                              title {
                                          zh_TW

                                                    }
                                                                                                                       variants {


                                                                                                                                          listPrice

                                                                                                                                                          totalPrice

                                                                                                                                                                        }
                                                                                                                                                                              coverImage {

                                                                                                                                                                                                  scaledSrc {
                                                                                                                                                                                                                                                                                                 w1920

                                                                                                                                                                                                                                                                                                                            }

                                                                                                                                                                                                                                                                                                                                          }

                                                                                                                                                                                                                                                                                                                                }

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        }
}
"""

    variables = {"search": {"size": 500, "from": 0, "filter": {"and": [{"type": "exact", "field": "status", "query": "1"}], "or": [
    ]}, "sort": [{"field": "createdAt", "order": "desc"}], "showVariants": True, "showMainFile": True}}

    def parse(self):
        url = "https://www.miashi.com.tw/api/graphql"
        for offset in range(0, 2000, 500):
            try:
                print(offset)
                self.variables["search"]["from"] = offset
                response = requests.request(
                    "POST",
                    url,
                    headers=self.headers,
                    json={'query': self.query, 'variables': {**self.variables}},
                )
                items = json.loads(response.text)["data"]["computeProductList"]["data"]
                self.result.extend([self.parse_product(item) for item in items])

            except:
                print(offset)
                break

    def parse_product(self, item):

        title = item['title']['zh_TW']
        link_id = item['id']
        link = f"{self.base_url}{link_id}"
        image_url = item['coverImage']['scaledSrc']['w1920']

        price = item["variants"]
        original_price = ""
        sale_price = price[0]["totalPrice"]
        return Product(title, link, link_id, image_url, original_price, sale_price)


class NelmuseoCrawler(BaseCrawler):
    id = 423
    name = "nelmuseo"
    base_url = "https://www.nelmuseo.com.tw/product/"  # 要記得改
    query = """query getProducts($search: searchInputObjectType)
{
      computeProductList(search: $search) {
              data {
                        id
                              title {
                                          zh_TW

                                                    }
                                                                                                                       variants {


                                                                                                                                          listPrice

                                                                                                                                                          totalPrice

                                                                                                                                                                        }
                                                                                                                                                                              coverImage {

                                                                                                                                                                                                  scaledSrc {
                                                                                                                                                                                                                                                                                                 w1920

                                                                                                                                                                                                                                                                                                                            }

                                                                                                                                                                                                                                                                                                                                          }

                                                                                                                                                                                                                                                                                                                                }

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        }
}
"""

    variables = {"search": {"size": 500, "from": 0, "filter": {"and": [{"type": "exact", "field": "status", "query": "1"}], "or": [
    ]}, "sort": [{"field": "createdAt", "order": "desc"}], "showVariants": True, "showMainFile": True}}

    def parse(self):
        url = "https://www.nelmuseo.com.tw/api/graphql"
        for offset in range(0, 2000, 500):
            try:
                print(offset)
                self.variables["search"]["from"] = offset
                response = requests.request(
                    "POST",
                    url,
                    headers=self.headers,
                    json={'query': self.query, 'variables': {**self.variables}},
                )
                items = json.loads(response.text)["data"]["computeProductList"]["data"]
                self.result.extend([self.parse_product(item) for item in items])
            except:
                print(offset)
                break

    def parse_product(self, item):

        title = item['title']['zh_TW']
        link_id = item['id']
        link = f"{self.base_url}{link_id}"
        image_url = item['coverImage']['scaledSrc']['w1920']
        price = item["variants"]
        original_price = ""
        sale_price = price[0]["totalPrice"]
        return Product(title, link, link_id, image_url, original_price, sale_price)


class FeelneCrawler(BaseCrawler):
    id = 392
    name = "feelne"
    base_url = "https://www.feelne.com/product/"  # 要記得改
    query = """query getProducts($search: searchInputObjectType)
{
      computeProductList(search: $search) {
              data {
                        id
                              title {
                                          zh_TW

                                                    }
                                                                                                                       variants {


                                                                                                                                          listPrice

                                                                                                                                                          totalPrice

                                                                                                                                                                        }
                                                                                                                                                                              coverImage {

                                                                                                                                                                                                  scaledSrc {
                                                                                                                                                                                                                                                                                                 w1920

                                                                                                                                                                                                                                                                                                                            }

                                                                                                                                                                                                                                                                                                                                          }

                                                                                                                                                                                                                                                                                                                                }

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        }
}
"""

    variables = {"search": {"size": 500, "from": 0, "filter": {"and": [{"type": "exact", "field": "status", "query": "1"}], "or": [
    ]}, "sort": [{"field": "createdAt", "order": "desc"}], "showVariants": True, "showMainFile": True}}

    def parse(self):
        url = "https://www.feelne.com/api/graphql"
        for offset in range(0, 2000, 500):
            try:
                print(offset)
                self.variables["search"]["from"] = offset
                response = requests.request(
                    "POST",
                    url,
                    headers=self.headers,
                    json={'query': self.query, 'variables': {**self.variables}},
                )
                items = json.loads(response.text)["data"]["computeProductList"]["data"]
                self.result.extend([self.parse_product(item) for item in items])
            except:
                print(offset)
                break

    def parse_product(self, item):

        title = item['title']['zh_TW']
        link_id = item['id']
        link = f"{self.base_url}{link_id}"
        image_url = item['coverImage']['scaledSrc']['w1920']
        price = item["variants"]
        original_price = ""
        sale_price = price[0]["totalPrice"]
        return Product(title, link, link_id, image_url, original_price, sale_price)

# 10_EFSHOP
class EfshopCrawler(BaseCrawler):
    id = 10
    name = "efshop"
    prefix_urls = [
        "https://www.efshop.com.tw/category/1",
        "https://www.efshop.com.tw/category/72",
        "https://www.efshop.com.tw/category/491",
        "https://www.efshop.com.tw/category/11",
        "https://www.efshop.com.tw/category/478",
        "https://www.efshop.com.tw/category/10",
    ]

    def parse(self):
        for prefix in self.prefix_urls:
            for i in range(1, 20):
                urls = [f"{prefix}/{i}"]
                for url in urls:
                    print(url)
                    response = requests.get(url, headers=self.headers)
                    soup = BeautifulSoup(response.text, features="html.parser")
                    if (soup.find_all("div", {"class": "idx_pro2"})):
                        items = soup.find_all("div", {"class": "idx_pro2"})
                    else:
                        print("break")
                        break
                    self.result.extend([self.parse_product(item) for item in items])
                else:
                    continue
                break

    def parse_product(self, item):
        title = item.find("a").get("title")
        link = item.find("a").get("href")
        link_id = item.find("input").get("value")
        image_url = item.find("img").get("src")
        if item.find("span", {"class": "monenyBig"}).find_next_sibling("span", {"class": "monenyBig"}):
            original_price = item.find("span", {"class": "monenyBig"}).find_next_sibling(
                "span", {"class": "monenyBig"}).text.strip()
            sale_price = self.get_price(item.find("span", {"class": "monenyBig"}).text)
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("span", {"class": "monenyBig"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 11_MODA
class ModaCrawler(BaseCrawler):
    id = 11
    name = "moda"
    base_url = "https://www.modalovemoda.com/Shop"

    def parse(self):
        get_max_page = "https://www.modalovemoda.com/Shop/itemList.aspx?m=1&o=4&sa=0&smfp=100&"
        response = requests.request("GET", get_max_page, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        max_page = soup.find("span", {"class": "spCount"}).text
        max_page = max_page.replace("]", "").replace("[", "")
        max_page = int(max_page)
        urls = [
            f"{self.base_url}/itemList.aspx?m=1&o=4&sa=0&smfp={i}" for i in range(1, max_page+1)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find_all("div", {"class": "itemListDiv"})
            except:
                print(url)
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "itemListMerName"}).find("a").text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        link = b_stripID(link, "&m")
        link_id = b_stripID(link_id, "&m")
        link_id = stripID(link_id, "mNo1=")
        image_url = item.find("img").get("src")
        image_url = f"https:{image_url}"
        original_price = self.get_price(item.find(
            "div", {"class": "itemListMoney"}).find('span').text)
        sale_price = self.get_price(
            item.find("div", {"class": "itemListMoney"}).find('span').find_next('span').text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class LovsoCrawler(BaseCrawler):
    id = 71
    name = "lovso"
    base_url = "https://www.lovso.com.tw"

    def parse(self):
        url = f"{self.base_url}/Shop/itemList.aspx?&m=8&smfp=0"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = list(
            json.loads(
                soup.find("div", {"id": "ctl00_ContentPlaceHolder1_ilItems"})
                .find("script")
                .findNext("script")
                .string.replace("var itemListJson = '", "")
                .replace("';", "")
                .replace('href=\\\\"https', "href=\\\\'https")
                .replace('\\\\">', "\\\\'>")
                .replace('img src=\\\\"https', "img src=\\\\'https")
            )["Data"]["StItem"].values()
        )

        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        title = item["mername"].replace("<br>", "")
        link_id = f"mNo1={item['merNo1']}"
        link = f"{self.base_url}/Shop/itemDetail.aspx?{link_id}"
        link_id = stripID(link_id, "mNo1=")
        image_url = item['photosmpath']
        original_price = item["originalPrice"]
        sale_price = item["price"]
        return Product(title, link, link_id, image_url, original_price, sale_price)

# 45_GOGOSING
class GogosingCrawler(BaseCrawler):
    id = 45
    name = "gogosing"
    prefix_urls = [
        "https://ggsing.tw/category/%E8%A4%B2%E5%AD%90/47/?page=",
        "https://ggsing.tw/category/%E4%B8%8A%E8%A1%A3/31/?page=",
        "https://ggsing.tw/category/%E8%A5%AF%E8%A1%AB%E9%9B%AA%E7%B4%A1%E4%B8%8A%E8%A1%A3/46/?page=",
        "https://ggsing.tw/category/%E8%A3%99%E5%AD%90/26/?page=",
        "https://ggsing.tw/category/%E6%B4%8B%E8%A3%9D/197/?page=",
        "https://ggsing.tw/category/%E5%A4%96%E5%A5%97/7/?page=",
        "https://ggsing.tw/category/%E6%99%82%E5%B0%9A%E9%85%8D%E9%A3%BE/1771/?page=",
    ]
    urls = [
        f"{prefix}/{i}" for prefix in prefix_urls for i in range(1, 5)]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find_all("li", {"class": "item xans-record-"})
            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p").find("a").text
        link = item.find("a").get("href")
        link = f"https://ggsing.tw/{link}"
        link_id = item.find("a").get("name")
        link_id = stripID(link_id, "anchorBoxName_")
        image_url = item.find("a").find("img").get("src")
        image_url = f"https:{image_url}"
        original_price = ""
        sale_price = self.get_price(item.find("ul").find("span").find_next("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class PazzoCrawler(BaseCrawler):
    id = 56
    name = "pazzo"
    prefix_urls = [
        "https://www.pazzo.com.tw/zh-tw/category/tops?P=",
        "https://www.pazzo.com.tw/zh-tw/category/bottoms?P=",
        "https://www.pazzo.com.tw/zh-tw/category/onepiece?P=",
        "https://www.pazzo.com.tw/zh-tw/category/darlingme?P=",
        "https://www.pazzo.com.tw/zh-tw/category/accessories?P=",
    ]

    def parse(self):
        for prefix in self.prefix_urls:
            for i in range(1, page_Max):
                urls = [f"{prefix}{i}"]
                for url in urls:
                    print(url)
                    response = requests.get(url, headers=self.headers)
                    soup = BeautifulSoup(response.text, features="html.parser")
                    items = soup.find_all("li", {"class": "item"})
                    if not items:
                        print(url, "break")
                        break
                    self.result.extend([self.parse_product(item) for item in items])
                else:
                    continue
                break

    def parse_product(self, item):
        title = item.find("p", {"class": "item__name"}).text
        link = item.find("a").get("href")
        link = f"https://www.pazzo.com.tw{link}"
        link_id = stripID(link, "/n/")
        link_id = b_stripID(link_id, "?")
        image_url = item.find("img").get("src")
        if (item.find("p", {"class": "item__price"}).find("span").find_next_sibling("span") != None):
            original_price = self.get_price(item.find("p", {"class": "item__price"}).find("span").text)
            sale_price = self.get_price(item.find("p", {"class": "item__price"}).find(
                "span").find_next_sibling("span").text)
        else:
            original_price = ""
            sale_price = self.get_price(item.find("p", {"class": "item__price"}).find("span").text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class KiyumiCrawler(BaseCrawler):
    id = 81
    name = "kiyumi"
    prefix_urls = [
        "https://www.kiyumishop.com/catalog.php?m=73&s=0&t=0&sort=&page=",
        "https://www.kiyumishop.com/catalog.php?m=75&s=0&t=0&sort=&page=",
        "https://www.kiyumishop.com/catalog.php?m=76&s=0&t=0&sort=&page=",
        "https://www.kiyumishop.com/catalog.php?m=80&s=0&t=0&sort=&page=",
        "https://www.kiyumishop.com/catalog.php?m=81&s=0&t=0&sort=&page=",
        "https://www.kiyumishop.com/catalog.php?m=80&s=0&t=0&sort=&page=",
    ]

    def parse(self):
        for prefix in self.prefix_urls:
            for i in range(1, page_Max):
                urls = [f"{prefix}{i}"]
                for url in urls:
                    print(url)
                    response = requests.get(url, headers=self.headers)
                    soup = BeautifulSoup(response.text, features="html.parser")
                    items = soup.find("section", {"class": "cataList"}).find_all("li")
                    if not items:
                        print(url, "break")
                        break
                    self.result.extend([self.parse_product(item) for item in items])
                else:
                    continue
                break

    def parse_product(self, item):
        title = item.find("span", {"class": "info"}).text
        link = item.find("a").get("href")
        link_id = stripID(link, "id=")
        link = f"https://www.kiyumishop.com/{link}"
        image_url = item.find("img").get("src")
        original_price = ""
        sale_price = self.get_price(item.find("span", {"class": "price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class MeierqCrawler(BaseCrawler):
    id = 57
    name = "meierq"
    prefix_urls = [
        "https://www.meierq.com/zh-tw/category/bottomclothing?P=",
        "https://www.meierq.com/zh-tw/category/jewelry?P=",
        "https://www.meierq.com/zh-tw/category/outerclothing?P=",
        "https://www.meierq.com/zh-tw/category/accessories?P=",
    ]

    def parse(self):
        for prefix in self.prefix_urls:
            for i in range(1, page_Max):
                urls = [f"{prefix}{i}"]
                for url in urls:
                    print(url)
                    response = requests.get(url, headers=self.headers)
                    soup = BeautifulSoup(response.text, features="html.parser")
                    items = soup.find("ul", {"class": "items"}).find_all("li")
                    if not items:
                        print(url, "break")
                        break
                    self.result.extend([self.parse_product(item) for item in items])
                else:
                    continue
                break

    def parse_product(self, item):
        try:
            title = item.find("span", {"class": "title-tw"}).text
            link = item.find("a").get("href")
            link = f"https://www.meierq.com{link}"
            link_id = stripID(link, "/n/")
            link_id = b_stripID(link_id, "?")
            image_url = item.find("img").get("src")
        except:
            return
        try:
            original_price = self.get_price(item.find("p", {"class": "price"}).find("span").text)
            sale_price = self.get_price(item.find("p", {"class": "price"}).find("span").find_next("span").text)
            if (int(sale_price) < 50):
                sale_price = original_price
                original_price = ""
        except:
            original_price = ""
            sale_price = self.get_price(item.find("p", {"class": "price"}).find("span").text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class MercciCrawler(BaseCrawler):
    id = 64
    name = "mercci"
    base_url = "https://www.mercci22.com"

    def parse(self):
        urls = [f"{self.base_url}/zh-tw/all?P={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("ul", {"class": "items"}).find_all("li")
            print(url)
            if not items:
                print(url, "break")
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            title = item.find("div", {"class": "pdname"}).find("a").text
            link = item.find("a").get("href")
            link_id = stripID(link, "c=")
            link = f"{self.base_url}{link}"
            image_url = item.find("img").get("src")
        except:
            return
        try:
            original_price = self.get_price(item.find("div", {"class": "price"}).find("span").text)
            sale_price = self.get_price(item.find("div", {"class": "price"}).contents[2])
        except:
            original_price = ""
            sale_price = self.get_price(item.find("p", {"class": "price"}).find("span").text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class CozyfeeCrawler(BaseCrawler):
    id = 48
    name = "cozyfee"
    base_url = "https://www.cozyfee.com"

    def parse(self):

        urls = [f"https://www.cozyfee.com/product.php?page={i}&cid={j}" for j in range(2, 10) for i in range(1, 5)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("div", {"class": "wrapper-pdlist"}).find_all("li")
            # print(items)
            if not items:
                print(url, "break")
                return
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "overflow-sold-out"})):
            return
        try:
            title = item.find("div", {"class": "prod-name"}).find("a").text
            link = item.find("a").get("href")
            link_id = stripID(link, "pid=")
            image_url = item.find("img").get("data-original")
        except:
            return
        try:
            original_price = self.get_price(item.find("div", {"class": "prod-price"}).find("del").text)
            sale_price = self.get_price(item.find("div", {"class": "prod-price"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "prod-price"}).find("span").text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class MojpCrawler(BaseCrawler):
    id = 102
    name = "mojp"
    base_url = "https://www.mojp.com.tw"

    def parse(self):
        urls = [
            f"https://www.mojp.com.tw/product.php?page={i}&cid={j}#prod_list" for j in range(3, 10) for i in range(1, 10)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                if not soup.find("ul", {"class": "pagination"}).find("li", {"class": "active"}).find_next_sibling("li"):
                    continue
            except:
                if not soup.find("ul", {"class": "pagination"}):
                    continue
            items = soup.find_all("div", {"class": "thumbnail"})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "overflow-sold-out"})):
            return
        try:
            title = item.find("div", {"class": "prod-name"}).find("a").text.strip()
            link = item.find("a").get("href")
            link_id = stripID(link, "pid=")
            image_url = item.find("img").get("data-original")
        except:
            return
        try:
            original_price = self.get_price(item.find("div", {"class": "prod-price"}).find("del").text)
            sale_price = self.get_price(item.find("div", {"class": "prod-price"}).find("span").text)
        except:
            try:
                original_price = ""
                sale_price = self.get_price(item.find("div", {"class": "prod-price"}).text)
            except:
                print(title)
                return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class MiharaCrawler(BaseCrawler):
    id = 107
    name = "mihara"
    base_url = "https://www.mihara.com.tw"

    def parse(self):
        urls = [f"{self.base_url}/product.php?page={i}&cid=1" for i in range(1, page_Max)]
        flag = False
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-card"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):

        title = item.find("div", {"class": "card-title"}).find("a").text.strip()
        if(item.find("div", {"class": "overflow-sold-out"})):
            print(title)
            return
        link = item.find("a").get("href")
        link_id = stripID(link, "pid=")
        image_url = item.find("img").get("data-original")

        try:
            original_price = self.get_price(item.find("span", {"class": "product-price"}).text)
            sale_price = self.get_price(item.find("span", {"class": "product-price"}).find_next("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "product-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class UnefemmeCrawler(BaseCrawler):
    id = 304
    name = "unefemme"
    base_url = "https://www.unefemme.com.tw"

    def parse(self):
        urls = [f"{self.base_url}/product.php?page={i}&cid=7" for i in range(1, page_Max)]
        flag = False
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-card"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):

        title = item.find("div", {"class": "card-title"}).find("a").text.strip()
        if(item.find("div", {"class": "overflow-sold-out"})):
            print(title)
            return
        link = item.find("a").get("href")
        link_id = stripID(link, "pid=")
        image_url = item.find("img").get("data-original")

        try:
            original_price = self.get_price(item.find("span", {"class": "product-price"}).text)
            sale_price = self.get_price(item.find("span", {"class": "product-price"}).find_next("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "product-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class PennyncoCrawler(BaseCrawler):
    id = 303
    name = "pennynco"
    base_url = "https://www.pennynco.com.tw"

    def parse(self):
        urls = [f"{self.base_url}/product.php?page={i}&cid=34#prod_list" for i in range(1, 6)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "thumbnail"})
            print(url)
            if not soup.find("ul", {"class": "pagination"}).find("li", {"class": "active"}).find_next_sibling("li"):
                continue
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "overflow-sold-out"})):
            return
        title = item.find("div", {"class": "prod-name"}).find("a").text.strip()
        link = item.find("a").get("href")
        link_id = stripID(link, "pid=")
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find("div", {"class": "prod-price"}).find("del").text)
            sale_price = self.get_price(item.find("span", {"class": "text-danger"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "prod-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class MollyCrawler(BaseCrawler):
    id = 396
    name = "molly"
    base_url = "https://www.molly-m.com"

    def parse(self):
        urls = [f"{self.base_url}/product.php?page={i}&cid=1#prod_list" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "thumbnail"})
            if len(items) < 80:
                print(len(items))
                if flag == True:
                    print("break")
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "overflow-sold-out"})):
            return
        title = item.find("div", {"class": "prod-name"}).find("a").text.strip()
        link = item.find("a").get("href")
        link_id = stripID(link, "pid=")
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find("div", {"class": "prod-price"}).find("del").text)
            sale_price = self.get_price(item.find("span", {"class": "text-danger"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "prod-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class SomethingmeCrawler(BaseCrawler):
    id = 407
    name = "somethingme"
    base_url = "https://www.something-me.com"

    def parse(self):
        urls = [f"{self.base_url}/product.php?page={i}&cid=145" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "thumbnail"})
            if len(items) < 40:
                print(len(items))
                if flag == True:
                    print("break")
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "overflow-sold-out"})):
            return
        title = item.find("div", {"class": "prod-name"}).find("a").text.strip()
        link = item.find("a").get("href")
        link_id = stripID(link, "pid=")
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find("div", {"class": "prod-price"}).find("del").text)
            sale_price = self.get_price(item.find("span", {"class": "text-danger"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "prod-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class CycomyuCrawler(BaseCrawler):
    id = 432
    name = "cycomyu"
    base_url = "https://cycomyu2021.gogoshopapp.com"

    def parse(self):
        url = f"{self.base_url}/categories?page=-1"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = soup.find_all("div", {"class": "product-inner"})
        if not items:
            print(url, "break")
            return
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):

        title = item.find("h3").find("a").get("title")
        link = f'{self.base_url}{item.find("a").get("href")}'
        link_id = item.find("a").get("data-gtm-impression")
        image_url = item.find("img").get("src")

        try:
            original_price = self.get_price(item.find("div", {"class": "price"}).find("del").text)
            sale_price = self.get_price(item.find("div", {"class": "price"}).find("ins").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class NanaCrawler(BaseCrawler):
    id = 66
    name = "nana"
    base_url = "https://www.2nana.tw"

    def parse(self):
        url = f"{self.base_url}/product.php?page=1&cid=1#prod_list"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = soup.find_all("div", {"class": "thumbnail"})
        print(url)
        # print(items)
        if not items:
            print(url, "break")
            return
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("div", {"class": "overflow-sold-out"})):
            return
        try:
            title = item.find("div", {"class": "prod-name"}).find("a").text.strip()
            link = item.find("a").get("href")
            link_id = stripID(link, "pid=")
            image_url = item.find("img").get("data-original")
        except:
            return
        try:
            original_price = self.get_price(item.find("div", {"class": "prod-price"}).find("del").text)
            sale_price = self.get_price(item.find("div", {"class": "prod-price"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "prod-price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 62_Mouggan
class MougganCrawler(BaseCrawler):
    id = 62
    name = "mouggan"
    prefix_urls = [
        "https://www.mouggan.com/zh-tw/category/tops?P=",
        "https://www.mouggan.com/zh-tw/category/bottoms?P=",
        "https://www.mouggan.com/zh-tw/category/outerwear?P=",
        "https://www.mouggan.com/zh-tw/category/dress-jumpsuits?P=",
        "https://www.mouggan.com/zh-tw/category/suits?P=",
    ]

    def parse(self):
        for prefix in self.prefix_urls:
            for i in range(1, 3):
                urls = [f"{prefix}{i}"]
                for url in urls:
                    print(url)
                    response = requests.get(url, headers=self.headers)
                    soup = BeautifulSoup(response.text, features="html.parser")
                    items = soup.find_all("div", {"class": "item-box"})
                    if not items:
                        print(url, "break")
                        break
                    self.result.extend([self.parse_product(item) for item in items])
                else:
                    continue
                break

    def parse_product(self, item):
        title = item.find("a", {"class": "item-name"}).text
        link = item.find("a").get("href")
        link = f"https://www.mouggan.com{link}"
        link_id = stripID(link, "c=")
        image_url = item.find("img").get("src")
        original_price = ""
        sale_price = self.get_price(item.find("div", {"class": "item-price"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class LurehsuCrawler(BaseCrawler):
    id = 59
    name = "lurehsu"
    base_url = "https://www.lurehsu.com"

    def parse(self):
        urls = [f"{self.base_url}/zh-TW/lure/productList?item1=00&item2=16&page={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-item"})
            print(url)
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "pdlist_img_desc"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = stripID(link, "SaleID=")
        link_id = b_stripID(link_id, "&Color")
        image_url = item.find("img").get("src")
        original_price = ""
        sale_price = self.get_price(item.find("p", {"class": "pdcnt_info_price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class SquarebearCrawler(BaseCrawler):
    id = 101
    name = "lurehsu"
    base_url = "https://www.squarebearthelabel.com"

    def parse(self):
        urls = [f"{self.base_url}/zh-tw/all?P={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "item-box"})
            print(url)
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "soldout-mask"}):
            return
        title = item.find('h3').text
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = stripID(link, "c=")
        image_url = item.find("img").get("src")
        original_price = ""
        sale_price = self.get_price(item.find("span", {"class": "sell-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class GirlsmondayCrawler(BaseCrawler):
    id = 301
    name = "girlsmonday"
    base_url = "https://www.girlsmonday.com.tw"

    def parse(self):
        urls = [f"{self.base_url}/productlist?Page={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("figcaption", {"class": "grid-item"})
            print(url)
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("span", {"class": "pd_title1"}).text.strip()
        link = item.find("a").get("href")
        pattern = "SaleID=(.*?)&"
        link_id = re.search(pattern, link).group(1)
        link = f"{self.base_url}/{link}"
        image_url = item.find("source").get("srcset")
        try:
            original_price = self.get_price(item.find("span", {"class": "pd_defaultprice"}).text)
            sale_price = self.get_price(item.find("span", {"class": "pd_defaultprice"}).find_next('span').text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "pd_price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class GenquoCrawler(BaseCrawler):
    id = 82
    name = "genquo"
    base_url = "https://www.genquo.com"

    def parse(self):
        urls = [f"{self.base_url}/zh-tw/category/women?P={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("li", {"class": "item"})
            print(url)
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "item__name"}).find("a").text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = stripID(link, "/n/")
        link_id = b_stripID(link_id, "?")
        image_url = item.find("img").get("src")
        original_price = ""
        sale_price = self.get_price(item.find("p", {"class": "item__price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class MiyukiCrawler(BaseCrawler):
    id = 97
    name = "miyuki"
    base_url = "https://www.miyukiselect.com"

    def parse(self):
        urls = [f"{self.base_url}/zh-tw/category/ALL-ITEMS?P={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "item-detail"})
            if not items:
                print(url)
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a", {"class": "item-name"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = stripID(link, "c=")
        image_url = item.find("div", {"class": "like-counter"}).get("data-tracingdata")
        image_url = stripID(image_url, "product_image_url':'")
        image_url = b_stripID(image_url, "','product_url")
        try:
            original_price = self.get_price(item.find("span", {"class": "origin-price"}).text)
        except:
            original_price = ""
        sale_price = self.get_price(item.find("span", {"class": "sell-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class QueenshopCrawler(BaseCrawler):
    id = 42
    name = "queenshop"
    base_url = "https://www.queenshop.com.tw/zh-TW/QueenShop/"

    def parse(self):
        urls = [f"{self.base_url}ProductList?item1=01&item2=all&Page={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find("ul", {"class": "items-list list-array-2"}).find_all("li")
            except:
                print(url)
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        title = item.find("p").text
        link = item.find("a").get("href")
        link_id = stripID(link, "ID=")
        link_id = b_stripID(link_id, '&Page')
        link = f"{self.base_url}{link}"
        image_url = item.find("img").get("data-src")
        try:
            sale_price = self.get_price(item.find("span", {"name": "p_sale_d"}).text)
            original_price = self.get_price(item.find("span", {"name": "p_original_d"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"name": "p_original_d"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class PixelcakeCrawler(BaseCrawler):
    id = 96
    name = "pixelcake"
    base_url = "https://www.pixelcake.com.tw"

    def parse(self):
        urls = [f"{self.base_url}/zh-tw/category/ALL?P={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "item-detail"})
            if not items:
                print(url)
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a", {"class": "item-name"}).text.strip()
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.find("div", {"class": "like-counter"}).get("data-custommarketid")
        image_url = item.find("div", {"class": "like-counter"}).get("data-tracingdata")
        image_url = stripID(image_url, "product_image_url':'")
        image_url = b_stripID(image_url, "','product_url")
        try:
            original_price = self.get_price(item.find("span", {"class": "origin-price"}).text)
        except:
            original_price = ""
        sale_price = self.get_price(item.find("span", {"class": "sell-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

# 100_NAB
class NabCrawler(BaseCrawler):
    id = 100
    name = "nab"
    prefix_urls = ["https://www.nab.com.tw/product-list.ftl?rMinPrice=340&rMaxPrice=664&mid=02-01&p=",
                   "https://www.nab.com.tw/product-list.ftl?mid=02-02&p=",
                   "https://www.nab.com.tw/product-list.ftl?mid=02-03&p=",
                   "https://www.nab.com.tw/product-list.ftl?rMinPrice=390&rMaxPrice=880&mid=02-04&p=",
                   "https://www.nab.com.tw/product-list.ftl?mid=02-05&p=",
                   "https://www.nab.com.tw/product-list.ftl?mid=02-06&p=", ]
    urls = [
        f"{prefix}{i}" for prefix in prefix_urls for i in range(1, 5)]

    def parse(self):
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "card flaps-noPanelBorder"})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "cardName"}).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("a").get("data-product-goodscode")
        image_url = f"https://www.nab.com.tw/{item.find('a').find('img').get('data-src')}"
        if (item.find("span", {"class": "del"})):
            original_price = self.get_price(item.find("div", {"class": "caption"}).find("span").text)
        else:
            original_price = ""
        sale_price = self.get_price(item.find("a").get("data-product-price"))
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 53_KERINA
class KerinaCrawler(BaseCrawler):
    id = 53
    name = "kerina"
    base_url = "https://www.kerina.com.tw"

    def parse(self):
        url = f"{self.base_url}/Catalog/ALLPRODUCT"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        try:
            items = soup.find_all("div", {"class": "product-list"})
        except:
            return
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("span", {"class": "Sold_Out OutOfStock"})):
            return
        title = item.find("div", {"class": "name"}).text
        link = item.find("a").get("href")
        link_id = stripID(link, "/Product/")
        locate = link_id.find("?")
        link_id = link_id[:locate]
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find(
                "div", {"class": "price"}).find('span').text)
            sale_price = self.get_price(
                item.find("div", {"class": "price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)

class WhoiannCrawler(BaseCrawler):
    id = 221
    name = "whoiann"
    base_url = "https://www.whoiann.com"

    def parse(self):
        url = f"{self.base_url}/Catalog/All"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        try:
            items = soup.find_all("div", {"class": "product-list"})
        except:
            return
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("span", {"class": "Sold_Out OutOfStock"})):
            return
        title = item.find("div", {"class": "name"}).text
        link = item.find("a").get("href")
        link_id = item.get("id").replace("product-list-", "")
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find("span", {"class": "no-"}).text)
            sale_price = self.get_price(item.find("div", {"class": "price"}).contents[1])
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class KisssilverCrawler(BaseCrawler):
    id = 424
    name = "kisssilver"
    base_url = "https://kisssilver.tw"

    def parse(self):
        urls = [f"{self.base_url}/Category/search.html?page={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            print(url)
            items = soup.find_all("div", {"class": "list-one"})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("span", {"class": "Sold_Out OutOfStock"})):
            return
        title = item.find("div", {"class": "name"}).text
        link = item.find("a").get("href")
        link_id = stripID(link, "prodid=")
        link = f"{self.base_url}{link}"
        try:
            image_url = item.find("img").get("data-src")
        except:
            image_url = item.find("source").get("src")
        image_url = f"{self.base_url}{image_url}"
        try:
            original_price = self.get_price(item.find("div", {"class": "price"}).find("span").text)
            sale_price = self.get_price(item.find("div", {"class": "price"}).contents[2])
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "price"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class NovyyCrawler(BaseCrawler):
    id = 355
    name = "novyy"
    base_url = "https://www.novyy.com.tw"

    def parse(self):
        url = f"{self.base_url}/Catalog/Shop"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        try:
            items = soup.find_all("li", {"class": "product-list"})
        except:
            return
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("span", {"class": "item_mode"})):
            return
        title = item.find("img").get("alt")
        link = item.find("a").get("href")
        link_id = item.get("id").replace("product-list-", "")
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find("span", {"class": "info"}).find("span").text)
            sale_price = self.get_price(item.find("span", {"class": "sale"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("span", {"class": "info"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class MyameCrawler(BaseCrawler):
    id = 356
    name = "myame"
    base_url = "https://www.myame.com.tw"

    def parse(self):
        url = f"{self.base_url}/Catalog/women"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        try:
            items = soup.find_all("li", {"class": "product-list"})
        except:
            return
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("span", {"class": "item_mode"})):
            return
        title = item.find("img").get("alt")
        link = item.find("a").get("href")
        link_id = item.get("id").replace("product-list-", "")
        link_id = b_stripID(link_id, "-")
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find("span", {"class": "info"}).find("span").text)
            sale_price = self.get_price(item.find("span", {"class": "sale"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("span", {"class": "info"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class SuitangtangCrawler(BaseCrawler):
    id = 74
    name = "suitangtang"
    base_url = "https://www.suitangtang.com"

    def parse(self):
        url = f"{self.base_url}/Catalog/WOMAN"
        response = requests.request("POST", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")

        items = soup.find_all("div", {"class": "product-list"})

        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("img").get("alt")
        link = item.find("a").get("href")
        link_id = item.get("id")
        link_id = link_id.replace("product-list-", "")
        link_id = b_stripID(link_id, "-")
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find("div", {"class": "price"}).contents[0].text)
            sale_price = self.get_price(item.find("div", {"class": "price"}).contents[1])
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "price"}).contents[0])

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 63_JENDES
class JendesCrawler(BaseCrawler):
    id = 63
    name = "jendes"
    base_url = "https://www.jendesstudio.com/shop"

    def parse(self):
        urls = [
            f"{self.base_url}?c=de8eed41-acbf-4da7-a441-e6028d8b28c9&page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all(
                "div", {"class": "col-xl-3 col-lg-3 col-mb-3 col-sm-6 col-xs-6 squeeze-padding"})
            if not items:
                print(url)
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):

        title = item.find("h3", {"class": "product-title"}).find("a").text
        link = item.find("a").get("href")
        link_id = stripID(link, "/product/")
        link_id = b_stripID(link_id, "?c=")
        image_url = item.find("img").get("data-src")
        original_price = ""
        sale_price = self.get_price(
            item.find("div", {"class": "float-left"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 65_SIVIR
class SivirCrawler(BaseCrawler):
    id = 65
    name = "sivir"
    base_url = "https://www.sivir.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/new-all-所有?page={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product col-lg-3 col-sm-4 col-6"})
            if not items:
                print(url)
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "product_title"}).find(
            "a").get("data-name")
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        link_id = stripID(link_id, "/products/")
        image_url = f"https:{item.find('img').get('data-src')}"
        original_price = ""
        sale_price = self.get_price(
            item.find("div", {"class": "product_price"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class DfinaCrawler(BaseCrawler):
    id = 394
    name = "dfina"
    base_url = "https://www.dfina.com"

    def parse(self):
        urls = [
            f"{self.base_url}/all?limit=100&page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "inner"})
            if not items:
                print(url)
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("span", {"class": "label stock-status-label"}):
            return
        title = item.find("a").get("title")
        link = item.find("a").get("href")
        link_id = item.find("select").get('data-productid')

        image_url = f"https:{item.find('img').get('src')}"
        if 'max-260' in image_url:
            image_url = image_url.replace('max-260', 'max-w-1024')
        else:
            image_url = f"https:{item.find('img').get('data-src')}"
            image_url = image_url.replace('max-260', 'max-w-1024')
        try:
            original_price = self.get_price(item.find("span", {"class": "price-old"}).text)
            sale_price = self.get_price(item.find("span", {"class": "price-new"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "price-label"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class ThedailyCrawler(BaseCrawler):
    id = 403
    name = "thedaily"
    base_url = "https://www.thedailyxx.com"

    def parse(self):
        urls = [
            f"{self.base_url}/%E5%85%A8%E9%83%A8%E5%95%86%E5%93%81?limit=60&page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "inner"})
            if not items:
                print(url)
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("span", {"class": "label stock-status-label"}):
            return
        title = item.find("a").get("title")
        link = item.find("a").get("href")
        link_id = item.find("select").get('data-productid')

        image_url = f"https:{item.find('img').get('src')}"
        if '-cr-280x280' in image_url:
            image_url = image_url.replace('-cr-280x280', '-max-w-1024')
        else:
            image_url = f"https:{item.find('img').get('data-flipper')}"
            image_url = image_url.replace('-cr-280x280', '-max-w-1024')
        try:
            original_price = self.get_price(item.find("span", {"class": "price-old"}).text)
            sale_price = self.get_price(item.find("span", {"class": "price-new"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "price-label"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class OliolioliCrawler(BaseCrawler):
    id = 419
    name = "oliolioli"
    base_url = "https://oliolioli.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/all?page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "inner"})
            if not items:
                print(url)
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("span", {"class": "label stock-status-label"}):
            return
        title = item.find("a").get("title")
        link = item.find("a").get("href")
        link_id = item.find("select").get('data-productid')

        image_url = f"https:{item.find('img').get('src')}"
        if '-cr-270x270' in image_url:
            image_url = image_url.replace('-cr-270x270', '-max-w-1024')
        else:
            image_url = f"https:{item.find('img').get('data-src')}"
            image_url = image_url.replace('-cr-270x270', '-max-w-1024')
        try:
            original_price = self.get_price(item.find("span", {"class": "price-old"}).text)
            sale_price = self.get_price(item.find("span", {"class": "price-new"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "price-label"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class SpotlightCrawler(BaseCrawler):
    id = 298
    name = "spotlight"
    base_url = "https://www.s-spotlight.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, 12)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "grid-link__title"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        link_id = stripID(link_id, "/products/")
        image_url = item.find('img').get('src')
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        if len(sale_price) == 1:
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)

class PreuniCrawler(BaseCrawler):
    id = 296
    name = "preuni"
    base_url = "https://www.preuni-tw.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link text-center"})
            if len(items) < 72:
                print(len(items))
                if flag == True:
                    print("break")
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("span", {"class": "badge badge--sold-out"}):
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        link = f'{self.base_url}{item.find("a").get("href")}'
        link_id = item.find("div", {"class": "addToCartList btn large--hide"}).get("data-id")
        image_url = item.find('img').get('src')
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find_next_sibling("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        if len(sale_price) == 1:
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class ClothesCrawler(BaseCrawler):
    id = 421
    name = "clothes"
    base_url = "https://www.clothes153.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link text-center"})
            if len(items) < 72:
                print(len(items))
                if flag == True:
                    print("break")
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("span", {"class": "badge badge--sold-out"}):
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        image_url = item.find('img').get('src')
        pattern = "\/i\/(.+)\."
        link_id = re.search(pattern, image_url).group(1)

        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find_next_sibling("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        if len(sale_price) == 1:
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)

class FudgeCrawler(BaseCrawler):
    id = 347
    name = "fudge"
    base_url = "https://www.fudgetw.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("span", {"class": "badge badge--sold-out"}):
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        link_id = stripID(link_id, "/products/")
        image_url = item.find('img').get('src')
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        if len(sale_price) == 1:
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class LeviaCrawler(BaseCrawler):
    id = 375
    name = "levia"
    base_url = "https://www.levia-pc.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("span", {"class": "badge badge--sold-out"}):
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        link = f'{self.base_url}{item.find("a").get("href")}'
        image_url = item.find('img').get('src')
        try:
            link_id = item.find("div").get("data-id")
        except:
            pattern = "\/i\/(.+)\."
            link_id = re.search(pattern, image_url).group(1)

        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        if len(sale_price) == 1:
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)

class RewearingCrawler(BaseCrawler):
    id = 299
    name = "rewearing"
    base_url = "https://www.rewearing.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all-product?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("li", {"class": "grid__item"})
            if len(items) < 72:
                if flag == True:
                    print("break")
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("span", {"class": "badge badge--sold-out"}):
            return
        title = item.find("span", {"class": "card-information__text"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        link_id = stripID(link_id, "/products/")
        image_url = item.find('img').get('src')
        original_price = ""
        sale_price = self.get_price(item.find("span", {"class": "money"}).text).replace(".00", "")
        if len(sale_price) == 1:
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class AnderlosCrawler(BaseCrawler):
    id = 235
    name = "anderlos"
    base_url = "https://www.anderlos.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, 9)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            # print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        link_id = item.find("div").get("data-id")
        image_url = item.find('img').get('data-src')
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class IlymCrawler(BaseCrawler):
    id = 393
    name = "ilym"
    base_url = "https://ilymcollection.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            # print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('data-src')
        pattern = "\/i\/(.+)\."
        link_id = re.search(pattern, image_url).group(1)
        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class Ss33Crawler(BaseCrawler):
    id = 395
    name = "ss33"
    base_url = "https://www.ss33.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('src')
        pattern = "\/i\/(.+)\."
        link_id = re.search(pattern, image_url).group(1)
        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class ShiauzCrawler(BaseCrawler):
    id = 400
    name = "shiauz"
    base_url = "https://www.shiauz.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all-1?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('data-src')
        pattern = "\/i\/(.+)\."
        link_id = re.search(pattern, image_url).group(1)
        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class BigpotatoCrawler(BaseCrawler):
    id = 398
    name = "bigpotatodenim"
    base_url = "https://www.bigpotatodenim.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('data-src')
        pattern = "\/i\/(.+)\."
        link_id = re.search(pattern, image_url).group(1)
        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class HuestudiosCrawler(BaseCrawler):
    id = 404
    name = "huestudios"
    base_url = "https://huestudios.easy.co"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('data-src')
        pattern = "\/i\/(.+)\."
        link_id = re.search(pattern, image_url).group(1)
        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class MornmoodCrawler(BaseCrawler):
    id = 397
    name = "mornmood"
    base_url = "https://mornmood.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/%E6%89%80%E6%9C%89%E5%95%86%E5%93%81?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('src')
        pattern = "\/i\/(.+)\."
        link_id = re.search(pattern, image_url).group(1)
        link = f"{self.base_url}{prefix_link}"
        original_price = ""
        sale_price = self.get_price(
            item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class IspotyellowCrawler(BaseCrawler):
    id = 413
    name = "ispotyellow"
    base_url = "https://ispotyellow.easy.co"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link text-center"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('a', {"class": "grid-link__image-centered"}).find("img").get('src')
        pattern = "\/i\/(.+)\."
        try:
            link_id = re.search(pattern, image_url).group(1)
        except:
            return  # 客訂
        link = f"{self.base_url}{prefix_link}"
        original_price = ""
        sale_price = self.get_price(
            item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class HuitcoCrawler(BaseCrawler):
    id = 386
    name = "huitco"
    base_url = "https://www.huitco.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('src')
        try:
            link_id = item.find("div").get("data-id")
        except:
            pattern = "\/i\/(.+)\."
            link_id = re.search(pattern, image_url).group(1)

        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class ClubdianaCrawler(BaseCrawler):
    id = 425
    name = "clubdiana"
    base_url = "https://www.clubdianataiwan2021.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('src')
        try:
            link_id = item.find("div").get("data-id")
        except:
            pattern = "\/i\/(.+)\."
            link_id = re.search(pattern, image_url).group(1)

        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class FigwooCrawler(BaseCrawler):
    id = 426
    name = "figwoo"
    base_url = "https://www.figwoo.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('src')
        try:
            link_id = item.find("div").get("data-id")
        except:
            pattern = "\/i\/(.+)\."
            link_id = re.search(pattern, image_url).group(1)

        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class AphroCrawler(BaseCrawler):
    id = 433
    name = "aphro"
    base_url = "https://www.aphro723.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('src')
        try:
            link_id = item.find("div").get("data-id")
        except:
            pattern = "\/i\/(.+)\."
            link_id = re.search(pattern, image_url).group(1)

        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
            sale_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find_next_sibling("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class VvvlandCrawler(BaseCrawler):
    id = 436
    name = "vvvland"
    base_url = "https://www.vvvland.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img', {"class": "product-featured_image lozad"}).get('data-src')
        try:
            link_id = item.find("div").get("data-id")
        except:
            pattern = "\/i\/(.+)\."
            link_id = re.search(pattern, image_url).group(1)

        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class VstoreCrawler(BaseCrawler):
    id = 437
    name = "vstore2012"
    base_url = "https://www.vstore2012.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img', {"class": "product-featured_image"}).get('src')
        try:
            link_id = item.find("div").get("data-id")
        except:
            pattern = "\/i\/(.+)\."
            link_id = re.search(pattern, image_url).group(1)

        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)

class Vior2015Crawler(BaseCrawler):
    id = 443
    name = "vior2015"
    base_url = "https://www.vior2015.store"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('data-src')
        try:
            link_id = item.find("div").get("data-id")
        except:
            pattern = "\/i\/(.+)\."
            link_id = re.search(pattern, image_url).group(1)

        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class SymbolictrueCrawler(BaseCrawler):
    id = 447
    name = "symbolictrue"
    base_url = "https://www.symbolictrue.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        if (item.find("span", {"class": "badge badge--sold-out"})):
            print(item.find("p", {"class": "grid-link__title"}).text)
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        prefix_link = item.find("a").get("href")
        image_url = item.find('img').get('src')
        pattern = "\/i\/(.+)\."
        link_id = re.search(pattern, image_url).group(1)

        link = f"{self.base_url}{prefix_link}"
        if item.find("s", {"class": "grid-link__sale_price"}):
            sale_price = self.get_price(
                item.find("span", {"class": "money"}).find_next("span").text)
            sale_price = sale_price[:-3]
            original_price = self.get_price(
                item.find("s", {"class": "grid-link__sale_price"}).find("span").text).replace(".00", "")
        else:
            original_price = ""
            sale_price = self.get_price(
                item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class IruitwCrawler(BaseCrawler):
    id = 255
    name = "iruitw"
    base_url = "https://www.iruitw.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?limit=72&page={i}" for i in range(1, page_Max)]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-link"})
            if len(items) < 72:
                if flag == True:
                    print("break")
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("span", {"class": "badge badge--sold-out"}):
            return
        title = item.find("p", {"class": "grid-link__title"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        link_id = stripID(link_id, "/products/")
        image_url = item.find('img').get('src')
        original_price = ""
        sale_price = self.get_price(
            item.find("p", {"class": "grid-link__meta"}).find("span").text).replace(".00", "")
        if len(sale_price) == 1:
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)

class OhlalaCrawler(BaseCrawler):
    id = 410
    name = "ohlala"
    base_url = "https://gateway.1shop.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/gateway.php?a=view&m=website&WebPageID=OG2xp9RzW069aWMwJNgV3lje&page={i}&Token=&fbp=fb.2.1638889210454.1335955201&fbc=&pageTitle=Ohlala%E9%A3%BE%E5%93%81%20-%20%E5%AE%98%E7%B6%B2&pageId=DQ&FBPageID=0&FBPixelUrl=https%3A%2F%2Fwww.ohlala.com.tw%2Fall%3Fp%3D0&_=1638891716761" for i in range(0, 10)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            data_json = json.loads(response.text)
            items = data_json['data']['product']
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print("item:", item)
        # print(type(item))
        title = item.get('genP')[0].get('ProductName')
        link = f"https://www.ohlala.com.tw/{item.get('genP')[0].get('ProductSKU')}".lower()
        link_id = item.get('genP')[0].get('ProductID')
        image_url = item.get('genP')[0].get('MediaFile').get('OriginalFile')
        original_price = item.get('genP')[0].get('PriceBase')
        sale_price = item.get('genP')[0].get('PriceSpecial')

        return Product(title, link, link_id, image_url, original_price, sale_price)


class TheshapeCrawler(BaseCrawler):
    id = 427
    name = "theshape"
    base_url = "https://theshape.quickper.com"
    base_image = "https://cdn.quickper.com"

    def parse(self):
        url = f"{self.base_url}/api/products?offset=0&limit=1000"
        response = requests.request("GET", url, headers=self.headers)
        data_json = json.loads(response.text)
        items = data_json['data']
        print(url)
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        print(item)
        title = item['name']
        link = f"{self.base_url}/product/{item['id']}/MzI"
        link_id = item['id']
        image_url = f"{self.base_image}/{item['media']}"
        if item['specialPrice'] != 0:
            original_price = item['price']
            sale_price = item['specialPrice']
        else:
            original_price = ""
            sale_price = item['price']

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 83_POTATOCHICKS
class PotatochicksCrawler(BaseCrawler):
    id = 83
    name = "potatochicks"
    base_url = "https://www.potatochicks.tw/Shop/"

    def parse(self):
        urls = [
            f"{self.base_url}itemList.aspx?m=2&o=0&sa=0&smfp={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find_all(
                    "div", {"class": "itemListDiv"})
            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "itemListMerName"}).find(
            "a").text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        link_id = b_stripID(link_id, "&m")
        link_id = stripID(link_id, "mNo1=")
        image_url = item.find("a").find("img").get("src")
        try:
            original_price = self.get_price(
                item.find("div", {"class": "itemListMoney itemListOriMoney"}).find("span").text)
            sale_price = self.get_price(
                item.find("div", {"class": "itemListMoney itemListSpeacilMoney"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "itemListMoney"}).find("span").text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class CerealCrawler(BaseCrawler):
    id = 33
    name = "cereal"
    base_url = "https://www.cerealoutfit.com/"

    def parse(self):
        urls = [
            f"{self.base_url}product-tag/clothing/page/{i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find("div", {
                    "class": "site-content shop-content-area col-sm-12 content-with-products description-area-before"}).find_all("div", {"class": "wrap-price"})
            except:
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a").get("aria-label")
        title = title.replace("選取「", "")
        title = title.replace("」選項", "")
        link_id = item.find("a").get("data-product_id")
        link = item.find("a").get("href")
        image_url = item.find("div", {"class": "swatches-on-grid"}).find("div").get("data-image-src")
        try:
            sale_price = self.get_price(item.find("ins").find(
                "span", {"class": "woocommerce-Price-amount amount"}).text)
            original_price = self.get_price(item.find("span", {"class": "woocommerce-Price-amount amount"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "woocommerce-Price-amount amount"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class GalleryCrawler(BaseCrawler):
    id = 243
    name = "gallery-n"
    base_url = "https://gallery-n.co/"

    def parse(self):
        response = requests.request("GET", self.base_url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        try:
            items = soup.find_all("div", {"class": "card"})
        except:
            return
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("h5").text
        link_id = item.find("div", {"class": "add-cart"}).find("a").get("data-product_id")
        link = item.find("a").get("href")
        try:
            image_url = item.find("a").find("img").get("data-lazy-src")
        except:
            try:
                image_url = item.find("a").find("img").get("data-lazy-src")
            except:
                print(title)
                return
        sale_price = self.get_price(item.find("span", {"class": "price"}).text)
        original_price = ""

        return Product(title, link, link_id, image_url, original_price, sale_price)

# 47_Circlescinema
class CirclescinemaCrawler(BaseCrawler):
    id = 47
    name = "circlescinema"
    base_url = "https://www.circles-cinema.com.tw/Shop/"

    def parse(self):
        url = f"{self.base_url}itemList.aspx?m=9&p=0&o=0&sa=0&smfp=0"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = soup.find_all("div", {"class": "itemListDiv"})
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "itemListMerName"}).find(
            "a").text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        link_id = b_stripID(link_id, "&m")
        link_id = stripID(link_id, "mNo1=")
        image_url = item.find("a").find("img").get("src")
        try:
            original_price = self.get_price(
                item.find("div", {"class": "itemListOrigMoney"}).find("span").text)
            sale_price = self.get_price(
                item.find("div", {"class": "itemListMoney itemHasOrig"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "itemListMoney"}).find("span").text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 51_wstyle
class WstyleCrawler(BaseCrawler):
    id = 51
    name = "wstyle"
    base_url = "https://www.wstyle.com.tw/Shop/"
    page_list = ['24', '26', '27', '28', '29']

    def parse(self):
        urls = [
            f"{self.base_url}itemList.aspx?m={k}&o=0&sa=0&smfp={i}" for k in self.page_list for i in range(1, 10)]  # 頁碼會變
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find_all(
                    "div", {"class": "itemListDiv"})
                print(url)
            except:
                print(url, "break")
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "itemListMerName"}).find(
            "a").text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        link_id = stripID(link, "No1=")
        link_id = link_id[:link_id.find('&cno')]
        image_url = item.find("a").find("img").get("src")
        original_price = ""
        sale_price = self.get_price(
            item.find("div", {"class": "itemListMoney"}).find("span").text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 069_Boy2
class Boy2Crawler(BaseCrawler):
    id = 69
    name = "boy2"
    base_url = "https://www.boy2.com.tw/Shop/"

    def parse(self):
        urls = [
            f"{self.base_url}itemList.aspx?m=31&p=0&o=5&sa=1&smfp={i}" for i in range(1, 31)]  # 頁碼會變
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all(
                "div", {"class": "itemListDiv"})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "itemListMerName"}).find(
            "a").text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}{link_id}"
        link_id = stripID(link, "No1=")
        link_id = link_id[:link_id.find('&cno')]
        image_url = item.find("a").find("img").get("src")
        try:
            original_price = self.get_price(
                item.find("span", {"class": "itemPrice itemListSaleMoney"}).text)
            sale_price = self.get_price(
                item.find("span", {"class": "itemPrice itemListOrigMoney"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "itemListMoney"}).find("span").text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class PixyCrawler(BaseCrawler):
    id = 166
    name = "pixy"
    base_url = "https://www.pixyaccs.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products/Collection/Brand/pixy/?mode=search&lid=8&cid=21&sid=25&minRange=0&maxRange=2480&order=0&limit=32&page={i}" for i in range(1, page_Max)]  # 頁碼會變
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            print(url)
            if not soup.find("a", {"class": "page page-next"}):
                break
            items = soup.find_all(
                "div", {"class": "productBox"})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # pre_id = list(
        #     json.loads(
        #         item.find("script")
        #     )
        # )
        # link_id = pre_id["sku"]
        title = item.find("span", {"class": "product-name"}).text
        link_id = item.find("a").get("serial")
        pre_link = item.find("a").get("href")
        link = f"{self.base_url}{pre_link}"
        image_url = item.find("img").get("src")
        try:
            original_price = self.get_price(
                item.find("del", {"class": "font-delete"}).text)
            sale_price = self.get_price(
                item.find("span", {"class": "font-big"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("span", {"class": "font-big"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


class RoxyCrawler(BaseCrawler):
    id = 21
    name = "roxy"
    base_url = "https://www.roxytaiwan.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/new-collection?p={i}" for i in range(1, page_Max)]  # 頁碼會變
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            print(url)
            items = soup.find_all(
                "div", {"class": "product-thumb-info"})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "product-title"}).find(
            "a").text
        link = item.find("p", {"class": "product-title"}).find(
            "a").get("href")
        link_id = item.find("a").get("data-product")
        try:
            image_url = item.find("img").get("data-src")
        except:
            return
        try:
            original_price = self.get_price(
                item.find("span", {"class": "old-price"}).text)
            sale_price = self.get_price(
                item.find("span", {"class": "special-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("span", {"class": "regular-price"}).find("span").text)

        return Product(title, link, link_id, image_url, original_price, sale_price)

class SdareCrawler(BaseCrawler):
    id = 332
    name = "sdare"
    base_url = "https://www.sdare.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/Product/Index?pageCount={i}" for i in range(1, page_Max)]  # 頁碼會變
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            print(url)
            items = soup.find_all(
                "li", {"class": "pro"})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("h3").text
        link = item.find("a").get("href")
        onclick = item.find("div", {"class": "pro_buy"}).get("onclick")
        pattern = "\('(.*?)',"
        link_id = re.search(pattern, onclick).group(1)
        link = f'{self.base_url}{link}'
        try:
            image_url = item.find("img").get("data-imgurl")
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "pro_price sale"}).find("strike").text)
            sale_price = self.get_price(
                item.find("div", {"class": "pro_price sale"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "pro_price sale"}).text)

        return Product(title, link, link_id, image_url, original_price, sale_price)

# 85_SumiCrawler()
class SumiCrawler(BaseCrawler):
    id = 85
    name = "sumi"
    base_url = "https://www.sumi-life.com"
    payload = {'type': ' product',
               'value': ' all',
               'sort': ' default',
               }

    def parse(self):
        for i in range(0, 20):
            url = "https://www.sumi-life.com/productlist"
            response = requests.request("POST", url, headers=self.headers, data={**self.payload, "page": i})
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "clearfix"})
            if not items:
                print(i, 'break')
                break
            # print(items)
            self.result.extend([self.parse_product(item) for item in items])

    def get_id(
        self,
        raw_text,
        pattern="'id': '(.*)'",
    ):
        return re.search(pattern, raw_text).group(1)

    def get_price(
        self,
        raw_text,
        pattern="'price': '(.*)'",
    ):
        return re.search(pattern, raw_text).group(1)

    def parse_product(self, item):
        title = item.find("h4").text
        link = item.get("href")
        link_id = self.get_id(item.get('onclick'))
        image_url = item.find("span").get("data-src")

        # if (item.find("li", {"class": "item_origin item_actual item_visibility"})):
        #     original_price = ""
        #     if(item.find("span", {"class": "font_montserrat"})):
        #         sale_price = self.get_price(item.find("span", {"class": "font_montserrat"}).text)
        #     else:
        #         print(title)
        #         return
        # else:
        #     original_price = self.get_price(item.find("span", {"class": "font_montserrat line_through"}).text)
        #     sale_price = self.get_price(item.find("li", {"class": "item_sale"}).find("span").text)

        original_price = ""
        sale_price = self.get_price(item.get('onclick'))
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 126_SANDARU
class SandaruCrawler(BaseCrawler):
    id = 126
    name = "sandaru"
    base_url = "https://www.sandarushop.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/%E5%85%A8%E7%B3%BB%E5%88%97%E5%A5%B3%E9%9E%8B?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title text-primary-color"}).text
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            if(item.find("div", {"class": "global-primary dark-primary price sl-price"})):
                sale_price = self.get_price(
                    item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
            else:
                sale_price = self.get_price(
                    item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class YandjstyleCrawler(BaseCrawler):
    id = 411
    name = "yandjstyle"
    base_url = "https://www.yandjstyle.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("product-item")
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title text-primary-color title-container ellipsis"}).text.strip()
        link = f'{self.base_url}{item.find("a").get("href")}'
        link_id = item.get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            if(item.find("div", {"class": "global-primary dark-primary price sl-price"})):
                sale_price = self.get_price(
                    item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
            else:
                sale_price = self.get_price(
                    item.find("div", {"class": "global-primary dark-primary price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class NotjustonlyCrawler(BaseCrawler):
    id = 316
    name = "notjustonly"
    base_url = "https://www.notjustonly.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("product-item")
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title"}).text.strip()
        link = item.find("a").get("href")
        link_id = item.get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image m-fill"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            print(title)
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class HouseladiesCrawler(BaseCrawler):
    id = 412
    name = "31house4ladies"
    base_url = "https://www.31house4ladies.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "Product-title Label mix-primary-text"}).text.strip()
        link = item.get("href")
        link_id = item.get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price Label-price-original"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
        except:
            original_price = ""
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "Label-price sl-price is-sale primary-color-price"}).text)
            except:
                try:
                    sale_price = self.get_price(
                        item.find("div", {"class": "Label-price sl-price"}).text)
                except:
                    sale_price = self.get_price(
                        item.find("div", {"class": "Label-price sl-price primary-color-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class CarabellaCrawler(BaseCrawler):
    id = 428
    name = "carabella"
    base_url = "https://www.carabella.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": "Product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "Label-title"}).text.strip()
        link = item.get("href")
        link_id = item.get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "Image-boxify-image js-image-boxify-image sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return
        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "Label-price sl-price is-sale tertiary-color-price"}).text)
            except:
                sale_price = self.get_price(
                    item.find("div", {"class": "Label-price sl-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class UnuselfCrawler(BaseCrawler):
    id = 445
    name = "unuself"
    base_url = "https://www.unuself.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item-content"}):
            return
        title = item.find("div", {"class": "title text-primary-color"}).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            return

        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price"}).text)
        except:
            original_price = ""
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "price-sale price sl-price tertiary-color-price"}).text)
            except:
                try:
                    sale_price = self.get_price(
                        item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
                except:
                    return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class KoilifefCrawler(BaseCrawler):
    id = 446
    name = "koilife"
    base_url = "https://www.koilife-tw.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item-content"}):
            return
        title = item.find("div", {"class": "title text-primary-color"}).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            print(title)
            return

        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
        except:
            original_price = ""
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "price-sale price sl-price tertiary-color-price"}).text)
            except:
                try:
                    sale_price = self.get_price(
                        item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
                except:
                    return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class MymybagCrawler(BaseCrawler):
    id = 381
    name = "mymybag"
    base_url = "https://www.mymybag.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/%E6%89%80%E6%9C%89%E5%95%86%E5%93%81?page={i}&limit=72" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product-item"})
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item-content"}):
            return
        title = item.find("div", {"class": "title text-primary-color"}).text.strip()
        link = item.find("a").get("href")
        link_id = item.find("product-item").get("product-id")
        try:
            image_url = (
                item.find("div", {
                    "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
                .split("url(")[-1]
                .split("?)")[0]
            )
        except:
            print(title)
            return

        try:
            original_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price tertiary-color-price"}).text)
        except:
            original_price = ""
            try:
                sale_price = self.get_price(
                    item.find("div", {"class": "price-sale price sl-price tertiary-color-price"}).text)
            except:
                try:
                    sale_price = self.get_price(
                        item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
                except:
                    return
        return Product(title, link, link_id, image_url, original_price, sale_price)

class FabulousCrawler(BaseCrawler):
    id = 382
    name = "fabulousy"
    base_url = "https://www.fabulousyjewelry.com"

    def parse(self):
        urls = [
            f"{self.base_url}/product/all?page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            # print(soup)
            items = soup.find_all("li", {"class": 'item_block js_is_photo_style img_polaroid has_listing_cart'})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("h4").text
        link = item.find("a").get("href")
        try:
            link_id = item.find("button").get("data-pid")
        except:
            return
        image_url = item.find("span").get("data-src")
        try:
            original_price = self.get_price(
                item.find("li", {"class": "item_origin item_actual"}).find("span").text)
            sale_price = self.get_price(
                item.find("li", {"class": "item_sale"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("span", {"class": "font_montserrat"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class HermosaCrawler(BaseCrawler):
    id = 402
    name = "hermosa"
    base_url = "https://hermosa-m.waca.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/product/all?page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            # print(soup)
            items = soup.find_all("li", {"class": 'item_block js_is_photo_style'})
            if not items:
                break

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        onclick = item.find("a").get("onclick")
        title_pattern = "'name': '(.*?)',"
        title = re.search(title_pattern, onclick).group(1)
        link = item.find("a").get("href")
        id_pattern = "'id': '(.*?)',"
        link_id = re.search(id_pattern, onclick).group(1)
        image_url = item.find("span").get("data-src")
        price_pattern = "'price': '(.*?)'"
        original_price = ""
        sale_price = re.search(price_pattern, onclick).group(1)

        return Product(title, link, link_id, image_url, original_price, sale_price)

class LaconicCrawler(BaseCrawler):
    id = 94
    name = "laconic"
    base_url = "https://laconic.waca.ec/productlist"

    def parse(self):
        urls = [
            f"{self.base_url}?type=product&value=all&sort=default&page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("POST", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("a", {"class": 'clearfix'})
            # print(items)
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("li", {"class": "item_soldout"})):
            return
        title = item.find("h4").text
        link = item.get("href")
        link_id = stripID(link, "/detail/")
        image_url = item.find("span").get("data-src")
        original_price = ""
        sale_price = self.get_price(
            item.find("span", {"class": "font_montserrat"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class BigbaevdayCrawler(BaseCrawler):
    id = 354
    name = "bigbaevday"
    base_url = "https://bigbaevday.waca.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/category/64426?page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("li", {"class": 'item_block js_is_photo_style'})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("li", {"class": "item_soldout"})):
            return
        title = item.find("h4").text
        link = item.find("a").get("href")
        link_id = stripID(link, "/detail/")
        image_url = item.find("span").get("data-src")
        try:
            original_price = self.get_price(item.find("li", {"class": "item_origin item_actual"}).find("span").text)
            sale_price = self.get_price(item.find("li", {"class": "item_sale"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "font_montserrat"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class DafCrawler(BaseCrawler):
    id = 120
    name = "daf"
    base_url = "https://www.daf-shoes.com"

    def parse(self):
        urls = [
            f"{self.base_url}/product/list/all/{i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": 'commoditys'})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p").get("title")
        link = item.find("a").get("href")
        link = f"{self.base_url}{link}"
        link_id = item.find("p").get("pid")
        image_url = item.find("img").get("src")
        if(item.find("p", {"class": "soldout-text"})):
            return
        try:
            original_price = self.get_price(
                item.find("p", {"class": "c-price"}).find("span").text)
            sale_price = self.get_price(
                item.find("p", {"class": "c-price"}).find("span").find_next("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("p", {"class": "c-price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class NjmusesCrawler(BaseCrawler):
    id = 438
    name = "njmuses"
    base_url = "https://www.njmuses.com"

    def parse(self):
        flag = False
        urls = [
            f"{self.base_url}/category?page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": 'pd-item'})
            if len(items) < 12:
                if flag == True:
                    break
                flag = True
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if(item.find("span", {"class": "soldout"})):
            return
        title = item.get("title")
        link = item.find("a").get("href")
        link_id = stripID(link, "item/")
        image_url = item.find("img").get("src")

        try:
            original_price = self.get_price(
                item.find("span", {"class": "price original-price"}).text)
            sale_price = self.get_price(
                item.find("span", {"class": "price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("span", {"class": "price"}).text)
        if original_price == sale_price:
            original_price = ""
        return Product(title, link, link_id, image_url, original_price, sale_price)


class OpenladyCrawler(BaseCrawler):
    id = 17
    name = "openlady"
    base_url = "https://www.openlady.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/item.html?&id=157172&page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("li", {"class": 'item_block item_block_y'})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "item_name"}).find("a").text
        link = item.find("a").get("href")
        link_id = stripID(link, "id=")
        image_url = item.find("img").get("src")
        try:
            original_price = self.get_price(
                item.find("span", {"class": "item_cost"}).text)
            sale_price = self.get_price(
                item.find("span", {"class": "item_cost"}).find_next("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("p", {"class": "item_amount"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

# 127_BONBONS
class BonbonsCrawler(BaseCrawler):
    id = 127
    name = "bonbons"
    urls = [
        f"https://bonbons.com.tw/product-category/pcat-1/page/{i}"
        for i in range(1, page_Max)
    ]

    def parse(self):
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all(
                "div", {"class": 'product-small box'})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "box-text box-text-products"}).find("a").text
        link = item.find("div", {"class": "box-text box-text-products"}).find("a").get("href")
        link_id = stripID(link, "vid=")
        image_url = f"https:{item.find('img').get('src')}"

        original_price = ""
        # self.get_price(item.find("del").find(
        #     "span", {"class": "woocommerce-Price-amount amount"}).text)
        sale_price = self.get_price(item.find("button").get("data-price"))
        return Product(title, link, link_id, image_url, original_price, sale_price)


class CharleneCrawler(BaseCrawler):
    id = 409
    name = "charlene"
    prefix_urls = [ "https://www.charlene168.com/product-category/%e4%b8%8b%e8%ba%ab/page/",
                    "https://www.charlene168.com/product-category/%e5%a5%97%e8%a3%9d/page/",
                    "https://www.charlene168.com/product-category/%e6%8e%a8%e8%96%a6%e5%a5%bd%e7%89%a9/page/",
                    "https://www.charlene168.com/product-category/%e9%a0%90%e8%b3%bc/page/",
                    "https://www.charlene168.com/product-category/%e7%8f%be%e8%b2%a8%e5%95%86%e5%93%81/page/",
                    "https://www.charlene168.com/product-category/%e5%a4%96%e5%a5%97%e7%b3%bb%e5%88%97/page/",
                    "https://www.charlene168.com/product-category/%e4%b8%8a%e8%a1%a3/page/",
                    "https://www.charlene168.com/product-category/%e9%85%8d%e4%bb%b6/page",
                   ]

    def parse(self):
        for prefix in self.prefix_urls:
            for i in range(1, page_Max):
                urls = [f"{prefix}{i}?per_page=72"]
                for url in urls:
                    print(url)
                    response = requests.get(url, headers=self.headers)
                    soup = BeautifulSoup(response.text, features="html.parser")
                    items = soup.find_all(
                        "div", {"class": 'product-wrapper'})
                    if not items:
                        break
                    self.result.extend([self.parse_product(item) for item in items])
                else:
                    continue
                break

    def parse_product(self, item):
        title = item.find("h3").text
        link = item.find("a").get("href")
        link_id = item.find("div", {"class": "woodmart-add-btn"}).find("a").get("data-product_id")
        image_url = item.find('img').get('src').replace('-300x300', '')
        try:
            original_price = self.get_price(item.find("span", {"class": "woocommerce-Price-amount amount"}).text)
            sale_price = self.get_price(item.find("ins").find(
                "span", {"class": "woocommerce-Price-amount amount"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class MaisonmCrawler(BaseCrawler):
    id = 420
    name = "maisonm"
    prefix_urls = ["https://maisonm1965.com/product-category/earrings/page/",
                   "https://maisonm1965.com/product-category/earrings/dangle-%e5%a2%9c%e9%a3%be/page/",
                   "https://maisonm1965.com/product-category/rings/page/",
                   "https://maisonm1965.com/product-category/necklaces/page/",
                   "https://maisonm1965.com/product-category/bracelets-anklets-%e6%89%8b-%e8%85%b3%e9%8d%8a/page/",
                   "https://maisonm1965.com/product-category/birthstone-%e7%94%9f%e6%97%a5%e7%9f%b3%e5%96%ae%e5%93%81/page/",
                   "https://maisonm1965.com/product-category/mens-collection-%e7%94%b7%e5%a3%ab%e7%8f%a0%e5%af%b6/page/",
                   "https://maisonm1965.com/product-category/dogs-cats/page/", ]

    def parse(self):
        for prefix in self.prefix_urls:
            for i in range(1, page_Max):
                urls = [f"{prefix}{i}"]
                for url in urls:
                    print(url)
                    response = requests.get(url, headers=self.headers)
                    soup = BeautifulSoup(response.text, features="html.parser")
                    # print(soup)
                    items = soup.find_all(
                        "div", {"class": 'product-inner pr'})
                    if not items:
                        break
                    self.result.extend([self.parse_product(item) for item in items])
                else:
                    continue
                break

    def parse_product(self, item):
        title = item.find("h3").text
        link = item.find("a").get("href")
        link_id = item.find("div", {"class": "product-btn pa flex column ts__03"}).find("a").get("data-prod")
        image_url = item.find('img').get('src').replace('-470x470', '')
        try:
            original_price = self.get_price(item.find("span", {"class": "woocommerce-Price-amount amount"}).text)
            sale_price = self.get_price(item.find("ins").find(
                "span", {"class": "woocommerce-Price-amount amount"}).text)
        except:
            try:
                original_price = ""
                sale_price = self.get_price(item.find("span", {"class": "price"}).text)
            except:  # 沒價錢
                return
        return Product(title, link, link_id, image_url, original_price, sale_price)


class FeminCrawler(BaseCrawler):
    id = 385
    name = "femin"
    urls = [
        f"https://femin.tw/shop/page/{i}"
        for i in range(1, page_Max)
    ]

    def parse(self):
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            # print(soup)
            items = soup.find_all(
                "ul", {"class": 'woo-entry-inner clr'})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        title = item.find("h2").text
        link = item.find("a").get("href")
        link_id = item.find("li", {"class": "btn-wrap clr"}).find("a").get("data-product_id")
        image_url = item.find('img').get('srcset')
        pattern = ", (.*?) 768w"
        # print(image_url)
        image_url = re.search(pattern, image_url).group(1)
        try:
            original_price = self.get_price(item.find("span", {"class": "woocommerce-Price-amount amount"}).text)
            sale_price = self.get_price(item.find("ins").find(
                "span", {"class": "woocommerce-Price-amount amount"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class MoriiCrawler(BaseCrawler):
    id = 434
    name = "morii"
    base_url = "https://morii-life.com"

    def parse(self):
        urls = [f"{self.base_url}/product-category/all/page/{i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            # print(soup)
            try:
                items = soup.find(
                    "ul", {"class": 'products columns-4'}).find_all("li")
            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        title = item.find("h2").text
        link = item.find("a").get("href")
        link_id = stripID(link, "/shop/")
        image_url = item.find('img').get('src')

        # pattern = ", (.*?) 768w"
        # print(type(image_url))
        # # print(image_url)
        # image_url = re.search(pattern, image_url).group(1)
        original_price = ""
        sale_price = self.get_price(item.find("span", {"class": "woocommerce-Price-amount amount"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class N34Crawler(BaseCrawler):
    id = 430
    name = "n34"
    url = "https://www.n34.com.tw/all"

    def parse(self):
        response = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        # print(soup)
        items = soup.find(
            "ul", {"class": 'loops-wrapper products wc-products grid4 masonry boxed tf_rel tf_clearfix'}).find_all("li")
        if not items:
            return
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("figure").find("a").get("title")
        link = item.find("figure").find("a").get("href")
        link_id = item.find('div', {'class': 'wishlist-wrap tf_inline_b tf_vmiddle'}).find("a").get("data-id")

        noscript = item.find("noscript")
        # print(noscript)
        if noscript:
            img = noscript.find("img")
            if img:
                image_url = img['src']
        else:
            image_url = item.find("img").get("src")

        # pattern = ", (.*?) 768w"
        # print(image_url)
        # image_url = re.search(pattern, image_url).group(1)
        try:
            original_price = self.get_price(item.find("span", {"class": "woocommerce-Price-amount amount"}).text)
            sale_price = self.get_price(item.find("ins").find(
                "span", {"class": "woocommerce-Price-amount amount"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class HolkeeCrawler(BaseCrawler):
    id = 422
    name = "holkee"
    base_url = "https://www.holkee.com"
    base_image = "https://img.holkee.com"

    def parse(self):
        url = f"{self.base_url}/shop/lai"
        print(url)
        response = requests.get(url, headers=self.headers)
        # soup = BeautifulSoup(response.text, features="html.parser")
        pattern = "\s{2,}productInfo:[\s\S]{\s{2,}list:[\s\S]((?s).*),\s{2,}product:[\s\S]''"
        Creat_Json = re.search(pattern, response.text).group(1)
        # print(Creat_Json)
        items = list(json.loads(Creat_Json))
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        title = item['title']
        link = item['page_link']
        link_id = item['groupId']
        image_url = f"{self.base_image}/{item['images'][0]['src']}"
        original_price = item['info'][0]['price']
        sale_price = item['info'][0]['sale_price']
        return Product(title, link, link_id, image_url, original_price, sale_price)


class LovfeeCrawler(BaseCrawler):
    id = 142
    name = "lovfee"
    base_url = "https://www.lovfee.com"

    def parse(self):
        urls = [
            f"{self.base_url}/zh-TW/lovfee/productlist?pageitem=All"]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "pdBox"})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "pdBox_name"}).text
        if (item.find("a", {"class": "pdBox_img soldOut"})):
            return

        title = item.find("p", {"class": "pdBox_name"}).text
        link = f"{self.base_url}/{item.find('a').get('href')}"
        pattern = "SaleID=(.+)&ColorID=(.+)"

        try:
            link_id_1 = re.search(pattern, link).group(1)
            link_id_2 = re.search(pattern, link).group(2)
            link_id = link_id_1 + '-' + link_id_2
            image_url = item.find("source").get("srcset")
        except:
            return
        try:
            original_price = self.get_price(item.find("span", {"class": "price_original"}).text)
            sale_price = self.get_price(item.find("span", {"class": "price_sale"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("p", {"class": "pdBox_price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 143_MAJORIE
class MarjorieCrawler(BaseCrawler):
    id = 143
    name = "marjorie"
    urls = [
        f"https://www.marjorie.co/store/storelist.php?ed=all&page={i}"
        for i in range(1, 6)  # page會變
    ]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("div", {"class": "list"}).find_all("a")
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("title")
        link = "https" + item.get("href")
        link_id = link.split("?")[1]
        image_url = item.find_all("img")[1].get("src")
        original_price = 0
        sale_price = item.find("p").text.split(" ")[1]

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 144_PUREE
class PureeCrawler(BaseCrawler):
    id = 144
    name = "puree"
    urls = [
        f"https://www.puree.com.tw/products?page={i}"
        for i in range(1, 42)
    ]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("product-item")
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find(
            "div", {"class": "title text-primary-color title-container ellipsis"}
        ).text.strip()
        link = "https://www.puree.com.tw" + item.find("a").get("href")
        prefix_id = link.split("/")
        link_id = prefix_id[-1]

        try:
            pre_img = item.find(
                "div", {"class": "boxify-image center-contain sl-lazy-image"}
            ).get("style")
        except:
            pre_img = item.find(
                "div",
                {"class": "boxify-image center-contain sl-lazy-image out-of-stock"},
            ).get("style")
        image_url = pre_img.split(":url(")[1].replace(")", "")
        try:
            original_price = (
                item.find(
                    "div", {
                        "class": "global-primary dark-primary price price-crossed"}
                ).text
            ).strip()
        except:
            original_price = ""
        original_price = original_price.strip("NT$")

        try:
            sale_price = item.find(
                "div", {"class": "price-sale price"}).text.strip()
        except:
            sale_price = item.find(
                "div", {"class": "global-primary dark-primary price"}
            ).text.strip()
        sale_price = sale_price.strip("NT$")

        return Product(title, link, link_id, image_url, original_price, sale_price)


class RereburnCrawler(BaseCrawler):
    id = 147
    name = "rereburn"
    urls = [
        f"https://www.rereburn.com.tw/products?page={i}&limit=72"
        for i in range(1, 18)
    ]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("div", {"class": "col-xs-12 ProductList-list"}).find_all(
                "a"
            )
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "Label-title"}).text
        try:
            pic = item.find(
                "div",
                {"class": "Image-boxify-image js-image-boxify-image sl-lazy-image"},
            ).get("style")
        except:
            pic = item.find(
                "div",
                {
                    "class": "Image-boxify-image js-image-boxify-image sl-lazy-image out-of-stock"
                },
            ).get("style")
        image_url = (pic.split("url(")[1]).replace("?)", "")
        link = item.get("href")
        link_id = item.get("product-id")
        try:
            sale_price = item.find(
                "div", {"class": "Label-price sl-price is-sale primary-color-price"}
            ).text
            try:
                original_price = item.find(
                    "div", {"class": "Label-price sl-price Label-price-original"}
                ).text
            except:
                pass
        except:
            sale_price = item.find(
                "div", {"class": "Label-price sl-price"}).text
            original_price = ""
        original_price = original_price.lstrip()
        original_price = original_price.strip("NT$")
        sale_price = sale_price.lstrip()
        sale_price = sale_price.strip("NT$")
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 147_STYLENANDA
# class StylenandaCrawler(BaseCrawler):
#     id = 147
#     name = "stylenanda"
#     prefix_urls = [
#         "https://tw.stylenanda.com/product/list.html?cate_no=613",
#         "https://tw.stylenanda.com/product/list_3ce_main.html?cate_no=1784",
#         "https://tw.stylenanda.com/product/list_made_main.html?cate_no=182",
#         "https://tw.stylenanda.com/product/list.html?cate_no=460",
#         "https://tw.stylenanda.com/product/list.html?cate_no=1323",
#         "https://tw.stylenanda.com/product/list.html?cate_no=2094",
#         "https://tw.stylenanda.com/product/list.html?cate_no=51",
#         "https://tw.stylenanda.com/product/list.html?cate_no=50",
#         "https://tw.stylenanda.com/product/list.html?cate_no=54",
#         "https://tw.stylenanda.com/product/list.html?cate_no=52",
#         "https://tw.stylenanda.com/product/list.html?cate_no=53",
#         "https://tw.stylenanda.com/product/list.html?cate_no=56",
#         "https://tw.stylenanda.com/product/list.html?cate_no=77",
#         "https://tw.stylenanda.com/product/list.html?cate_no=55",
#         "https://tw.stylenanda.com/product/list.html?cate_no=174",
#         "https://tw.stylenanda.com/product/list_outlet.html?cate_no=3175",
#     ]
#     urls = [
#         f"{prefix}&page=4={i}" for prefix in prefix_urls for i in range(1, 14)]

#     def parse(self):
#         for url in self.urls:
#             response = requests.get(url, headers=self.headers)
#             soup = BeautifulSoup(response.text, features="html.parser")
#             items = soup.find_all("li", {"class": "item xans-record-"})
#             self.result.extend([self.parse_product(item) for item in items])

#     def parse_product(self, item):
#         pre_title = item.find("div", {"class": "name"}).text
#         title = pre_title.split(":")[1]
#         link = "https://tw.stylenanda.com" + item.find("a").get("href")
#         link_id = link.split("?")[-1]
#         image_url = item.find("img").get("src")
#         price = item.find("p", {"class": "price"})
#         sale_price = (price.find("span").text).replace("→", "")
#         original_price = item.find("p", {"class": "price"}).text.split("→")[0]
#         original_price = original_price.lstrip()
#         original_price = original_price.strip("NT$")
#         sale_price = sale_price.lstrip()
#         sale_price = sale_price.strip("NT$")
#         return Product(title, link, link_id, image_url, original_price, sale_price)


class ThegirlwhoCrawler(BaseCrawler):
    id = 148
    name = 'thegirlwho'
    prefix_urls = ["https://www.thegirlwhoshop.com/product.php?page={i}&cid=1#prod_list"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 12)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find_all('div', {'class': 'thumbnail'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            url = item.find('a').get('href')
            page_id = url.split('pid=')[-1]
            img_url = item.find('img').get('data-original')
            title = item.find('a').get('title')
            try:
                original_price = float(item.find('span', {'class': 'price-old'}
                                                 ).text.strip(' \n ').replace("$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find('div', {'class': 'prod-price'}
                                             ).text.strip(' \n ').replace("NT.", "").replace(",", ""))
            except:
                sale_price = float(item.find('div', {'class': 'prod-price'}
                                             ).text.strip(' \n ').replace("NT.", "").replace(",", ""))
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

# 150_CHUU
class ChuuCrawler(BaseCrawler):
    id = 150
    name = "chuu"
    urls = [
        "https://chuu.com.tw/product/list.html?cate_no=30",
        "https://chuu.com.tw/category/20210217%E8%81%B7%E5%A0%B4%E5%96%AE%E5%93%819%E6%8A%98/862/",
        "https://chuu.com.tw/product/list.html?cate_no=31",
        "https://chuu.com.tw/product/list.html?cate_no=39",
        "https://chuu.com.tw/product/list.html?cate_no=249",
        "https://chuu.com.tw/product/list.html?cate_no=224",
        "https://chuu.com.tw/product/list.html?cate_no=214",
        "https://chuu.com.tw/product/list.html?cate_no=35",
        "https://chuu.com.tw/product/list.html?cate_no=251",
        "https://chuu.com.tw/product/list.html?cate_no=252",
        "https://chuu.com.tw/product/list.html?cate_no=253",
        "https://chuu.com.tw/product/list.html?cate_no=254",
        "https://chuu.com.tw/product/list.html?cate_no=300",
        "https://chuu.com.tw/product/list.html?cate_no=301",
        "https://chuu.com.tw/product/list.html?cate_no=302",
        "https://chuu.com.tw/product/list.html?cate_no=36",
        "https://chuu.com.tw/product/list.html?cate_no=256",
        "https://chuu.com.tw/product/list.html?cate_no=218",
        "https://chuu.com.tw/product/list.html?cate_no=226",
        "https://chuu.com.tw/product/list.html?cate_no=232",
        "https://chuu.com.tw/product/list.html?cate_no=211",
        "https://chuu.com.tw/product/list.html?cate_no=257",
        "https://chuu.com.tw/product/list.html?cate_no=34",
        "https://chuu.com.tw/product/list.html?cate_no=258",
        "https://chuu.com.tw/product/list.html?cate_no=213",
        "https://chuu.com.tw/product/list.html?cate_no=236",
        "https://chuu.com.tw/product/list.html?cate_no=219",
        "https://chuu.com.tw/product/list.html?cate_no=229",
        "https://chuu.com.tw/product/list.html?cate_no=259",
        "https://chuu.com.tw/product/list.html?cate_no=67",
        "https://chuu.com.tw/product/list.html?cate_no=209",
        "https://chuu.com.tw/product/list.html?cate_no=220",
        "https://chuu.com.tw/product/list.html?cate_no=260",
        "https://chuu.com.tw/product/list.html?cate_no=225",
        "https://chuu.com.tw/product/list.html?cate_no=231",
        "https://chuu.com.tw/product/list.html?cate_no=261",
        "https://chuu.com.tw/product/list.html?cate_no=40",
        "https://chuu.com.tw/product/list.html?cate_no=41",
        "https://chuu.com.tw/product/list.html?cate_no=42",
        "https://chuu.com.tw/product/list.html?cate_no=262",
        "https://chuu.com.tw/product/list.html?cate_no=263",
        "https://chuu.com.tw/product/list.html?cate_no=264",
        "https://chuu.com.tw/product/list.html?cate_no=265",
        "https://chuu.com.tw/product/list.html?cate_no=266",
        "https://chuu.com.tw/product/list.html?cate_no=267",
        "https://chuu.com.tw/product/list.html?cate_no=753",
        "https://chuu.com.tw/product/list.html?cate_no=43",
        "https://chuu.com.tw/product/list.html?cate_no=268",
        "https://chuu.com.tw/product/list.html?cate_no=269",
        "https://chuu.com.tw/product/list.html?cate_no=270",
        "https://chuu.com.tw/product/list.html?cate_no=271",
        "https://chuu.com.tw/product/list.html?cate_no=32",
        "https://chuu.com.tw/products/-5kg%20jeans/189/",
    ]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("li", {"class": "item xans-record-"})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            pre_title = item.find("p", {"class": "name"}).text
            title = pre_title.split("商品名 :")[-1]
            link = "https://chuu.com.tw" + item.find("a").get("href")
            link_id = item.find("a").get("href").split("product_no=")[-1]
            image_url = item.find("img").get("src")
            rate = item.find_all("li", {"class": "xans-record-"})
            try:
                for z in rate:
                    op = (z.text).split(":")[-1]
                    if "$" in op:
                        original_price = op
                        break
            except:
                original_price = ""
            sale_price = (rate[-1].text).split(":")[-1]
        except:
            title = "no"

        original_price = original_price.lstrip()
        original_price = original_price.strip("NT$")
        sale_price = sale_price.lstrip()
        sale_price = sale_price.strip("NT$")
        return Product(title, link, link_id, image_url, original_price, sale_price)

# 151_Aley
class AleyCrawler(BaseCrawler):
    id = 151
    name = "aley"
    prefix_urls = ['https://www.alley152.com/product.php?page={i}&cid=1#prod_list']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 10)]

    def parse(self):

        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find('section', {'class': 'body wrapper-product-list'}
                                  ).find_all('div', {'class': 'thumbnail'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):
        try:
            url = prod.find('a').get('href')
            # print(url)
            page_id = url.split('pid=')[-1]
            # print(page_id)
            img_url = prod.find('img', {'class': 'pdimg lazy'}).get('src')
            # print(img_url)
            title = (prod.find('div', {'class': 'prod-name'}).text.strip())
            # print(title)
            try:
                orie = prod.find('div', {'class': 'prod-price'})
                original_price = orie.find('del').text.strip().replace("NT", "").replace(".", "")
            except:
                original_price = ""
            try:
                sale_price = prod.find('span', {'class': 'text-danger'}).text.replace("NT$", "").split('.')[-1].strip()
            except:
                sale_price = prod.find('div', {'class': 'prod-price'}).text.replace("NT$", "").split('.')[-1].strip()
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)

# 152_TRUDAMODA
class TrudamodaCrawler(BaseCrawler):
    id = 152
    name = "trudamoda"
    urls = []
    prefix_urls = [
        "https://www.truda-moda.com.tw/categories/top?page={}&limit=72",
        "https://www.truda-moda.com.tw/categories/bottom-%E4%B8%8B%E8%91%97?page={}&limit=72",
        "https://www.truda-moda.com.tw/categories/outer?page={}&limit=72",
        "https://www.truda-moda.com.tw/categories/jumpsuit-%E5%A5%97%E8%A3%9D?page={}&limit=72",
        "https://www.truda-moda.com.tw/categories/accessories-%E9%85%8D%E4%BB%B6?page={}&limit=72",
    ]
    for i in prefix_urls:
        for j in range(1, 7):
            f = i.format(j)
            urls.append(f)

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            pre_items = soup.find(
                "div", {"class": "col-xs-12 ProductList-list"})
            items = pre_items.find_all("product-item")
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            title = item.find(
                "div", {"class": "title text-primary-color"}).text
            link = item.find("a").get("href")
            link_id = link.split("/")[-1]
            pic_ = item.find(
                "div",
                {"class": "boxify-image js-boxify-image center-contain sl-lazy-image"},
            ).get("style")
            image_url = pic_.split("url(")[-1].replace(")", "")
            pr = item.find("div", {"class": "quick-cart-price"})
            div = pr.find_all("div")
            try:
                original_price = div[1].text.strip()
            except:
                original_price = ""
            sale_price = div[0].text.strip()
        except:
            pass
        return Product(title, link, link_id, image_url, original_price, sale_price)


class LamochaCrawler(BaseCrawler):
    id = 157
    name = "lamocha"
    urls = [
        f"https://www.lamocha.com.tw/PDList.asp?item1=3&item2=2&tbxKeyword=&recommand=&ob=B&gd=b&pageno={i}"
        for i in range(1, page_Max)
    ]

    def parse(self):
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find("section", {"id": "pdlist"}).find("ul").find_all("li")
            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "figcaption"}).find("p").text
        link = "https://www.lamocha.com.tw/" + item.find("a").get("href")
        link_id = "yano" + link.split("yano")[-1]
        image_url = item.find("img").get("src")
        original_price = (
            item.find("p", {"class": "salePrice"}).contents[0]
            if item.find("p", {"class": "salePrice"})
            else ""
        )
        sale_price = (
            item.find("p", {"class": "salePrice"}).find("span").text
            if item.find("p", {"class": "salePrice"})
            else item.find("div", {"class": "figcaption"}).find_all("p")[1].text
        )
        original_price = original_price.replace("$", "").replace(".00", "")
        sale_price = sale_price.replace("$", "").replace(".00", "")

        return Product(title, link, link_id, image_url, original_price, sale_price)
class VemarCrawler(BaseCrawler):
    id = 162
    name = "vemar"
    prefix_urls = [
        " https://fts-api.91app.com/pythia-cdn/graphql?shopId=588&lang=zh-TW&query=query%20cms_shopCategory(%24shopId%3A%20Int!%2C%20%24categoryId%3A%20Int!%2C%20%24startIndex%3A%20Int!%2C%20%24fetchCount%3A%20Int!%2C%20%24orderBy%3A%20String%2C%20%24isShowCurator%3A%20Boolean%2C%20%24locationId%3A%20Int%2C%20%24tagFilters%3A%20%5BItemTagFilter%5D%2C%20%24tagShowMore%3A%20Boolean%2C%20%24serviceType%3A%20String%2C%20%24minPrice%3A%20Float%2C%20%24maxPrice%3A%20Float%2C%20%24payType%3A%20%5BString%5D%2C%20%24shippingType%3A%20%5BString%5D)%20%7B%0A%20%20shopCategory(shopId%3A%20%24shopId%2C%20categoryId%3A%20%24categoryId)%20%7B%0A%20%20%20%20salePageList(startIndex%3A%20%24startIndex%2C%20maxCount%3A%20%24fetchCount%2C%20orderBy%3A%20%24orderBy%2C%20isCuratorable%3A%20%24isShowCurator%2C%20locationId%3A%20%24locationId%2C%20tagFilters%3A%20%24tagFilters%2C%20tagShowMore%3A%20%24tagShowMore%2C%20minPrice%3A%20%24minPrice%2C%20maxPrice%3A%20%24maxPrice%2C%20payType%3A%20%24payType%2C%20shippingType%3A%20%24shippingType%2C%20serviceType%3A%20%24serviceType)%20%7B%0A%20%20%20%20%20%20salePageList%20%7B%0A%20%20%20%20%20%20%20%20salePageId%0A%20%20%20%20%20%20%20%20title%0A%20%20%20%20%20%20%20%20picUrl%0A%20%20%20%20%20%20%20%20salePageCode%0A%20%20%20%20%20%20%20%20price%0A%20%20%20%20%20%20%20%20suggestPrice%0A%20%20%20%20%20%20%20%20isFav%0A%20%20%20%20%20%20%20%20isComingSoon%0A%20%20%20%20%20%20%20%20isSoldOut%0A%20%20%20%20%20%20%20%20soldOutActionType%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20totalSize%0A%20%20%20%20%20%20shopCategoryId%0A%20%20%20%20%20%20shopCategoryName%0A%20%20%20%20%20%20statusDef%0A%20%20%20%20%20%20listModeDef%0A%20%20%20%20%20%20orderByDef%0A%20%20%20%20%20%20dataSource%0A%20%20%20%20%20%20tags%20%7B%0A%20%20%20%20%20%20%20%20isGroupShowMore%0A%20%20%20%20%20%20%20%20groups%20%7B%0A%20%20%20%20%20%20%20%20%20%20groupId%0A%20%20%20%20%20%20%20%20%20%20groupDisplayName%0A%20%20%20%20%20%20%20%20%20%20isKeyShowMore%0A%20%20%20%20%20%20%20%20%20%20keys%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20keyId%0A%20%20%20%20%20%20%20%20%20%20%20%20keyDisplayName%0A%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20priceRange%20%7B%0A%20%20%20%20%20%20%20%20min%0A%20%20%20%20%20%20%20%20max%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A&operationName=cms_shopCategory&variables=%7B%22shopId%22%3A588%2C%22categoryId%22%3A0%2C%22startIndex%22%3A{i}%2C%22fetchCount%22%3A100%2C%22orderBy%22%3A%22Newest%22%2C%22isShowCurator%22%3Afalse%2C%22locationId%22%3A0%2C%22tagFilters%22%3A%5B%5D%2C%22tagShowMore%22%3Afalse%2C%22minPrice%22%3Anull%2C%22maxPrice%22%3Anull%2C%22payType%22%3A%5B%5D%2C%22shippingType%22%3A%5B%5D%7D"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(0, 3000, 100)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            response = requests.get(url, headers=header)
            soup = response.json()
            items = soup['data']['shopCategory']['salePageList']['salePageList']
            if items == []:
                print(url)
                continue
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            page_id = item['salePageId']
            img_url = 'https:'+item['picUrl']
            title = item['title']
            url = f'https://www.vemar.com.tw/SalePage/Index/{page_id}'
            try:
                original_price = item['suggestPrice']
            except:
                original_price = ""
            try:
                sale_price = item['price']
            except:
                pass
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class AnnadollyCrawler(BaseCrawler):
    id = 170
    name = "annadolly"
    prefix_urls = ['https://www.annadolly.com/collections/??_view-all?page=',
                   'https://www.annadolly.com/collections/??_view-all?page=',
                   'https://www.annadolly.com/collections/??_???page=',
                   'https://www.annadolly.com/collections/??_???page=',
                   'https://www.annadolly.com/collections/??_???page=',
                   'https://www.annadolly.com/collections/??_????page=',
                   'https://www.annadolly.com/collections/??_????page=',
                   'https://www.annadolly.com/collections/?????page=',
                   'https://www.annadolly.com/collections/??????????page=',
                   'https://www.annadolly.com/collections/?????page=',
                   'https://www.annadolly.com/collections/?????page=',
                   'https://www.annadolly.com/collections/????????page=',
                   'https://www.annadolly.com/collections/kimy???page=',
                   'https://www.annadolly.com/collections/?????page=',
                   'https://www.annadolly.com/collections/???page=',
                   'https://www.annadolly.com/collections/?????page=',
                   'https://www.annadolly.com/collections/?????page=']
    urls = [f'{prefix}{i}' for prefix in prefix_urls for i in range(1, 10)]

    def parse(self):
        for url in self.urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")

            items = soup.find('div', {'class': 'products_content'}).find_all('div', {'class': 'product with_slogan'})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, prod):
        url = "https://www.annadolly.com"+prod.find('a', {'class': 'productClick'}).get('href')
        page_id = prod.find('a', {'class': 'productClick'}).get('data-id')
        img_url = prod.find('img').get('data-src')
        # print(img_url)
        title = (prod.find('a', {'class': 'productClick'}).get('data-name'))
        # print(title)
        try:
            original_price = prod.find('span', {'class': 'price'}).text.strip('.').replace("NT$", "").replace(".", "")
            # print(original_price)
        except:
            original_price = ""
        try:
            sale_price = prod.find('p', {'class': 'price'}).text.replace("NT$", "").split('.')[-1]
        except:
            sale_price = original_price

        return Product(title, url, page_id, img_url, original_price, sale_price)

class RobinmayCrawler(BaseCrawler):
    id = 172
    name = "robinmay"
    prefix_urls = ['https://www.robinmaybag.com/categories/hot-robinmay?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/1980?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/new-arrival?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/collection?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/rm-x-ella?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/plus?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/stay-magic?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/all-you-need?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/evolution?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/platinum-nylon-collection?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/belle�s-collection?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/platinum-quilted-collections?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/bags?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/clutches?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/handbags?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/shoulder-bags?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/crossbody-bags?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/backpacks?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/chest-bags?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/wallet?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/large?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/meduim?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/small?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/small-wallets-for-men?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/card-holders-coin-purses?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/bag-straps?page={i}&limit=72',
                   'https://www.robinmaybag.com/categories/more-to-discover?page={i}&limit=72']
    urls = [f'{prefix}'.replace('{i}', str(i))for prefix in prefix_urls for i in range(1, 7)]

    def parse(self):
        for url in self.urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}).find_all('div', {'class': 'product-item'})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, prod):
        url = prod.find('a', {'class': 'quick-cart-item js-quick-cart-item'}).get('href')
        page_id = prod.find('product-item').get('product-id')
        img_url = prod.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image'}
                            ).get('style').split('background-image:url(')[1].replace('?)', "")
        title = (prod.find('div', {'class': 'title text-primary-color'})).text
        try:
            original_price = prod.find(
                'div', {'class': 'global-primary dark-primary price sl-price'}).text.strip('.').replace("NT$", "").replace(".", "")
        except:
            original_price = ""
        try:
            sale_price = prod.find('p', {'class': 'price'}).text.replace("NT$", "").split('.')[-1]
        except:
            sale_price = original_price
        return Product(title, url, page_id, img_url, original_price, sale_price)

class StarkikiCrawler(BaseCrawler):
    id = 179
    name = "starikki"
    prefix_urls = ['https://www.starkiki.com/Shop/itemList.aspx?m=48&p=194&o=0&sa=0&smfp={i}&']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 50)]

    def parse(self):

        for url in self.urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find('div', {'id': 'ctl00_ContentPlaceHolder1_ilItems'}
                                  ).find_all('div', {'class': 'itemListDiv'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):
        try:
            url = prod.find('a').get('href')
            # print(url)
            page_id = prod.find('h4').text
            # print(page_id)
            img_url = prod.find('img').get('src')
            # print(img_url)
            title = (prod.find('h5').text.strip())
            # print(title)
            try:
                original_price = prod.find('span', {'class': 'itemListOrigMoney'}
                                           ).text.strip().replace("NT", "").replace(".", "")
                # print(original_price)
            except:
                original_price = ""
            try:
                sale_price = prod.find('span', {'class': 'itemListMoney'}
                                       ).text.replace("NT$", "").split('.')[-1].strip()
            except:
                sales_price = original_price
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)

class AramodalCrawler(BaseCrawler):
    id = 183
    name = "aramodal"
    prefix_urls = ['https://www.aroommodel.com/products?page={i}&limit=72']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 14)]

    def parse(self):
        for url in self.urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find('div', {'class': 'row'}).find_all('div', {'class': 'product-item'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):
        try:
            url = prod.find('a').get('href')
            # print(url)
            page_id = prod.find('product-item').get('product-id')
            # print(page_id)
            img_url = prod.find('div', {'boxify-image js-boxify-image center-contain sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            # print(img_url)
            title = (prod.find('div', {'class': 'title text-primary-color'}).text.strip())
            # print(title)

            try:
                original_price = prod.find(
                    'div', {'class': 'global-primary dark-primary price sl-price price-crossed'}).text.strip().replace("NT$", "").replace(".", "")
            except:
                original_price = ""
            try:
                sale_price = prod.find(
                    'div', {'class': 'price-sale price sl-price primary-color-price'}).text.replace("NT$", "").split('.')[-1].strip()
            except:
                sale_price = prod.find('div', {'class': 'global-primary dark-primary price sl-price'}
                                       ).text.replace("NT$", "").split('.')[-1].strip()
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)
class BuchaCrawler(BaseCrawler):
    id = 182
    name = 'bucha'
    prefix_urls = [
        "https://www.bucha.tw/categories/%E6%89%80%E6%9C%89%E5%95%86%E5%93%81%E3%83%BBall?page={i}&limit=72"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 50)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}).find_all("product-item")

                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            page_id = item.get('product-id')
            img_url = item.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = item.find('div', {'class': 'title'}).text

            url = item.find('a').get('href')
            try:
                original_price = float(item.find('div', {
                                       'class': 'global-primary dark-primary price sl-price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find(
                    'div', {'class': 'price-sale price sl-price primary-color-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                try:
                    sale_price = float(item.find(
                        'div', {'class': 'global-primary dark-primary price sl-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
                except:

                    sale_price = item.find('div', {'class': 'price-sale price sl-price primary-color-price'}
                                           ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~")
                    if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                        sale_price = float(sale_price[0].strip())
                    elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                        sale_price = float(sale_price[-1].strip())
                    else:
                        sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class RachelworldCrawler(BaseCrawler):
    id = 241
    name = "rachelworld"
    base_url = "https://www.rachelworld.com.tw"
    url = f"{base_url}/ajaxpro/Mallbic.U.UShopShareUtil.Ajax.GlobalAjaxProductUtil,ULibrary.ashx?ajax=GetAllProductByViewOption"

    def get_cookies(self):
        cookies = requests.request("POST", self.base_url, headers=self.headers).cookies
        print(cookies)
        return cookies

    def parse(self):
        # session = requests.Session()
        # cookie = self.get_cookies()
        for i in range(1, 1000, 10):
            payload = {"aOpt": {"SearchType": -1, "CacheId": 35616,
                                "CategoryID": "-1", "BlockNo": list(range(i, i+9))}}  # list(range(1, 1000))
            response = requests.request("POST", self.url, headers={
                                        **self.headers, "Content-Type": "application/json", "X-AjaxPro-Method": "GetAllProductByViewOption", "Cookie": "ASP.NET_SessionId=r2s1y8e7f7sapa56nevullfcob2qdn1qh"}, json=payload)
            raw_text = re.sub('new Ajax\.Web\.Dictionary\(.*?\),|new Date\(.*?\)',
                              '"",', response.content.decode(encoding='utf-8'))
            raw_text = raw_text.replace('"",,', '"",')
            raw_text = raw_text.replace('"",}', '""}')
            raw_text = raw_text.replace('}]])', '')
            # print(raw_text)
            try:
                items = json.loads(raw_text)["value"]["ListData"]
                self.result.extend([self.parse_product(item) for item in items])
            except:
                print(i)
                continue

    def parse_product(self, item):
        title = item.get("ProductName")
        link_id = item.get("ProductID")
        link = f'{self.base_url}/pitem/{link_id}'
        image_url = item.get("SmallPicUrl")
        original_price = item.get("MaxDeletePrice")
        sale_price = item.get("MinDisplayPrice")
        return Product(title, link, link_id, image_url, original_price, sale_price)

class AlmashopCrawler(BaseCrawler):
    id = 194
    name = "almashop"
    base_url = "https://www.alma-shop.com.tw"
    url = f"{base_url}/ajaxpro/Mallbic.U.UShopShareUtil.Ajax.GlobalAjaxProductUtil,ULibrary.ashx?ajax=GetAllProductByViewOption"

    def get_cookies(self):
        cookies = requests.request("POST", self.base_url, headers=self.headers).cookies
        print(cookies)
        return cookies

    def parse(self):
        # session = requests.Session()
        # cookie = self.get_cookies()
        # for i in range(1, 1000, 10):
        # payload = {"aOpt": {"SearchType": -1, "CacheId": 35616,
        #                     "CategoryID": "-1", "BlockNo": list(range(i, i+9))}}  # list(range(1, 1000))
        payload = {"aOpt": {"SearchType": -1, "CacheId": -1, "CategoryID": "64",
                            "SortingMode": 0, "IsInStock": False, "BlockNo": list(range(1, 1000))}}
        # payload = {"aOpt": {"SearchType": -1, "CategoryID": "-1",
        #                 "SortingMode": 0, "IsInStock": False, "BlockNo": list(range(1, 1000))}}
        response = requests.request("POST", self.url, headers={
                                    **self.headers, "Content-Type": "application/json", "X-AjaxPro-Method": "GetAllProductByViewOption", "Cookie": "ASP.NET_SessionId=r2t1v8ta52m6t3eeuekortavkvqingaew"}, json=payload)
        raw_text = re.sub('new Ajax\.Web\.Dictionary\(.*?\),|new Date\(.*?\)',
                          '"",', response.content.decode(encoding='utf-8'))
        raw_text = raw_text.replace('"",,', '"",')
        raw_text = raw_text.replace('"",}', '""}')
        raw_text = raw_text.replace('}]])', '')
        # print(raw_text)
        try:
            items = json.loads(raw_text)["value"]["ListData"]
            self.result.extend([self.parse_product(item) for item in items])
        except:
            print('failed')

    def parse_product(self, item):
        title = item.get("ProductName")
        link_id = item.get("ProductID")
        link = f'{self.base_url}/pitem/{link_id}'
        image_url = item.get("SmallPicUrl")
        original_price = item.get("MaxDeletePrice")
        sale_price = item.get("MinDisplayPrice")
        return Product(title, link, link_id, image_url, original_price, sale_price)


# class AlmashopCrawler(BaseCrawler):
#     id = 194
#     name = "almashop"
#     base_url = "https://www.alma-shop.com.tw"

#     def parse(self):
#         url = f"{self.base_url}/ajaxpro/Mallbic.U.UShopShareUtil.Ajax.GlobalAjaxProductUtil,ULibrary.ashx"
#         payload = {"aOpt": {"SearchType": -1, "CategoryID": "-1",
#                             "SortingMode": 0, "IsInStock": False, "BlockNo": list(range(1, 1000))}}
#         response = requests.request("GET", url, headers={
#                                     **self.headers, "Content-Type": "application/json", "X-AjaxPro-Method": "GetAllProductByViewOption"}, json=payload)
#         print(response.content.decode(encoding='utf-8'))
#         raw_text = re.sub('new Ajax\.Web\.Dictionary\(.*?\),|new Date\(.*?\)',
#                           '"",', response.content.decode(encoding='utf-8'))
#         # raw_text = re.sub('new Ajax\.Web\.Dictionary\(.*?\)', '""', raw_text)
#         raw_text = raw_text.replace('"",,', '"",')
#         raw_text = raw_text.replace('"",}', '""}')
#         # print(raw_text)
#         items = json.loads(raw_text)["value"]["ListData"]
#         self.result.extend([self.parse_product(item) for item in items])

#     def parse_product(self, item):
#         title = item.get("ProductName")
#         link_id = item.get("ProductID")
#         link = f'{self.base_url}/pitem/{link_id}'
#         image_url = item.get("SmallPicUrl")
#         original_price = item.get("MaxDeletePrice")
#         sale_price = item.get("MinDisplayPrice")
#         return Product(title, link, link_id, image_url, original_price, sale_price)

class ControlfreakCrawler(BaseCrawler):
    id = 236
    name = "controlfreak"

    base_url = 'https://www.controlfreak2011.com'

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?page={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            if (soup.find("div", {"class": "product product_tag"})):
                items = soup.find("div", {"class": "products_content"}).find_all(
                    "div", {"class": "product product_tag"})
            else:
                break

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a", {"class": "productClick"}).get("data-name")
        link = item.find("a", {"class": "productClick"}).get("href")
        link_id = item.find("a", {"class": "productClick"}).get('data-id')
        link = f"{self.base_url}{link}"
        image_url = item.find("img").get("data-src")
        image_url = f"https:{image_url}"
        try:
            original_price = self.get_price(item.find("div", {"class": "product_price"}).find("del").text)
            sale_price = self.get_price(item.find("div", {"class": "product_price"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "product_price"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class OutfitCrawler(BaseCrawler):
    id = 408
    name = "outfitstw"

    base_url = 'https://outfitstw.com'

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?page={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            if (soup.find("div", {"class": "grid-view-item product-card"})):
                items = soup.find_all("div", {"class": "grid-view-item product-card"})
            else:
                break

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "h4 grid-view-item__title product-card__title"}).text
        link = item.find("a").get("href")
        link_id = stripID(link, "/products/")
        link = f"{self.base_url}{link}"
        image_url = item.find("img").get("data-src").replace("{width}", "1080")
        image_url = f"https:{image_url}"
        try:
            original_price = self.get_price(
                item.find("s", {"class": "price-item price-item--regular"}).text).replace(".00", "")
            sale_price = self.get_price(
                item.find("span", {"class": "price-item price-item--sale"}).text).replace(".00", "")
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("span", {"class": "price-item price-item--sale"}).text).replace(".00", "")
        try:
            if (int(original_price) <= int(sale_price)):
                original_price = ""
        except:
            print(title)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class DarkcirclesCrawler(BaseCrawler):
    id = 399
    name = "darkcircles"

    base_url = 'https://darkcircleswomen.com'

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?page={i}"
            for i in range(1, page_Max)
        ]
        flag = 0
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "grid-product__wrapper"})
            if len(items) < 12:
                print(len(items))
                if flag == True:
                    print("break")
                    break
                flag = True
            print(url)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "grid-product__sold-out"}):
            return
        title = item.find("span", {"class": "grid-product__title"}).text
        link = item.find("a", {"class": "grid-product__meta"}).get("href")
        link = f"{self.base_url}{link}"
        try:
            image_url = item.find("img", {"class": "grid-product__image"}).get("src")
            pattern = "v=(.+)"
            link_id = re.search(pattern, image_url).group(1)
        except:
            return
        image_url = f"https:{image_url}"
        original_price = ""
        sale_price = self.get_price(item.find("span", {"class": "grid-product__price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class FeatherCrawler(BaseCrawler):
    id = 387
    name = "feather"

    base_url = 'https://www.feather-tw.com'

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?page={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            if (soup.find("div", {"class": "product product_tag"})):
                items = soup.find("div", {"class": "products_content"}).find_all(
                    "div", {"class": "product product_tag"})
            else:
                break

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a", {"class": "productClick"}).get("data-name")
        link = item.find("a", {"class": "productClick"}).get("href")
        link_id = item.find("a", {"class": "productClick"}).get('data-id')
        link = f"{self.base_url}{link}"
        image_url = item.find("img").get("data-src")
        image_url = f"https:{image_url}"
        try:
            original_price = self.get_price(item.find("div", {"class": "product_price"}).find("del").text)
            sale_price = self.get_price(item.find("div", {"class": "product_price"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "product_price"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class LiusannCrawler(BaseCrawler):
    id = 416
    name = "liusann"

    base_url = 'https://www.liusann.com'

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?page={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            if (soup.find("div", {"class": "product product_tag"})):
                items = soup.find("div", {"class": "products_content"}).find_all(
                    "div", {"class": "product product_tag"})
            else:
                break

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a", {"class": "productClick"}).get("data-name")
        link = item.find("a", {"class": "productClick"}).get("href")
        link_id = item.find("a", {"class": "productClick"}).get('data-id')
        link = f"{self.base_url}{link}"
        image_url = item.find("img").get("data-src")
        image_url = f"https:{image_url}"
        try:
            original_price = self.get_price(item.find("div", {"class": "product_price"}).find("del").text)
            sale_price = self.get_price(item.find("div", {"class": "product_price"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "product_price"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class ClothinglabCrawler(BaseCrawler):
    id = 418
    name = "clothinglab"

    base_url = 'https://www.clothinglab.cc'

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?page={i}"
            for i in range(1, page_Max)
        ]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("div", {"class": "product product_tag with_slogan"})
            if not items:
                break

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a", {"class": "productClick"}).get("data-name")
        link = item.find("a", {"class": "productClick"}).get("href")
        link_id = item.get('product_id')
        link = f"{self.base_url}{link}"
        image_url = item.find("img").get("data-src")
        image_url = f"https:{image_url}"
        try:
            original_price = self.get_price(item.find("div", {"class": "product_price"}).find("del").text)
            sale_price = self.get_price(item.find("div", {"class": "product_price"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "product_price"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


class GutenCrawler(BaseCrawler):
    id = 222
    name = "guten"

    base_url = 'https://www.guten.co'

    def parse(self):
        urls = [f"{self.base_url}/collections/all?page={i}"for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            if (soup.find("div", {"class": "product"})):
                items = soup.find("div", {"class": "products_content"}).find_all(
                    "div", {"class": "product"})
            else:
                break

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a", {"class": "productClick"}).get("data-name")
        link = item.find("a", {"class": "productClick"}).get("href")
        link_id = item.find("a", {"class": "productClick"}).get('data-id')
        link = f"{self.base_url}{link}"
        image_url = item.find("img").get("data-src")
        image_url = f"https:{image_url}"
        try:
            original_price = self.get_price(item.find("div", {"class": "product_price"}).find("del").text)
            sale_price = self.get_price(item.find("div", {"class": "product_price"}).find("span").text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("div", {"class": "product_price"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class GozoCrawler(BaseCrawler):
    id = 246
    name = "gozo"

    prefix_urls = ['https://www.gozo.com.tw/products?page={i}&sort_by&order_by&limit=72'
                   ]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 50)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}
                                  ).find_all('div', {'class': 'product-item'})
                if len(items) < 1:
                    break
                else:
                    self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):
        try:
            title = (prod.find('div', {'class': 'title'}).text.strip()).replace('\x08', "")
            url = prod.find('a').get('href').replace('\x08', "")
            try:
                page_id = prod.find('product-item').get('product-id')
            except:
                page_id = ""
            try:
                img_url = prod.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image m-fill'}).get(
                    'style').split('background-image:url(')[-1].replace(')', "")
            except:
                img_url = prod.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image out-of-stock second-image'}).get(
                    'style').split('background-image:url(')[-1].replace(')', "")
            try:
                orie = prod.find('div', {'class': 'quick-cart-price'}).find_all('div')
                original_price = orie[1].text.strip().replace("NT$", "").replace(",", "")
                sale_price = orie[0].text.strip().replace("NT$", "").replace(",", "")
            except:
                orie = prod.find('div', {'class': 'quick-cart-price'}).find_all('div')
                sale_price = orie[0].text.strip().replace("NT$", "").replace(",", "")
                original_price = ""
            # print(title, url, page_id, img_url, original_price, sale_price)
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)

class ToofitCrawler(BaseCrawler):
    id = 244
    name = "toofit"

    prefix_urls = ['https://www.toofit.tw/products?page={i}&limit=72']
    prefix_urls_1 = ['https://www.toofit.tw/categories/全站商品?page={i}&sort_by&order_by&limit=24']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 50)]
    urls_1 = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 50)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}
                                  ).find_all('div', {'class': 'product-item'})
                if len(items) < 1:
                    break
                else:
                    self.result.extend([self.parse_product(item) for item in items])
            except:
                break
            for url in self.urls_1:
                print(url)
                response = requests.get(url, headers=header)
                soup = BeautifulSoup(response.text, features='html.parser')
                try:
                    items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}
                                      ).find_all('div', {'class': 'product-item'})
                    if len(items) < 1:
                        break
                    else:
                        self.result.extend([self.parse_product(item) for item in items])
                except:
                    break

    def parse_product(self, prod):
        try:
            title = prod.find('div', {'class': 'title text-primary-color'}).text

            url = prod.find('a').get('href')

            try:
                page_id = prod.find('product-item').get('product-id')
            except:
                page_id = ""

            try:
                img_url = prod.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image'}
                                    ).get('style').split('background-image:url(')[-1].replace(')', "")
            except:
                img_url = prod.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image  second-image'}).get(
                    'style').split('background-image:url(')[-1].replace(')', "")

            try:
                orie = prod.find('div', {'class': 'global-primary dark-primary price sl-price price-crossed'})
                original_price = orie.text.strip().replace("NT$", "").replace(",", "")
                sale_price = prod.find('div', {'class': 'price-sale price sl-price primary-color-price'})
                sale_price = sale_price.text.replace("NT$", "").replace(",", "").strip()
            except:
                original_price = " "
                orie = prod.find('div', {'class': 'global-primary dark-primary price sl-price'})
                sale_price = orie.text.strip().replace("NT$", "").replace(",", "")

            # print(title, url, page_id, img_url)
            # print(title, url, page_id, img_url, original_price, sale_price)
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)

class StylemooncatCrawler(BaseCrawler):
    id = 141
    name = "stylemooncat"

    prefix_urls = ['https://www.stylemooncat.com.tw/pdlist.asp?p1=&p2=&keyword=&recommand=&ob=F&gd=%20&pageno={i}']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 50)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:

                items = soup.find('div', {'class': 'pdlist_wrap is-clearfix'}).find_all('div', {'class': 'grid-item'})
                if len(items) < 1:
                    break
                else:
                    self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, prod):
        try:
            title = prod.find('a').get('title')

            url = "https://www.stylemooncat.com.tw/"+prod.find('a').get('href')

            page_id = prod.find('a').get('href').split('?yano=')[-1].replace('-dn', "")

            img_url = prod.find('div', {'class': 'pdlist_img'}).find('img').get('src')

            try:
                orie = prod.find('span', {'class': 'pdcnt_info_price-origin'})
                original_price = orie.text.strip().replace("NTD.", "").replace(",", "").strip()
                sale_price = prod.find('span', {'class': 'pdcnt_info_price-sale'})
                sale_price = sale_price.text.replace("NTD.", "").replace(",", "").strip()
            except:
                original_price = " "
                sale_price = prod.find('p', {'class': 'pdcnt_info_price'})
                sale_price = sale_price.text.replace("NTD.", "").replace(",", "").strip()

            # print(title, url, page_id, img_url)
            # print(title, url, page_id, img_url, "o" ,original_price,"s", sale_price)
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)


class KokokoreaCrawler(BaseCrawler):
    id = 237
    name = "kokokorea"

    prefix_urls = ['https://www.kokokorea.co/categories/all?page={i}&limit=24']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 50)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}
                                  ).find_all('div', {'class': 'product-item'})
                if len(items) < 1:
                    break
                else:
                    self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, prod):
        try:
            title = prod.find('div', {'class': 'title'}).text

            url = prod.find('a').get('href')

            try:
                page_id = prod.find('product-item').get('product-id')
            except:
                page_id = ""

            try:
                img_url = prod.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image m-fill'}).get(
                    'style').split('background-image:url(')[-1].replace(')', "")
            except:
                img_url = prod.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image second-image'}).get(
                    'style').split('background-image:url(')[-1].replace(')', "")

            try:
                orie = prod.find('div', {'class': 'quick-cart-price'}).find_all('div')
                original_price = orie[1].text.strip().replace("NT$", "").replace(",", "")
                sale_price = orie[0].text.strip().replace("NT$", "").replace(",", "")
            except:
                orie = prod.find('div', {'class': 'quick-cart-price'}).find_all('div')
                sale_price = orie[0].text.strip().replace("NT$", "").replace(",", "")
                original_price = ""

            # print(title, url, page_id, img_url)
            # print(title, url, page_id, img_url, original_price, sale_price)
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)


class RubysCrawler(BaseCrawler):
    id = 3
    name = "rubys"

    prefix_urls = ['https://www.rubys.com.tw/categories/all?page={i}&sort_by&order_by&limit=72']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 25)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}).find_all('div', {'class': 'product-item'})
            if len(items) < 1:
                break
            else:
                self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, prod):

        try:
            title = prod.find('div', {'class': 'title text-primary-color'}).text

            url = prod.find('a').get('href')

            try:
                page_id = prod.find('product-item').get('product-id')
            except:
                page_id = ""
            try:
                img_url = prod.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image'}
                                    ).get('style').split('background-image:url(')[-1].replace(')', "")
            except:
                img_url = prod.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image out-of-stock'}).get(
                    'style').split('background-image:url(')[-1].replace(')', "")
            try:
                orie = prod.find('div', {'class': 'global-primary dark-primary price sl-price price-crossed'})
                original_price = orie.text.strip().replace("NT$", "").replace(",", "")
                sale_price = prod.find('div', {'class': 'price-sale price sl-price primary-color-price'})
                sale_price = sale_price.text.replace("NT$", "").replace(",", "").strip()
            except:
                original_price = ""
                orie = prod.find('div', {'class': 'global-primary dark-primary price sl-price'})
                sale_price = orie.text.strip().replace("NT$", "").replace(",", "")

                # print(title, url, page_id, img_url)
            # print(title, url, page_id, img_url, original_price, "sale", sale_price)

        except:
            title = url = page_id = img_url = original_price = sale_price = ""
        return Product(title, url, page_id, img_url, original_price, sale_price)

class MosdressCrawler(BaseCrawler):
    id = 60
    name = "mosdress"
    base_url = 'https://www.mosdress.com.tw'

    def parse(self):
        urls = [f"{self.base_url}/productlist?page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all(
                "div", {"class": 'column is-half-mobile is-one-third-tablet is-one-quarter-widescreen pdbox'})
            if not items:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("p", {"class": "pdbox_name"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        pattern = "id=(.+)&"
        link_id = re.search(pattern, link).group(1)
        image_url = item.find("img").get("src")
        try:
            original_price = self.get_price(item.find("span", {"class": "pdbox_price-origin"}).text)
            sale_price = self.get_price(item.find("span", {"class": "pdbox_price-sale"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "pdbox_price"}).text)
        return Product(title, link, link_id, image_url, original_price, sale_price)

class StudioCrawler(BaseCrawler):
    id = 89
    name = "studio"

    prefix_urls = ['https://studiodoe.com/products/actived']

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.prefix_urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'event'}).find_all('a', {'class': 'item-link'})
                if len(items) < 1:
                    break
                else:
                    self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, prod):
        try:

            title = prod.find('div', {'class': 'name'}).text

            url = 'https://studiodoe.com'+prod.get('href')
            try:
                page_id = prod.get('href').split('/')[-1]
            except:
                page_id = ""
#             try:
            img_url = prod.find('div', {'class': 'item-inner'}).get('data-src')
#             except:
#                 img_url=""

            try:
                orie = prod.find_all('div', {'class': 'price'})[0]
                original_price = orie.text.strip().replace("NT$", "").replace(",", "")
                sale_price = prod.find_all('span', {'class': 'woocommerce-Price-amount amount'})[1]
                sale_price = sale_price.text.replace("NT$", "").replace(",", "").strip()
            except:
                original_price = " "
                sale_price = prod.find_all('div', {'class': 'price'})[0]
                sale_price = orie.text.strip().replace("NT$", "").replace(",", "")

                # print(title, url, page_id, img_url)
            # print(title, url, page_id, img_url, original_price, sale_price)

        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price.strip(), sale_price.strip())

class YurubraCrawler(BaseCrawler):
    id = 245
    name = "yurubra"

    prefix_urls = [
        'https://www.yurubra.com.tw/product_list.html?page={i}&currlang=big5&cupid=&label=&Sort=&id=&txtKeyword=']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 50)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'row'}).find_all('div', {'class': 'col-3'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, prod):
        try:
            title = prod.find('figure', {'class': 'img'}).find('a').get('title')

            url = 'https://www.yurubra.com.tw/'+prod.find('figure', {'class': 'img'}).find('a').get('href')

            page_id = prod.find('figure', {'class': 'img'}).find('a').get('href').split('?no=')[-1].replace('&id=', "")

            img_url = 'https://www.yurubra.com.tw/' + \
                prod.find('figure', {'class': 'img'}).find('a').find('img').get('src')
#             print(title, url, page_id, img_url)
            try:
                orie = prod.find('span', {'class': 'original'}).find('b')
                original_price = orie.text.strip().replace("NT$", "").replace(",", "")
                sale_price = prod.find('span', {'class': 'special'}).find('b')
                sale_price = sale_price.text.replace("NT$", "").replace(",", "").strip()
            except:
                original_price = " "
                sale_price = prod.find('span', {'class': 'original'}).find('b')
                sale_price = sale_price.text.replace("NT$", "").replace(",", "").strip()

            # print(title, url, page_id, img_url)
            # print( title, url, page_id, img_url, original_price, sale_price)
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)

# class QuentinaCrawler(BaseCrawler):
#     id = 242
#     name = "quentina"
#     prefix_urls = ['https://www.quentina.com.tw/products?limit=50&offset=0&price=0%2C10000&sort=createdAt-desc&tags=%E7%89%9B%E4%BB%94%E8%A4%B2',
#                    'https://www.quentina.com.tw/products?limit=50&offset=0&price=0%2C10000&search=%E8%A4%B2&sort=createdAt-desc&tags=%E7%89%9B%E4%BB%94%E8%A3%99',
#                    'https://www.quentina.com.tw/products?limit=50&offset=0&price=0%2C10000&search=%E5%8C%85&sort=createdAt-desc&tags=%E7%89%9B%E4%BB%94%E5%A4%96%E5%A5%97',
#                    'https://www.quentina.com.tw/products?limit=50&offset=0&price=0%2C10000&sort=createdAt-desc&tags=%E7%89%9B%E4%BB%94%E8%A5%AF%E8%A1%AB',
#                    'https://www.quentina.com.tw/products?limit=50&offset=0&price=0%2C10000&sort=createdAt-desc&tags=%E7%89%9B%E4%BB%94%E6%B4%8B%E8%A3%9D'
#                    ]
#     urls = prefix_urls  # [f'{prefix}'.replace('{i}',str(i))  for prefix in prefix_urls for i in range(1,10)]

#     def parse(self):
#         header = {
#             'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
#         }
#         for url in self.urls:
#             # print(url)
#             response = requests.get(url, headers=header)
#             soup = BeautifulSoup(response.text, features='html.parser')

#             items = soup.find('div', {'class': 'rmq-478728fa'}).find_all('div', {'class': 'rmq-3ab81ca3'})
#             self.result.extend([self.parse_product(item) for item in items])

#     def parse_product(self, prod):

#         try:
#             title = prod.find('img').get('alt').strip()

#             url = 'https://www.quentina.com.tw'+prod.find('a').get('href')

#             try:
#                 page_id = prod.find('a').get('href').split('/')[-1]
#             except:
#                 page_id = ""

#             try:
#                 img_url = prod.find('img').get('src').strip()
#             except:
#                 img_url = " "
#             try:
#                 orie = prod.find('span')
#                 original_price = orie.text.strip().replace("NT$", "").replace(",", "")
#                 sale_price = prod.find('div', {'style': 'font-size:15px;font-weight:bold'})
#                 sale_price = sale_price.text.replace("NT$", "").replace(",", "").strip()
#             except:
#                 original_price = " "
#                 sale_price = prod.find('div', {'style': 'font-size:15px;font-weight:bold'})
#                 sale_price = sale_price.text.replace("NT$", "").replace(",", "").strip()

#         except:
#             title = url = page_id = img_url = original_price = sale_price = ""
#         return Product(title, url, page_id, img_url, original_price, sale_price)

class LativCrawler(BaseCrawler):
    id = 116
    name = 'lativ'
    header = {
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml,*/*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,la;q=0.5,ja;q=0.4',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    }
    url = 'https://www.lativ.com.tw/WOMEN'
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.text, features='html.parser')

    prefix_urls = []
    li = soup.find_all("ul", {'class': 'sale_category'})
    for i in li:
        cat = i.find_all('li')
        for j in cat:
            prefix_urls.append("https://www.lativ.com.tw/"+j.find('a').get('href'))

    urls = [f'{prefix}' for prefix in prefix_urls]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')

            item1 = soup.find_all('li', {'class': 'lazy_show'})
            item2 = soup.find_all('li', {'class': 'row_before'})
            items = item1+item2
            self.result.extend([self.parse_product(item) for item in items])
            time.sleep(3)

    def parse_product(self, item):
        try:
            url = 'https://www.lativ.com.tw'+item.find('a').get('href')
            page_id = url.split('/')[-1]
            img_url = 'https://www.lativ.com.tw' + \
                item.find('a', {'class': 'imgd'}).find(
                    'img', {'class': 'outfitPic'}).get('data-outfitpic').split(',')[0]
            title = item.find('div', {'class': 'productname'}).text.strip()
            original_price = int(item.find("span").find('span').text.split("NT$")[-1])
            sale_price = int(item.find("span").find_all('span')[-1].text.split("NT$")[-1])
            if sale_price < original_price:
                original_price = original_price
                sale_price = sale_price
            elif sale_price == original_price:
                original_price = ""
                sale_price = sale_price

        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class CocojojoCrawler(BaseCrawler):
    id = 88
    name = 'cocojojo'
    prefix_urls = ['https://cocojojo.cyberbiz.co/collections/上衣',
                   'https://cocojojo.cyberbiz.co/collections/下著',
                   'https://cocojojo.cyberbiz.co/collections/連身',
                   'https://cocojojo.cyberbiz.co/collections/外套',
                   'https://cocojojo.cyberbiz.co/collections/鞋包',
                   'https://cocojojo.cyberbiz.co/collections/飾品',
                   'https://cocojojo.cyberbiz.co/collections/運動服',
                   'https://cocojojo.cyberbiz.co/collections/underware內在美',
                   ]
    urls = [f'{prefix}' for prefix in prefix_urls]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')

            items = soup.find('div', {'class': 'products_content'}).find_all('div', {'class': 'product'})

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:

            url = "https://cocojojo.cyberbiz.co"+item.find('a').get('href')

            page_id = item.find('a').get('data-id')
            title = item.find('a').get('data-name')

            img_url = "https:"+item.find('div', {'class': 'product_image'}).find("img").get('data-src')

            try:
                original_price = float(item.find('div', {
                                       'class': 'global-primary dark-primary price sl-price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""

            try:
                sale_price = float(item.find('div', {'class': 'product_price'}).find('span').text.replace("NT$", ""))

            except:
                sale_price = float(item.find('div', {'class': 'quick-cart-price'}
                                             ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~"))

            # print(title, url, page_id, img_url, original_price, sale_price)
        except:
            return

        return Product(title, url, page_id, img_url, original_price, sale_price)

class CocochiliCrawler(BaseCrawler):
    id = 228
    name = 'cocochilitw'
    prefix_urls = ["https://cocochilitw.easy.co/collections/all-1?limit=9999&page=1&sort=featured"]
    urls = [f'{prefix}' for prefix in prefix_urls]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            # try:

            items = soup.find('div', {'class': 'grid-uniform grid-link__container'}
                              ).find_all('div', {'class': 'grid-link text-center'})

            self.result.extend([self.parse_product(item) for item in items])
            # except:
            #     pass

    def parse_product(self, item):
        try:
            url = 'https://cocochilitw.easy.co/'+item.find('a').get('href')

            page_id = item.find('img').get('alt').replace('.jpeg', '')
            title = item.find('p', {'class': 'grid-link__title'}).text

            img_url = item.find('img').get('src')

            price = item.find_all('span', {'class': 'money'})
            if len(price) > 1:
                if float(price[0].get('data-ori-price').replace(',', ' ').replace(" ", "")) > float(price[1].get('data-ori-price').replace(',', ' ').replace(" ", "")):

                    sale_price = float(price[1].get('data-ori-price').replace(',', ' ').replace(" ", ""))
                    original_price = float(price[0].get('data-ori-price').replace(',', ' ').replace(" ", ""))
                else:
                    sale_price = float(price[0].get('data-ori-price').replace(',', ' ').replace(" ", ""))
                    original_price = float(price[1].get('data-ori-price').replace(',', ' ').replace(" ", ""))
            else:
                sale_price = float(price[-1].get('data-ori-price').replace(',', ' ').replace(" ", ""))
                original_price = ''
        except:
            return

        return Product(title, url, page_id, img_url, original_price, sale_price)

class AttentionCrawler(BaseCrawler):
    id = 216
    name = 'attention'
    prefix_urls = ["https://attention2015.shoplineapp.com/products?page={i}"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 10)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            if soup.find("div", {'class': 'product-list-empty-placeholder'}):
                break

            try:

                items = soup.find('ul', {'class': 'boxify-container'}).find_all("product-item")

                self.result.extend([self.parse_product(item) for item in items])
            except:

                pass

    def parse_product(self, item):
        try:
            url = 'https://attention2015.shoplineapp.com/'+item.find('a').get('href')
            page_id = item.get('product-id')
            img_url = item.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = item.find('div', {'class': 'title text-primary-color title-container ellipsis'}).text.strip()

            try:
                sale_price = float(item.find('div', {'class': 'price-sale price'}).text.replace("NT$", ""))
                original_price = float(
                    item.find('div', {'class': 'global-primary dark-primary price price-crossed'}).text.replace("NT$", ""))
            except:
                try:
                    sale_price = float(
                        item.find('div', {'class': 'global-primary dark-primary price'}).text.replace("NT$", ""))
                    original_price = ","
                except:
                    sale_price = float(
                        item.find('div', {'class': 'Label-price sl-price is-sale primary-color-price'}).text.replace("NT$", ""))
                    original_price = ","
                    sale_price = float(sale_price.replace(",", ""))
            try:
                original_price = float(original_price.replace(",", ""))
            except:
                original_price = ""
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)


class AndenhudCrawler(BaseCrawler):
    id = 159
    name = 'andenhud'
    header = {
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml,*/*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,la;q=0.5,ja;q=0.4',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    }
    url = 'https://www.andenhud.com.tw'
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.text, features='html.parser')
    urls = [
        'https://www.andenhud.com.tw/list/550',
        'https://www.andenhud.com.tw/list/538',
        'https://www.andenhud.com.tw/list/570',
        'https://www.andenhud.com.tw/list/576',
        'https://www.andenhud.com.tw/list/585',
        'https://www.andenhud.com.tw/list/563',
    ]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }

        for url in self.urls:
            i = 1
            end_page = 1
            while end_page != 0:
                url_page = f'{url}?page={i}'
                print(url_page)
                response = requests.get(url_page, headers=header)
                soup = BeautifulSoup(response.text, features='html.parser')
                end_page = int(soup.find('div', {'class': 'pagination-switch-total'}).find('span').text)
                try:
                    items = soup.find("ul", {'class': 'product-list row medium-list'}).find_all('li')
                    self.result.extend([self.parse_product(item) for item in items])
                except:
                    pass
                i += 1

    def parse_product(self, item):
        try:
            url = item.find('a').get('href')
            page_id = item.find('div', {'class': 'cart icon select'}).get('data-id') + '-' + \
                item.find('div', {'class': 'cart icon select'}).get('color-id')
            img_url = item.find('div', {'class': 'image'}).get('style').split(
                "background-image: url('")[-1].replace("');", "")
            title = item.find('div', {'class': 'image'}).get('title')
            try:
                w = item.find('div', {'class': 'price'})
                original_price = float(w.find('span', {'class': 'original-price'}
                                              ).text.replace("$", ""))
                sale_price = float(w.find_all('label')[-1].text)
            except:
                pass

        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)


class VacanzaCrawler(BaseCrawler):
    id = 280
    name = 'vacanza'
    prefix_urls = [
        'https://webapi.91app.com/webapi/shopCategory/GetSalePageList/40200/0?order=&startIndex={i}&maxCount=60&isCuratorable=false&site=www.vacanza.com.tw&v=0&shopId=40200&lang=zh-TW']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(0, 10)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            response = urlopen(url)
            data_json = json.loads(response.read())
            try:
                items = data_json['Data']['SalePageList']

                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            title = item['Title']
            page_id = item['Id']
            url = f'https://www.vacanza.com.tw/SalePage/Index/{page_id}?cid=0'
            img_url = 'https:'+item['PicUrl']
            original_price = ""
            sale_price = item['Price']
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)


class MumushopCrawler(BaseCrawler):
    id = 149
    name = "mumushop"

    prefix_urls = ['https://www.mumushop.com.tw/plist/399/s0/p{i}']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 181)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        self.count = 0
        for url in self.urls:
            print(url)
            session = HTMLSession()
            r = session.get(url)

            r.html.render(sleep=1, keep_page=True, scrolldown=1)
            prd = r.html.find('#gl-container')
            htm = prd[0].html
            soup = BeautifulSoup(htm, features='html.parser')

            try:

                items = soup.find_all('div', {'class': 'divFormProductListItem gl-box'})

                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):
        try:
            if self.count % 30 == 0:
                time.sleep(20)
            title = (prod.find('div', {'class': 'gl-img'})).get('title')
            if title.find('Title') == -1:
                try:
                    url = 'https://www.mumushop.com.tw/'+prod.find('a', {'class': 'img-link'}).get('href')
                except:
                    url = " "
                try:
                    page_id = prod.find('a', {'class': 'img-link'}).get('href').split('/')[-1]
                except:
                    page_id = ""
                try:
                    img_url = prod.find('a', {'class': 'img-link'}).find('img').get('src')
                except:
                    img_url = " "
                # print(title,url,page_id,img_url)
                try:
                    orie = prod.find('span', {'class': 'notranslate'})
                    original_price = float(orie.text.strip().replace("NTD", "").replace(",", "").strip())
                except:
                    original_price = " "
                try:
                    sale_price = prod.find('span', {'class': 'gl-price-origin-price'})
                    sale_price = float(sale_price.text.replace("特價 NTD", "").replace(",", "").strip())
                except:
                    sale_price = ""
                # print(title, url, page_id, img_url, original_price, sale_price)
            else:
                title = url = page_id = img_url = original_price = sale_price = ""
        except:
            title = url = page_id = img_url = original_price = sale_price = ""
        self.count = self.count+1
        return Product(title, url, page_id, img_url, original_price, sale_price)

class VizzleCrawler(BaseCrawler):
    id = 163
    name = 'vizzle'
    prefix_urls = ['https://vizzle2014.com/shop/page/{i}']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 30)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'products product-content-item-wrapper products-grid grid-view-method'}
                                  ).find_all('div', {'class': 'product-content-item'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, item):
        try:
            url = item.find('a').get('href')
            page_id = url.split('/')[-1].replace('.html', "")
            title = item.find('a', {'class': 'woocommerce-loop-product-link'}).text.strip()

            img_url = item.find('a', {'class': 'lorada-product-img-link catalog-image'}).find('img').get('data-src')

            try:
                original_price = float(item.find('div', {
                                       'class': 'global-primary dark-primary price sl-price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""

            try:
                sale_price = float(item.find('span', {'class': 'price'}).text.strip(
                    ' \n ').replace("NT$", "").replace(",", ""))

            except:
                sale_price = item.find('span', {'class': 'price'}).text.strip(
                    ' \n ').replace("NT$", "").replace(",", "").split("–")
                if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                    sale_price = float(sale_price[0].strip())
                elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                    sale_price = sale_price[-1].strip()
                else:
                    sale_price = float(sale_price[0].strip())
        except:
            return

        return Product(title, url, page_id, img_url, original_price, sale_price)

class WemeCrawler(BaseCrawler):
    id = 164
    name = 'weme'
    prefix_urls = ['https://www.wemekr.com/products?page={i}&limit=72']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 30)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            try:
                print(url)
                response = requests.get(url, headers=header)
                soup = BeautifulSoup(response.text, features='html.parser')
                items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}
                                  ).find_all('div', {'class': 'product-item'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            url = item.find('a').get('href')
            page_id = item.find("product-item").get("product-id")
            title = (item.find('div', {'class': 'title text-primary-color'}).text).strip(' \n ')
            try:
                img_url = item.find('div', {'class': 'boxify-image-wrapper js-quick-boxify-image'}
                                    ).find('div').get('style').split('background-image:url(')[1].replace('?)', "")
            except:
                img_url = item.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image'}
                                    ).find('div').get('style').split('background-image:url(')[1].replace('?)', "")
            try:
                original_price = float(item.find('div', {
                                       'class': 'global-primary dark-primary price sl-price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find(
                    'div', {'class': 'price-sale price sl-price primary-color-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                sale_price = item.find('div', {'class': 'quick-cart-price'}
                                       ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~")
                if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                    sale_price = float(sale_price[0].strip())
                elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                    sale_price = float(sale_price[-1].strip())
                else:
                    sale_price = float(sale_price[0].strip())

        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class KavaCrawler(BaseCrawler):
    id = 180
    name = "kava"
    base_url = "https://www.kava-acc.com"

    def parse(self):
        prefix_urls = [
            f'{self.base_url}/ALL?page=',
            f'{self.base_url}/ALL-2?page=',
            f'{self.base_url}/ALL-3?page=',
            f'{self.base_url}/ALL-4?page=',
            f'{self.base_url}/ALL-5?page=',
        ]
        for prefix in prefix_urls:
            for i in range(1, page_Max):
                urls = [f"{prefix}{i}"]
                for url in urls:
                    response = requests.request("GET", url, headers=self.headers)
                    soup = BeautifulSoup(response.text, features="html.parser")
                    items = soup.find_all("div", {"class": "grid-box"})
                    print(url)
                    if not items:
                        print(url, "break")
                        break
                    self.result.extend([self.parse_product(item) for item in items])
                else:
                    continue
                break

    def parse_product(self, item):
        if item.find("span", {"class": "label label-important text-right"}):
            return

        title = item.find("a").get("title")
        link = item.find("a").get("href")
        link_id = item.get("data-producttlid")

        image_url = f"https:{item.find('img').get('data-src')}"
        if '-cr-270x420' in image_url:
            image_url = image_url.replace('-cr-270x420', '-max-w-1024')
        else:
            image_url = f"https:{item.find('img').get('src')}"
            image_url = image_url.replace('-cr-270x420', '-max-w-1024')

        original_price = ""
        sale_price = self.get_price(item.find("div", {"class": "price"}).get("data-price"))

        return Product(title, link, link_id, image_url, original_price, sale_price)


class BelloCrawler(BaseCrawler):
    id = 206
    name = 'bello'
    prefix_urls = ['https://www.bellostore.me/products?page={i}']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 100)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('ul', {'class': 'boxify-container'}).find_all('li',
                                                                                {'class': 'boxify-item product-item'})

                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            #                 print(item)
            url = "https://www.bellostore.me"+item.find('a').get('href')

            page_id = item.find("product-item").get("product-id")
            title = (
                item.find('div', {'class': 'title text-primary-color title-container ellipsis'}).text).strip(' \n ')
            try:
                img_url = item.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                                    ).get('style').split('background-image:url(')[1].replace('?)', "")
            except:
                # item.find('div',{'class':'boxify-image js-boxify-image center-contain sl-lazy-image'}).get('style').split('background-image:url(')[1].replace('?)',"")
                img_url = ""
            try:
                original_price = float(item.find(
                    'div', {'class': 'global-primary dark-primary price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(
                    item.find('div', {'class': 'global-primary dark-primary price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))

            except:
                sale_price = item.find('div', {'class': 'price-sale price'}).text.strip(
                    ' \n ').replace("\n", "").replace("NT$", "").replace(",", "").split("~")

                if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                    sale_price = float(sale_price[0].strip())
                elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                    sale_price = sale_price[-1].strip()
                else:
                    sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)


class UneCrawler(BaseCrawler):
    id = 140
    name = '6une'
    prefix_urls = ["https://www.6une.com.tw/categories/all-items?page={i}&limit=72"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 10)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}).find_all("product-item")
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            page_id = item.get('product-id')
            img_url = item.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image m-fill'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = item.find('div', {'class': 'title'}).text

            url = item.find('a').get('href')
            try:
                original_price = float(item.find('div', {
                                       'class': 'global-primary dark-primary price sl-price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""

            try:
                sale_price = float(item.find(
                    'div', {'class': 'price-sale price sl-price primary-color-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))

            except:
                try:
                    sale_price = float(item.find(
                        'div', {'class': 'global-primary dark-primary price sl-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
                except:

                    sale_price = item.find('div', {'class': 'price-sale price sl-price primary-color-price'}
                                           ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~")
                    if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                        sale_price = float(sale_price[0].strip())
                    elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                        sale_price = float(sale_price[-1].strip())
                    else:
                        sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)


class ShopCrawler(BaseCrawler):
    id = 189
    name = '50shop'
    base_url = 'https://www.50-shop.com/Shop/'

    def parse(self):
        url = f'{self.base_url}itemList.aspx?m=6&smfp=0'
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = soup.find_all("div", {'class': 'products_list fbNo1'})
        if not items:
            print('no item')
            return
        # print(items)
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            option = item.find('div', {'class': 'size_option_wrapper'}).text
            title = b_stripID(option, 'NT.')
            link = f"{self.base_url}{item.find('a').get('href')}"
            link_id = b_stripID(link, "&cno")
            link_id = stripID(link_id, "mNo1=")
            image_url = item.find('a').find('img').get('src')
            temp_price = stripID(option, 'NT.')
            if 'NT.' in temp_price:
                original_price = b_stripID(temp_price, 'NT.')
                sale_price = stripID(temp_price, 'NT.')
            else:
                original_price = ''
                sale_price = temp_price
        except:
            print(title)
            return
        return Product(title, link, link_id, image_url, original_price, sale_price)

class SnatchCrawler(BaseCrawler):
    id = 312
    name = 'snatch'
    prefix_urls = ['https://www.snatch-store.com/categories/all-product?page={i}']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 100)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('ul', {'class': 'boxify-container'}).find_all('li',
                                                                                {'class': 'boxify-item product-item'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            url = "https://www.snatch-store.com"+item.find('a').get('href')
            page_id = item.find("product-item").get("product-id")
            title = (
                item.find('div', {'class': 'title text-primary-color title-container ellipsis'}).text).strip(' \n ')
            try:
                img_url = item.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                                    ).get('style').split('background-image:url(')[1].replace('?)', "")
            except:
                img_url = item.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image'}
                                    ).get('style').split('background-image:url(')[1].replace('?)', "")
            try:
                original_price = float(item.find(
                    'div', {'class': 'global-primary dark-primary price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(
                    item.find('div', {'class': 'global-primary dark-primary price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                sale_price = item.find('div', {'class': 'price-sale price'}).text.strip(
                    ' \n ').replace("\n", "").replace("NT$", "").replace(",", "").split("~")
                if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                    sale_price = float(sale_price[0].strip())
                elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                    sale_price = sale_price[-1].strip()
                else:
                    sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)


class ZouwaCrawler(BaseCrawler):
    id = 383
    name = 'zouwa'
    prefix_urls = ['https://www.zouwa.me/categories/全部商品?page={i}&limit=72']
    # 'https://www.zouwa.me/products?page={i}&limit=72']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 10)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            try:
                soup = BeautifulSoup(response.text, features='html.parser')
                items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}
                                  ).find_all('div', {'class': 'product-item'})
            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            url = item.find('a').get('href')
            page_id = item.find("product-item").get("product-id")
            title = (item.find('div', {'class': 'title text-primary-color'}).text).strip(' \n ')
            img_url = item.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            try:
                original_price = float(item.find('div', {
                                       'class': 'global-primary dark-primary price sl-price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find(
                    'div', {'class': 'price-sale price sl-price tertiary-color-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                sale_price = item.find('div', {'class': 'global-primary dark-primary price sl-price'}
                                       ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~")
                if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                    sale_price = float(sale_price[0].strip())
                elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                    sale_price = sale_price[-1].strip()
                else:
                    sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class DastoreCrawler(BaseCrawler):
    id = 315
    name = 'dastore'
    prefix_urls = ['https://www.dastore.co/categories/女裝?page={i}&limit=24']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 100)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}).find_all('a')
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:

            url = item.get('href')
            page_id = item.get("product-id")
            title = (item.find('div', {'class': 'Label-title'}).text).strip(' \n ')
            try:
                img_url = item.find('div', {'class': 'Image-boxify-image js-image-boxify-image sl-lazy-image'}
                                    ).get('style').split('background-image:url(')[1].replace('?)', "")
            except:
                img_url = item.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image'}
                                    ).get('style').split('background-image:url(')[1].replace('?)', "")

            try:
                original_price = float(item.find(
                    'div', {'class': 'Label-price sl-price Label-price-original'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find('div', {
                                   'class': 'Label-price sl-price is-sale tertiary-color-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))

            except:
                sale_price = item.find('div', {'class': 'Label-price sl-price is-sale tertiary-color-price'}
                                       ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~")
                if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                    sale_price = float(sale_price[0].strip())
                elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                    sale_price = sale_price[-1].strip()
                else:
                    sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class DejavuCrawler(BaseCrawler):
    id = 178
    name = "dejavu"
    prefix_urls = ['https://www.dejavustore.co/categories/shop-all?page={i}&limit=72']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 15)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('ul', {'class': 'boxify-container'}).find_all('li')
                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):
        try:
            url = 'https://www.dejavustore.co' + prod.find('a').get('href')
            page_id = prod.find('product-item').get('product-id')
            img_url = prod.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = (prod.find('div', {'class': 'title text-primary-color title-container ellipsis'})).text.strip()
            try:
                original_price = float(prod.find('div', {
                    'class': 'global-primary dark-primary price'}).text.strip(
                    ' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(
                    prod.find('div', {'class': 'global-primary dark-primary price'}).text.strip(
                        ' \n ').replace("NT$", "").replace(",", ""))
            except:
                try:
                    sale_price = float(
                        prod.find('div', {'class': 'global-primary dark-primary price'}).text.strip(
                            ' \n ').replace("NT$", "").replace(",", ""))
                except:
                    sale_price = prod.find('div',
                                           {'class': 'global-primary dark-primary price'}).text.strip(
                        ' \n ').replace("NT$", "").replace(",", "").split("~")
                    if (float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                        sale_price = float(sale_price[0].strip())
                    elif (float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                        sale_price = float(sale_price[-1].strip())
                    else:
                        sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)


class YveCrawler(BaseCrawler):
    id = 183
    name = 'yve'
    prefix_urls = ["https://www.yvestore.com/products?page={i}"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 100)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('ul', {'class': 'boxify-container'}).find_all("a")
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            url = 'https://www.yvestore.com'+item.get('href')
            page_id = item.get('product-id')
            img_url = item.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = item.find('div', {'class': 'title'}).text.strip()

            try:
                original_price = float(item.find(
                    'div', {'class': 'global-primary dark-primary price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find('div', {'class': 'price-sale price'}
                                             ).text.strip(' \n ').replace("NT$", "").replace(",", ""))

            except:
                try:
                    sale_price = float(item.find('div', {
                                       'class': 'global-primary dark-primary price force-text-align-'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
                except:

                    sale_price = item.find('div', {'class': 'price-sale price'}
                                           ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~")
                    if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                        sale_price = float(sale_price[0].strip())
                    elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                        sale_price = float(sale_price[-1].strip())
                    else:
                        sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class AfashionshowroomCrawler(BaseCrawler):
    id = 174
    name = 'afashionshowroom'
    prefix_urls = ["https://www.afashionshowroom.com/products?page={i}"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 50)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('ul', {'class': 'boxify-container'}).find_all("a")
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            page_id = item.get('product-id')
            img_url = item.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = item.find(
                'div', {'class': 'title text-primary-color title-container ellipsis force-text-align-'}).text.strip()
            url = 'https://www.afashionshowroom.com'+item.get('href')
            try:
                original_price = float(item.find('div', {
                                       'class': 'global-primary dark-primary price price-crossed force-text-align-'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
                sale_price = float(item.find(
                    'div', {'class': 'price-sale price force-text-align-'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
                sale_price = float(item.find('div', {
                                   'class': 'global-primary dark-primary price force-text-align-'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)


class MimiriccoCrawler(BaseCrawler):
    id = 171
    name = 'mimiricco'
    prefix_urls = [
        "https://www.mimiricco.com/categories/5ccde94e17a08d003bed325d?col_class=col-md-3&format=html&is_quick_cart=true&limit=24&offset=72&open_link_in_new_tab=true&page={i}&statuses%5B%5D=active"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 30)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'ProductList-list'}).find_all('a')
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            url = item.get('href')
            page_id = item.get('product-id')
            img_url = item.find('div', {'class': 'Image-boxify-image js-image-boxify-image sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = item.find('div', {'class': 'Product-title Label mix-primary-text'}).text.strip()
            try:
                original_price = float(item.find(
                    'div', {'class': 'Label-price sl-price Label-price-original'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find('div', {'class': 'Label-price'}
                                             ).text.strip(' \n ').replace("NT$", "").replace(",", ""))

            except:
                try:
                    sale_price = float(item.find('div', {
                                       'class': 'Label-price sl-price is-sale primary-color-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
                except:
                    sale_price = item.find('div', {'class': 'price-sale price'}
                                           ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~")
                    if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                        sale_price = float(sale_price[0].strip())
                    elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                        sale_price = float(sale_price[-1].strip())
                    else:
                        sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class GoodlogoCrawler(BaseCrawler):
    id = 187
    name = 'goodlogo'
    prefix_urls = [
        "https://fts-api.91app.com/pythia-cdn/graphql?shopId=38874&lang=zh-TW&query=query%20cms_shopCategory(%24shopId%3A%20Int!%2C%20%24categoryId%3A%20Int!%2C%20%24startIndex%3A%20Int!%2C%20%24fetchCount%3A%20Int!%2C%20%24orderBy%3A%20String%2C%20%24isShowCurator%3A%20Boolean%2C%20%24locationId%3A%20Int%2C%20%24tagFilters%3A%20%5BItemTagFilter%5D%2C%20%24tagShowMore%3A%20Boolean%2C%20%24serviceType%3A%20String%2C%20%24minPrice%3A%20Float%2C%20%24maxPrice%3A%20Float%2C%20%24payType%3A%20%5BString%5D%2C%20%24shippingType%3A%20%5BString%5D)%20%7B%0A%20%20shopCategory(shopId%3A%20%24shopId%2C%20categoryId%3A%20%24categoryId)%20%7B%0A%20%20%20%20salePageList(startIndex%3A%20%24startIndex%2C%20maxCount%3A%20%24fetchCount%2C%20orderBy%3A%20%24orderBy%2C%20isCuratorable%3A%20%24isShowCurator%2C%20locationId%3A%20%24locationId%2C%20tagFilters%3A%20%24tagFilters%2C%20tagShowMore%3A%20%24tagShowMore%2C%20minPrice%3A%20%24minPrice%2C%20maxPrice%3A%20%24maxPrice%2C%20payType%3A%20%24payType%2C%20shippingType%3A%20%24shippingType%2C%20serviceType%3A%20%24serviceType)%20%7B%0A%20%20%20%20%20%20salePageList%20%7B%0A%20%20%20%20%20%20%20%20salePageId%0A%20%20%20%20%20%20%20%20title%0A%20%20%20%20%20%20%20%20picUrl%0A%20%20%20%20%20%20%20%20salePageCode%0A%20%20%20%20%20%20%20%20price%0A%20%20%20%20%20%20%20%20suggestPrice%0A%20%20%20%20%20%20%20%20isFav%0A%20%20%20%20%20%20%20%20isComingSoon%0A%20%20%20%20%20%20%20%20isSoldOut%0A%20%20%20%20%20%20%20%20soldOutActionType%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20totalSize%0A%20%20%20%20%20%20shopCategoryId%0A%20%20%20%20%20%20shopCategoryName%0A%20%20%20%20%20%20statusDef%0A%20%20%20%20%20%20listModeDef%0A%20%20%20%20%20%20orderByDef%0A%20%20%20%20%20%20dataSource%0A%20%20%20%20%20%20tags%20%7B%0A%20%20%20%20%20%20%20%20isGroupShowMore%0A%20%20%20%20%20%20%20%20groups%20%7B%0A%20%20%20%20%20%20%20%20%20%20groupId%0A%20%20%20%20%20%20%20%20%20%20groupDisplayName%0A%20%20%20%20%20%20%20%20%20%20isKeyShowMore%0A%20%20%20%20%20%20%20%20%20%20keys%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20keyId%0A%20%20%20%20%20%20%20%20%20%20%20%20keyDisplayName%0A%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20priceRange%20%7B%0A%20%20%20%20%20%20%20%20min%0A%20%20%20%20%20%20%20%20max%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A&operationName=cms_shopCategory&variables=%7B%22shopId%22%3A38874%2C%22categoryId%22%3A0%2C%22startIndex%22%3A{i}%2C%22fetchCount%22%3A900%2C%22orderBy%22%3A%22%22%2C%22isShowCurator%22%3Afalse%2C%22locationId%22%3A0%2C%22tagFilters%22%3A%5B%5D%2C%22tagShowMore%22%3Afalse%7D"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(100, 3000, 100)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            response = requests.get(url, headers=header)
            soup = response.json()
            items = soup['data']['shopCategory']['salePageList']['salePageList']
            if items == []:
                # print(url)
                continue
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            page_id = item['salePageId']
            img_url = 'https:'+item['picUrl']
            title = item['title']
            url = f'https://www.good-logo.com.tw/SalePage/Index/{page_id}'
            try:
                original_price = item['suggestPrice']
            except:
                original_price = ""
            try:
                sale_price = item['price']
            except:
                pass
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class EvaCrawler(BaseCrawler):
    id = 161
    name = 'eva'
    prefix_urls = [
        "https://fts-api.91app.com/pythia-cdn/graphql?shopId=40686&lang=zh-TW&query=query%20cms_shopCategory(%24shopId%3A%20Int!%2C%20%24categoryId%3A%20Int!%2C%20%24startIndex%3A%20Int!%2C%20%24fetchCount%3A%20Int!%2C%20%24orderBy%3A%20String%2C%20%24isShowCurator%3A%20Boolean%2C%20%24locationId%3A%20Int%2C%20%24tagFilters%3A%20%5BItemTagFilter%5D%2C%20%24tagShowMore%3A%20Boolean%2C%20%24serviceType%3A%20String%2C%20%24minPrice%3A%20Float%2C%20%24maxPrice%3A%20Float%2C%20%24payType%3A%20%5BString%5D%2C%20%24shippingType%3A%20%5BString%5D)%20%7B%0A%20%20shopCategory(shopId%3A%20%24shopId%2C%20categoryId%3A%20%24categoryId)%20%7B%0A%20%20%20%20salePageList(startIndex%3A%20%24startIndex%2C%20maxCount%3A%20%24fetchCount%2C%20orderBy%3A%20%24orderBy%2C%20isCuratorable%3A%20%24isShowCurator%2C%20locationId%3A%20%24locationId%2C%20tagFilters%3A%20%24tagFilters%2C%20tagShowMore%3A%20%24tagShowMore%2C%20minPrice%3A%20%24minPrice%2C%20maxPrice%3A%20%24maxPrice%2C%20payType%3A%20%24payType%2C%20shippingType%3A%20%24shippingType%2C%20serviceType%3A%20%24serviceType)%20%7B%0A%20%20%20%20%20%20salePageList%20%7B%0A%20%20%20%20%20%20%20%20salePageId%0A%20%20%20%20%20%20%20%20title%0A%20%20%20%20%20%20%20%20picUrl%0A%20%20%20%20%20%20%20%20salePageCode%0A%20%20%20%20%20%20%20%20price%0A%20%20%20%20%20%20%20%20suggestPrice%0A%20%20%20%20%20%20%20%20isFav%0A%20%20%20%20%20%20%20%20isComingSoon%0A%20%20%20%20%20%20%20%20isSoldOut%0A%20%20%20%20%20%20%20%20soldOutActionType%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20totalSize%0A%20%20%20%20%20%20shopCategoryId%0A%20%20%20%20%20%20shopCategoryName%0A%20%20%20%20%20%20statusDef%0A%20%20%20%20%20%20listModeDef%0A%20%20%20%20%20%20orderByDef%0A%20%20%20%20%20%20dataSource%0A%20%20%20%20%20%20tags%20%7B%0A%20%20%20%20%20%20%20%20isGroupShowMore%0A%20%20%20%20%20%20%20%20groups%20%7B%0A%20%20%20%20%20%20%20%20%20%20groupId%0A%20%20%20%20%20%20%20%20%20%20groupDisplayName%0A%20%20%20%20%20%20%20%20%20%20isKeyShowMore%0A%20%20%20%20%20%20%20%20%20%20keys%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20keyId%0A%20%20%20%20%20%20%20%20%20%20%20%20keyDisplayName%0A%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20priceRange%20%7B%0A%20%20%20%20%20%20%20%20min%0A%20%20%20%20%20%20%20%20max%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A&operationName=cms_shopCategory&variables=%7B%22shopId%22%3A40686%2C%22categoryId%22%3A0%2C%22startIndex%22%3A{i}%2C%22fetchCount%22%3A100%2C%22orderBy%22%3A%22Newest%22%2C%22isShowCurator%22%3Afalse%2C%22locationId%22%3A0%2C%22tagFilters%22%3A%5B%5D%2C%22tagShowMore%22%3Afalse%2C%22minPrice%22%3Anull%2C%22maxPrice%22%3Anull%2C%22payType%22%3A%5B%5D%2C%22shippingType%22%3A%5B%5D%7D"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(100, 3000, 100)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            response = requests.get(url, headers=header)
            soup = response.json()
            items = soup['data']['shopCategory']['salePageList']['salePageList']
            if items == []:
                print(url)
                continue
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            page_id = item['salePageId']
            img_url = 'https:'+item['picUrl']
            title = item['title']
            url = f'https://www.evaevaacc.com.tw/SalePage/Index/{page_id}'
            try:
                original_price = item['suggestPrice']
            except:
                original_price = ""
            try:
                sale_price = item['price']
            except:
                pass
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)


class AnnsCrawler(BaseCrawler):
    id = 158
    name = "anns"
    prefix_urls = [
        "https://fts-api.91app.com/pythia-cdn/graphql?shopId=123&lang=zh-TW&query=query%20cms_shopCategory(%24shopId%3A%20Int!%2C%20%24categoryId%3A%20Int!%2C%20%24startIndex%3A%20Int!%2C%20%24fetchCount%3A%20Int!%2C%20%24orderBy%3A%20String%2C%20%24isShowCurator%3A%20Boolean%2C%20%24locationId%3A%20Int%2C%20%24tagFilters%3A%20%5BItemTagFilter%5D%2C%20%24tagShowMore%3A%20Boolean%2C%20%24serviceType%3A%20String%2C%20%24minPrice%3A%20Float%2C%20%24maxPrice%3A%20Float%2C%20%24payType%3A%20%5BString%5D%2C%20%24shippingType%3A%20%5BString%5D)%20%7B%0A%20%20shopCategory(shopId%3A%20%24shopId%2C%20categoryId%3A%20%24categoryId)%20%7B%0A%20%20%20%20salePageList(startIndex%3A%20%24startIndex%2C%20maxCount%3A%20%24fetchCount%2C%20orderBy%3A%20%24orderBy%2C%20isCuratorable%3A%20%24isShowCurator%2C%20locationId%3A%20%24locationId%2C%20tagFilters%3A%20%24tagFilters%2C%20tagShowMore%3A%20%24tagShowMore%2C%20minPrice%3A%20%24minPrice%2C%20maxPrice%3A%20%24maxPrice%2C%20payType%3A%20%24payType%2C%20shippingType%3A%20%24shippingType%2C%20serviceType%3A%20%24serviceType)%20%7B%0A%20%20%20%20%20%20salePageList%20%7B%0A%20%20%20%20%20%20%20%20salePageId%0A%20%20%20%20%20%20%20%20title%0A%20%20%20%20%20%20%20%20picUrl%0A%20%20%20%20%20%20%20%20salePageCode%0A%20%20%20%20%20%20%20%20price%0A%20%20%20%20%20%20%20%20suggestPrice%0A%20%20%20%20%20%20%20%20isFav%0A%20%20%20%20%20%20%20%20isComingSoon%0A%20%20%20%20%20%20%20%20isSoldOut%0A%20%20%20%20%20%20%20%20soldOutActionType%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20totalSize%0A%20%20%20%20%20%20shopCategoryId%0A%20%20%20%20%20%20shopCategoryName%0A%20%20%20%20%20%20statusDef%0A%20%20%20%20%20%20listModeDef%0A%20%20%20%20%20%20orderByDef%0A%20%20%20%20%20%20dataSource%0A%20%20%20%20%20%20tags%20%7B%0A%20%20%20%20%20%20%20%20isGroupShowMore%0A%20%20%20%20%20%20%20%20groups%20%7B%0A%20%20%20%20%20%20%20%20%20%20groupId%0A%20%20%20%20%20%20%20%20%20%20groupDisplayName%0A%20%20%20%20%20%20%20%20%20%20isKeyShowMore%0A%20%20%20%20%20%20%20%20%20%20keys%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20keyId%0A%20%20%20%20%20%20%20%20%20%20%20%20keyDisplayName%0A%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20priceRange%20%7B%0A%20%20%20%20%20%20%20%20min%0A%20%20%20%20%20%20%20%20max%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A&operationName=cms_shopCategory&variables=%7B%22shopId%22%3A123%2C%22categoryId%22%3A0%2C%22startIndex%22%3A{i}%2C%22fetchCount%22%3A100%2C%22orderBy%22%3A%22Newest%22%2C%22isShowCurator%22%3Afalse%2C%22locationId%22%3A0%2C%22tagFilters%22%3A%5B%5D%2C%22tagShowMore%22%3Afalse%2C%22minPrice%22%3Anull%2C%22maxPrice%22%3Anull%2C%22payType%22%3A%5B%5D%2C%22shippingType%22%3A%5B%5D%7D"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(100, 3000, 100)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            response = requests.get(url, headers=header)
            soup = response.json()
            items = soup['data']['shopCategory']['salePageList']['salePageList']
            if items == []:
                print(url)
                continue
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            page_id = item['salePageId']
            img_url = 'https:'+item['picUrl']
            title = item['title']
            url = f'https://www.anns.tw/SalePage/Index/{page_id}'
            try:
                original_price = item['suggestPrice']
            except:
                original_price = ""
            try:
                sale_price = item['price']
            except:
                pass
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class ActivherCrawler(BaseCrawler):
    id = 114
    name = 'activher'
    prefix_urls = ["https://tw.activher.com/shop/page/{i}/"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 30)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:

                items = soup.find('ul', {'class': 'products columns-3'}).find_all("li")

                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            page_id = item.get('class')[2]
            img_url = item.find('img').get('src')
            title = item.find('h2', {'class': 'woocommerce-loop-product__title'}).text

            url = item.find('a').get('href')
            try:
                original_price = float(item.find('div', {
                                       'class': 'global-primary dark-primary price sl-price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find('span', {'class': 'price'}).text.strip(
                    ' \n ').replace("NT$", "").replace(",", ""))

            except:
                try:
                    sale_price = float(item.find(
                        'div', {'class': 'global-primary dark-primary price sl-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
                except:

                    sale_price = item.find('div', {'class': 'price-sale price sl-price primary-color-price'}
                                           ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~")
                    if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                        sale_price = float(sale_price[0].strip())
                    elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                        sale_price = float(sale_price[-1].strip())
                    else:
                        sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class FmshoesCrawler(BaseCrawler):
    id = 131
    name = 'fmshoes'
    prefix_urls = [
        "https://www.fmshoes.com.tw/product_store?attribute_min_price=&attribute_max_price=&store_type_sn=26&category_sn=&sort_by=top_sale&page={i}&col_items=#div_middle"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 50)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            # print(soup)
            # break
            try:
                items = soup.find('ul', {'class': 'pd_list row_2'}).find_all("li")
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):

        try:

            img_url = item.find('img').get('data-original')
            title = item.find('h2').text

            url = item.find('a').get('href')
            page_id = url.split('product_sn=')[-1].split('&color_sn=')[0]
            if url.find('&color_sn=') > -1:
                page_id = page_id+'_'+url.split('&color_sn=')[-1]
            try:
                original_price = float(item.find('span', {'class': 'sale_price'}).text.strip(
                    ' \n ').replace("$", "").replace(",", ""))
            except:
                original_price = ""

            try:
                sale_price = float(item.find('span', {'class': 'activity_price'}
                                             ).text.strip(' \n ').replace("$", "").replace(",", ""))

            except:
                try:
                    sale_price = float(item.find(
                        'div', {'class': 'global-primary dark-primary price sl-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
                except:

                    sale_price = item.find('div', {'class': 'price-sale price sl-price primary-color-price'}
                                           ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~")
                    if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                        sale_price = float(sale_price[0].strip())
                    elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                        sale_price = float(sale_price[-1].strip())
                    else:
                        sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)


class Red21Crawler(BaseCrawler):
    id = 257
    name = 'red21'
    prefix_urls = ["https://www.red-21.co/products?page={i}&sort_by=&order_by=&limit=72"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 20)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:

                items = soup.find('div', {'class': 'col-xs-12 ProductList-list'}).find_all('product-item')

                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            url = item.find('a').get('href')
            page_id = item.get('product-id')
            img_url = item.find('div', {'class': 'boxify-image js-boxify-image center-contain sl-lazy-image second-image'}).get(
                'style').split('(')[-1].replace('?)', '')
            title = item.find('div', {'class': 'title text-primary-color'}).text
            try:
                original_price = float(item.find('div', {
                                       'class': 'global-primary dark-primary price sl-price price-crossed'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find(
                    'div', {'class': 'global-primary dark-primary price sl-price'}).text.strip(' \n ').replace("NT$", "").replace(",", ""))
            except:
                sale_price = item.find('div', {'class': 'price-sale price sl-price primary-color-price'}
                                       ).text.strip(' \n ').replace("NT$", "").replace(",", "").split("~")
                if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                    sale_price = float(sale_price[0].strip())
                elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                    sale_price = float(sale_price[-1].strip())
                else:
                    sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class CordateCrawler(BaseCrawler):
    id = 132
    name = 'cordate'
    prefix_urls = ["https://www.cordate.tw/products?offset={i}"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(0, 1000, 21)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        session = HTMLSession()
        for url in self.urls:
            print(url)
            response = session.get(url)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find('div', {'class': 'rmq-478728fa'}).find_all('div', {'class': 'rmq-3ab81ca3'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        data = (item.text)
        dt = data.split('NT$')
        try:
            url = 'https://www.cordate.tw'+item.find('a').get('href')
            title = dt[0]
            img_url = item.find('img').get('src')
            page_id = url.split('/')[-1]
            try:
                original_price = float(item.find('s').text.strip(' \n ').replace("NT$", "").replace(",", "").strip())
            except:
                original_price = ""
            sale_price = float(item.find_all('div')[-1].text.strip(' \n ').replace("NT$", "").replace(",", ""))
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class ChuchustyleCrawler(BaseCrawler):
    id = 91
    name = 'chuchustyle'
    prefix_urls = ["https://www.chuchustyle.com.tw/product.php?page={i}&cid=24#prod_list"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 6)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find_all('div', {'class': 'thumbnail'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            url = item.find('a').get('href')
            title = item.find('a').get('title')
            img_url = item.find('img').get('data-original')
            try:
                a = img_url.split('/')[-1]
                page_id = (str(base64.b64decode(a)).split('.jpg')[0].split('/')[-1])
            except:
                page_id = url.split('&pid=')[-1]
            try:
                original_price = float(
                    item.find('div', {'class': 'prod-price'}).find('del').text.strip(' \n ').replace("NT.", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find('div', {'class': 'prod-price'}
                                             ).text.strip(' \n ').replace("NT.", "").replace(",", ""))
            except:
                sale_price = float(item.find('span', {'class': 'text-danger'}
                                             ).text.strip(' \n ').replace("NT.", "").replace(",", ""))
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class IpinkCrawler(BaseCrawler):
    id = 137
    name = "ipink"
    prefix_urls = [
        "https://fts-api.91app.com/pythia-cdn/graphql?shopId=618&lang=zh-TW&query=query%20cms_shopCategory(%24shopId%3A%20Int!%2C%20%24categoryId%3A%20Int!%2C%20%24startIndex%3A%20Int!%2C%20%24fetchCount%3A%20Int!%2C%20%24orderBy%3A%20String%2C%20%24isShowCurator%3A%20Boolean%2C%20%24locationId%3A%20Int%2C%20%24tagFilters%3A%20%5BItemTagFilter%5D%2C%20%24tagShowMore%3A%20Boolean%2C%20%24serviceType%3A%20String%2C%20%24minPrice%3A%20Float%2C%20%24maxPrice%3A%20Float%2C%20%24payType%3A%20%5BString%5D%2C%20%24shippingType%3A%20%5BString%5D)%20%7B%0A%20%20shopCategory(shopId%3A%20%24shopId%2C%20categoryId%3A%20%24categoryId)%20%7B%0A%20%20%20%20salePageList(startIndex%3A%20%24startIndex%2C%20maxCount%3A%20%24fetchCount%2C%20orderBy%3A%20%24orderBy%2C%20isCuratorable%3A%20%24isShowCurator%2C%20locationId%3A%20%24locationId%2C%20tagFilters%3A%20%24tagFilters%2C%20tagShowMore%3A%20%24tagShowMore%2C%20minPrice%3A%20%24minPrice%2C%20maxPrice%3A%20%24maxPrice%2C%20payType%3A%20%24payType%2C%20shippingType%3A%20%24shippingType%2C%20serviceType%3A%20%24serviceType)%20%7B%0A%20%20%20%20%20%20salePageList%20%7B%0A%20%20%20%20%20%20%20%20salePageId%0A%20%20%20%20%20%20%20%20title%0A%20%20%20%20%20%20%20%20picUrl%0A%20%20%20%20%20%20%20%20salePageCode%0A%20%20%20%20%20%20%20%20price%0A%20%20%20%20%20%20%20%20suggestPrice%0A%20%20%20%20%20%20%20%20isFav%0A%20%20%20%20%20%20%20%20isComingSoon%0A%20%20%20%20%20%20%20%20isSoldOut%0A%20%20%20%20%20%20%20%20soldOutActionType%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20totalSize%0A%20%20%20%20%20%20shopCategoryId%0A%20%20%20%20%20%20shopCategoryName%0A%20%20%20%20%20%20statusDef%0A%20%20%20%20%20%20listModeDef%0A%20%20%20%20%20%20orderByDef%0A%20%20%20%20%20%20dataSource%0A%20%20%20%20%20%20tags%20%7B%0A%20%20%20%20%20%20%20%20isGroupShowMore%0A%20%20%20%20%20%20%20%20groups%20%7B%0A%20%20%20%20%20%20%20%20%20%20groupId%0A%20%20%20%20%20%20%20%20%20%20groupDisplayName%0A%20%20%20%20%20%20%20%20%20%20isKeyShowMore%0A%20%20%20%20%20%20%20%20%20%20keys%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20keyId%0A%20%20%20%20%20%20%20%20%20%20%20%20keyDisplayName%0A%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20priceRange%20%7B%0A%20%20%20%20%20%20%20%20min%0A%20%20%20%20%20%20%20%20max%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A&operationName=cms_shopCategory&variables=%7B%22shopId%22%3A618%2C%22categoryId%22%3A0%2C%22startIndex%22%3A{i}%2C%22fetchCount%22%3A100%2C%22orderBy%22%3A%22Newest%22%2C%22isShowCurator%22%3Afalse%2C%22locationId%22%3A0%2C%22tagFilters%22%3A%5B%5D%2C%22tagShowMore%22%3Afalse%2C%22minPrice%22%3Anull%2C%22maxPrice%22%3Anull%2C%22payType%22%3A%5B%5D%2C%22shippingType%22%3A%5B%5D%7D"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(0, 3000, 100)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            response = requests.get(url, headers=header)
            soup = response.json()
            items = soup['data']['shopCategory']['salePageList']['salePageList']
            if items == []:
                print(url)
                continue

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            page_id = item['salePageId']
            img_url = 'https:'+item['picUrl']
            title = item['title']

            url = f'https://www.ipink.com.tw/SalePage/Index/{page_id}'
            try:
                original_price = item['suggestPrice']
            except:
                original_price = ""

            try:
                sale_price = item['price']
            except:
                pass
            if original_price == sale_price:
                original_price = ""
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class SuizaCrawler(BaseCrawler):
    id = 156
    name = 'suiza'
    prefix_urls = ["https://www.suizaitaly.com.tw/product.php?page={i}&cid=1#prod_list"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 20)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:

                items = soup.find_all('div', {'class': 'thumbnail'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            url = item.find('a').get('href')
            title = item.find('a').get('title')
            img_url = item.find('img').get('data-original')
            try:
                a = img_url.split('/')[-1]
                page_id = (str(base64.b64decode(a)).split('.jpg')[0].split('/')[-1])
            except:
                page_id = url.split('&pid=')[-1]
            try:
                original_price = float(
                    item.find('div', {'class': 'prod-price'}).find('del').text.strip(' \n ').replace("NT.", "").replace(",", ""))
            except:
                original_price = ""

            try:
                sale_price = float(item.find('div', {'class': 'prod-price'}
                                             ).text.strip(' \n ').replace("NT.", "").replace(",", ""))
            except:
                sale_price = float(item.find('span', {'class': 'text-danger'}
                                             ).text.strip(' \n ').replace("NT.", "").replace(",", ""))

        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class QmomoCrawler(BaseCrawler):
    id = 121
    name = "qmomo"
    prefix_urls = [
        "https://fts-api.91app.com/pythia-cdn/graphql?shopId=348&lang=zh-TW&query=query%20cms_shopCategory(%24shopId%3A%20Int!%2C%20%24categoryId%3A%20Int!%2C%20%24startIndex%3A%20Int!%2C%20%24fetchCount%3A%20Int!%2C%20%24orderBy%3A%20String%2C%20%24isShowCurator%3A%20Boolean%2C%20%24locationId%3A%20Int%2C%20%24tagFilters%3A%20%5BItemTagFilter%5D%2C%20%24tagShowMore%3A%20Boolean%2C%20%24serviceType%3A%20String%2C%20%24minPrice%3A%20Float%2C%20%24maxPrice%3A%20Float%2C%20%24payType%3A%20%5BString%5D%2C%20%24shippingType%3A%20%5BString%5D)%20%7B%0A%20%20shopCategory(shopId%3A%20%24shopId%2C%20categoryId%3A%20%24categoryId)%20%7B%0A%20%20%20%20salePageList(startIndex%3A%20%24startIndex%2C%20maxCount%3A%20%24fetchCount%2C%20orderBy%3A%20%24orderBy%2C%20isCuratorable%3A%20%24isShowCurator%2C%20locationId%3A%20%24locationId%2C%20tagFilters%3A%20%24tagFilters%2C%20tagShowMore%3A%20%24tagShowMore%2C%20minPrice%3A%20%24minPrice%2C%20maxPrice%3A%20%24maxPrice%2C%20payType%3A%20%24payType%2C%20shippingType%3A%20%24shippingType%2C%20serviceType%3A%20%24serviceType)%20%7B%0A%20%20%20%20%20%20salePageList%20%7B%0A%20%20%20%20%20%20%20%20salePageId%0A%20%20%20%20%20%20%20%20title%0A%20%20%20%20%20%20%20%20picUrl%0A%20%20%20%20%20%20%20%20salePageCode%0A%20%20%20%20%20%20%20%20price%0A%20%20%20%20%20%20%20%20suggestPrice%0A%20%20%20%20%20%20%20%20isFav%0A%20%20%20%20%20%20%20%20isComingSoon%0A%20%20%20%20%20%20%20%20isSoldOut%0A%20%20%20%20%20%20%20%20soldOutActionType%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20totalSize%0A%20%20%20%20%20%20shopCategoryId%0A%20%20%20%20%20%20shopCategoryName%0A%20%20%20%20%20%20statusDef%0A%20%20%20%20%20%20listModeDef%0A%20%20%20%20%20%20orderByDef%0A%20%20%20%20%20%20dataSource%0A%20%20%20%20%20%20tags%20%7B%0A%20%20%20%20%20%20%20%20isGroupShowMore%0A%20%20%20%20%20%20%20%20groups%20%7B%0A%20%20%20%20%20%20%20%20%20%20groupId%0A%20%20%20%20%20%20%20%20%20%20groupDisplayName%0A%20%20%20%20%20%20%20%20%20%20isKeyShowMore%0A%20%20%20%20%20%20%20%20%20%20keys%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20keyId%0A%20%20%20%20%20%20%20%20%20%20%20%20keyDisplayName%0A%20%20%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20priceRange%20%7B%0A%20%20%20%20%20%20%20%20min%0A%20%20%20%20%20%20%20%20max%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A&operationName=cms_shopCategory&variables=%7B%22shopId%22%3A348%2C%22categoryId%22%3A0%2C%22startIndex%22%3A{i}%2C%22fetchCount%22%3A100%2C%22orderBy%22%3A%22Newest%22%2C%22isShowCurator%22%3Afalse%2C%22locationId%22%3A0%2C%22tagFilters%22%3A%5B%5D%2C%22tagShowMore%22%3Afalse%2C%22minPrice%22%3Anull%2C%22maxPrice%22%3Anull%2C%22payType%22%3A%5B%5D%2C%22shippingType%22%3A%5B%5D%7D"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(0, 3000, 100)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            response = requests.get(url, headers=header)
            soup = response.json()
            items = soup['data']['shopCategory']['salePageList']['salePageList']
            if items == []:
                print(url)
                continue
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            page_id = item['salePageId']
            img_url = 'https:'+item['picUrl']
            title = item['title']
            url = f'https://www.qmomo.com.tw/SalePage/Index/{page_id}'
            try:
                original_price = item['suggestPrice']
            except:
                original_price = ""
            try:
                sale_price = item['price']
            except:
                pass
            if original_price == sale_price:
                original_price = ""
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

class BrodnydCrawler(BaseCrawler):
    id = 177
    name = 'brodnyd'
    prefix_urls = ["https://www.brodnyd.tw/%E5%85%A8%E9%83%A8%E5%95%86%E5%93%81?page={i}"]
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 30)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            print(url)
            response = requests.get(url, headers=header)
            soup = BeautifulSoup(response.text, features='html.parser')
            try:
                items = soup.find_all('div', {'class': 'grid-box'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, item):
        try:
            url = item.find('a').get('href')
            page_id = item.get('data-producttlid')
            try:
                img_url = 'https:'+item.find('img').get('data-src')
            except:
                img_url = 'https:'+item.find('img').get('src')
            title = item.find('img').get('title')
            try:
                original_price = float(item.find('span', {'class': 'price-old'}
                                                 ).text.strip(' \n ').replace("$", "").replace(",", ""))
            except:
                original_price = ""
            try:
                sale_price = float(item.find('span', {'class': 'price-new'}
                                             ).text.strip(' \n ').replace("$", "").replace(",", ""))
            except:
                try:
                    sale_price = float(item.find('span', {'class': 'price-label'}
                                                 ).text.strip(' \n ').replace("$", "").replace(",", ""))
                except:
                    sale_price = item.find('div', {'class': 'price'}).text.strip(
                        ' \n ').replace("$", "").replace(",", "").split("~")
                    if(float(sale_price[0].strip()) < float(sale_price[-1].strip())):
                        sale_price = float(sale_price[0].strip())
                    elif(float(sale_price[0].strip()) > float(sale_price[-1].strip())):
                        sale_price = float(sale_price[-1].strip())
                    else:
                        sale_price = float(sale_price[0].strip())
        except:
            return
        return Product(title, url, page_id, img_url, original_price, sale_price)

def get_crawler(crawler_id):
    crawlers = {
        "1": GracegiftCrawler(),
        "2": LegustCrawler(),
        "3": RubysCrawler(),
        "4": AjpeaceCrawler(),
        "5": MajormadeCrawler(),
        "7": BasicCrawler(),
        "8": AirspaceCrawler(),
        # "9": YocoCrawler(),
        "10": EfshopCrawler(),
        "11": ModaCrawler(),
        "13": KkleeCrawler(),
        "14": WishbykoreaCrawler(),
        "15": AspeedCrawler(),
        "17": OpenladyCrawler(),
        "20": AzoomCrawler(),
        "21": RoxyCrawler(),
        "22": ShaxiCrawler(),
        "24": InshopCrawler(),
        "25": AmesoeurCrawler(),
        "28": FolieCrawler(),
        "29": CorbanCrawler(),
        "31": JulyCrawler(),
        "32": PerCrawler(),
        "33": CerealCrawler(),
        "37": IrisCrawler(),
        "39": NookCrawler(),
        "41": RainbowCrawler(),
        "42": QueenshopCrawler(),
        "43": NeedCrawler(),
        "45": GogosingCrawler(),
        "46": RoshopCrawler(),
        "47": CirclescinemaCrawler(),
        "48": CozyfeeCrawler(),  # li沒class
        "49": ReishopCrawler(),
        "50": YourzCrawler(),
        "51": WstyleCrawler(),
        "52": ApplestarryCrawler(),
        "53": KerinaCrawler(),
        "54": SeoulmateCrawler(),
        "56": PazzoCrawler(),
        "57": MeierqCrawler(),  # li沒class
        "58": HarperCrawler(),  # json
        "59": LurehsuCrawler(),
        "60": MosdressCrawler(),
        # "61": PufiiCrawler(),  # json
        "62": MougganCrawler(),
        "63": JendesCrawler(),
        "64": MercciCrawler(),  # li沒class
        "65": SivirCrawler(),
        "66": NanaCrawler(),
        "69": Boy2Crawler(),
        "70": AachicCrawler(),
        "71": LovsoCrawler(),
        "74": SuitangtangCrawler(),
        "76": MiustarCrawler(),
        "78": ChochobeeCrawler(),  # V
        "79": BasezooCrawler(),  # 搬家中
        "81": KiyumiCrawler(),
        "82": GenquoCrawler(),
        "83": PotatochicksCrawler(),
        "85": SumiCrawler(),
        "86": OolalaCrawler(),
        "88": CocojojoCrawler(),
        "89": StudioCrawler(),
        "90": SchemingggCrawler(),
        "91": ChuchustyleCrawler(),
        "92": BisouCrawler(),
        "94": LaconicCrawler(),
        "95": LulusCrawler(),
        "96": PixelcakeCrawler(),
        "97": MiyukiCrawler(),
        "99": PerchaCrawler(),
        "100": NabCrawler(),
        "101": SquarebearCrawler(),
        "102": MojpCrawler(),
        "103": GoddessCrawler(),
        "104": PleatsCrawler(),
        "105": ZebraCrawler(),  # json
        "107": MiharaCrawler(),
        # "108": EyecreamCrawler(),
        "109": CandyboxCrawler(),
        "112": VeryyouCrawler(),
        "113": StayfoxyCrawler(),
        "114": ActivherCrawler(),
        "115": GracechowCrawler(),
        "116": LativCrawler(),
        "118": RightonCrawler(),
        "120": DafCrawler(),
        "121": QmomoCrawler(),
        "122": SexyinshapeCrawler(),
        "125": MiniqueenCrawler(),
        "126": SandaruCrawler(),
        "127": BonbonsCrawler(),
        "130": BaibeautyCrawler(),
        "131": FmshoesCrawler(),
        "132": CordateCrawler(),
        "136": DaimaCrawler(),
        "137": IpinkCrawler(),
        "138": MiakiCrawler(),
        "139": VinaclosetCrawler(),
        "140": UneCrawler(),
        "141": StylemooncatCrawler(),
        "142": LovfeeCrawler(),
        # "143": MarjorieCrawler(),
        "144": PureeCrawler(),
        "147": RereburnCrawler(),
        # "147": StylenandaCrawler(),
        "148": ThegirlwhoCrawler(),
        # "149": MumushopCrawler(), Exceeded: 8000 ms exceeded.
        # "150": ChuuCrawler(),
        # "151": AleyCrawler(),
        # "152": TrudamodaCrawler(),
        "155": EvermoreCrawler(),
        "156": SuizaCrawler(),
        "157": LamochaCrawler(),
        "158": AnnsCrawler(),
        "159": AndenhudCrawler(),
        "161": EvaCrawler(),
        "162": VemarCrawler(),
        "163": VizzleCrawler(),
        "164": WemeCrawler(),
        "166": PixyCrawler(),  # V
        # "170": AnnadollyCrawler(),
        "171": MimiriccoCrawler(),
        # "172": RobinmayCrawler(),
        "174": AfashionshowroomCrawler(),
        "177": BrodnydCrawler(),
        "178": DejavuCrawler(),
        "179": StarkikiCrawler(),
        "180": KavaCrawler(),
        "182": BuchaCrawler(),
        "183": YveCrawler(),
        "185": TennyshopCrawler(),
        "186": MypopcornCrawler(),
        "187": GoodlogoCrawler(),
        "189": ShopCrawler(),
        "190": HealerCrawler(),
        "194": AlmashopCrawler(),
        "196": LeatherCrawler(),  # V
        "198": MuminCrawler(),
        "206": BelloCrawler(),
        "216": AttentionCrawler(),
        "221": WhoiannCrawler(),
        "222": GutenCrawler(),
        "223": DesireCrawler(),
        "228": CocochiliCrawler(),
        "225": ReallifeCrawler(),  # V
        "234": CoochadCrawler(),  # V
        "235": AnderlosCrawler(),  # V
        "236": ControlfreakCrawler(),  # V
        "237": KokokoreaCrawler(),
        "238": OhherCrawler(),
        "239": AfadCrawler(),
        "240": KiiwioCrawler(),
        "241": RachelworldCrawler(),  # V
        # "242": QuentinaCrawler(), #lazy
        "243": GalleryCrawler(),  # V
        "244": ToofitCrawler(),  # V
        "245": YurubraCrawler(),
        "246": GozoCrawler(),
        "248": ChiehCrawler(),  # V
        "250": ChangeuCrawler(),  # V
        "255": IruitwCrawler(),
        "257": Red21Crawler(),
        "266": LalalatwCrawler(),
        "272": AormoreCrawler(),
        "278": AriaspaceCrawler(),
        "280": VacanzaCrawler(),
        "295": DeerwCrawler(),
        "296": PreuniCrawler(),
        "297": Seaaa1Crawler(),
        "298": SpotlightCrawler(),  # V
        "299": RewearingCrawler(),
        "300": LstylestudioCrawler(),
        "301": GirlsmondayCrawler(),
        "302": OurstudioCrawler(),
        "303": PennyncoCrawler(),
        "304": UnefemmeCrawler(),
        "306": YsquareCrawler(),
        "312": SnatchCrawler(),
        "313": OliviaCrawler(),
        "315": DastoreCrawler(),
        "316": NotjustonlyCrawler(),
        "332": SdareCrawler(),
        "337": AllgenderCrawler(),
        "341": PimgoCrawler(),
        "342": GotobuyCrawler(),
        "347": FudgeCrawler(),
        "354": BigbaevdayCrawler(),
        "355": NovyyCrawler(),
        "356": MyameCrawler(),
        "375": LeviaCrawler(),
        "381": MymybagCrawler(),
        "382": FabulousCrawler(),  # 倒
        "383": ZouwaCrawler(),
        "384": NinetwonineCrawler(),
        "385": FeminCrawler(),
        "386": HuitcoCrawler(),
        "387": FeatherCrawler(),
        "388": HoukoreaCrawler(),
        "389": MaaCrawler(),
        "390": RosirosCrawler(),
        "391": Me30Crawler(),
        "392": FeelneCrawler(),
        "393": IlymCrawler(),
        "394": DfinaCrawler(),
        "395": Ss33Crawler(),
        "396": MollyCrawler(),
        "397": MornmoodCrawler(),
        "398": BigpotatoCrawler(),
        "399": DarkcirclesCrawler(),
        "400": ShiauzCrawler(),
        "401": MandoCrawler(),
        "402": HermosaCrawler(),
        "403": ThedailyCrawler(),
        "404": HuestudiosCrawler(),
        "405": OmostudioCrawler(),
        "406": PeachanCrawler(),
        "407": SomethingmeCrawler(),
        "408": OutfitCrawler(),
        "409": CharleneCrawler(),
        "410": OhlalaCrawler(),
        "411": YandjstyleCrawler(),
        "412": HouseladiesCrawler(),
        "413": IspotyellowCrawler(),
        "414": MiashiCrawler(),
        "415": FashionforyesCrawler(),
        "416": LiusannCrawler(),
        "417": WondershopCrawler(),
        "418": ClothinglabCrawler(),
        "419": OliolioliCrawler(),
        "420": MaisonmCrawler(),
        "421": ClothesCrawler(),
        "422": HolkeeCrawler(),
        "423": NelmuseoCrawler(),
        "424": KisssilverCrawler(),
        "425": ClubdianaCrawler(),
        "426": FigwooCrawler(),
        "427": TheshapeCrawler(),
        "428": CarabellaCrawler(),
        "430": N34Crawler(),
        "431": WhomforCrawler(),
        "432": CycomyuCrawler(),
        "433": AphroCrawler(),
        "434": MoriiCrawler(),
        "435": XwysiblingsCrawler(),
        "436": VvvlandCrawler(),
        "437": VstoreCrawler(),
        "438": NjmusesCrawler(),
        "439": GirlsdiaryCrawler(),
        "440": Closet152Crawler(),
        "441": XuaccCrawler(),
        "442": Menu12Crawler(),
        "443": Vior2015Crawler(),
        "444": Nora38Crawler(),
        "445": UnuselfCrawler(),
        "446": KoilifefCrawler(),
        "447": SymbolictrueCrawler(),
    }
    return crawlers.get(str(crawler_id))
