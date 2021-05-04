import re
import json
from collections import namedtuple
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

from config import ENV_VARIABLE

fold_path = "./crawler_data"
page_Max = 100

def stripID(url, wantStrip):
    loc = url.find(wantStrip)
    length = len(wantStrip)
    return url[loc+length:]


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
        filename = "_".join(
            [str(self.id), self.name, datetime.today().strftime("%Y%m%d")]
        )

        book = Workbook()
        sheet = book.active
        sheet.append(Product._fields)
        for product in self.result:
            if product:
                sheet.append([*product])
        book.save(f"{fold_path}/{filename}.xlsx")

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
                    filename + ".xlsx",
                    open(f"{fold_path}/{filename}.xlsx", "rb"),
                ),
            }
            response = requests.post(
                verify=False, url=url, files=files, headers=headers
            )
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
        url = f"{self.base_url}/product/categoryproducts"
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
        link_id = link_id.replace("/product/detail/pmc/", "").replace("/cid/239", "")
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
            items = soup.find_all("product-item")
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        if item.find("div", {"class": "sold-out-item"}):
            return

        title = item.find(
            "div", {"class": "title text-primary-color"}
        ).text.strip()
        link = item.find("a").get("href")
        link_id = item.get("product-id")
        image_url = (
            item.find("div", {
                      "class": "boxify-image js-boxify-image center-contain sl-lazy-image"})["style"]
            .split("url(")[-1]
            .split("?)")[0]
        )
        original_price = self.get_price(item.find(
            "div", {"class": "global-primary dark-primary price sl-price price-crossed"}).text)
        sale_price = self.get_price(
            item.find(
                "div", {"class": "price-sale price sl-price primary-color-price"}).text
        )
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
            try:
                items = soup.find("div", {"id": "goods-list"}).find_all(
                    "div", {"class": "col-sm-4 col-xs-6"}
                )
            except:
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
        title = item["mername"]
        link_id = f"mNo1={item['merNo1']}&cno={item['orderNum']}"
        link = f"{self.base_url}/Shop/itemDetail.aspx?{link_id}"
        link_id = stripID(link_id, "mNo1=")
        link_id = link_id[:link_id.find("&cno")]
        image_url = f"http://{item['photosmpath'].replace('//', '')}"
        original_price = item["originalPrice"]
        sale_price = item["price"]
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 052_ApplestarryCrawler()
class ApplestarryCrawler(BaseCrawler):
    id = 52
    name = "applestarry"
    base_url = "https://www.applestarry.com.tw"

    def parse(self):
        url = [f"{self.base_url}/Shop/itemList.aspx?m=1&smfp={i}" for i in range(1, page_Max)]
        response = requests.request("POST", url, headers=self.headers)
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
        link_id = item['orderNum']
        link = f"{self.base_url}/Shop/itemDetail.aspx?mNo1={item['merNo1']}&cno={item['orderNum']}"
        image_url = f"http://{item['photosmpath'].replace('//', '')}"
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
        link_id = link_id.replace("product?saleid=", "")
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


# 008_AirspaceCrawler()
class AirspaceCrawler(BaseCrawler):
    id = 8
    name = "airspace"
    base_url = "https://www.airspaceonline.com"

    def parse(self):
        urls = [
            f"{self.base_url}/PDList.asp?pp1=all&pageno={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find("div", {"id": "item"}).find_all("li")
            except:
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


# 10_EFSHOP
class EfshopCrawler(BaseCrawler):
    id = 10
    name = "efshop"
    prefix_urls = [
        "https://www.efshop.com.tw/category/123",
        "https://www.efshop.com.tw/category/541",
        "https://www.efshop.com.tw/category/1",
        "https://www.efshop.com.tw/category/72",
        "https://www.efshop.com.tw/category/491/1",
        "https://www.efshop.com.tw/category/11",
        "https://www.efshop.com.tw/category/478",
        "https://www.efshop.com.tw/category/10",
        "https://www.efshop.com.tw/category/498",
    ]
    urls = [
        f"{prefix}/{i}" for prefix in prefix_urls for i in range(1, page_Max)]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find_all("div", {"class": "idx_pro2"})
            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("a").get("title")
        link = item.find("a").get("href")
        link_id = stripID(link, "/product/")
        image_url = item.find("img").get("src")
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
        urls = [
            f"{self.base_url}/itemList.aspx?m=1&p=851&o=0&sa=0&smfp={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find_all("div", {"class": "itemListDiv"})
            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "itemListMerName"}).find("a").text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        link_id = link_id.replace(
            "itemDetail.aspx?mNo1=", "").replace("&m=1&p=851", "")
        image_url = item.find("img").get("src")
        image_url = f"https:{image_url}"
        original_price = self.get_price(item.find(
            "div", {"class": "itemListMoney"}).find('span').text)
        sale_price = self.get_price(
            item.find("div", {"class": "itemListMoney"}).find('span').find_next('span').text)
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


