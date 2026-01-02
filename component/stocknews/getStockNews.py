import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import time
import random
from urllib.parse import quote

from common import file_manager, get_daily_folder_path, get_today_str
from component.excel_utils import auto_adjust_column_width

# -----------------------------------------------------------------------------------------
# [교육용 주석: 구글 뉴스 RSS 크롤링]
# 이 스크립트는 'total_YYYYMMDD.xlsx' 파일에 있는 종목명으로 구글 뉴스 검색을 수행합니다.
# 웹페이지를 직접 긁는 것(Parsing)보다 RSS 피드를 사용하는 것이 훨씬 안정적이고 빠릅니다.
#
# RSS URL 예시: https://news.google.com/rss/search?q={검색어}&hl=ko&gl=KR&ceid=KR:ko
# -----------------------------------------------------------------------------------------

def search_google_news_rss(query):
    """
    구글 뉴스 RSS를 검색하여 최신 뉴스 (최대 2~3개)를 반환합니다.
    """
    # URL 인코딩 (한글 검색어 처리)
    encoded_query = quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        # User-Agent 설정 (봇 차단 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(rss_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            # XML 파싱
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            news_results = []
            # 상위 2개 뉴스만 가져오기 (너무 많으면 엑셀이 복잡해짐. 필요시 조정 가능)
            for item in items[:2]: 
                title = item.title.text
                link = item.link.text
                # RSS에서 source 태그가 매체명임
                source = item.source.text if item.source else "Google News"
                
                news_results.append({
                    'media': source,
                    'title': title,
                    'url': link
                })
            return news_results
        else:
            print(f"  - RSS 요청 실패 ({response.status_code})")
            return []
            
    except Exception as e:
        print(f"  - 에러 발생: {e}")
        return []

def getStockNews():
    """
    메인 실행 함수: 종목 리스트를 읽어 뉴스 검색 후 엑셀 저장
    """
    print("="*50)
    print("구글 뉴스 검색(RSS) 기반 종목 뉴스 수집을 시작합니다.")
    print("="*50)

    today = get_today_str()
    folder_path = get_daily_folder_path()
    
    # 1. 입력 파일 로딩
    input_filename = f'total_{today}.xlsx'
    input_filepath = os.path.join(folder_path, input_filename)
    
    if not os.path.exists(input_filepath):
        print(f"오류: 입력 파일({input_filename})이 없습니다.")
        return

    try:
        df = pd.read_excel(input_filepath, sheet_name='종목분석')
    except ValueError:
        print("오류: '종목분석' 시트가 없습니다.")
        return

    all_news_data = []
    
    print(f"총 {len(df)}개 종목에 대해 뉴스를 검색합니다. (시간이 조금 걸릴 수 있습니다)")
    
    for idx, row in df.iterrows():
        code = str(row['종목코드']).zfill(6)
        name = row['종목명']
        
        print(f"[{idx+1}/{len(df)}] '{name}' 뉴스 검색 중...")
        
        # 뉴스 검색
        news_items = search_google_news_rss(name)
        
        if news_items:
            for news in news_items:
                all_news_data.append({
                    '번호': idx + 1,
                    '종목코드': code,
                    '종목명': name,
                    '뉴스매체': news['media'],
                    '뉴스내용': news['title'],
                    'url': news['url']
                })
        else:
            # 뉴스가 없는 경우도 표시할지 여부. 현재는 뉴스 있는 경우만 추가.
            pass
            
        # 구글 서버 보호를 위해 약간의 딜레이 (0.5~1초)
        time.sleep(random.uniform(0.5, 1.0))

    # 2. 결과 저장
    output_filename = f'stock_find_news_{today}.xlsx'
    output_filepath = os.path.join(folder_path, output_filename)
    
    file_manager.check_and_delete_file(output_filepath)
    
    if not all_news_data:
        print("검색된 뉴스가 하나도 없습니다.")
        return

    df_result = pd.DataFrame(all_news_data)
    
    try:
        with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
            df_result.to_excel(writer, sheet_name='종목뉴스', index=False)
            
            # [서식 적용]
            auto_adjust_column_width(writer)
            
            ws = writer.sheets['종목뉴스']
            
            # URL 컬럼은 25로 고정, 뉴스내용은 좀 넓게(80)
            col_indices = {cell.value: cell.column_letter for cell in ws[1]}
            if 'url' in col_indices:
                ws.column_dimensions[col_indices['url']].width = 25
            if '뉴스내용' in col_indices:
                ws.column_dimensions[col_indices['뉴스내용']].width = 80
            if '번호' in col_indices:
                ws.column_dimensions[col_indices['번호']].width = 8
                
        print(f"\n성공: 뉴스 수집 완료. '{output_filename}' 저장됨.")
        
    except Exception as e:
        print(f"저장 중 오류 발생: {e}")

if __name__ == "__main__":
    getStockNews()
