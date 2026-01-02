import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import shutil
import time
import sys

from common import file_manager, get_daily_folder_path, get_today_str

# -----------------------------------------------------------------------------------------
# [교육용 주석: 네이버 금융 테마 상세 정보 크롤링]
# 이 스크립트는 이전에 수집한 '네이버 테마 목록(CSV)'을 읽어서,
# 각 테마별 상세 페이지(구성 종목, 편입 사유 등)를 크롤링하여 저장합니다.
#
# Process:
# 1. 오늘 날짜의 테마 목록 파일 읽기
# 2. 각 테마의 URL에서 고유 번호 추출
# 3. 상세 페이지 접근하여 종목 정보 수집
# 4. 결과 저장
# -----------------------------------------------------------------------------------------

def get_theme_detail(themeNm, themeRate, theme_no):
    """
    특정 테마의 상세 페이지에서 구성 종목 정보를 수집합니다.
    Args:
        themeNm (str): 테마 이름
        themeRate (str): 테마 평균 등락률
        theme_no (str): 테마 고유 번호 (네이버 URL 파라미터)
    Returns:
        list: 해당 테마에 속한 종목들의 상세 정보 리스트
    """
    theme_nm = themeNm
    theme_rate = themeRate
    
    # 테마 상세 페이지 URL 구성
    url = f"https://finance.naver.com/sise/sise_group_detail.naver?type=theme&no={theme_no}"
    
    response = requests.get(url)
    response.encoding = 'euc-kr'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 종목 테이블 찾기 (class='type_5')
    stock_table = soup.find('table', {'class': 'type_5'})
    
    # 헤더(제목) 행 2개를 제외하고 데이터 행부터 가져옴
    stock_rows = stock_table.find_all('tr')[2:]
    
    stocks_data = []
    
    for row in stock_rows:
        cols = row.find_all('td')
        
        # 데이터가 있는 유효한 행인지 확인
        if len(cols) > 1:
            # 첫 번째 컬럼에서 종목코드 링크 찾기
            code_link = cols[0].find('a')
            if code_link:
                # href 링크에서 종목코드 추출 (...code=005930)
                code = code_link['href'].split('code=')[1]
                name = code_link.text.strip()
                
                # 데이터 정제 (공백, 줄바꿈 제거, 기호 통일 등)
                price_diff = cols[3].text.strip().replace(chr(10),'').replace('\t','').replace(' ','').replace('상승','+').replace('하락','-')
                change_rate = cols[4].text.strip().replace('%', '')
                volume = cols[7].text.strip().replace(',', '')
                
                # 편입 사유 추출 (p 태그의 info_txt 클래스)
                reason_tag = cols[1].find('p', {'class': 'info_txt'})
                reason = reason_tag.text.strip() if reason_tag else ""
                
                stocks_data.append({
                    '테마' : theme_nm, 
                    '테마등락률': theme_rate,
                    '종목코드': code,
                    '종목명': name,
                    '전일비': price_diff,
                    '등락률': change_rate,
                    '거래량': volume,
                    '편입사유': reason,
                })
    return stocks_data

def naverThemeDtl():
    """메인 실행 함수"""
    print("="*50)
    print("네이버 금융 테마 상세 정보(종목 및 편입사유) 수집을 시작합니다.")
    print("="*50)
    
    # 1. 날짜 및 경로 설정 (common 모듈 사용)
    today = get_today_str()
    folder_path = get_daily_folder_path()

    # 2. 테마 목록 파일 읽기
    # 먼저 실행되어야 하는 'getNaverTheme.py'의 결과물을 참조합니다.
    theme_list_file = os.path.join(folder_path, f'naver_themes_list_{today}.csv')
    
    if not os.path.exists(theme_list_file):
        print(f"오류: 테마 목록 파일이 없습니다. ({theme_list_file})")
        print("getNaverTheme.py를 먼저 실행해주세요.")
        return

    theme_df = pd.read_csv(theme_list_file)
    print(f"총 {len(theme_df)}개의 테마에 대한 상세 정보를 수집합니다.")

    all_stocks_data = []
    
    # 3. 각 테마별 상세 정보 수집
    # iterrows()는 데이터프레임의 각 행을 반복합니다.
    for idx, row in theme_df.iterrows():
        theme_nm = row.get('테마명')
        theme_rate = row.get('전일대비')
        theme_url = row.get('상세url')

        if theme_url:
            # URL에서 'no=' 뒤의 숫자(테마 번호) 추출
            theme_no = theme_url.split('no=')[1]
            
            # 진행상황 출력
            print(f"[{idx + 1}/{len(theme_df)}] 테마 정보 수집 중: {theme_nm}")
            
            stocks_data = get_theme_detail(theme_nm, theme_rate, theme_no)
            all_stocks_data.extend(stocks_data)
            
            time.sleep(0.5)  # 서버 부하 방지
    
    # 4. 결과 저장
    output_filename = f'naver_themes_dtl_list_{today}.csv'
    save_path = os.path.join(folder_path, output_filename)

    # 동일 파일 삭제
    file_manager.check_and_delete_file(save_path)
    
    # DataFrame 생성 및 CSV 저장
    df = pd.DataFrame(all_stocks_data)
    df.to_csv(save_path, index=False, encoding='utf-8-sig')
    
    print(f"성공: 테마 상세 정보가 '{output_filename}' 파일로 저장되었습니다.")

if __name__ == "__main__":
    naverThemeDtl()