# 58_HARPER
class HarperCrawler(BaseCrawler):
    id = 58
    name = "harper"
    base_url = "https://www.harper.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/Shop/itemList.aspx?&m=13&smfp={i}" for i in range(1, page_Max)]
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
        title = item.find("div", {"class": "itemListMerName"}).find("a").text
        link = item.find("a").get("href")
        link_id = stripID(link, "cno=")
        link_id = link_id.replace("&m=13", "")
        image_url = item.find("img").get("src")
        original_price = ""
        sale_price = self.get_price(
            item.find("div", {"class": "m_itemListMoney"}).find("span").text)
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
            try:
                items = soup.find_all(
                    "div", {"class": "col-xl-3 col-lg-3 col-mb-3 col-sm-6 col-xs-6 squeeze-padding"})
            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("h3", {"class": "product-title"}).find("a").text
        link = item.find("a").get("href")
        link_id = link.replace("https://www.jendesstudio.com/product/",
                               "").replace("?c=de8eed41-acbf-4da7-a441-e6028d8b28c9", "")
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
            f"{self.base_url}/collections/new-all-%E6%89%80%E6%9C%89?page={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find_all(
                    "div", {"class": "product col-lg-3 col-sm-4 col-6"})
            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "product_title"}).find(
            "a").get("data-name")
        link_id = item.find("a").get("href").replace("/products/", "")
        link = f"{self.base_url}/products/{link_id}"
        link_id = link_id.replace("/products/", "")
        image_url = f"https:{item.find('img').get('data-src')}"
        original_price = ""
        sale_price = self.get_price(
            item.find("div", {"class": "product_price"}).find("span").text)
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
        link_id = link_id.replace(
            "itemDetail.aspx?mNo1=", "").replace("&m=2", "")
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


# 85_SumiCrawler()
class SumiCrawler(BaseCrawler):
    id = 85
    name = "sumi"
    base_url = "https://www.sumi-life.com"

    def parse(self):
        url = f"{self.base_url}/product/all"
        response = requests.request("GET", url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="html.parser")
        try:
            items = soup.find_all("li", {"class": " item_block js_is_photo_style  has_listing_cart "})
        except:
            return
        self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("h4").text
        link = item.find("a").get("href")
        link_id = link.replace("https://www.sumi-life.com/product/detail/", "")
        image_url = item.find("span").get("data-src")

        if (item.find("li", {"class": "item_origin item_actual"})):
            original_price = self.get_price(item.find("li", {"class": "item_sale"}).find("span").text)
            sale_price = self.get_price(item.find("li", {"class": "item_origin item_actual"}).find("span").text)
        else:
            original_price = ""
            sale_price = self.get_price(item.find("li", {"class": "item_origin"}).find("span").text)

        return Product(title, link, link_id, image_url, original_price, sale_price)


