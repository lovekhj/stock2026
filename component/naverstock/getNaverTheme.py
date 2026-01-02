import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import sys

from common import file_manager, get_daily_folder_path, get_today_str

# -----------------------------------------------------------------------------------------
# [교육용 주석: 네이버 금융 테마 크롤링]
# 이 스크립트는 네이버 금융(https://finance.naver.com/sise/theme.naver)에서
# 현재 시장의 테마 목록과 등락률 정보를 수집합니다.
# 
# 사용된 주요 라이브러리:
# 1. requests: 웹페이지의 HTML 코드를 가져옵니다.
# 2. BeautifulSoup: 가져온 HTML 코드를 분석해서 원하는 데이터(테마명, 등락률 등)를 추출합니다.
# 3. pandas: 수집한 데이터를 엑셀이나 CSV 파일로 쉽게 저장하기 위해 사용합니다.
# -----------------------------------------------------------------------------------------

def get_theme_data(page_num):
    """
    특정 페이지의 테마 정보를 수집하여 리스트로 반환하는 함수입니다.
    Args:
        page_num (int): 수집할 페이지 번호
    Returns:
        list: 테마 정보(딕셔너리)가 담긴 리스트
    """
    url_basic = "https://finance.naver.com/sise"
    url = f"https://finance.naver.com/sise/theme.naver?&page={page_num}"
    
    # 웹 서버에 요청을 보냅니다.
    response = requests.get(url)
    
    # 네이버 금융은 오래된 사이트라 인코딩이 'euc-kr'로 되어 있는 경우가 많습니다.
    # 한글 깨짐을 방지하기 위해 인코딩을 명시해줍니다.
    response.encoding = 'euc-kr'
    
    # HTML 분석기(Parser) 생성
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 테마 테이블 찾기 (class='type_1'인 테이블)
    theme_table = soup.find('table', {'class': 'type_1'})
    
    # 테이블의 행(tr)들을 모두 가져오되, 앞의 2줄은 헤더(제목)이므로 제외([2:])합니다.
    theme_rows = theme_table.find_all('tr')[2:]
    
    themes_data = []
    
    for row in theme_rows:
        cols = row.find_all('td')
        
        # 데이터가 있는 행인지 확인 (구분선 등 빈 행 제외)
        if len(cols) > 1:
            # print("cols==>", cols) # 디버깅용 출력
            
            # 테마 상세 페이지 링크 추출
            # HTML 구조: <td> <a href="...">테마명</a> </td>
            link_tag = cols[0].find('a')
            theme_url = url_basic + link_tag['href']
            # print("theme_url==>", theme_url)
            
            theme_name = link_tag.text.strip()
            change_rate = cols[1].text.strip()
            
            themes_data.append({
                '테마명': theme_name,
                '전일대비': change_rate,
                '상세url': theme_url,
            })
    
    return themes_data


def naverTheme():
    """메인 실행 함수"""
    print("="*50)
    print("네이버 금융 테마 목록 수집을 시작합니다.")
    print("="*50)

    # 1. 데이터 수집 (1페이지 ~ 8페이지)
    # 네이버 테마 페이지는 보통 7~8페이지 정도입니다. 넉넉하게 9까지 반복합니다.
    all_themes_data = []
    for page in range(1, 9):
        print(f"{page} 페이지 수집 중...")
        page_data = get_theme_data(page)
        all_themes_data.extend(page_data)
        time.sleep(0.5)  # 서버에 무리를 주지 않기 위해 잠시 대기
    
    print(f"총 {len(all_themes_data)}개의 테마 정보를 수집했습니다.")

    # 2. 날짜 및 경로 설정 (common 모듈 사용)
    today = get_today_str()
    folder_path = get_daily_folder_path()

    # 3. 파일 저장
    output_filename = f'naver_themes_list_{today}.csv'
    
    # 이미 파일이 있다면 삭제
    file_manager.check_and_delete_file(os.path.join(folder_path, output_filename))

    # 데이터프레임 생성 및 CSV 저장
    df = pd.DataFrame(all_themes_data)
    
    # utf-8-sig: 엑셀에서 한글이 깨지지 않게 하는 인코딩
    save_path = os.path.join(folder_path, output_filename)
    df.to_csv(save_path, index=False, encoding='utf-8-sig')
    
    print(f"성공: 테마 목록이 '{output_filename}' 파일로 저장되었습니다.")

if __name__ == "__main__":
    naverTheme()
