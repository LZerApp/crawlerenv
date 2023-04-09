import click
from application import create_app
from application.services.crawler import get_crawler
from application.services.tempcrawler import get_tempcrawler


app = create_app()


@app.cli.command("run-crawler")
@click.argument("crawler_id")
def run_crawler(crawler_id):
    """ Run the crawler with given CRAWLER_ID """
    print("------------------------")
    print(f"Run Crawler No. {crawler_id}")
    print("------------------------")
    crawler = get_crawler(crawler_id)

    if crawler:
        print(f"Crawler No. {crawler_id} written in crawler.py.")
        try:
            crawler.parse()
            crawler.save()
            crawler.upload()
        except Exception as e:
            print(e)
        return None

    crawler = get_tempcrawler(crawler_id)

    if crawler:
        print(f"Crawler No. {crawler_id} written in tempcrawler.py.")
        try:
            crawler()
        except Exception as e:
            print(e)
        return None

    print(f"Crawler No. {crawler_id} haven't been implemented yet.")
