import requests
from flask_apscheduler import APScheduler
from application.services.crawler import get_crawler
from application.services.tempcrawler import get_tempcrawler
from config import ENV_VARIABLE

scheduler = APScheduler()


# @scheduler.task('interval', id='do_job_1', seconds=30, misfire_grace_time=900)
# def job1():
#     brands = get_brands()
#     print(brands)
@scheduler.task('cron', id='do_job_4', hour='18', minute='58')
def job_crawler():
    brands = get_brands()
    for brand in brands:
        print(f"CURRENT CRAWLER: NO. {brand[0]} {brand[1]}")
        crawler = get_crawler(brand[0])

        if crawler:
            try:
                crawler.parse()
                crawler.save()
                crawler.upload()
                continue
            except:
                pass

        crawler = get_tempcrawler(brand[0])

        if crawler:
            try:
                crawler()
            except:
                pass


def get_brands():
    url = f"{ENV_VARIABLE['SERVER_URL']}/api/spider/brands"
    headers = {
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml,*/*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,la;q=0.5,ja;q=0.4',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        'cache-control': "no-cache",
        'authorization': ENV_VARIABLE['SERVER_TOKEN'],
    }

    try:
        response = requests.get(url=url, headers=headers, verify=False)
        result = response.json().get('data')
    except Exception as e:
        print(e)

    return [(brand['id'], brand['name']) for brand in result if brand['status'] == True]
