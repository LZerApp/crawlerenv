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
        crawler.parse()
        crawler.save()
        crawler.upload()
        return None

    crawler = get_tempcrawler(crawler_id)

    if crawler:
        print(f"Crawler No. {crawler_id} written in tempcrawler.py.")
        crawler()
        return None

    print(f"Crawler No. {crawler_id} haven't been implemented yet.")
