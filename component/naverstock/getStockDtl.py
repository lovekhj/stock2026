import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import sys

from common import file_manager, get_daily_folder_path, get_today_str

# -----------------------------------------------------------------------------------------
# [교육용 주석: 네이버 금융 시가총액 정보 크롤링]
# 이 스크립트는 네이버 금융의 '시가총액' 페이지에서 코스피/코스닥 전 종목의 핵심 지표를 수집합니다.
# 수집 항목: 현재가, 전일비, 등락률, 거래량, PER 등
# 
# 이 데이터는 종목별 재무 상태나 시장 관심도를 파악하는 기초 데이터로 활용됩니다.
# -----------------------------------------------------------------------------------------

def get_market_cap_info(gubun, url):
    """
    네이버 금융 시가총액 페이지의 표 데이터를 크롤링합니다.
    Args:
        gubun (int): 0(=코스피), 1(=코스닥)
        url (str): 크롤링할 대상 URL
    Returns:
        list: 종목 정보 딕셔너리의 리스트
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://finance.naver.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    gubunNm = "코스피"
    if gubun == 1:
        gubunNm = "코스닥"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')

        stocks_data = []
        # type_2 테이블의 본문(tbody) 내의 모든 행(tr)을 선택
        rows = soup.select('table.type_2 tbody tr')
        
        for row in rows:
            tds = row.select('td')
            # 네이버 금융 표에는 구분선 목적의 빈 행이 많으므로 데이터가 적은 행은 건너뜀
            if len(tds) <= 1:
                continue
                
            try:
                # 종목명/링크가 있는 두 번째 컬럼(tds[1])에서 a 태그 찾기
                name_link = tds[1].select_one('a')
                if name_link:
                    code = name_link['href'].split('code=')[1]
                    name = name_link.text.strip()
                    
                    # 각 컬럼의 데이터 추출 및 특수문자 제거
                    # tds 인덱스는 페이지 소스 보기로 확인해야 함
                    current_price = tds[2].text.strip().replace(chr(10),'').replace(chr(13),'')
                    price_diff = tds[3].text.strip().replace(chr(10),'').replace(chr(13),'').replace('\t','').replace('상승','+').replace('하락','-').replace('보합','')
                    change_ratio = tds[4].text.strip().replace(chr(10),'').replace(chr(13),'')
                    volume = tds[9].text.strip().replace(chr(10),'').replace(chr(13),'')
                    per = tds[10].text.strip().replace(chr(10),'').replace(chr(13),'')
                    
                    stocks_data.append({
                        '종목코드': code,
                        '종목명': name,
                        '구분': gubunNm,
                        '현재가': current_price,
                        '전일비': price_diff,
                        '등락률': change_ratio,
                        '거래량': volume,
                        'PER': per
                    })
            except Exception as e:
                # 특정 종목 처리 중 에러가 나더라도 전체 중단하지 않고 로그만 출력 후 계속 진행
                print(f"데이터 추출 중 오류 발생 - 종목: {name if 'name' in locals() else 'Unknown'}, 오류: {str(e)}")
                continue

        if not stocks_data:
            # 페이지가 비어있거나 마지막 페이지를 넘긴 경우일 수 있음
            # raise ValueError("수집된 데이터가 없습니다.") # 에러로 처리하기보다 빈 리스트 반환이 나을 수 있음
            return []

        return stocks_data

    except requests.RequestException as e:
        print(f"네트워크 요청 중 오류 발생: {str(e)}")
        return None
    except Exception as e:
        print(f"데이터 처리 중 오류 발생: {str(e)}")
        return None

def stockDtl():
    """메인 실행 함수"""
    print("="*50)
    print("네이버 금융 시가총액 정보 수집을 시작합니다.")
    print("="*50)
    
    # 1. 날짜 및 경로 설정 (common 모듈 사용)
    today = get_today_str()
    folder_path = get_daily_folder_path()

    all_stocks_data  = []
    
    # 2. 크롤링 대상 설정
    # idx1: 시장 구분 (0=코스피, 1=코스닥)
    # idx2: 페이지 번호 (1 ~ 50페이지 등, 충분히 많이 설정)
    for idx1 in range(0, 2):
        market_name = "코스피" if idx1 == 0 else "코스닥"
        print(f"\n[{market_name}] 데이터 수집 시작...")
        
        # for idx2 in range(1, 50): # 실제 운영 시에는 페이지 수를 넉넉히
        for idx2 in range(1, 50): # 테스트용으로 1페이지만
            url = f'https://finance.naver.com/sise/sise_market_sum.naver?sosok={idx1}&page={idx2}'
            # print(f' - {idx2} 페이지 요청 중...')
            
            stocks_data = get_market_cap_info(idx1, url)
            
            # 수집된 데이터가 없으면(마지막 페이지 도달) 해당 시장 수집 종료
            if not stocks_data:
                print(f" - {idx2} 페이지에서 데이터가 없어 다음 시장으로 넘어갑니다.")
                break

            all_stocks_data.extend(stocks_data)
            time.sleep(0.5) # 서버 부하 방지

    # 3. 결과 저장
    output_filename = f'stock_dtl_list_{today}.csv'
    save_path = os.path.join(folder_path, output_filename)

    # 동일 파일 삭제
    file_manager.check_and_delete_file(save_path)
    
    # DataFrame 생성 및 CSV 저장
    df = pd.DataFrame(all_stocks_data)
    df.to_csv(save_path, index=False, encoding='utf-8-sig')
    
    print(f"\n성공: 종목 상세 정보가 '{output_filename}' 파일로 저장되었습니다. (총 {len(df)}개 종목)")

if __name__ == "__main__":
    stockDtl()

    