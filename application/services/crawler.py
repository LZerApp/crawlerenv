import re
import json
from collections import namedtuple
from datetime import datetime
from typing import ItemsView
from requests_html import HTMLSession
import requests
import csv
from bs4 import BeautifulSoup
from openpyxl import Workbook
from base64 import b64decode
from gzip import decompress
from config import ENV_VARIABLE

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
        "user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
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
            response = requests.post(
                verify=False, url=url, files=files, headers=headers
            )
            print(response.status_code)
            # os.remove(filename+'.xlsx')
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
            f"{self.base_url}/categories/all-%E6%89%80%E6%9C%89%E5%95%86%E5%93%81?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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
            f"{self.base_url}/products?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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
            f"{self.base_url}/categories/all-items-1?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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


class AspeedCrawler(BaseCrawler):
    id = 15
    name = "aspeed"
    base_url = "https://www.aspeed.co"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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

    def parse(self):
        urls = [
            f"{self.base_url}/catalog.php?m=115&s=249&t=0&sort=&page={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("section", {"class": "cataList cataList-align-left cataList-4x"}).find_all("li")
            print(url)
            if not items:
                print(url, 'break')
                break
            self.result.extend([self.parse_product(item) for item in items])

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
            f"{self.base_url}/categories/view-all?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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
            f"{self.base_url}/products?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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
            f"{self.base_url}/products?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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

class StayfoxyCrawler(BaseCrawler):
    id = 113
    name = "stayfoxy"
    base_url = "https://www.stayfoxyshop.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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
            f"{self.base_url}/categories/women?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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


class DeerwCrawler(BaseCrawler):
    id = 295
    name = "deerw"
    base_url = "https://www.deerw.net"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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
            f"{self.base_url}/products?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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


class KkleeCrawler(BaseCrawler):
    id = 13
    name = "kklee"
    base_url = "https://www.kklee.co"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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

class OolalaCrawler(BaseCrawler):
    id = 86
    name = "oolala"
    base_url = "https://www.styleoolala.com"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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

class ChiehCrawler(BaseCrawler):
    id = 248
    name = "chieh"
    base_url = "https://www.chieh.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/products?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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


class Seaaa1Crawler(BaseCrawler):
    id = 297
    name = "seaaa1"
    base_url = "https://www.seaaa1.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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


class KiiwioCrawler(BaseCrawler):
    id = 240
    name = "kiiwio"
    base_url = "https://www.kiiwio.com"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all-product?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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
            f"{self.base_url}/categories/all?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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
            f"{self.base_url}/categories/?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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

class OhherCrawler(BaseCrawler):
    id = 238
    name = "ohher"
    base_url = "https://www.ohher.co"

    def parse(self):
        urls = [
            f"{self.base_url}/categories/all?page={i}&sort_by=&order_by=&limit=72" for i in range(1, page_Max)]
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
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "global-primary dark-primary price sl-price"}).text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "price-sale price sl-price primary-color-price"}).text)
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
            f"{self.base_url}/products?page={i}" for i in range(1, page_Max)]
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
                sale_price = self.get_price(item.find("div", {"class": "price-sale price"}).text)
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
        get_max_page = "https://www.airspaceonline.com/PDList.asp?color=&keyword=&pp1=all&pp2=&pp3=&newpd=&ob=A&pageno=200"
        response = requests.request("GET", get_max_page, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        max_page = soup.find("div", {"class": "pdpager"}).find("font").text
        max_page = int(max_page)
        print(max_page)
        urls = [
            f"{self.base_url}/PDList.asp?color=&keyword=&pp1=all&pp2=&pp3=&newpd=&ob=A&pageno={i}" for i in range(1, max_page+1)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
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
    base_url = "https://www.corban.com.tw/SalePage/Index/"  # 要記得改
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

    variables = {"shopId": 40995, "categoryId": 382947, "fetchCount": 200,
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
    base_url = "https://www.lovso.com.tw/Shop"

    def parse(self):
        url = f"{self.base_url}/itemList.aspx?m=8&o=0&sa=0&smfp=0"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = soup.find_all("div", {"class": "itemListDiv"})
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "itemListMerName"}).find("a").text
        link = item.find("a").get("href")
        link_id = stripID(link, "mNo1=")
        link_id = b_stripID(link_id, "&m")
        link = f"{self.base_url}/{link}"

        image_url = item.find("img").get("src")
        try:
            original_price = self.get_price(item.find(
                "div", {"class": "itemListOrigMoney"}).find('span').text)
            sale_price = self.get_price(
                item.find("div", {"class": "itemListMoney itemHasOrig"}).find('span').text)
        except:
            original_price = ""
            sale_price = self.get_price(
                item.find("div", {"class": "itemListMoney"}).find('span').text)
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
        urls = [f"{self.base_url}/zh-tw/tag/HOTTEST?P={i}" for i in range(1, page_Max)]
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
    urls = [
        f"https://www.mihara.com.tw/product.php?page={i}&cid=1#prod_list"
        for i in range(1, 15)
    ]

    def parse(self):
        for url in self.urls:
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


class UnefemmeCrawler(BaseCrawler):
    id = 304
    name = "unefemme"
    base_url = "https://www.unefemme.com.tw"

    def parse(self):
        urls = [f"{self.base_url}/product.php?page={i}&cid=60#prod_list" for i in range(1, 3)]
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


class NanaCrawler(BaseCrawler):
    id = 66
    name = "nana"
    base_url = "https://www.2nana.tw"

    def parse(self):
        url = f"{self.base_url}/product.php?page=1&cid=1#prod_list"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        items = soup.find_all("div", {"class": "col-xs-6 col-sm-4 col-md-3"})
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
                items = soup.find("ul", {"class": "items-list list-array-4"}).find_all("li")
            except:
                print(url)
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        # print(item)
        title = item.find("p").text
        link = item.find("a").get("href")
        link_id = stripID(link, "ID=")
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
        title = item.find("div", {"class": "cardName"}).text
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
        link_id = b_stripID(link_id, "-")
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find("span", {"class": "no-"}).text)
            sale_price = self.get_price(item.find("div", {"class": "price"}).contents[1])
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
        # if(item.find("div", {"class": "Sold_Out"})):
        #     return
        title = item.find("img").get("alt")
        link = item.find("a").get("href")
        link_id = item.get("id")
        link_id = link_id.replace("product-list-", "")
        link_id = b_stripID(link_id, "-")
        image_url = item.find("img").get("data-original")
        try:
            original_price = self.get_price(item.find("span", {"class": "price"}).contents[0].text)
            sale_price = self.get_price(item.find("span", {"class": "price"}).contents[1])
        except:
            original_price = ""
            sale_price = self.get_price(item.find("span", {"class": "price"}).contents[0])

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
            f"{self.base_url}/collections/all-1?limit=72&page={i}&sort=featured" for i in range(1, page_Max)]
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
        link_id = stripID(link_id, "/products/")
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
            print(item.find("p", {"class": "grid-link__title"}).text)
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
        image_url = item.find("img").get("data-lazy-src")
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
    base_url = "https://sandarushop.com"

    def parse(self):
        urls = [
            f"{self.base_url}/product/all?page={i}" for i in range(1, page_Max)]
        for url in urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("ul", {"class": "list-unstyled item_content clearfix"}).find_all(
                "a", {"class": 'clearfix'})
            if not items:
                break

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("h4").text
        link = item.get("href")
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


