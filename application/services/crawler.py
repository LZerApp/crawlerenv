from datetime import datetime
from collections import namedtuple
import requests
from openpyxl import Workbook
from bs4 import BeautifulSoup
from config import ENV_VARIABLE

fold_path = "./crawler_data/"

Product = namedtuple('Product', [
                     'title', 'page_link', 'page_id', 'pic_link', 'ori_price', 'sale_price'])
# Product = namedtuple('Product', ['title', 'url', 'page_id', 'img_url', 'original_price', 'sale_price'])


class BaseCrawler(object):
    header = {
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml,*/*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,la;q=0.5,ja;q=0.4',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        'cache-control': "no-cache"
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
        filename = '_'.join(
            [str(self.id), self.name, datetime.today().strftime("%Y%m%d")])

        book = Workbook()
        sheet = book.active
        sheet.append(Product._fields)
        for product in self.result:
            sheet.append([*product])
        book.save(fold_path + filename + '.xlsx')

    def upload(self):
        filename = '_'.join(
            [str(self.id), self.name, datetime.today().strftime("%Y%m%d")])
        try:
            headers = {
                **self.headers,
                'authorization': ENV_VARIABLE['SERVER_TOKEN'],
            }
            url = f"{ENV_VARIABLE['SERVER_URL']}/api/import/product"
            files = {
                'file': (filename + '.xlsx', open(fold_path + filename + '.xlsx', 'rb')),
            }
            response = requests.post(
                verify=False, url=url, files=files, headers=headers)
            # os.remove(filename+'.xlsx')
        except Exception as e:
            print(e)


# 142_LOVFEE
class LovfeeCrawler(BaseCrawler):
    id = 142
    name = 'lovfee'
    urls = [
        f'https://www.lovfee.com/PDList2.asp?item1=01&item2=&item3=&keyword=&ob=A&pagex=&pageno={i}' for i in range(1, 18)]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.header)
            soup = BeautifulSoup(response.text, features='html.parser')
            items = soup.find('div', {'id': 'productList'}).find_all('li')
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "pdname"}).text
        url = 'https://www.lovfee.com/' + item.find('a').get('href')
        page_id = url.split('?')[1]
        img_url = item.find('img').get('src')
        original_price = item.find("span", {"class": "original"}).text if item.find(
            "span", {"class": "original"}) else ""
        sale_price = item.find("span", {"class": "sale"}).text if item.find(
            "span", {"class": "original"}) else item.find("span", {"class": "normal"}).text

        return Product(title, url, page_id, img_url, original_price, sale_price)


# 143_MAJORIE
class MarjorieCrawler(BaseCrawler):
    id = 143
    name = 'marjorie'
    urls = [
        f'https://www.marjorie.co/store/storelist.php?ed=all&page={i}' for i in range(1, 18)]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.header)
            soup = BeautifulSoup(response.text, features='html.parser')
            items = soup.find('div', {'class': 'list'}).find_all('a')
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.get('title')
        url = 'https' + item.get('href')
        page_id = url.split('?')[1]
        img_url = item.find_all('img')[1].get('src')
        original_price = 0
        sale_price = item.find('p').text.split(" ")[1]

        return Product(title, url, page_id, img_url, original_price, sale_price)


# 144_PUREE
class PureeCrawler(BaseCrawler):
    id = 144
    name = 'puree'
    prefix_urls = [
        'https://www.puree.com.tw/categories/5de0fcefebae29002aba2258?limit=72&page=',
        'https://www.puree.com.tw/categories/5de0fd8257f0813f7eb79301?limit=72&page=',
        'https://www.puree.com.tw/categories/5de0ed61764cf40a3cb104ba?limit=72&page=',
        'https://www.puree.com.tw/categories/%E5%96%AE%E4%B8%80%E5%83%B9?limit=72&page=',
        'https://www.puree.com.tw/categories/%E9%AB%98%E8%B2%B4%E4%B8%8D%E8%B2%B4?limit=72&page=',
        'https://www.puree.com.tw/categories/169%E5%85%83%E5%B0%88%E5%8D%80?limit=72&page=',
        'https://www.puree.com.tw/categories/49%E5%B0%88%E5%8D%80?limit=72&page=',
        'https://www.puree.com.tw/categories/269%E5%B0%88%E5%8D%80?limit=72&page='
    ]
    urls = [f'{prefix}{i}' for prefix in prefix_urls for i in range(1, 18)]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.header)
            soup = BeautifulSoup(response.text, features='html.parser')
            items = soup.find_all('product-item')
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find(
            'div', {
                'class': 'title text-primary-color title-container ellipsis'
            }).text.strip()
        page_link = 'https://www.puree.com.tw' + (item.find('a').get('href'))
        prefix_id = page_link.split('/')
        page_id = prefix_id[-1]

        try:
            pre_img = item.find(
                'div', {
                    'class': 'boxify-image center-contain sl-lazy-image'
                }).get('style')
        except:
            pre_img = item.find('div', {
                'class':
                'boxify-image center-contain sl-lazy-image out-of-stock'
            }).get('style')
        pic_link = pre_img.split(':url(')[1].replace(')', "")
        try:

            ori_price = (item.find(
                'div', {
                    'class': 'global-primary dark-primary price price-crossed'
                }).text).strip()
        except:
            ori_price = ""
        ori_price = ori_price.strip('NT$')

        try:
            sale_price = item.find('div', {
                'class': 'price-sale price'
            }).text.strip()
        except:
            sale_price = item.find(
                'div', {
                    'class': 'global-primary dark-primary price'
                }).text.strip()
        sale_price = sale_price.strip('NT$')

        return Product(title, page_link, page_id, pic_link, ori_price,
                       sale_price)


# 146_Rereburn
class RereburnCrawler(BaseCrawler):
    id = 146
    name = 'rereburn'
    urls = [
        f'https://www.rereburn.com.tw/products?page={i}&sort_by=&order_by=&limit=24' for i in range(1, 20)]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.header)
            soup = BeautifulSoup(response.text, features='html.parser')
            items = soup.find('div', {
                'class': 'col-xs-12 ProductList-list'
            }).find_all('a')
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find('div', {'class': 'Label-title'}).text
        try:
            pic = item.find('div', {
                'class':
                'Image-boxify-image js-image-boxify-image sl-lazy-image'
            }).get('style')
        except:
            pic = item.find(
                'div', {
                    'class':
                    'Image-boxify-image js-image-boxify-image sl-lazy-image out-of-stock'
                }).get('style')
        pic_link = (pic.split('url(')[1]).replace('?)', "")
        page_link = item.get('href')
        page_id = item.get('product-id')
        try:
            sale_price = item.find(
                'div', {
                    'class': 'Label-price sl-price is-sale primary-color-price'
                }).text
            try:
                ori_price = item.find(
                    'div', {
                        'class': 'Label-price sl-price Label-price-original'
                    }).text
            except:
                pass
        except:
            sale_price = item.find('div', {
                'class': 'Label-price sl-price'
            }).text
            ori_price = ""
        ori_price = ori_price.lstrip()
        ori_price = ori_price.strip('NT$')
        sale_price = sale_price.lstrip()
        sale_price = sale_price.strip('NT$')
        return Product(title, page_link, page_id, pic_link, ori_price,
                       sale_price)


# 147_STYLENANDA
class StylenandaCrawler(BaseCrawler):
    id = 147
    name = 'stylenanda'
    prefix_urls = [
        'https://tw.stylenanda.com/product/list.html?cate_no=613',
        'https://tw.stylenanda.com/product/list_3ce_main.html?cate_no=1784',
        'https://tw.stylenanda.com/product/list_made_main.html?cate_no=182',
        'https://tw.stylenanda.com/product/list.html?cate_no=460',
        'https://tw.stylenanda.com/product/list.html?cate_no=1323',
        'https://tw.stylenanda.com/product/list.html?cate_no=2094',
        'https://tw.stylenanda.com/product/list.html?cate_no=51',
        'https://tw.stylenanda.com/product/list.html?cate_no=50',
        'https://tw.stylenanda.com/product/list.html?cate_no=54',
        'https://tw.stylenanda.com/product/list.html?cate_no=52',
        'https://tw.stylenanda.com/product/list.html?cate_no=53',
        'https://tw.stylenanda.com/product/list.html?cate_no=56',
        'https://tw.stylenanda.com/product/list.html?cate_no=77',
        'https://tw.stylenanda.com/product/list.html?cate_no=55',
        'https://tw.stylenanda.com/product/list.html?cate_no=174',
        'https://tw.stylenanda.com/product/list_outlet.html?cate_no=3175'
    ]
    urls = [
        f'{prefix}&page=4={i}' for prefix in prefix_urls for i in range(1, 14)
    ]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.header)
            soup = BeautifulSoup(response.text, features='html.parser')
            items = soup.find_all('li', {'class': 'item xans-record-'})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        pre_title = item.find('div', {'class': 'name'}).text
        title = pre_title.split(':')[1]
        page_link = 'https://tw.stylenanda.com' + item.find('a').get('href')
        prefix_id = page_link.split('?')
        page_id = prefix_id[1]
        pic_link = item.find('img').get('src')
        price = item.find('p', {'class': 'price'})
        sale_price = (price.find('span').text).replace("→", "")
        ori_price = item.find('p', {'class': 'price'}).text.split('→')[0]
        ori_price = ori_price.lstrip()
        ori_price = ori_price.strip('NT$')
        sale_price = sale_price.lstrip()
        sale_price = sale_price.strip('NT$')
        return Product(title, page_link, page_id, pic_link, ori_price,
                       sale_price)


# 148_THEGIRLWHO
class ThegirlwhoCrawler(BaseCrawler):
    id = 148
    name = 'thegirlwho'
    urls = [
        f'https://www.thegirlwhoshop.com/product.php?page={i}&cid=1#prod_list' for i in range(1, 9)]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.header)
            soup = BeautifulSoup(response.text, features='html.parser')
            items = soup.find_all('div',
                                  {'class': 'col-xs-6 col-sm-4 col-md-3'})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find('a').get('title')
        page_link = item.find('a').get('href')
        pre_id = item.find('a').get('href').split('&pid=')
        page_id = pre_id[-1]
        pic_link = item.find('img').get('src')
        ori_price = ""
        sale_price = item.find('div', {'class': 'prod-price'}).text
        ori_price = ori_price.strip('NT$.')
        sale_price = sale_price.strip('NT$.')
        return Product(title, page_link, page_id, pic_link, ori_price,
                       sale_price)


# 150_CHUU
class ChuuCrawler(BaseCrawler):
    id = 150
    name = 'chuu'
    urls = [
        'https://chuu.com.tw/product/list.html?cate_no=30',
        'https://chuu.com.tw/category/20210217%E8%81%B7%E5%A0%B4%E5%96%AE%E5%93%819%E6%8A%98/862/',
        'https://chuu.com.tw/product/list.html?cate_no=31',
        'https://chuu.com.tw/product/list.html?cate_no=39',
        'https://chuu.com.tw/product/list.html?cate_no=249',
        'https://chuu.com.tw/product/list.html?cate_no=224',
        'https://chuu.com.tw/product/list.html?cate_no=214',
        'https://chuu.com.tw/product/list.html?cate_no=35',
        'https://chuu.com.tw/product/list.html?cate_no=251',
        'https://chuu.com.tw/product/list.html?cate_no=252',
        'https://chuu.com.tw/product/list.html?cate_no=253',
        'https://chuu.com.tw/product/list.html?cate_no=254',
        'https://chuu.com.tw/product/list.html?cate_no=300',
        'https://chuu.com.tw/product/list.html?cate_no=301',
        'https://chuu.com.tw/product/list.html?cate_no=302',
        'https://chuu.com.tw/product/list.html?cate_no=36',
        'https://chuu.com.tw/product/list.html?cate_no=256',
        'https://chuu.com.tw/product/list.html?cate_no=218',
        'https://chuu.com.tw/product/list.html?cate_no=226',
        'https://chuu.com.tw/product/list.html?cate_no=232',
        'https://chuu.com.tw/product/list.html?cate_no=211',
        'https://chuu.com.tw/product/list.html?cate_no=257',
        'https://chuu.com.tw/product/list.html?cate_no=34',
        'https://chuu.com.tw/product/list.html?cate_no=258',
        'https://chuu.com.tw/product/list.html?cate_no=213',
        'https://chuu.com.tw/product/list.html?cate_no=236',
        'https://chuu.com.tw/product/list.html?cate_no=219',
        'https://chuu.com.tw/product/list.html?cate_no=229',
        'https://chuu.com.tw/product/list.html?cate_no=259',
        'https://chuu.com.tw/product/list.html?cate_no=67',
        'https://chuu.com.tw/product/list.html?cate_no=209',
        'https://chuu.com.tw/product/list.html?cate_no=220',
        'https://chuu.com.tw/product/list.html?cate_no=260',
        'https://chuu.com.tw/product/list.html?cate_no=225',
        'https://chuu.com.tw/product/list.html?cate_no=231',
        'https://chuu.com.tw/product/list.html?cate_no=261',
        'https://chuu.com.tw/product/list.html?cate_no=40',
        'https://chuu.com.tw/product/list.html?cate_no=41',
        'https://chuu.com.tw/product/list.html?cate_no=42',
        'https://chuu.com.tw/product/list.html?cate_no=262',
        'https://chuu.com.tw/product/list.html?cate_no=263',
        'https://chuu.com.tw/product/list.html?cate_no=264',
        'https://chuu.com.tw/product/list.html?cate_no=265',
        'https://chuu.com.tw/product/list.html?cate_no=266',
        'https://chuu.com.tw/product/list.html?cate_no=267',
        'https://chuu.com.tw/product/list.html?cate_no=753',
        'https://chuu.com.tw/product/list.html?cate_no=43',
        'https://chuu.com.tw/product/list.html?cate_no=268',
        'https://chuu.com.tw/product/list.html?cate_no=269',
        'https://chuu.com.tw/product/list.html?cate_no=270',
        'https://chuu.com.tw/product/list.html?cate_no=271',
        'https://chuu.com.tw/product/list.html?cate_no=32',
        'https://chuu.com.tw/products/-5kg%20jeans/189/',
    ]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.header)
            soup = BeautifulSoup(response.text, features='html.parser')
            items = soup.find_all('li', {'class': 'item xans-record-'})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            pre_title = item.find('p', {'class': 'name'}).text
            title = pre_title.split('商品名 :')[-1]
            page_link = 'https://chuu.com.tw' + item.find('a').get('href')
            page_id = item.find('a').get('href').split('product_no=')[-1]
            pic_link = item.find('img').get('src')
            rate = item.find_all('li', {'class': 'xans-record-'})
            try:
                for z in rate:
                    op = (z.text).split(':')[-1]
                    if '$' in op:
                        ori_price = op
                        break
            except:
                ori_price = ""
            sale_price = (rate[-1].text).split(':')[-1]
        except:
            title = 'no'

        ori_price = ori_price.lstrip()
        ori_price = ori_price.strip('NT$')
        sale_price = sale_price.lstrip()
        sale_price = sale_price.strip('NT$')
        return Product(title, page_link, page_id, pic_link, ori_price,
                       sale_price)


# 151_AJPEACE
class AjpeaceCrawler(BaseCrawler):
    id = 151
    name = 'ajpeace'
    urls = [
        f'https://www.ajpeace.com.tw/index.php?app=search&cate_id=all&order=g.first_shelves_date%20desc&page={i}' for i in range(1, 40)]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.header)
            soup = BeautifulSoup(response.text, features='html.parser')
            items = soup.find_all('div', {'class': 'col-sm-4 col-xs-6'})
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find('h5').text
        page_link = 'https://www.ajpeace.com.tw/' + \
            item[0].find('a').get('href')
        pg = item.find('a').get('href')
        page_id = pg.split('goods&')[-1]
        pic_link = item.find('img').get('src')
        try:
            ori_price = item.find('span').text
        except:
            ori_price = ""
        sale_price = item.find_all('span')[1].text
        return Product(title, page_link, page_id, pic_link, ori_price,
                       sale_price)


# 152_TRUDAMODA
class TrudamodaCrawler(BaseCrawler):
    id = 152
    name = 'trudamoda'
    urls = []
    prefix_urls = [
        'https://www.truda-moda.com.tw/categories/top?page={}&sort_by=&order_by=&limit=72',
        'https://www.truda-moda.com.tw/categories/bottom-%E4%B8%8B%E8%91%97?page={}&sort_by=&order_by=&limit=72',
        'https://www.truda-moda.com.tw/categories/outer?page={}&sort_by=&order_by=&limit=72',
        'https://www.truda-moda.com.tw/categories/jumpsuit-%E5%A5%97%E8%A3%9D?page={}&sort_by=&order_by=&limit=72',
        'https://www.truda-moda.com.tw/categories/accessories-%E9%85%8D%E4%BB%B6?page={}&sort_by=&order_by=&limit=72'
    ]
    for i in prefix_urls:
        for j in range(1, 7):
            f = i.format(j)
            urls.append(f)

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.header)
            soup = BeautifulSoup(response.text, features='html.parser')
            pre_items = soup.find('div',
                                  {'class': 'col-xs-12 ProductList-list'})
            items = pre_items.find_all('product-item')
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        try:
            title = item.find('div', {
                'class': 'title text-primary-color'
            }).text
            page_link = item.find('a').get('href')
            page_id = page_link.split('/')[-1]
            pic_ = item.find(
                'div', {
                    'class':
                    'boxify-image js-boxify-image center-contain sl-lazy-image'
                }).get('style')
            pic_link = pic_.split('url(')[-1].replace(")", "")
            pr = item.find('div', {'class': 'quick-cart-price'})
            div = pr.find_all('div')
            try:
                ori_price = div[1].text.strip()
            except:
                ori_price = ""
            sale_price = div[0].text.strip()
        except:
            pass
        return Product(title, page_link, page_id, pic_link, ori_price,
                       sale_price)


# 159_LAMOCHA
class LamochaCrawler(BaseCrawler):
    id = 159
    name = 'lamocha'
    urls = [
        f'https://www.lamocha.com.tw/PDList.asp?item1=3&item2=2&tbxKeyword=&recommand=&ob=B&gd=b&pageno={i}' for i in range(1, 90)]

    def parse(self):
        for url in self.urls:
            response = requests.get(url, headers=self.header)
            soup = BeautifulSoup(response.text, features='html.parser')
            items = soup.find(
                'section', {'id': 'pdlist'}).find('ul').find_all('li')
            self.result.extend([self.parse_product(item) for item in items])

    def parse_product(self, item):
        title = item.find("div", {"class": "figcaption"}).find("p").text
        url = 'https://www.lamocha.com.tw/' + item.find('a').get('href')
        page_id = 'yano' + url.split('yano')[-1]
        img_url = item.find('img').get('src')
        original_price = item.find("p", {"class": "salePrice"}).find(
            "span").text if item.find("p", {"class": "salePrice"}) else ""
        sale_price = item.find("p", {"class": "salePrice"}).contents[0] if item.find(
            "p", {"class": "salePrice"}) else item.find("div", {"class": "figcaption"}).find_all("p")[1].text
        return Product(title, url, page_id, img_url, original_price, sale_price)


def get_crawler(crawler_id):
    crawlers = {
        '142': LovfeeCrawler(),
        '143': MarjorieCrawler(),
        '144': PureeCrawler(),
        '146': RereburnCrawler(),
        '147': StylenandaCrawler(),
        '148': ThegirlwhoCrawler(),
        '150': ChuuCrawler(),
        '151': AjpeaceCrawler(),
        '152': TrudamodaCrawler(),
        '159': LamochaCrawler(),
    }
    return crawlers.get(str(crawler_id))
