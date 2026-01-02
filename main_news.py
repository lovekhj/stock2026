# todo
# naver news crawling
# politics : https://news.naver.com/section/100
# economy : https://news.naver.com/section/101
# society : https://news.naver.com/section/102
# culture : https://news.naver.com/section/103
# science : https://news.naver.com/section/105
# world : https://news.naver.com/section/104

from component.navernews import getNaverNewsList

def call_news_main():
    """
    네이버 뉴스 크롤링을 실행합니다.
    실제 로직은 component/navernews/getNaverNewsList.py 에 구현되어 있습니다.
    (엑셀 저장, 정렬, 키워드 분석 등 포함)
    """
    print("main_news.py: 뉴스 크롤링 호출")
    getNaverNewsList.getNaverNews()
    print("main_news.py: 완료")

# KoNLPy 관련 기능은 현재 getNaverNewsList.py의 자체 분석 기능으로 대체되었으므로 주석 처리합니다.
# 필요 시 다시 활성화하거나 getNaverNewsList.py로 통합할 수 있습니다.
# def call_konlpy(fileNm):
#     ...

if __name__ == '__main__':
    call_news_main()