# 142_LOVFEE
class LovfeeCrawler(BaseCrawler):
    id = 142
    name = "lovfee"
    urls = [
        f"https://www.lovfee.com/PDList2.asp?item1=01&item2=&item3=&keyword=&ob=A&pagex=&pageno={i}"
        for i in range(1, 22)
    ]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("div", {"id": "productList"}).find_all("li")
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "pdname"}).text
        link = "https://www.lovfee.com/" + item.find("a").get("href")
        link_id = link.split("?")[-1]
        image_url = item.find("img").get("src")
        original_price = (
            item.find("span", {"class": "original"}).text
            if item.find("span", {"class": "original"})
            else ""
        )
        sale_price = (
            item.find("span", {"class": "sale"}).text
            if item.find("span", {"class": "original"})
            else item.find("span", {"class": "normal"}).text
        )

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


# 146_Rereburn
class RereburnCrawler(BaseCrawler):
    id = 146
    name = "rereburn"
    urls = [
        f"https://www.rereburn.com.tw/products?page={i}&sort_by=&order_by=&limit=24"
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
class StylenandaCrawler(BaseCrawler):
    id = 147
    name = "stylenanda"
    prefix_urls = [
        "https://tw.stylenanda.com/product/list.html?cate_no=613",
        "https://tw.stylenanda.com/product/list_3ce_main.html?cate_no=1784",
        "https://tw.stylenanda.com/product/list_made_main.html?cate_no=182",
        "https://tw.stylenanda.com/product/list.html?cate_no=460",
        "https://tw.stylenanda.com/product/list.html?cate_no=1323",
        "https://tw.stylenanda.com/product/list.html?cate_no=2094",
        "https://tw.stylenanda.com/product/list.html?cate_no=51",
        "https://tw.stylenanda.com/product/list.html?cate_no=50",
        "https://tw.stylenanda.com/product/list.html?cate_no=54",
        "https://tw.stylenanda.com/product/list.html?cate_no=52",
        "https://tw.stylenanda.com/product/list.html?cate_no=53",
        "https://tw.stylenanda.com/product/list.html?cate_no=56",
        "https://tw.stylenanda.com/product/list.html?cate_no=77",
        "https://tw.stylenanda.com/product/list.html?cate_no=55",
        "https://tw.stylenanda.com/product/list.html?cate_no=174",
        "https://tw.stylenanda.com/product/list_outlet.html?cate_no=3175",
    ]
    urls = [
        f"{prefix}&page=4={i}" for prefix in prefix_urls for i in range(1, 14)]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all("li", {"class": "item xans-record-"})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        pre_title = item.find("div", {"class": "name"}).text
        title = pre_title.split(":")[1]
        link = "https://tw.stylenanda.com" + item.find("a").get("href")
        link_id = link.split("?")[-1]
        image_url = item.find("img").get("src")
        price = item.find("p", {"class": "price"})
        sale_price = (price.find("span").text).replace("→", "")
        original_price = item.find("p", {"class": "price"}).text.split("→")[0]
        original_price = original_price.lstrip()
        original_price = original_price.strip("NT$")
        sale_price = sale_price.lstrip()
        sale_price = sale_price.strip("NT$")
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 148_THEGIRLWHO
class ThegirlwhoCrawler(BaseCrawler):
    id = 148
    name = "thegirlwho"
    urls = [
        f"https://www.thegirlwhoshop.com/product.php?page={i}&cid=1#prod_list"
        for i in range(1, 9)
    ]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find_all(
                "div", {"class": "col-xs-6 col-sm-4 col-md-3"})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a").get("title")
        link = item.find("a").get("href")
        pre_id = item.find("a").get("href").split("&pid=")
        link_id = pre_id[-1]
        image_url = item.find("img").get("src")
        original_price = ""
        sale_price = item.find("div", {"class": "prod-price"}).text
        original_price = original_price.strip("NT$.")
        sale_price = sale_price.strip("NT$.")
        return Product(title, link, link_id, image_url, original_price, sale_price)


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
        "https://www.truda-moda.com.tw/categories/top?page={}&sort_by=&order_by=&limit=72",
        "https://www.truda-moda.com.tw/categories/bottom-%E4%B8%8B%E8%91%97?page={}&sort_by=&order_by=&limit=72",
        "https://www.truda-moda.com.tw/categories/outer?page={}&sort_by=&order_by=&limit=72",
        "https://www.truda-moda.com.tw/categories/jumpsuit-%E5%A5%97%E8%A3%9D?page={}&sort_by=&order_by=&limit=72",
        "https://www.truda-moda.com.tw/categories/accessories-%E9%85%8D%E4%BB%B6?page={}&sort_by=&order_by=&limit=72",
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


# 159_LAMOCHA
class LamochaCrawler(BaseCrawler):
    id = 159
    name = "lamocha"
    urls = [
        f"https://www.lamocha.com.tw/PDList.asp?item1=3&item2=2&tbxKeyword=&recommand=&ob=B&gd=b&pageno={i}"
        for i in range(1, 90)
    ]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find("section", {"id": "pdlist"}).find(
                "ul").find_all("li")
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "figcaption"}).find("p").text
        link = "https://www.lamocha.com.tw/" + item.find("a").get("href")
        link_id = "yano" + link.split("yano")[-1]
        image_url = item.find("img").get("src")
        original_price = (
            item.find("p", {"class": "salePrice"}).find("span").text
            if item.find("p", {"class": "salePrice"})
            else ""
        )
        sale_price = (
            item.find("p", {"class": "salePrice"}).contents[0]
            if item.find("p", {"class": "salePrice"})
            else item.find("div", {"class": "figcaption"}).find_all("p")[1].text
        )
        return Product(title, link, link_id, image_url, original_price, sale_price)

