from io import BytesIO
import requests
import json
import pandas as pd
# import datetime
import time
import os
# from file_manager import FileManager
from common import file_manager, get_daily_folder_path, get_today_str, get_last_trading_day_str,get_trading_day_folder_path, KRX_DATA_DOWNLOAD_URL, KRX_OTP_GENERATE_URL, DEFAULT_HEADERS

# 미리셋팅
# pip install requests pandas

# file_manager = FileManager()

def get_krx_stock_list():
    """
    KRX(한국거래소) 주식시장의 전종목 시세를 가져오는 함수입니다.
    
    KRX 정보데이터 시스템은 데이터를 받기 위해 두 단계의 과정이 필요합니다:
    1. 원하는 데이터의 설정값(파라미터)을 보내서 'OTP(일회용 비밀번호)' 같은 코드를 발급받습니다.
    2. 발급받은 코드를 이용해 실제 데이터(CSV) 다운로드를 요청합니다.
    
    이 방식은 크롤링을 방지하거나 보안을 위해 흔히 사용되는 방식입니다.
    """
    print("*" * 80)
    print("KRX 주식시장의 전종목 시세를 가져오는 함수")
    print("*" * 80)
    
    # 1. 세션 객체 생성
    session = requests.Session()

    # 2. 로그인 수행 (로그인 페이지 URL과 데이터 필요)
    login_url = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001.cmd" # 실제 로그인 처리 URL 확인 필요
    login_data = {
        'loginId': 'lostjack',
        'password': 'krxdlatl001!@'
    }
    session.post(login_url, data=login_data)

    # 오늘 날짜 생성 (YYYYMMDD 형식)
    # get_today_str() 함수를 통해 오늘 날짜를 문자열로 가져옵니다.
    today = get_today_str()

    # 거래일자 설정
    # 주말에는 장이 열리지 않으므로, 가장 최근 평일(거래일)을 계산해서 가져옵니다.
    tradingday = get_last_trading_day_str()

    # 데이터 저장 폴더 경로 가져오기 (없으면 생성)
    folder_path = get_trading_day_folder_path()
    
    # --- 1단계: OTP(One-Time Password) 코드 발급 요청 ---
    # KRX 시스템에 "이 조건으로 데이터를 받고 싶어요"라고 요청하여 코드를 받습니다.
    
    gen_otp_url = KRX_OTP_GENERATE_URL
    headers = DEFAULT_HEADERS
    
    # 요청 보낼 데이터 파라미터 설정
    # 이 값들은 브라우저 개발자 도구(F12) > Network 탭에서 실제 요청을 분석하여 알아낸 값들입니다.
    query_str_params = {
        "locale": "ko_KR",      # 언어 설정
        "mktId": "ALL",         # 시장 구분 (ALL: 전체, STK: 코스피, KSQ: 코스닥 등)
        "trdDd": tradingday,    # 조회할 날짜 (YYYYMMDD)
        "share": "1",           # 주식 수
        "money": "1",           # 금액
        "csvxls_isNo": "false", # CSV/Excel 여부
        "name": "fileDown",     # 요청 이름
        "url": "dbms/MDC/STAT/standard/MDCSTAT01501" # 요청할 데이터의 내부 경로 ID
    }

    try:
        # requests 라이브러리를 사용해 GET 요청을 보냅니다.
        res = requests.get(gen_otp_url, query_str_params, headers=headers)
        time.sleep(1.0)  # 서버에 과부하를 주지 않기 위해 1초 대기
        res.raise_for_status() # 요청이 실패(404, 500 등)하면 에러를 발생시킵니다.
        
        # 응답으로 받은 텍스트가 바로 OTP 코드입니다.
        down_data = {"code": res.content}
        print("OTP 코드 발급 완료")

        # --- 2단계: 실제 데이터(CSV) 다운로드 요청 ---
        # 위에서 받은 코드를 이용해 파일을 내려받습니다.
        
        down_url = KRX_DATA_DOWNLOAD_URL
        down_headers = headers.copy()
        # POST 요청을 보낼 때는 데이터 타입을 명시해야 할 수 있습니다.
        down_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        # OTP 코드를 담아 POST 요청을 보냅니다.
        # 이제 session은 로그인 쿠키를 기억하고 있습니다.
        down_csv = session.post(down_url, data=down_data, headers=down_headers)
        # down_csv = requests.post(down_url, data=down_data, headers=down_headers)
        down_csv.raise_for_status()
        print("데이터 다운로드 완료")
        time.sleep(1.0)

        # --- 3단계: 다운로드 받은 데이터 처리 및 저장 ---
        
        # 다운 받은 바이너리 데이터(content)를 메모리 상의 파일처럼 다루기 위해 BytesIO를 사용합니다.
        # 인코딩은 'EUC-KR'로 되어 있는 경우가 많으므로 지정해줍니다.
        df = pd.read_csv(BytesIO(down_csv.content), encoding='EUC-KR')
        
        # 저장할 파일 이름 설정
        output_filename = f'krx_stock_list_{tradingday}.csv'
        output_excel_filename = f'krx_stock_list_{tradingday}.xlsx'
        
        # 혹시 같은 이름의 파일이 이미 있다면 삭제하여 충돌 방지
        file_manager.check_and_delete_file(folder_path+'/'+ output_filename)

        # CSV와 Excel 두 가지 형식으로 저장합니다.
        # utf-8-sig 인코딩을 사용하면 엑셀에서 한글이 깨지지 않고 잘 열립니다.
        df.to_csv(folder_path+'/'+ output_filename, index=False, encoding='utf-8-sig')
        df.to_excel(folder_path+'/'+ output_excel_filename, index=False)
        print(f"데이터가 {output_filename}로 저장되었습니다.")
        
        return folder_path+'/'+ output_excel_filename
    
    except requests.exceptions.RequestException as e:
        # 네트워크 요청 관련 에러 처리
        print(f"데이터 요청 중 오류가 발생했습니다: {e}")
        return None
    except Exception as e:
        # 그 외 기타 모든 에러 처리
        print(f"처리 중 오류가 발생했습니다: {e}")
        return None

