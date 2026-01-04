import pandas as pd
import os
import datetime
from common import file_manager, get_daily_folder_path, get_today_str, get_last_trading_day_str,get_trading_day_folder_path



# pip install openpyxl



def getFileSum():
    # 거래일자 설정
    # 주말에는 장이 열리지 않으므로, 가장 최근 평일(거래일)을 계산해서 가져옵니다.
    tradingday = get_last_trading_day_str()

    # 데이터 저장 폴더 경로 가져오기 (없으면 생성)
    folder_path = get_trading_day_folder_path()
    # CSV 파일로 저장
    output_filename = f'total_{tradingday}.xlsx'
    
    # 동일 파일 삭제
    file_manager.check_and_delete_file(folder_path+'/'+ output_filename)

    # 파일 경로 설정
    krx_file = folder_path + f'/krx_stock_list_{tradingday}.csv'
    theme_file = folder_path + f'/naver_themes_list_{tradingday}.csv'
    theme_dtl_file = folder_path + f'/naver_themes_dtl_list_{tradingday}.csv'
    stock_dtl_file = folder_path + f'/stock_dtl_list_{tradingday}.csv'
    stock_analysis = folder_path + f'/00_stock_analysis_pivoted_{tradingday}.xlsx'


    # 각 CSV 파일 읽기
    try:
        # KRX 주식 목록 읽기 (필요한 컬럼만 선택)
        krx_df = pd.read_csv(krx_file, usecols=['종목코드', '종목명', '시장구분', '상장주식수', '고가','저가','종가', '등락률'])
        
        # 테마 목록 읽기
        theme_df = pd.read_csv(theme_file)
        
        # 테마 상세 목록 읽기
        theme_dtl_df = pd.read_csv(theme_dtl_file)

        # 종목 상세 목록 읽기
        stock_dtl_df = pd.read_csv(stock_dtl_file)

        # 등락률 15% 이상 & 거래대금 500억 이상
        stock_analysis_df = pd.read_excel(stock_analysis)
        
        # 거래대금 억원 단위로 변환
        stock_analysis_df['거래대금'] = (stock_analysis_df['거래대금'] / 100000000).round(1)
        
        # 정렬: 선정사유(오름차순), 거래대금(내림차순)
        stock_analysis_df = stock_analysis_df.sort_values(by=['선정사유', '거래대금'], ascending=[True, False])
        
        # 테마별 요약 정보 생성 (excel_utils 모듈 사용)
        # create_theme_summary 함수는 '테마' 컬럼을 기준으로 종목 수를 세어 반환합니다.
        from component.excel_utils import create_theme_summary, apply_conditional_formatting, auto_adjust_column_width
        
        theme_summary_df = create_theme_summary(stock_analysis_df)

        # Excel 파일로 저장 (with 구문을 사용하여 파일을 안전하게 열고 닫음)
        with pd.ExcelWriter(folder_path + '/' +output_filename, engine='openpyxl') as writer:
            # 각 데이터프레임을 지정된 시트 이름으로 저장
            stock_analysis_df.to_excel(writer, sheet_name='종목분석', index=False)
            theme_summary_df.to_excel(writer, sheet_name='테마별분석', index=False)
            krx_df.to_excel(writer, sheet_name='주식종목', index=False)
            stock_dtl_df.to_excel(writer, sheet_name='주식종목상세', index=False)
            theme_df.to_excel(writer, sheet_name='테마', index=False)
            theme_dtl_df.to_excel(writer, sheet_name='테마상세', index=False)

            # --- 엑셀 서식 적용 (공통 유틸리티 사용) ---
            
            # 1. 조건부 서식 적용 (색상 강조)
            # 선정사유(A/B)와 테마 빈도수에 따라 셀 색상을 변경합니다.
            apply_conditional_formatting(writer, '종목분석', stock_analysis_df)

            # 2. 컬럼 너비 자동 조정
            # 글자 수에 맞춰 열 너비를 적절하게 늘려줍니다.
            auto_adjust_column_width(writer)
        
        print(f"'{output_filename}' 파일이 성공적으로 생성되었습니다.")

    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e.filename}")
    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")



if __name__ == "__main__":
    getFileSum()