# 162 BONYREAD
class BonyreadCrawler(BaseCrawler):
    prefix_urls = ['https://www.bonnyread.com.tw/categories/03-15',
                   'https://www.bonnyread.com.tw/categories/03-08',
                   'https://www.bonnyread.com.tw/categories/03-02',
                   'https://www.bonnyread.com.tw/categories/02-22',
                   'https://www.bonnyread.com.tw/categories/02-01',
                   'https://www.bonnyread.com.tw/categories/01-25',
                   'https://www.bonnyread.com.tw/categories/01-18',
                   'https://www.bonnyread.com.tw/categories/01-11',
                   'https://www.bonnyread.com.tw/categories/12-28',
                   'https://www.bonnyread.com.tw/categories/12-21',
                   'https://www.bonnyread.com.tw/categories/petty-girl',
                   'https://www.bonnyread.com.tw/categories/petty-girl-earring',
                   'https://www.bonnyread.com.tw/categories/petty-girl-ear-clip',
                   'https://www.bonnyread.com.tw/categories/petty-girl-necklaces',
                   'https://www.bonnyread.com.tw/categories/pretty-girl-rings',
                   'https://www.bonnyread.com.tw/categories/pretty-girl-hair-accessory',
                   'https://www.bonnyread.com.tw/categories/pretty-girl-sunglasses',
                   'https://www.bonnyread.com.tw/categories/petty-girl-bracelets',
                   'https://www.bonnyread.com.tw/categories/special-recommend',
                   'https://www.bonnyread.com.tw/categories/thanksgiving-1',
                   'https://www.bonnyread.com.tw/categories/earrings-thank',
                   'https://www.bonnyread.com.tw/categories/earclip-thank',
                   'https://www.bonnyread.com.tw/categories/necklaces-thank',
                   'https://www.bonnyread.com.tw/categories/rings-thank',
                   'https://www.bonnyread.com.tw/categories/hair-accessory-thank',
                   'https://www.bonnyread.com.tw/categories/sunglasses-thank',
                   'https://www.bonnyread.com.tw/categories/pin-thank',
                   'https://www.bonnyread.com.tw/categories/bracelets-thank',
                   'https://www.bonnyread.com.tw/categories/1010',
                   'https://www.bonnyread.com.tw/categories/mothers-day',
                   'https://www.bonnyread.com.tw/categories/best-selling',
                   'https://www.bonnyread.com.tw/categories/instock-1',
                   'https://www.bonnyread.com.tw/categories/earrings',
                   'https://www.bonnyread.com.tw/categories/recommend',
                   'https://www.bonnyread.com.tw/categories/silverpost-????',
                   'https://www.bonnyread.com.tw/categories/multipack-???',
                   'https://www.bonnyread.com.tw/categories/circle-earrings',
                   'https://www.bonnyread.com.tw/categories/long-earrings????',
                   'https://www.bonnyread.com.tw/categories/studearrings',
                   'https://www.bonnyread.com.tw/categories/chain-earrings',
                   'https://www.bonnyread.com.tw/categories/earclip-????',
                   'https://www.bonnyread.com.tw/categories/dangle-earrings',
                   'https://www.bonnyread.com.tw/categories/????',
                   'https://www.bonnyread.com.tw/categories/????',
                   'https://www.bonnyread.com.tw/categories/studearclip',
                   'https://www.bonnyread.com.tw/categories/circle-earclips',
                   'https://www.bonnyread.com.tw/categories/rings??',
                   'https://www.bonnyread.com.tw/categories/chain-ring',
                   'https://www.bonnyread.com.tw/categories/tail-ring-??',
                   'https://www.bonnyread.com.tw/categories/multipack-???',
                   'https://www.bonnyread.com.tw/categories/lovers-ring',
                   'https://www.bonnyread.com.tw/categories/adjustable-ring',
                   'https://www.bonnyread.com.tw/categories/ring16cm',
                   'https://www.bonnyread.com.tw/categories/ring17cm',
                   'https://www.bonnyread.com.tw/categories/bracelets',
                   'https://www.bonnyread.com.tw/categories/bracelet-1',
                   'https://www.bonnyread.com.tw/categories/bracelet',
                   'https://www.bonnyread.com.tw/categories/anklets',
                   'https://www.bonnyread.com.tw/categories/redline',
                   'https://www.bonnyread.com.tw/categories/necklaces',
                   'https://www.bonnyread.com.tw/categories/choker-necklace-??',
                   'https://www.bonnyread.com.tw/categories/clavicle-necklace',
                   'https://www.bonnyread.com.tw/categories/long-necklaces',
                   'https://www.bonnyread.com.tw/categories/replacement-necklace',
                   'https://www.bonnyread.com.tw/categories/silver-necklace',
                   'https://www.bonnyread.com.tw/categories/mask-chain',
                   'https://www.bonnyread.com.tw/categories/????',
                   'https://www.bonnyread.com.tw/categories/antiallergy',
                   'https://www.bonnyread.com.tw/categories/silver',
                   'https://www.bonnyread.com.tw/categories/s925',
                   'https://www.bonnyread.com.tw/categories/silver-1',
                   'https://www.bonnyread.com.tw/categories/silver-needle',
                   'https://www.bonnyread.com.tw/categories/hello-kitty-silver',
                   'https://www.bonnyread.com.tw/categories/steel',
                   'https://www.bonnyread.com.tw/categories/stainless-steel',
                   'https://www.bonnyread.com.tw/categories/pin',
                   'https://www.bonnyread.com.tw/categories/hair-accessory',
                   'https://www.bonnyread.com.tw/categories/headband',
                   'https://www.bonnyread.com.tw/categories/hair-tie',
                   'https://www.bonnyread.com.tw/categories/hair-clip',
                   'https://www.bonnyread.com.tw/categories/hair-band',
                   'https://www.bonnyread.com.tw/categories/cap',
                   'https://www.bonnyread.com.tw/categories/hottest',
                   'https://www.bonnyread.com.tw/categories/2021pantone',
                   'https://www.bonnyread.com.tw/categories/western',
                   'https://www.bonnyread.com.tw/categories/flower-space',
                   'https://www.bonnyread.com.tw/categories/star',
                   'https://www.bonnyread.com.tw/categories/caramel-coco',
                   'https://www.bonnyread.com.tw/categories/cream-white',
                   'https://www.bonnyread.com.tw/categories/pink',
                   'https://www.bonnyread.com.tw/categories/pearl',
                   'https://www.bonnyread.com.tw/categories/brass',
                   'https://www.bonnyread.com.tw/categories/daisy',
                   'https://www.bonnyread.com.tw/categories/04-29',
                   'https://www.bonnyread.com.tw/categories/koreaaccessory',
                   'https://www.bonnyread.com.tw/categories/earrings-k',
                   'https://www.bonnyread.com.tw/categories/earclip-k',
                   'https://www.bonnyread.com.tw/categories/necklaces-k',
                   'https://www.bonnyread.com.tw/categories/rings-k',
                   'https://www.bonnyread.com.tw/categories/hair-accessory-k',
                   'https://www.bonnyread.com.tw/categories/sunglasses-k',
                   'https://www.bonnyread.com.tw/categories/bracelets-k',
                   'https://www.bonnyread.com.tw/categories/cartoons',
                   'https://www.bonnyread.com.tw/categories/sanrio-family',
                   'https://www.bonnyread.com.tw/categories/kikilala',
                   'https://www.bonnyread.com.tw/categories/hello-kitty-amusement-park',
                   'https://www.bonnyread.com.tw/categories/the-powerpuff-girls',
                   'https://www.bonnyread.com.tw/categories/cosmic-mansion',
                   'https://www.bonnyread.com.tw/categories/candle',
                   'https://www.bonnyread.com.tw/categories/diffuser',
                   'https://www.bonnyread.com.tw/categories/roomspray',
                   'https://www.bonnyread.com.tw/categories/scentedcard',
                   'https://www.bonnyread.com.tw/categories/swarovski',
                   'https://www.bonnyread.com.tw/categories/sunglasses',
                   'https://www.bonnyread.com.tw/categories/carin-sunglasses',
                   'https://www.bonnyread.com.tw/categories/other-??',
                   'https://www.bonnyread.com.tw/categories/????',
                   'https://www.bonnyread.com.tw/categories/?????',
                   'https://www.bonnyread.com.tw/categories/preorder',
                   'https://www.bonnyread.com.tw/categories/series',
                   'https://www.bonnyread.com.tw/categories/feedback',
                   'https://www.bonnyread.com.tw/categories/furry-ball',
                   'https://www.bonnyread.com.tw/categories/office-lady',
                   'https://www.bonnyread.com.tw/categories/blogger-recommended',
                   'https://www.bonnyread.com.tw/categories/yanxi-palace',
                   'https://www.bonnyread.com.tw/categories/matte-brass',
                   'https://www.bonnyread.com.tw/categories/coral-orange',
                   'https://www.bonnyread.com.tw/categories/transparency',
                   'https://www.bonnyread.com.tw/categories/watercolor',
                   'https://www.bonnyread.com.tw/categories/teddybear',
                   'https://www.bonnyread.com.tw/categories/crystal',
                   'https://www.bonnyread.com.tw/categories/no-rules',
                   'https://www.bonnyread.com.tw/categories/chain',
                   'https://www.bonnyread.com.tw/categories/new-year',
                   'https://www.bonnyread.com.tw/categories/end-of-the-year',
                   'https://www.bonnyread.com.tw/categories/purple',
                   'https://www.bonnyread.com.tw/categories/dessert-time',
                   'https://www.bonnyread.com.tw/categories/planet',
                   'https://www.bonnyread.com.tw/categories/interview',
                   'https://www.bonnyread.com.tw/categories/luxury',
                   'https://www.bonnyread.com.tw/categories/triangle',
                   'https://www.bonnyread.com.tw/categories/milktea',
                   'https://www.bonnyread.com.tw/categories/????',
                   'https://www.bonnyread.com.tw/categories/blue',
                   'https://www.bonnyread.com.tw/categories/baby-blue',
                   'https://www.bonnyread.com.tw/categories/avocado-green',
                   'https://www.bonnyread.com.tw/categories/aliceinwonderland',
                   'https://www.bonnyread.com.tw/categories/wooden',
                   'https://www.bonnyread.com.tw/categories/feather-earrings',
                   'https://www.bonnyread.com.tw/categories/cherry-blossoms',
                   'https://www.bonnyread.com.tw/categories/love',
                   'https://www.bonnyread.com.tw/categories/retro',
                   'https://www.bonnyread.com.tw/categories/leopard-print',
                   'https://www.bonnyread.com.tw/categories/checked',
                   'https://www.bonnyread.com.tw/categories/glitter',
                   'https://www.bonnyread.com.tw/categories/shell',
                   'https://www.bonnyread.com.tw/categories/weave',
                   'https://www.bonnyread.com.tw/categories/disney-???',
                   'https://www.bonnyread.com.tw/categories/natural-stone-????',
                   'https://www.bonnyread.com.tw/categories/tassels',
                   'https://www.bonnyread.com.tw/categories/cotton-pearl',
                   'https://www.bonnyread.com.tw/categories/dreamcatcher-???',
                   'https://www.bonnyread.com.tw/categories/bow',
                   'https://www.bonnyread.com.tw/categories/black',
                   'https://www.bonnyread.com.tw/categories/diamond',
                   'https://www.bonnyread.com.tw/categories/bohemian',
                   'https://www.bonnyread.com.tw/categories/animal',
                   'https://www.bonnyread.com.tw/categories/sweet-wedding',
                   'https://www.bonnyread.com.tw/categories/ocean',
                   'https://www.bonnyread.com.tw/categories/geometry',
                   'https://www.bonnyread.com.tw/categories/man-accessory',
                   'https://www.bonnyread.com.tw/categories/bestieacc',
                   'https://www.bonnyread.com.tw/categories/xmas',
                   'https://www.bonnyread.com.tw/categories/letters',
                   'https://www.bonnyread.com.tw/categories/????',
                   'https://www.bonnyread.com.tw/categories/top10',
                   'https://www.bonnyread.com.tw/categories/wind',
                   'https://www.bonnyread.com.tw/categories/consumable',
                   'https://www.bonnyread.com.tw/categories/water',
                   'https://www.bonnyread.com.tw/categories/fire',
                   'https://www.bonnyread.com.tw/categories/earth',
                   'https://www.bonnyread.com.tw/categories/twelve-constellation',
                   'https://www.bonnyread.com.tw/categories/instock',
                   'https://www.bonnyread.com.tw/categories/revive',
                   'https://www.bonnyread.com.tw/categories/discount',
                   'https://www.bonnyread.com.tw/categories/ngsunglasses',
                   'https://www.bonnyread.com.tw/categories/54630f54e37ec65d35000002',
                   'https://www.bonnyread.com.tw/categories/hello-kitty',
                   'https://www.bonnyread.com.tw/categories/hello-kitty-afternoon-tea']
    urls = [f'{prefix}' for prefix in prefix_urls]

    def parse(self):
        for url in self.urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            prod = soup.find('ul', {'class': 'ProductList-categoryMenu is-collapsed is-mobile-collapsed'})
            items = prod.find_all('div', {'class': 'col-xs-12 ProductList-list'})

            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            product = item.find('a', {'class': 'Product-item'})
            page_id = product.get('product-id')
            img_url = product.find('div', {'class': 'Image-boxify-image js-image-boxify-image sl-lazy-image'}
                                   ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = product.find('div', {'class': 'Product-title Label mix-primary-text'}).text
            sale_price = ""
            url = product.get('href')
            original_price = (product.find('div', {'class': 'Product-info'})).find_all('div')[1].text.replace("NT$", "")
        except:
            pass

        return Product(title, url, page_id, img_url, original_price, sale_price)

# 167 WEME
class WemeCrawler(BaseCrawler):
    id = 167
    name = 'weme'
    prefix_urls = ['https://www.wemekr.com/products']
    urls = [f'{prefix}' for prefix in prefix_urls]

    def parse(self):
        for url in self.urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find('ul', {'class': 'boxify-container'}).find_all('li')
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        url = "https://www.wemekr.com"+item.find('a', {'class': 'quick-cart-item'}).get('href')
        page_id = url.split('/')[-1].replace('.html', "")
        title = (item.find('div', {'class': 'title text-primary-color title-container ellipsis'}).text).strip(' \n ')
        img_url = item.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                            ).get('style').split('background-image:url(')[1].replace('?)', "")
        try:
            original_price = item.find(
                'div', {'class': 'global-primary dark-primary price price-crossed'}).text.strip(' \n ').replace("NT$", "")
        except:
            original_price = ""
        try:
            sale_price = item.find('div', {'class': 'price-sale price'}).text.strip(' \n ').replace("NT$", "")
        except:
            sale_price = ""

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
    prefix_urls = ['https://www.robinmaybag.com/categories/hot-robinmay?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/1980?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/new-arrival?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/collection?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/rm-x-ella?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/plus?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/stay-magic?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/all-you-need?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/evolution?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/platinum-nylon-collection?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/belle�s-collection?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/platinum-quilted-collections?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/bags?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/clutches?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/handbags?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/shoulder-bags?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/crossbody-bags?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/backpacks?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/chest-bags?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/wallet?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/large?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/meduim?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/small?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/small-wallets-for-men?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/card-holders-coin-purses?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/bag-straps?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.robinmaybag.com/categories/more-to-discover?page={i}&sort_by=&order_by=&limit=72']
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

