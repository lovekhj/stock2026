from typing import Any
import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import os
import sys
import re
from collections import Counter
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font

from common import file_manager, get_daily_folder_path, get_today_str
from component.excel_utils import auto_adjust_column_width

# install lxml

# -----------------------------------------------------------------------------------------
# [교육용 주석: 네이버 뉴스 크롤링]
# 이 스크립트는 네이버 뉴스의 섹션별(정치, 경제, 사회 등) 주요 기사 목록을 수집합니다.
# 
# 사용된 라이브러리:
# - requests: HTTP 요청
# - BeautifulSoup (bs4): HTML 파싱 (lxml 파서 사용)
# - pandas: CSV 저장
# -----------------------------------------------------------------------------------------

def request_url(url):
    """
    주어진 URL에 GET 요청을 보내고 BeautifulSoup 객체를 반환합니다.
    브라우저처럼 보이기 위해 User-Agent 정보를 헤더에 포함합니다.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    # lxml 파서가 설치되어 있어야 함 (pip install lxml)
    soup = BeautifulSoup(response.text, "lxml")
    return soup

def naver_news(url) -> list[Any]:
    """
    특정 섹션 페이지(url)에서 헤드라인이나 주요 뉴스를 추출하여 리스트로 반환합니다.
    """
    soup = request_url(url)
    
    # 섹션 이름 추출 (예: 정치, 경제 ...)
    # CSS Selector 경로를 사용하여 원하는 요소 선택
    chapter = soup.select_one("#ct_wrap > div.ct_scroll_wrapper > div.column0 > div > h2 > a")
    
    # 기사 목록 추출 (경로는 네이버 페이지 구조에 따라 달라질 수 있음)
    articles = soup.select("li > div > div > div.sa_text")

    news = []
    for tag in articles:
        # 각 기사 항목에서 링크, 제목, 언론사 정보 추출
        link_tag = tag.select_one("a")
        url = link_tag["href"]
        title = tag.select_one("strong").text
        
        # 언론사 정보 (없을 수도 있으므로 체크)
        press_tag = tag.select_one("div.sa_text_info_left > div")
        press = press_tag.text if press_tag else "알수없음"
        
        news.append({
            'section': chapter.text if chapter else "기타", 
            'press': press, 
            'title': title, 
            'url': url
        })
    return news

# -----------------------------------------------------------------------------------------
# [키워드 분석 로직]
# 
# 1. 자연어 처리 패키지(konlpy)가 환경에 없을 수 있으므로, 정규표현식과 불용어(Stopwords) 사전을 활용합니다.
# 2. 명사/대명사 위주로 추출하기 위해 조사가 붙은 단어의 끝을 잘라내는 휴리스틱(Heuristic) 방식을 일부 적용할 수 있으나,
#    여기서는 2글자 이상의 단어를 추출하고 '의미 없는 단어'를 필터링하는 방식으로 구현합니다.
# -----------------------------------------------------------------------------------------

def analyze_keywords(news_list):
    """
    뉴스 리스트를 분석하여 전체 키워드 빈도수를 계산합니다. (섹션 구분 없음)
    Args:
        news_list (list): 뉴스 정보 딕셔너리 리스트
    Returns:
        pd.DataFrame: [키워드, 빈도수] 컬럼을 가진 데이터프레임
    """
    all_words = []
    
    # 1. 불용어 사전 (분석에서 제외할 단어들)
    # 조사, 어미, 일반적인 뉴스 용어 등 실질적인 의미가 적은 단어들
    stop_words = {
        '뉴스', '속보', '종합', '오늘', '내일', '오전', '오후', '이번', '지난', '관련',
        '위해', '통해', '대해', '대한', '인해', '까지', '부터', '하고', '있는', '없는',
        '등등', '따른', '가장', '경우', '무엇', '어디', '언제', '누구', '어떻게',
        '특징주', '공시', '마감', '개장', '시황', '전망',
        '작년', '올해', '내년', '하루', '아침', '저녁', '시간', '직전',
        '작은', '많은', '좋은', '나쁜', '크게', '작게', '높은', '낮은',
        '논란에', '아침까지', '밝혀', '말해', '전해'  # 사용자 요청 불용어 및 유사 어휘 추가
    }

    for item in news_list:
        title = item['title']
        
        # 2. 정규표현식으로 한글 단어만 추출
        # ([가-힣]+) : 한글로 된 1글자 이상의 연속된 문자열
        words = re.findall(r'[가-힣]+', title)
        
        for w in words:
            # 3. 2글자 이상인 단어만 선택
            if len(w) > 1:
                # 4. 불용어 제외 (정확히 일치하거나, 불용어로 끝나는 조사 포함 단어 필터링 시도)
                if w in stop_words:
                    continue
                
                # 추가 필터링: 끝글자가 조사/어미인 경우 단순 제외보다는, stop_words에 없는 명사 파악이 어려우므로
                # 일단 사용자 요청 단어들을 stop_words에 최대한 등록하는 방식으로 대응합니다.
                all_words.append(w)
    
    # 5. 빈도수 계산
    # 전체 뉴스에서 가장 많이 등장한 상위 50개 키워드 추출
    counts = Counter(all_words).most_common(50)
    
    analysis_data = []
    for word, count in counts:
        analysis_data.append({
            '키워드': word,
            '빈도수': count
        })
            
    # DataFrame 변환
    df_analysis = pd.DataFrame(analysis_data)
    
    return df_analysis

def getNaverNews():
    """메인 실행 함수"""
    print("="*50)
    print("네이버 뉴스 섹션별 주요 기사 수집을 시작합니다.")
    print("="*50)

    today = get_today_str()
    folder_path = get_daily_folder_path()
    
    total_news = []
    
    # 네이버 뉴스 주요 섹션 ID (100:정치 ~ 105:IT/과학)
    # 100:정치, 101:경제, 102:사회, 103:생활/문화, 104:세계, 105:IT/과학
    for i in range(100, 106):
        section_url = f"https://news.naver.com/section/{i}"
        print(f"섹션 {i} 수집 중...")
        
        try:
            news = naver_news(section_url)
            total_news.extend(news)
        except Exception as e:
            print(f"섹션 {i} 수집 중 오류: {e}")

    # 1. 뉴스 데이터프레임 생성 및 정렬
    df_news = pd.DataFrame(total_news)
    
    # 제목(Title) 기준으로 정렬하여 비슷한 내용끼리 모이게 함
    if not df_news.empty:
        df_news = df_news.sort_values(by=['title'])
    
    # 2. 뉴스 분석(키워드 추출) 데이터프레임 생성 (섹션 구분 없이 전체 빈도)
    df_analysis = analyze_keywords(total_news)

    # 3. 엑셀 파일로 저장
    output_filename = f'today_news_{today}.xlsx'
    save_path = os.path.join(folder_path, output_filename)
    
    file_manager.check_and_delete_file(save_path)

    try:
        with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
            # 시트 1: 뉴스 목록
            df_news.to_excel(writer, sheet_name='뉴스목록', index=False)
            
            # 시트 2: 뉴스 분석
            df_analysis.to_excel(writer, sheet_name='뉴스분석', index=False)
            
            # --- 서식 적용 ---
            # 1. 자동 컬럼 너비 조정 (기본)
            auto_adjust_column_width(writer)
            
            # 2. '뉴스목록' 시트의 특정 컬럼 너비 강제 조정
            ws_list = writer.sheets['뉴스목록']
            
            # 헤더 인덱스 매핑
            col_idx_list = {cell.value: cell.column_letter for cell in ws_list[1]}
            
            if 'title' in col_idx_list:
                ws_list.column_dimensions[col_idx_list['title']].width = 80
            if 'url' in col_idx_list:
                ws_list.column_dimensions[col_idx_list['url']].width = 25
            if 'press' in col_idx_list:
                ws_list.column_dimensions[col_idx_list['press']].width = 25

            # 3. '뉴스분석' 시트 서식
            ws_analysis = writer.sheets['뉴스분석']
            col_idx_analysis = {cell.value: cell.column_letter for cell in ws_analysis[1]}
            
            if '키워드' in col_idx_analysis:
                # 키워드 컬럼이 잘리지 않도록 넉넉하게 설정 (자동 조정보다 우선)
                ws_analysis.column_dimensions[col_idx_analysis['키워드']].width = 30 # 한글 단어는 보통 10~20픽셀이면 충분하지만 넉넉히
            if '빈도수' in col_idx_analysis:
                ws_analysis.column_dimensions[col_idx_analysis['빈도수']].width = 15

            # 1. 하이퍼링크용 스타일 설정 (파란색 + 밑줄)
            link_font = Font(color="0000FF", underline="single")

            # 2. 'url' 컬럼이 몇 번째 열인지 확인 (예: col_idx_list에서 가져옴)
            if 'url' in col_idx_list:
                url_col_letter = col_idx_list['url'] # 예: 'C'
                
                # 3. 데이터가 있는 행(보통 2행부터)을 돌면서 링크 적용
                # ws_list[url_col_letter]는 해당 열의 모든 셀을 가져옵니다.
                for cell in ws_list[url_col_letter]:
                    if cell.row == 1: continue # 제목줄은 건너뜁니다.
                    
                    if cell.value and str(cell.value).startswith('http'):
                        # 하이퍼링크 설정
                        cell.hyperlink = cell.value
                        # 글자 색상과 밑줄 스타일 적용
                        cell.font = link_font
                        
        print(f"\n성공: 뉴스 데이터가 '{output_filename}' 파일로 저장되었습니다.")
        
    except Exception as e:
        print(f"\n오류: 파일 저장 중 문제가 발생했습니다: {e}")

if __name__ == '__main__':
    getNaverNews()