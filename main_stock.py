
from component.krx import getKrxStockList
from component.naverstock import getNaverTheme
from component.naverstock import getNaverThemDtl
from component.naverstock import getStockDtl
from component import getFileSum
from component.stockanalysis import daily_analysis_stocks
from component.naverstock import getStockChart
# from file_manager import FileManager
import datetime, time
import pandas as pd
from common import file_manager, get_daily_folder_path, get_today_str

# file_manager = FileManager()

def krxStockList():
    getKrxStockList.get_krx_stock_list()

def krxStockList100():
    getKrxStockList.get_krx_100()  

def daily_analysis_stock():
    daily_analysis_stocks.analyze_stocks_with_themes()

def naverTheme():
    # 모든 페이지의 데이터 수집
    all_themes_data = []
    for page in range(1, 9):  # 1페이지부터 8페이지까지
        page_data = getNaverTheme.get_theme_data(page)
        all_themes_data.extend(page_data)
        time.sleep(1)  # 서버 부하 방지를 위한 지연

    # print(all_themes_data)
    for item in all_themes_data:
        print(item)

    # 오늘 날짜 생성 (YYYYMMDD 형식)
    # today = datetime.datetime.now().strftime("%Y%m%d")
    today = get_today_str()

    # 폴더 만들기
    # folder_path = file_manager.make_folder(today)
    folder_path = get_daily_folder_path()

    # CSV 파일로 저장
    output_filename = f'naver_themes_list_{today}.csv'
    
    # 동일 파일 삭제
    file_manager.check_and_delete_file(folder_path+'/'+ output_filename)

    # # DataFrame 생성 및 CSV 저장
    df = pd.DataFrame(all_themes_data)
    df.to_csv(folder_path+'/'+ output_filename, index=False, encoding='utf-8-sig')
    print(f"데이터가 {output_filename}로 저장되었습니다.")

def naverThemeDtl():
    getNaverThemDtl.main()

def stockDtl():
    # 오늘 날짜 생성 (YYYYMMDD 형식)
    today = datetime.datetime.now().strftime("%Y%m%d")
    # 폴더 만들기
    folder_path = file_manager.make_folder(today)

    all_stocks_data  = []
    # url = "https://finance.naver.com/sise/sise_market_sum.naver?sosok=0&page=4"
    for idx1 in range(0,2):
        for idx2 in range(1,50):
        # for idx2 in range(1,2):
            url = f'https://finance.naver.com/sise/sise_market_sum.naver?sosok={idx1}&page={idx2}'
            print('url=>', url)

            stocks_data = getStockDtl.get_market_cap_info(idx1, url)
            if stocks_data == None:
                break

            all_stocks_data.extend(stocks_data)
            time.sleep(1)

    # CSV 파일로 저장
    output_filename = f'stock_dtl_list_{today}.csv'

    # 동일 파일 삭제
    file_manager.check_and_delete_file(folder_path+'/'+ output_filename)
    
    # DataFrame 생성 및 CSV 저장
    df = pd.DataFrame(all_stocks_data)
    df.to_csv(folder_path+'/'+ output_filename, index=False, encoding='utf-8-sig')
    print(f"데이터가 {output_filename}로 저장되었습니다.")

def fileSum():
    getFileSum.getFileSum()

def stockChart():
    getStockChart.generate_chart_urls()

if __name__ == '__main__':
    # call function
    # krxStockList()
    # krxStockList100()
    # naverTheme()
    # naverThemeDtl()
    # stockDtl()
    # daily_analysis_stock()  # 전일대비 15%, 거래대금500억이상
    # fileSum()
    stockChart() # stock chart
    