class ImfineCrawler(BaseCrawler):
    id = 174
    name = "imfine"
    prefix_urls = ['https://www.imfinetw.com//categories/in-stock-%E5%BF%AB%E9%80%9F%E5%87%BA%E8%B2%A8%E5%8D%80?limit=72',
                   'https://www.imfinetw.com//categories/0311-new?limit=72',
                   'https://www.imfinetw.com//categories/0217?limit=72',
                   'https://www.imfinetw.com//categories/top?limit=72',
                   'https://www.imfinetw.com//categories/t-shirttee?limit=72',
                   'https://www.imfinetw.com//categories/blouse?limit=72',
                   'https://www.imfinetw.com//categories/bottom?limit=72',
                   'https://www.imfinetw.com//categories/pants?limit=72',
                   'https://www.imfinetw.com//categories/skirt?limit=72',
                   'https://www.imfinetw.com//categories/denim?limit=72',
                   'https://www.imfinetw.com//categories/short?limit=72',
                   'https://www.imfinetw.com//categories/kint?limit=72',
                   'https://www.imfinetw.com//categories/outer?limit=72',
                   'https://www.imfinetw.com//categories/set?limit=72',
                   'https://www.imfinetw.com//categories/dress?limit=72',
                   'https://www.imfinetw.com//categories/vest--bra?limit=72',
                   'https://www.imfinetw.com//categories/%E6%AD%A3%E9%9F%93%E5%95%86%E5%93%81?limit=72',
                   'https://www.imfinetw.com//categories/acc?limit=72',
                   'https://www.imfinetw.com//categories/korean?limit=72']
    urls = [f'{prefix}' for prefix in prefix_urls]

    def parse(self):
        for url in self.urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find('ul', {'class': 'boxify-container'}).find_all('li')
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, prod):
        url = prod.find('a').get('href')
        page_id = prod.find('a').get('product-id')
        img_url = prod.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                            ).get('style').split('background-image:url(')[1].replace('?)', "")
        title = (
            prod.find('div', {'class': 'title text-primary-color title-container ellipsis force-text-align-'})).text.strip()
        try:
            original_price = prod.find(
                'div', {'class': 'global-primary dark-primary price force-text-align-'}).text.strip().replace("NT$", "").replace(".", "")
        except:
            original_price = ""
        try:
            sale_price = prod.find('p', {'class': 'price'}).text.replace("NT$", "").split('.')[-1]
        except:
            sale_price = original_price
        return Product(title, url, page_id, img_url, original_price, sale_price)
