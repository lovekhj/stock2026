import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import datetime
import shutil
import time
from file_manager import FileManager

# pip install requests beautifulsoup4 pandas

file_manager = FileManager()

def get_theme_detail(themeNm, themeRate, theme_no):
    theme_nm = themeNm
    theme_rate = themeRate

    # print("theme_nm===>", theme_nm)
    # print("theme_rate===>", theme_rate)
    # print("theme_no===>", theme_no)
    
    url = f"https://finance.naver.com/sise/sise_group_detail.naver?type=theme&no={theme_no}"
    response = requests.get(url)
    response.encoding = 'euc-kr'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 종목 테이블 찾기
    stock_table = soup.find('table', {'class': 'type_5'})
    stock_rows = stock_table.find_all('tr')[2:]  # 헤더 제외
    
    stocks_data = []
    
    for row in stock_rows:
        cols = row.find_all('td')
        if len(cols) > 1:  # 빈 행 제외
            # 종목코드와 종목명 추출
            code_link = cols[0].find('a')
            if code_link:
                # for index, col in enumerate(cols):
                #     print(index, col)

                code = code_link['href'].split('code=')[1]
                name = code_link.text.strip()
                price_diff = cols[3].text.strip().replace(chr(10),'').replace('\t','').replace(' ','').replace('상승','+').replace('하락','+')
                change_rate = cols[4].text.strip().replace('%', '')
                volume = cols[7].text.strip().replace(',', '')
                reason = cols[1].find('p', {'class': 'info_txt'}).text.strip()
                
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

def main():
    # theme_no = 62  # 테마 번호
    
    # # 데이터 수집
    # stocks_data = get_theme_detail(theme_no)
    
    # 오늘 날짜 생성 (YYYYMMDD 형식)
    today = datetime.datetime.now().strftime("%Y%m%d")
    # 폴더 만들기
    folder_path = file_manager.make_folder(today)

    theme_df = pd.read_csv(folder_path + f'/naver_themes_list_{today}.csv')

    # print("theme_df ==>", theme_df)
    all_stocks_data = []
    # 테마 URL에서 테마 번호 추출 및 상세 정보 수집
    for idx, row in theme_df.iterrows():
        theme_nm = row['테마명'] if '테마명' in row else None
        theme_rate = row['전일대비'] if '전일대비' in row else None
        theme_url = row['상세url'] if '상세url' in row else None

        if theme_url:
            theme_no = theme_url.split('no=')[1]
            # print("idx ==>", idx)
            # print("theme_nm ==>", theme_nm)
            # print("theme_rate ==>", theme_rate)
            # print("theme_no ==>", theme_no)
            print(f"테마 정보 수집 중 ============================ ({idx + 1}/{len(theme_df)})")
            stocks_data = get_theme_detail(theme_nm, theme_rate, theme_no)
            all_stocks_data.extend(stocks_data)
            time.sleep(1)  # 서버 부하 방지
    
    # CSV 파일로 저장
    output_filename = f'naver_themes_dtl_list_{today}.csv'

    # 동일 파일 삭제
    file_manager.check_and_delete_file(folder_path+'/'+ output_filename)
    
    # DataFrame 생성 및 CSV 저장
    df = pd.DataFrame(all_stocks_data)
    df.to_csv(folder_path+'/'+ output_filename, index=False, encoding='utf-8-sig')
    print(f"데이터가 {output_filename}로 저장되었습니다.")

if __name__ == "__main__":
    main()