def get_krx_100():
    """
    저장된 KRX 주식 목록에서 거래대금 상위 100개, 등락률 상위 100개를 뽑아
    교집합(둘 다 속하는 종목)을 추출하여 저장하는 함수입니다.
    """
    # 거래일자 설정
    # 주말에는 장이 열리지 않으므로, 가장 최근 평일(거래일)을 계산해서 가져옵니다.
    tradingday = get_last_trading_day_str()

    # 데이터 저장 폴더 경로 가져오기 (없으면 생성)
    folder_path = get_trading_day_folder_path()
    
    # temp -----start
    df = pd.read_csv(folder_path +'/'+ f'data_1744_20260104.csv', encoding='EUC-KR')
    # 저장할 파일 이름 설정
    output_excel_filename = f'krx_stock_list_{tradingday}.xlsx'
    df.to_excel(folder_path+'/'+ output_excel_filename, index=False)
    print(f"데이터가 {output_excel_filename}로 저장되었습니다.")
    # temp -----end


    # 1. 저장된 엑셀 파일 읽어오기
    krx_file = folder_path +'/'+ f'krx_stock_list_{tradingday}.xlsx'

    print("krx_file ==>", krx_file)
    print("krx_file ==>", krx_file)

    df = pd.read_excel(krx_file)
    print(df.columns)
    
    volumn_col = '거래대금'
    change_col = '등락률'
    
    # 2. 거래대금 상위 100개 추출 (내림차순 정렬)
    top_volume = df.sort_values(by=volumn_col, ascending=False).head(100)
    
    # 3. 등락률 상위 100개 추출 (내림차순 정렬)
    top_change = df.sort_values(by=change_col, ascending=False).head(100)

    # 4. 두 조건 모두 만족하는(교집합) 종목 찾기 (inner join)
    # 종목명이 같은 것끼리 연결합니다.
    top_inter = pd.merge(top_volume, top_change, how='inner', on='종목명')
    
    # 파일 저장
    output_excel_filename = f'krx_top_100_{tradingday}.xlsx'
    file_manager.check_and_delete_file(folder_path+'/'+ output_excel_filename)
    
    # 종목코드가 중복되어 _x 등의 접미사가 붙을 수 있으므로 이름 정리
    top_inter = top_inter.rename(columns={'종목코드_x': '종목코드'})
    col_to_save = ['종목코드', '종목명']
    
    # 필요한 컬럼만 선택하여 저장
    top_inter[col_to_save].to_excel(folder_path+'/'+ output_excel_filename, index=False)


def test_file():
    # 주말에는 장이 열리지 않으므로, 가장 최근 평일(거래일)을 계산해서 가져옵니다.
    tradingday = get_last_trading_day_str()

    # 데이터 저장 폴더 경로 가져오기 (없으면 생성)
    folder_path = get_trading_day_folder_path()
    
    # temp -----start
    df = pd.read_csv(folder_path +'/'+ f'data_1744_20260104.csv', encoding='EUC-KR')
    # 저장할 파일 이름 설정
    output_filename = f'krx_stock_list_{tradingday}.csv'
    output_excel_filename = f'krx_stock_list_{tradingday}.xlsx'
    
    # 혹시 같은 이름의 파일이 이미 있다면 삭제하여 충돌 방지
    file_manager.check_and_delete_file(folder_path+'/'+ output_filename)

    # CSV와 Excel 두 가지 형식으로 저장합니다.
    # utf-8-sig 인코딩을 사용하면 엑셀에서 한글이 깨지지 않고 잘 열립니다.
    df.to_csv(folder_path+'/'+ output_filename, index=False, encoding='utf-8-sig')
    df.to_excel(folder_path+'/'+ output_excel_filename, index=False)
    print(f"데이터가 {output_filename}로 저장되었습니다.")
    # temp -----end


if __name__ == "__main__":
    # 이 파일이 직접 실행될 때만 아래 코드가 돕니다.
    # krxExcel = get_krx_stock_list()
    # get_krx_100()
    test_file()