class MirricoCrawler(BaseCrawler):
    id = 175
    name = "mimiricco"
    prefix_urls = ['https://www.mimiricco.com/products?page=1&sort_by=&order_by=&limit=72',
                   'https://www.mimiricco.com/products?page=2&sort_by=&order_by=&limit=72',
                   'https://www.mimiricco.com/categories/?????limit=72',
                   'https://www.mimiricco.com/categories/blackwhite?limit=72',
                   'https://www.mimiricco.com/categories/?????limit=72',
                   'https://www.mimiricco.com/categories/dress?limit=72',
                   'https://www.mimiricco.com/categories/???limit=72',
                   'https://www.mimiricco.com/categories/???limit=72',
                   'https://www.mimiricco.com/categories/??????limit=72',
                   'https://www.mimiricco.com/categories/??limit=72',
                   'https://www.mimiricco.com/categories/??limit=72',
                   'https://www.mimiricco.com/categories/coat?limit=72',
                   'https://www.mimiricco.com/categories/???limit=72',
                   'https://www.mimiricco.com/categories/?????limit=72',
                   'https://www.mimiricco.com/categories/?????limit=72',
                   'https://www.mimiricco.com/categories/???limit=72',
                   'https://www.mimiricco.com/categories/5ca3017f5f5c3f00327a82a9?limit=72',
                   'https://www.mimiricco.com/categories/????????limit=72',
                   'https://www.mimiricco.com/categories/ig???limit=72']
    urls = [f'{prefix}' for prefix in prefix_urls]

    def parse(self):
        for url in self.urls:
            print(url)
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            items = soup.find('div', {'class': 'ProductList-list'}).find_all('a', {'class': 'Product-item'})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, prod):
        try:
            url = prod.get('href')
            page_id = url.split('/')[-1]
            img_url = prod.find('div', {'class': 'Image-boxify-image js-image-boxify-image sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = (prod.find('div', {'Product-title Label mix-primary-text'})).text.strip()
            try:
                sale_price = prod.find(
                    'div', {'class': 'Label-price sl-price is-sale primary-color-price'}).text.strip().replace("NT$", "").replace(".", "")
            except:
                sale_price = prod.find('div', {'class': 'Label-price sl-price '}
                                       ).text.strip().replace("NT$", "").replace(".", "")

            try:
                original_price = prod.find(
                    'div', {'class': 'Label-price sl-price Label-price-original'}).text.replace("NT$", "")
            except:
                original_price = ""
        except:
            title = url = page_id = img_url = original_price = sale_price = None

        return Product(title, url, page_id, img_url, original_price, sale_price)

class AfashionshowroomCrawler(BaseCrawler):
    id = 178
    name = "afashionshowroom"
    prefix_urls = ['https://www.afashionshowroom.com/categories/%E6%96%B0%E5%93%81%E5%B0%88%E5%8D%80?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/%E6%97%A9%E6%98%A5%E6%8E%A8%E8%96%A6%E5%84%AA%E6%83%A0%E5%B0%88%E5%8D%80?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/tops?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/tops-1?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/coats?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/bottoms?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/bottoms-1?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/dresses?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/bags?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/accessories?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/accessories-1?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/shoes?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/glasses?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/hats?limit=72&page=',
                   'https://www.afashionshowroom.com/categories/bras?limit=72&page=']
    urls = [f'{prefix}{i}' for prefix in prefix_urls for i in range(1, 5)]

    def parse(self):
        for url in self.urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find('ul', {'class': 'boxify-container'}).find_all('li')
                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):
        try:
            url = prod.find('a').get('href')
            page_id = prod.find('a').get('product-id')
            img_url = prod.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = (
                prod.find('div', {'class': 'title text-primary-color title-container ellipsis force-text-align-'})).text.strip()
            try:
                original_price = prod.find(
                    'div', {'class': 'global-primary dark-primary price force-text-align-'}).text.strip().replace("NT$", "").replace(".", "")
            except:
                original_price = (prod.find('div', {
                    'class': 'global-primary dark-primary price price-crossed force-text-align-'}).text.strip().replace("NT$", "").replace(".", "")).strip()
            try:
                sale_price = prod.find('div', {'class': 'price-sale price force-text-align-'}
                                       ).text.replace("NT$", "").split('.')[-1]
            except:
                sale_price = original_price
        except:
            title = url = page_id = img_url = original_price = sale_price = None
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

class BrodntdCrawler(BaseCrawler):
    id = 181
    name = "brodntd"
    prefix_urls = ['https://www.brodnyd.tw/%E5%85%A8%E9%83%A8%E5%95%86%E5%93%81?page={i}']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 6)]

    def parse(self):
        for url in self.urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find('div', {'class': 'product-grid row-fluid cols-3'}
                                  ).find_all('div', {'class': 'grid-box'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):
        try:
            url = prod.find('a').get('href')
            # print(url)
            page_id = url.split('/')[-1]
            # print(page_id)
            img_url = 'http:'+prod.find('img').get('src')
            # print(img_url)
            title = str((prod.find('a')).get('title')).strip()
            title = title.split(' ')[0]
            try:
                original_price = prod.find('span', {'class': 'price-label'}
                                           ).text.strip().replace("$", "").replace(",", "")
                # print(original_price)
            except:
                original_price = prod.find('span', {'class': 'price-old'}
                                           ).text.strip().replace("$", "").replace(",", "")
            try:
                sale_price = prod.find('span', {'class': 'price-label'}).text.replace("$", "").replace(",", "")
            except:
                try:
                    sale_price = prod.find('span', {'class': 'price-new'}).text.replace("$", "").replace(",", "")
                except:
                    sale_price = original_price
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)

class DejavustoreeCrawler(BaseCrawler):
    id = 182
    name = "dejavustore"
    prefix_urls = ['https://www.dejavustore.co/pages/about-us?limit=72&page=',
                   'https://www.dejavustore.co/categories/end-of-season-sale?limit=72&page=',
                   'https://www.dejavustore.co/categories/30off?limit=72&page=',
                   'https://www.dejavustore.co/categories/20off?limit=72&page=',
                   'https://www.dejavustore.co/categories/new-arrival?limit=72&page=',
                   'https://www.dejavustore.co/categories/top?limit=72&page=',
                   'https://www.dejavustore.co/categories/bottom?limit=72&page=',
                   'https://www.dejavustore.co/categories/one-piece?limit=72&page=',
                   'https://www.dejavustore.co/categories/outer?limit=72&page=',
                   'https://www.dejavustore.co/categories/limited-edition?limit=72&page=',
                   'https://www.dejavustore.co/categories/accessory?limit=72&page=',
                   'https://www.dejavustore.cohttps://www.dejavustore.co/categories/julynine?limit=72&page=',
                   'https://www.dejavustore.cohttps://www.dejavustore.co/categories/undercontrol-studio?limit=72&page=',
                   'https://www.dejavustore.co/categories/pf-candle-co?limit=72&page=',
                   'https://www.dejavustore.co/categories/julynine?limit=72&page=',
                   'https://www.dejavustore.co/categories/all-ihatemonday?limit=72&page=',
                   'https://www.dejavustore.co/categories/sublime-headwear?limit=72&page=',
                   'https://www.dejavustore.co/categories/all-marylou?limit=72&page=',
                   'https://www.dejavustore.co/categories/aprilpoolday?limit=72&page=',
                   'https://www.dejavustore.co/categories/wushih50?limit=72&page=',
                   'https://www.dejavustore.co/categories/kelty?limit=72&page=',
                   'https://www.dejavustore.co/pages/special-column?limit=72&page=',
                   'https://www.dejavustore.co/pages/julyninexaniao?limit=72&page=',
                   'https://www.dejavustore.co/pages/the-apple-in-your-eye?limit=72&page=',
                   'https://www.dejavustore.co/categories/shop-all?limit=72&page=']
    urls = [f'{prefix}{i}' for prefix in prefix_urls for i in range(1, 7)]

    def parse(self):
        for url in self.urls:

            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find('ul', {'class': 'boxify-container'}).find_all('li')
                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):
        try:
            url = prod.find('a').get('href')
            page_id = prod.find('product-item').get('product-id')
            img_url = prod.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = (prod.find('div', {'class': 'title text-primary-color title-container ellipsis'})).text.strip()
            try:
                original_price = prod.find('div', {'class': 'global-primary dark-primary price'}
                                           ).text.strip().replace("NT$", "").replace(".", "")
            except:
                original_price = ""
            try:
                sale_price = prod.find('p', {'class': 'price'}).text.replace("NT$", "").split('.')[-1]
            except:
                sale_price = original_price
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)
class AramodalCrawler(BaseCrawler):
    id = 183
    name = "aramodal"
    prefix_urls = ['https://www.aroommodel.com/products?page={i}&sort_by=&order_by=&limit=72']
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
    id = 186
    name = "bucha"
    prefix_urls = [
        'https://www.bucha.tw/categories/%E6%89%80%E6%9C%89%E5%95%86%E5%93%81%E3%83%BBall?page={i}&sort_by=&order_by=&limit=72']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 10)]

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