# 92_BISOU
class BisouCrawler(BaseCrawler):
    id = 92
    name = "bisou"
    base_url = "https://www.cn.bisoubisoustore.com"

    def parse(self):
        urls = [
            f"{self.base_url}/collections/all?page={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            # print("response=", response.text)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find_all(
                    "div", {"class": "product-block detail-mode-permanent  main-image-loaded"})

            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title"}).text
        link_id = item.find("div", {"class": "data-product-id"})
        link = item.find("a").get("href")
        image_url = f"https:{item.find('img').get('src')}"
        original_price = ""
        sale_price = self.get_price(
            item.find("span", {"class": "price"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 112_VERYYOU
class VeryyouCrawler(BaseCrawler):
    id = 112
    name = "veryyou"
    base_url = "https://www.veryyou.com.tw"

    def parse(self):
        urls = [
            f"{self.base_url}/PDList.asp?pp1=all&pageno={i}" for i in range(1, page_Max)]
        for url in urls:
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find(
                    "div", {"class": "section-product-list"}).find_all("figure")
            except:
                break
            print("items = ", items)
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "title"}).text
        link_id = item.find("a").get("href")
        link = f"{self.base_url}/{link_id}"
        image_url = item.find("img").get("src")
        original_price = self.get_price(
            item.find("div").find("span").text)
        sale_price = self.get_price(
            item.find("div").find("span").find_next('span').text)
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
            response = requests.request("GET", url, headers=self.headers)
            soup = BeautifulSoup(response.text, features="html.parser")
            try:
                items = soup.find_all(
                    "ul", {"class": ' item_block js_is_photo_style img_polaroid has_listing_cart '})
            except:
                break
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("h4").text
        link = item.find("a").get("href")
        link_id = link.replace(
            "https://sandarushop.com/product/detail/", "")
        image_url = item.find("a").find("span").get("data-src")
        original_price = self.get_price(
            item.find("li", {"class": "item_origin item_actual"}).find("span").text)
        sale_price = self.get_price(
            item.find("div", {"class": "item_sale"}).find("span").text)
        return Product(title, link, link_id, image_url, original_price, sale_price)


# 142_LOVFEE
class LovfeeCrawler(BaseCrawler):
    id = 142
    name = "lovfee"
    urls = [
        f"https://www.lovfee.com/PDList2.asp?item1=01&item2=&item3=&keyword=&ob=A&pagex=&pageno={i}"
        for i in range(1, 18)
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
        for i in range(1, 18)
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
    prefix_urls = [
        "https://www.puree.com.tw/categories/5de0fcefebae29002aba2258?limit=72&page=",
        "https://www.puree.com.tw/categories/5de0fd8257f0813f7eb79301?limit=72&page=",
        "https://www.puree.com.tw/categories/5de0ed61764cf40a3cb104ba?limit=72&page=",
        "https://www.puree.com.tw/categories/%E5%96%AE%E4%B8%80%E5%83%B9?limit=72&page=",
        "https://www.puree.com.tw/categories/%E9%AB%98%E8%B2%B4%E4%B8%8D%E8%B2%B4?limit=72&page=",
        "https://www.puree.com.tw/categories/169%E5%85%83%E5%B0%88%E5%8D%80?limit=72&page=",
        "https://www.puree.com.tw/categories/49%E5%B0%88%E5%8D%80?limit=72&page=",
        "https://www.puree.com.tw/categories/269%E5%B0%88%E5%8D%80?limit=72&page=",
    ]
    urls = [f"{prefix}{i}" for prefix in prefix_urls for i in range(1, 18)]

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
        for i in range(1, 20)
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


# 151_AJPEACE
# class AjpeaceCrawler(BaseCrawler):
#     id = 151
#     name = "ajpeace"
#     urls = [
#         f"https://www.ajpeace.com.tw/index.php?app=search&cate_id=all&order=g.first_shelves_date%20desc&page={i}"
#         for i in range(1, 40)
#     ]

#     def parse(self):
#         for url in self.urls:
#             response = requests.get(url, headers=self.headers)
#             soup = BeautifulSoup(response.text, features="html.parser")
#             items = soup.find_all("div", {"class": "col-sm-4 col-xs-6"})
#             self.result.extend([self.parse_product(item) for item in items])

#     def parse_product(self, item):
#         title = item.find("h5").text
#         link = "https://www.ajpeace.com.tw/" + item[0].find("a").get("href")
#         link_id = item.find("a").get("href").split("goods&")[-1]
#         image_url = item.find("img").get("src")
#         try:
#             original_price = item.find("span").text
#         except:
#             original_price = ""
#         sale_price = item.find_all("span")[1].text
#         return Product(title, link, link_id, image_url, original_price, sale_price)


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


def get_crawler(crawler_id):
    crawlers = {
        "1": GracegiftCrawler(),
        "2": LegustCrawler(),
        "4": AjpeaceCrawler(),
        "5": MajormadeCrawler(),
        "7": BasicCrawler(),
        "8": AirspaceCrawler(),
        "9": YocoCrawler(),
        "10": EfshopCrawler(),
        "11": ModaCrawler(),
        "45": GogosingCrawler(),
        "53": KerinaCrawler(),
        "52": ApplestarryCrawler(),
        # "58": HarperCrawler(),
        "63": JendesCrawler(),
        "65": SivirCrawler(),
        "83": PotatochicksCrawler(),
        # "85": SumiCrawler(),
        # "92": BisouCrawler(),
        # "112": VeryyouCrawler(),
        # "126": SandaruCrawler(),
        "142": LovfeeCrawler(),
        "143": MarjorieCrawler(),
        "144": PureeCrawler(),
        "146": RereburnCrawler(),
        "147": StylenandaCrawler(),
        "148": ThegirlwhoCrawler(),
        "150": ChuuCrawler(),
        "152": TrudamodaCrawler(),
        "159": LamochaCrawler(),
    }
    return crawlers.get(str(crawler_id))
