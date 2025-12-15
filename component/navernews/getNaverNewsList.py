from typing import Any
import requests
from bs4 import BeautifulSoup
from file_manager import FileManager
import datetime
import pandas as pd

# install lxml

file_manager = FileManager()

def request_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
    }
    response = requests.get(url, headers = headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    return soup

def naver_news(url) -> list[Any]:
    soup = request_url(url)
    chapter = soup.select_one("#ct_wrap > div.ct_scroll_wrapper > div.column0 > div > h2 > a")
    articles = soup.select("li > div > div > div.sa_text")

    news = []
    for tag in articles:
        url = tag.select_one("a")["href"]
        title = tag.select_one("strong").text
        press = tag.select_one("div.sa_text_info_left > div").text
        news.append({'chater':chapter.text, 'press': press, 'title': title, 'url': url})
    return news

if __name__ == '__main__':

    today = datetime.datetime.now().strftime("%Y%m%d")
    folder_path = file_manager.make_folder(today)
    total_news = []
    for i in range(6):
        news = naver_news(f"https://news.naver.com/section/10{i}")
        total_news = total_news + news

    output_filename = f'today_news_{today}.csv'
    file_manager.check_and_delete_file(folder_path+'/'+output_filename)

    df = pd.DataFrame(total_news)
    df.to_csv(folder_path+'/'+output_filename, index=False, encoding='utf-8-sig')
    print("done")