class YvestoreCrawler(BaseCrawler):
    id = 187
    name = "yvestore"
    prefix_urls = ['https://www.yvestore.com/pages/%E9%97%9C%E6%96%BC%E3%80%90yve%EF%BC%8C%E3%80%91?limit=72&page=',
                   'https://www.yvestore.com/pages/%E8%B3%BC%E8%B2%B7%E8%BE%A6%E6%B3%95%E5%8F%8A%E8%A6%8F%E5%89%87?limit=72&page=',
                   'https://www.yvestore.com/pages/vip%E5%84%AA%E6%83%A0?limit=72&page=',
                   'https://www.yvestore.com/pages/%E7%89%A9%E6%B5%81%E9%85%8D%E9%80%81?limit=72&page=',
                   'https://www.yvestore.com/pages/%E5%94%AE%E5%BE%8C%E6%9C%8D%E5%8B%99?limit=72&page=',
                   'https://www.yvestore.com/categories/new-arrivals?limit=72&page=',
                   'https://www.yvestore.com/categories/new-arrivals%EF%BD%9C%E6%9C%AC%E6%9C%88%E6%96%B0%E5%93%81?limit=72&page=',
                   'https://www.yvestore.com/categories/sep%EF%BD%9C%E4%B9%9D%E6%9C%88%E6%96%B0%E5%93%81?limit=72&page=',
                   'https://www.yvestore.com/categories/jan%EF%BD%9C%E4%B8%80%E6%9C%88%E6%96%B0%E5%93%81?limit=72&page=',
                   'https://www.yvestore.com/categories/classic?limit=72&page=',
                   'https://www.yvestore.com/categories/classic%EF%BD%9C%E7%B6%93%E5%85%B8%E5%95%86%E5%93%81?limit=72&page=',
                   'https://www.yvestore.com/categories/in-stock?limit=72&page=',
                   'https://www.yvestore.com/categories/instock%EF%BD%9C%E7%86%B1%E8%B3%A3%E7%8F%BE%E8%B2%A8?limit=72&page=',
                   'https://www.yvestore.com/categories/clothes?limit=72&page=',
                   'https://www.yvestore.com/categories/top%EF%BD%9C%E4%B8%8A%E8%A1%A3?limit=72&page=',
                   'https://www.yvestore.com/categories/pant-sskirt%EF%BD%9C%E4%B8%8B%E8%91%97?limit=72&page=',
                   'https://www.yvestore.com/categories/dress-jumpsuit%EF%BD%9C%E6%B4%8B%E8%A3%9D-%E9%80%A3%E8%BA%AB%E8%A4%B2?limit=72&page=',
                   'https://www.yvestore.com/categories/coat%EF%BD%9C%E5%A4%96%E5%A5%97?limit=72&page=',
                   'https://www.yvestore.com/categories/shoesbag%E2%88%A3%E9%9E%8B%E5%AD%90-%E5%8C%85%E5%8C%85-%E5%B8%BD%E5%AD%90?limit=72&page=',
                   'https://www.yvestore.com/categories/scarf%EF%BD%9C%E5%9C%8D%E5%B7%BE-%E7%B5%B2%E5%B7%BE?limit=72&page=',
                   'https://www.yvestore.com/categories/acc?limit=72&page=',
                   'https://www.yvestore.com/categories/necklace%EF%BD%9C%E9%A0%85%E9%8D%8A?limit=72&page=',
                   'https://www.yvestore.com/categories/choker%EF%BD%9C%E9%A0%B8%E9%8D%8A?limit=72&page=',
                   'https://www.yvestore.com/categories/bracelet%EF%BD%9C%E6%89%8B%E9%8D%8A-%E6%89%8B%E7%92%B0?limit=72&page=',
                   'https://www.yvestore.com/categories/watch%E2%88%A3%E6%89%8B%E9%8C%B6?limit=72&page=',
                   'https://www.yvestore.com/categories/ring%EF%BD%9C%E6%88%92%E6%8C%87?limit=72&page=',
                   'https://www.yvestore.com/categories/ring-set%EF%BD%9C%E6%88%92%E6%8C%87%E7%B5%84%E5%90%88?limit=72&page=',
                   'https://www.yvestore.com/categories/earring%EF%BD%9C%E8%80%B3%E7%92%B0?limit=72&page=',
                   'https://www.yvestore.com/categories/clip-earring%EF%BD%9C%E8%80%B3%E6%8E%9B-%E8%80%B3%E5%A4%BE?limit=72&page=',
                   'https://www.yvestore.com/categories/925silver%E2%88%A3%E6%8A%97%E9%81%8E%E6%95%8F925%E7%B4%94%E9%8A%80?limit=72&page=',
                   'https://www.yvestore.com/categories/stainless-steel%EF%BD%9C%E4%B8%8D%E9%8F%BD%E9%8B%BC%E9%87%9D?limit=72&page=',
                   'https://www.yvestore.com/categories/anklechain%EF%BD%9C%E8%85%B3%E9%8D%8A?limit=72&page=',
                   'https://www.yvestore.com/categories/handmade%EF%BD%9C%E6%89%8B%E4%BD%9C?limit=72&page=',
                   'https://www.yvestore.com/categories/hair-ornaments%EF%BD%9C%E9%AB%AE%E9%A3%BE?limit=72&page=',
                   'https://www.yvestore.com/categories/glasses%EF%BD%9C%E7%9C%BC%E9%8F%A1-%E5%A2%A8%E9%8F%A1?limit=72&page=',
                   'https://www.yvestore.com/categories/vintage%EF%BD%9C%E5%8F%A4%E8%91%A3%E5%95%86%E5%93%81?limit=72&page=',
                   'https://www.yvestore.com/categories/brand%EF%BD%9C%E5%93%81%E7%89%8C%E4%BB%A3%E8%B3%BC?limit=72&page=',
                   'https://www.yvestore.com/categories/japan%EF%BD%9Cmiyuki-matsuo?limit=72&page=',
                   'https://www.yvestore.com/categories/korea%EF%BD%9Cdepound?limit=72&page=',
                   'https://www.yvestore.com/categories/korea%EF%BD%9Chairich?limit=72&page=',
                   'https://www.yvestore.com/categories/korea%EF%BD%9Cjmsolution?limit=72&page=',
                   'https://www.yvestore.com/categories/korea%EF%BD%9Conce32?limit=72&page=',
                   'https://www.yvestore.com/categories/korea%EF%BD%9C23years-old?limit=72&page=',
                   'https://www.yvestore.com/categories/espoir?limit=72&page=',
                   'https://www.yvestore.com/categories/sweden%EF%BD%9Cchimi?limit=72&page=',
                   'https://www.yvestore.com/categories/taiwan%EF%BD%9C10?limit=72&page=',
                   'https://www.yvestore.com/categories/thailand%EF%BD%9Capalepetal?limit=72&page=',
                   'https://www.yvestore.com/categories/thailand%EF%BD%9Cchatt?limit=72&page=',
                   'https://www.yvestore.com/categories/thailand%EF%BD%9Chyde?limit=72&page=',
                   'https://www.yvestore.com/categories/thailand%EF%BD%9Ckanni-studio?limit=72&page=',
                   'https://www.yvestore.com/categories/karmakamet?limit=72&page=',
                   'https://www.yvestore.com/categories/mitr?limit=72&page=',
                   'https://www.yvestore.com/categories/thailand%EF%BD%9Ctwotwice?limit=72&page=',
                   'https://www.yvestore.com/categories/thailand%EF%BD%9Cwaterandothers?limit=72&page=',
                   'https://www.yvestore.com/categories/thailand%EF%BD%9Cwhiteoakfactory?limit=72&page=']
    urls = [f'{prefix}{i}' for prefix in prefix_urls for i in range(1, 5)]

    def parse(self):
        for url in self.urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find('ul', {'class': 'boxify-container'}).find_all('li')
                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):
        try:
            url = 'https://www.yvestore.com'+prod.find('a').get('href')
            # print(url)
            page_id = prod.find('a').get('product-id')
            # print(page_id)
            img_url = prod.find('div', {'class': 'boxify-image center-contain sl-lazy-image'}
                                ).get('style').split('background-image:url(')[1].replace('?)', "")
            title = (
                prod.find('div', {'class': 'title text-primary-color title-container ellipsis force-text-align-'}).text.strip())
            try:
                original_price = prod.find('div', {'class': 'global-primary dark-primary price'}
                                           ).text.strip().replace("NT$", "").replace(".", "")
            except:
                original_price = ""
            try:
                sale_price = prod.find(
                    'div', {'class': 'global-primary dark-primary price force-text-align-'}).text.replace("NT$", "").split('.')[-1].strip()
            except:
                sale_price = original_price
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)

