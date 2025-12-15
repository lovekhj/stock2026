from io import BytesIO
import requests
import json
import pandas as pd
# import datetime
import time
import os
# from file_manager import FileManager
from common import file_manager, get_daily_folder_path, get_today_str, get_last_trading_day_str, KRX_DATA_DOWNLOAD_URL, KRX_OTP_GENERATE_URL, DEFAULT_HEADERS

# 미리셋팅
# pip install requests pandas

# file_manager = FileManager()

def get_krx_stock_list():
    """KRX 주식시장의 전종목 시세를 가져오는 함수"""
    print("*" * 80)
    print("KRX 주식시장의 전종목 시세를 가져오는 함수")
    print("*" * 80)
    
    
    # 오늘 날짜 생성 (YYYYMMDD 형식)
    # today = datetime.datetime.now().strftime("%Y%m%d")
    today = get_today_str()

    # 거래일자 
    tradingday = get_last_trading_day_str()

    # 폴더 만들기
    # folder_path = file_manager.make_folder(today)
    folder_path = get_daily_folder_path()
    
    # otp 데이터 가져오기
    # gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
    gen_otp_url = KRX_OTP_GENERATE_URL
    headers = DEFAULT_HEADERS
    query_str_params = {
        "locale": "ko_KR",
        "mktId": "ALL",
        "trdDd": tradingday,
        "share": "1",
        "money": "1",
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT01501"
    }

    try:

        # return df
        res = requests.get(gen_otp_url, query_str_params, headers=headers)
        time.sleep(1.0)  # 1초
        res.raise_for_status()
        down_data = {"code": res.content}
        print("OTP 코드 발급 완료")

        # 데이터 다운로드 요청
        # down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
        down_url = KRX_DATA_DOWNLOAD_URL
        down_headers = headers.copy()
        down_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        down_csv = requests.post(down_url, data=down_data, headers=down_headers)
        down_csv.raise_for_status()
        print("데이터 다운로드 완료")
        time.sleep(1.0)

        # 다운 받은 csv파일을 pandas의 read_csv 함수를 이용하여 읽어 들임.
        # read_csv 함수의 argument에 적합할 수 있도록 BytesIO함수를 이용하여 바이너 스트림 형태로

        # 데이터프레임 생성
        df = pd.read_csv(BytesIO(down_csv.content), encoding='EUC-KR')
        # CSV 파일로 저장
        output_filename = f'krx_stock_list_{today}.csv'
        output_excel_filename = f'krx_stock_list_{today}.xlsx'
        # 동일 파일 삭제
        file_manager.check_and_delete_file(folder_path+'/'+ output_filename)

        df.to_csv(folder_path+'/'+ output_filename, index=False, encoding='utf-8-sig')
        df.to_excel(folder_path+'/'+ output_excel_filename, index=False)
        print(f"데이터가 {output_filename}로 저장되었습니다.")
        
        # 상위100개 파일 만들기
        # krx100_file = folder_path+'/'+ output_excel_filename
        # get_krx_100(krx100_file)
        
        return folder_path+'/'+ output_excel_filename
    
    except requests.exceptions.RequestException as e:
        print(f"데이터 요청 중 오류가 발생했습니다: {e}")
        return None
    except Exception as e:
        print(f"처리 중 오류가 발생했습니다: {e}")
        return None

# def get_krx_100(krxExcel):
def get_krx_100():
    # file_manager = FileManager()

    # 오늘 날짜 생성 (YYYYMMDD 형식)
    # today = datetime.datetime.now().strftime("%Y%m%d")
    today = get_today_str()
    # 폴더 만들기
    # folder_path = file_manager.make_folder(today)
    folder_path = get_daily_folder_path()
    
    # df = pd.read_excel("./20250507/krx_stock_list_20250507.xlsx")
    krx_file = folder_path +'/'+ f'krx_stock_list_{today}.xlsx'
    df = pd.read_excel(krx_file)
    print(df.columns)
    volumn_col = '거래대금'
    change_col = '등락률'
    # 거래량 상위 100
    top_volume = df.sort_values(by=volumn_col, ascending=False).head(100)
    # 등락률
    top_change = df.sort_values(by=change_col, ascending=False).head(100)

    # 두개 만족하는 교집합
    top_inter = pd.merge(top_volume, top_change, how='inner', on='종목명') # 종목명 기준 병합
    # print(top_inter.head(100))
    # print(top_inter[['종목명', volumn_col, change_col]])

    output_excel_filename = f'krx_top_100_{today}.xlsx'
    # 동일 파일 삭제
    file_manager.check_and_delete_file(folder_path+'/'+ output_excel_filename)
    top_inter = top_inter.rename(columns={'종목코드_x': '종목코드'})
    col_to_save = ['종목코드', '종목명']
    top_inter[col_to_save].to_excel(folder_path+'/'+ output_excel_filename, index=False)
if __name__ == "__main__":
    krxExcel = get_krx_stock_list()
    # get_krx_100(krxExcel)
    get_krx_100()
