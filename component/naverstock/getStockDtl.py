import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import datetime
import time
from file_manager import FileManager

file_manager = FileManager()

def get_market_cap_info(gubun, url):
    # url = "https://finance.naver.com/sise/sise_market_sum.naver"
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
        rows = soup.select('table.type_2 tbody tr')
        
        for row in rows:
            tds = row.select('td')
            if len(tds) <= 1:  # N/A 행 건너뛰기
                continue
                
            try:
                # a 태그가 있는지 확인
                name_link = tds[1].select_one('a')
                if name_link:
                    code = name_link['href'].split('code=')[1]
                    name = name_link.text.strip()
                    
                    # 각 컬럼의 데이터 추출
                    current_price = tds[2].text.strip().replace(chr(10),'').replace(chr(13),'')
                    price_diff = tds[3].text.strip().replace(chr(10),'').replace(chr(13),'').replace('\t','').replace('상승','+').replace('하락','-').replace('보합','')
                    change_ratio = tds[4].text.strip().replace(chr(10),'').replace(chr(13),'')
                    volume = tds[9].text.strip().replace(chr(10),'').replace(chr(13),'')
                    per = tds[10].text.strip().replace(chr(10),'').replace(chr(13),'')
                    # 데이터 검증을 위한 출력
                    # print(f"종목: {name}, 현재가: {current_price}, 전일비: {price_diff}, 등락률: {change_ratio}, 거래량: {volume}, PER: {per}")
                    
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
                print(f"데이터 추출 중 오류 발생 - 종목: {name if 'name' in locals() else 'Unknown'}, 오류: {str(e)}")
                continue

        if not stocks_data:
            raise ValueError("수집된 데이터가 없습니다.")

        return stocks_data

    except requests.RequestException as e:
        print(f"네트워크 요청 중 오류 발생: {str(e)}")
        return None
    except Exception as e:
        print(f"데이터 처리 중 오류 발생: {str(e)}")
        return None

if __name__ == "__main__":

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

            stocks_data = get_market_cap_info(idx1, url)
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

    