class TennyshopCrawler(BaseCrawler):
    pass
class MypopcornCrawler(BaseCrawler):
    id = 190
    name = "mypopcorn"
    prefix_urls = ['https://www.mypopcorn.com.tw/categories/55de85f4e37ec6e917000022?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/????page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcorndesigncollection?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/?????????page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/??????page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcornlive?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/top???page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/????page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/????190??page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/?????page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/??????page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcornclothes?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcorntopitems?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcornshirtitems?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcornvestitems?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcornbottom?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcornpantsitems?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcornskirtitems?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcorndressone-piecesuit?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/popcornouterwear?page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/?????page={i}&sort_by=&order_by=&limit=72',
                   'https://www.mypopcorn.com.tw/categories/????????????-100?page={i}&sort_by=&order_by=&limit=72']
    urls = [f'{prefix}{i}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 5)]

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
                original_price = prod.find('div', {'class': 'global-primary dark-primary price'}
                                           ).text.strip().replace("NT$", "").replace(".", "")
            except:
                original_price = ""
            try:
                sale_price = prod.find('div', {'class': 'global-primary dark-primary price sl-price'}
                                       ).text.replace("NT$", "").split('.')[-1].strip()
            except:
                sale_price = original_price
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)

class RachelworldCrawler(BaseCrawler):
    id = 241
    name = "rachelworld"
    base_url = "https://www.rachelworld.com.tw"

    def parse(self):
        url = f"{self.base_url}/ajaxpro/Mallbic.U.UShopShareUtil.Ajax.GlobalAjaxProductUtil,ULibrary.ashx"
        payload = {"aOpt": {"SearchType": -1, "CategoryID": "-1",
                            "SortingMode": 0, "IsInStock": False, "BlockNo": list(range(1, 1000))}}
        response = requests.request("POST", url, headers={
                                    **self.headers, "Content-Type": "application/json", "X-AjaxPro-Method": "GetAllProductByViewOption"}, json=payload)
        raw_text = re.sub("new Ajax\.Web\.Dictionary\(.*?\)|new Date\(.*?\)",
                          '""', response.content.decode(encoding='utf-8'))
        items = json.loads(raw_text)["value"]["ListData"]
        self.result.extend([self.parse_product(item) for item in items])

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

    def parse(self):
        url = f"{self.base_url}/ajaxpro/Mallbic.U.UShopShareUtil.Ajax.GlobalAjaxProductUtil,ULibrary.ashx"
        payload = {"aOpt": {"SearchType": -1, "CategoryID": "-1",
                            "SortingMode": 0, "IsInStock": False, "BlockNo": list(range(1, 1000))}}
        response = requests.request("POST", url, headers={
                                    **self.headers, "Content-Type": "application/json", "X-AjaxPro-Method": "GetAllProductByViewOption"}, json=payload)
        # print(response.content.decode(encoding='utf-8'))
        raw_text = re.sub('new Ajax\.Web\.Dictionary\(.*?\),|new Date\(.*?\)',
                          '"",', response.content.decode(encoding='utf-8'))
        # raw_text = re.sub('new Ajax\.Web\.Dictionary\(.*?\)', '""', raw_text)
        raw_text = raw_text.replace('"",,', '"",')
        raw_text = raw_text.replace('"",}', '""}')
        # print(raw_text)
        items = json.loads(raw_text)["value"]["ListData"]
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get("ProductName")
        link_id = item.get("ProductID")
        link = f'{self.base_url}/pitem/{link_id}'
        image_url = item.get("SmallPicUrl")
        original_price = item.get("MaxDeletePrice")
        sale_price = item.get("MinDisplayPrice")
        return Product(title, link, link_id, image_url, original_price, sale_price)

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

    prefix_urls = ['https://www.toofit.tw/products?page={i}&sort_by=&order_by=&limit=72']
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

            #print(title, url, page_id, img_url)
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

            #print(title, url, page_id, img_url)
            # print(title, url, page_id, img_url, "o" ,original_price,"s", sale_price)
        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)

class AfadCrawler(BaseCrawler):
    id = 239
    name = "afad"

    prefix_urls = ['https://www.afad.com.tw/PDList2.asp?item1=02&item2=ALL&keyword=&pagex=all',
                   'https://www.afad.com.tw/PDList2.asp?item1=04&item2=ALL&item3=&keyword=&pagex=all',
                   'https://www.afad.com.tw/PDList2.asp?item1=&item2=&item3=&keyword=&pagex=all',
                   'https://www.afad.com.tw/PDList2.asp?item1=00&item2=ALL&item3=&keyword=&pagex=all',
                   'https://www.afad.com.tw/PDList2.asp?item1=01&item2=ALL&item3=&keyword=&pagex=all']
    #urls =[f'{prefix}'.replace('{i}',str(i))  for prefix in prefix_urls for i in range(1,30)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.prefix_urls:
            print(url)
            response = requests.get(url, headers=header)
            try:
                soup = BeautifulSoup(response.text, features='html.parser')
                items = soup.find('div', {'id': 'even_dist'}).find_all('div', {'class': 'PDItem'})
                self.result.extend([self.parse_product(item) for item in items])
            except:
                pass

    def parse_product(self, prod):

        try:
            title = prod.find('a', {'class': 'permalink'}).text.strip()

            url = 'https://www.afad.com.tw/'+prod.find('a', {'class': 'permalink'}).get('href')

            try:
                page_id = prod.find('a', {'class': 'permalink'}).get('href').split('?yano=')[-1].split('&')[0]
            except:
                page_id = ""

            try:
                img_url = prod.find('img', {'class': 'imgPDItem'}).get('src').strip()
            except:
                img_url = " "

            try:
                orie = prod.find('div', {'class': 'pditemPrice'}).find_all('span')[0]
                original_price = orie.text.strip().replace("NT$", "").replace(",", "")
                sale_price = prod.find('div', {'class': 'pditemPrice'}).find_all('span')[1]
                sale_price = sale_price.text.replace("NT$", "").replace(",", "").strip()
            except:
                original_price = " "
                sale_price = prod.find('div', {'class': 'pditemPrice'}).find_all('span')[0]
                sale_price = orie.text.strip().replace("NT$", "").replace(",", "")

            # print(title,url,page_id,img_url,original_price,sale_price)
                #print(title, url, page_id, img_url)
           # print(title, url, page_id, img_url, original_price, sale_price)

        except:
            title = url = page_id = img_url = original_price = sale_price = ""
        return Product(title, url, page_id, img_url, original_price, sale_price)


