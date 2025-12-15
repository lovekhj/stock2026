# todo
# naver news crawling

# 정치 : https://news.naver.com/section/100
# 경제 : https://news.naver.com/section/101
# 사회 : https://news.naver.com/section/102
# 생활/문화 : https://news.naver.com/section/103
# IT/과학 : https://news.naver.com/section/105
# 세계 : https://news.naver.com/section/104
# 랭킹 : https://news.naver.com/main/ranking/popularDay.naver?mid=etc&sid1=111





from component.navernews import getNaverNewsList
from file_manager import FileManager
import datetime
import pandas as pd
from konlpy.tag import Okt
from collections import Counter

file_manager = FileManager()

def call_news_main():
    print("main")

    today = datetime.datetime.now().strftime("%Y%m%d")
    folder_path = file_manager.make_folder(today)
    total_news = []
    for i in range(6):
        # print(f"https://news.naver.com/section/10{i}")
        news = getNaverNewsList.naver_news(f"https://news.naver.com/section/10{i}")
        total_news = total_news + news

    output_filename = f'today_news_{today}.csv'
    output_excel_filename = f'today_news_{today}.xlsx'
    file_manager.check_and_delete_file(folder_path+'/'+output_filename)

    df = pd.DataFrame(total_news)
    df.to_csv(folder_path+'/'+output_filename, index=False, encoding='utf-8-sig')
    df.to_excel(folder_path+'/'+output_excel_filename, index=False, columns=None)
    
    print("done")

    return folder_path+'/'+output_filename

def call_konlpy(fileNm):
# def call_konlpy():
    # CSV 파일 읽기
    # df = pd.read_csv("20250502/today_news_20250502.csv")
    df = pd.read_csv(fileNm)

    # 형태소 분석기
    okt = Okt()

    # 명사/동사 추출
    nouns = []
    verbs = []

    for title in df['title']:
        tokens = okt.pos(title)
        nouns += [word for word, pos in tokens if pos == 'Noun']
        verbs += [word for word, pos in tokens if pos == 'Verb']

    # 빈도 수 계산
    noun_freq = Counter(nouns).most_common(20)
    verb_freq = Counter(verbs).most_common(20)

    print("명사 상위 20개:", noun_freq)
    print("동사 상위 20개:", verb_freq)


if __name__ == '__main__':
    csv_file = call_news_main()
    # call_konlpy(csv_file)
    # call_konlpy()