class KokokoreaCrawler(BaseCrawler):
    id = 237
    name = "kokokorea"

    prefix_urls = ['https://www.kokokorea.co/categories/all?page={i}&sort_by=&order_by=&limit=24']
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

            #print(title, url, page_id, img_url)
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

                #print(title, url, page_id, img_url)
            # print(title, url, page_id, img_url, original_price, "sale", sale_price)

        except:
            title = url = page_id = img_url = original_price = sale_price = ""
        return Product(title, url, page_id, img_url, original_price, sale_price)


class MosdressCrawler(BaseCrawler):
    id = 60
    name = "mosdress"

    prefix_urls = ['https://www.mosdress.com.tw/shop-zorka/page/{i}/']
    urls = [f'{prefix}'.replace('{i}', str(i)) for prefix in prefix_urls for i in range(1, 60)]

    def parse(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        for url in self.urls:
            try:
                print(url)
                response = requests.get(url, headers=header)
                soup = BeautifulSoup(response.text, features='html.parser')
                items = soup.find('div', {'class': 'products row row-small large-columns-4 medium-columns-3 small-columns-2'}).find_all(
                    'div', {'class': 'product-small box'})
                if len(items) < 1:
                    break
                else:
                    self.result.extend([self.parse_product(item) for item in items])
            except:
                break

    def parse_product(self, prod):
        try:

            title = prod.find('p', {'class': 'name product-title'}).text

            url = prod.find('p', {'class': 'name product-title'}).find('a').get('href')

            try:
                page_id = prod.find('a', {'class': 'add_to_wishlist'}).get('data-product-id')
            except:
                page_id = ""
            try:
                img_url = prod.find('img').get('src')
            except:
                img_url = ""
            try:
                orie = prod.find_all('span', {'class': 'woocommerce-Price-amount amount'})[0]
                original_price = orie.text.strip().replace("NT$", "").replace(",", "")
                sale_price = prod.find_all('span', {'class': 'woocommerce-Price-amount amount'})[1]
                sale_price = sale_price.text.replace("NT$", "").replace(",", "").strip()
            except:
                original_price = " "
                sale_price = prod.find('span', {'class': 'price'})
                sale_price = sale_price.text.replace("NT$", "").replace(",", "").strip()

                #print(title, url, page_id, img_url)
            # print(title, url, page_id, img_url, original_price, sale_price)

        except:
            title = url = page_id = img_url = original_price = sale_price = None
        return Product(title, url, page_id, img_url, original_price, sale_price)

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

                #print(title, url, page_id, img_url)
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

            #print(title, url, page_id, img_url)
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
#             try:
            item1 = soup.find_all('li', {'class': 'lazy_show'})
            item2 = soup.find_all('li', {'class': 'row_before'})
            items = item1+item2
#                 for k in items:
#                     k.find_all('li',{'class':'row_before'})
            self.result.extend([self.parse_product(item) for item in items])
#             except:
#                 pass

    def parse_product(self, item):
        try:
            url = 'https://www.lativ.com.tw'+item.find('a').get('href')
            page_id = url.split('/')[-1]
            img_url = 'https://www.lativ.com.tw' + \
                item.find('a', {'class': 'imgd'}).find('img', {'class': 'outfitPic'}).get('data-outfitpic')
            title = item.find('div', {'class': 'productname'}).text.strip()
            original_price = int(item.find("span").find('span').text.split("NT$")[-1])
            sale_price = int(item.find("span").find_all('span')[-1].text.split("NT$")[-1])
            if sale_price < original_price:
                original_price = original_price
                sale_price = sale_price
            elif sale_price == original_price:
                original_price = ""
                sale_price = sale_price
            # print(title, url, page_id, img_url, original_price, sale_price)
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
        # "11": ModaCrawler(),
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
        "47": CirclescinemaCrawler(),
        "48": CozyfeeCrawler(),  # li沒class
        "49": ReishopCrawler(),
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
        "92": BisouCrawler(),
        "94": LaconicCrawler(),
        "95": LulusCrawler(),
        "96": PixelcakeCrawler(),
        "97": MiyukiCrawler(),
        "99": PerchaCrawler(),
        "100": NabCrawler(),
        "102": MojpCrawler(),
        "103": GoddessCrawler(),
        "104": PleatsCrawler(),
        "105": ZebraCrawler(),  # json
        "107": MiharaCrawler(),
        # "108": EyecreamCrawler(),
        "109": CandyboxCrawler(),
        "112": VeryyouCrawler(),
        "113": StayfoxyCrawler(),
        "115": GracechowCrawler(),
        "116": LativCrawler(),
        "118": RightonCrawler(),
        "120": DafCrawler(),
        "122": SexyinshapeCrawler(),
        "125": MiniqueenCrawler(),
        "126": SandaruCrawler(),
        "127": BonbonsCrawler(),
        "130": BaibeautyCrawler(),
        "136": DaimaCrawler(),
        "138": MiakiCrawler(),
        "139": VinaclosetCrawler(),
        "141": StylemooncatCrawler(),
        # "142": LovfeeCrawler(),
        # "143": MarjorieCrawler(),
        "144": PureeCrawler(),
        # "146": RereburnCrawler(),
        # "147": StylenandaCrawler(),
        # "148": ThegirlwhoCrawler(),
        # "150": ChuuCrawler(),
        # "151": AleyCrawler(),
        # "152": TrudamodaCrawler(),
        "155": EvermoreCrawler(),  # V
        # "159": LamochaCrawler(),
        # "162": BonyreadCrawler(),
        "166": PixyCrawler(),  # V
        # "167": WemeCrawler(),
        # "170": AnnadollyCrawler(),
        # "172": RobinmayCrawler(),
        # "174": ImfineCrawler(),
        # "175": MirricoCrawler(),
        # "178": AfashionshowroomCrawler(),
        "179": StarkikiCrawler(),
        # "181": BrodntdCrawler(),
        # "182": DejavustoreeCrawler(),
        # "183": AramodalCrawler(),
        "186": BuchaCrawler(),
        # "187": YvestoreCrawler(),
        # "189": TennyshopCrawler(),
        # "190": MypopcornCrawler(),
        "194": AlmashopCrawler(),
        "196": LeatherCrawler(),  # V
        "198": MuminCrawler(),
        "221": WhoiannCrawler(),
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
        "266": LalalatwCrawler(),
        "295": DeerwCrawler(),
        "296": PreuniCrawler(),
        "297": Seaaa1Crawler(),
        "298": SpotlightCrawler(),  # V
        "299": RewearingCrawler(),
        "300": LstylestudioCrawler(),
        "302": OurstudioCrawler(),
        "304": UnefemmeCrawler(),
        "355": NovyyCrawler(),
        "356": MyameCrawler(),

    }
    return crawlers.get(str(crawler_id))
