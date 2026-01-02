import pandas as pd
import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가하여 'common' 모듈을 임포트할 수 있도록 함
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from common import get_daily_folder_path, get_today_str

def analyze_stocks_with_themes():
    """
    KRX 주식 목록 데이터와 네이버 테마 상세 데이터를 병합하여
    각 종목에 해당하는 테마 정보를 추가하고 결과를 파일로 저장합니다.
    """
    today_str = get_today_str()
    daily_folder_path = get_daily_folder_path()

    # 1. 파일 경로 설정
    krx_stock_filepath = os.path.join(daily_folder_path, f'krx_stock_list_{today_str}.xlsx')
    naver_themes_dtl_filepath = os.path.join(daily_folder_path, f'naver_themes_dtl_list_{today_str}.csv')
    output_filepath = os.path.join(daily_folder_path, f'00_stock_analysis_stocks_{today_str}.xlsx')

    try:
        # 2. 데이터 로드
        print("데이터 로드를 시작합니다...")
        df_krx = pd.read_excel(krx_stock_filepath)
        print(f"- '{os.path.basename(krx_stock_filepath)}' 로드 완료 (총 {len(df_krx)}개 종목)")

        df_themes = pd.read_csv(naver_themes_dtl_filepath)
        print(f"- '{os.path.basename(naver_themes_dtl_filepath)}' 로드 완료 (총 {len(df_themes)}개 테마-종목 연결)")

        # '종목코드' 컬럼 타입 통일 (병합 오류 방지)
        df_krx['종목코드'] = df_krx['종목코드'].astype(str).str.zfill(6)
        df_themes['종목코드'] = df_themes['종목코드'].astype(str).str.zfill(6)
        
        # 3. 데이터 필터링
        # 조건: 1. 등락률 15% 이상  OR  2. (거래대금 500억 이상 AND 변동폭 6% 이상)
        min_fluctuation_rate = 15
        min_trading_amount = 50_000_000_000
        min_range_rate = 6

        # 변동폭(%) 계산: (고가 - 저가) / 저가 * 100
        # 저가가 0인 경우(거래정지 등) 0으로 처리하여 오류 방지
        df_krx['변동폭'] = 0.0
        mask_valid = df_krx['저가'] > 0
        df_krx.loc[mask_valid, '변동폭'] = (df_krx.loc[mask_valid, '고가'] - df_krx.loc[mask_valid, '저가']) / df_krx.loc[mask_valid, '저가'] * 100

        df_krx_filtered = df_krx[
            (df_krx['등락률'] >= min_fluctuation_rate) | 
            (
                (df_krx['거래대금'] >= min_trading_amount) &
                (df_krx['변동폭'] >= min_range_rate)
            )
        ]
        
        print(f"\n필터링 적용: 1. 등락률 {min_fluctuation_rate}% 이상 OR 2. (거래대금 {min_trading_amount/1e8:.0f}억 이상 AND 변동폭 {min_range_rate}% 이상)")
        print(f"필터링 전 {len(df_krx)}개 종목 -> 필터링 후 {len(df_krx_filtered)}개 종목")

        # 4. 데이터 병합 (필터링된 종목만 대상으로)
        merged_df = pd.merge(
            df_krx_filtered, 
            df_themes[['종목코드', '테마', '테마등락률']], 
            on='종목코드', 
            how='left'
        )

        print("\n데이터 병합이 완료되었습니다.")
        print(f"병합 후 총 {len(merged_df)}개 행이 생성되었습니다 (한 종목이 여러 테마에 속한 경우 중복 표시).")

        # 5. 데이터 재구성: 여러 테마를 옆으로 나열하기
        print("\n데이터 재구성을 시작합니다 (테마를 열로 변환)...")
        
        # 종목의 기본 정보는 유지하고, 테마들만 리스트로 묶습니다.
        # 1. 종목별로 고유한 컬럼들을 가져옵니다.
        stock_info_cols = df_krx_filtered.columns.tolist()
        stock_info_df = merged_df[stock_info_cols].drop_duplicates().set_index('종목코드')

        # 2. 종목코드별로 테마를 리스트로 그룹화합니다.
        themes_grouped_series = merged_df.groupby('종목코드')['테마'].apply(lambda x: x.dropna().tolist())
        
        # 3. 테마 리스트를 '테마_1', '테마_2', ... 컬럼으로 분리합니다.
        themes_expanded_df = themes_grouped_series.apply(pd.Series)
        themes_expanded_df = themes_expanded_df.rename(columns=lambda x: f'테마_{x+1}')
        
        # 4. 종목 정보와 확장된 테마 데이터를 '종목코드'를 기준으로 합칩니다.
        final_df = stock_info_df.join(themes_expanded_df).reset_index()

        print("데이터 재구성이 완료되었습니다.")

        # 6. 최종 컬럼 선택 및 순서 재정렬
        base_cols = ['종목코드', '종목명', '시장구분', '종가', '등락률', '거래량', '거래대금']
        theme_cols = sorted([col for col in final_df.columns if col.startswith('테마_')])
        
        # 최종적으로 저장할 컬럼 리스트
        final_output_cols = base_cols + theme_cols
        
        # final_df에 있는 컬럼만으로 최종 리스트를 다시 필터링 (오류 방지)
        final_output_cols = [col for col in final_output_cols if col in final_df.columns]
        
        output_df = final_df[final_output_cols]

        # 7. 재구성 및 정렬된 데이터 저장
        pivoted_output_filepath = os.path.join(daily_folder_path, f'00_stock_analysis_pivoted_{today_str}.xlsx')
        output_df.to_excel(pivoted_output_filepath, index=False)
        print(f"\n성공: 최종 데이터가 다음 파일로 저장되었습니다:\n{pivoted_output_filepath}")

        # 간단한 결과 미리보기
        print("\n--- 최종 데이터 샘플 (상위 5개) ---")
        print(output_df.head())
        
        return output_df

    except FileNotFoundError as e:
        print(f"\n오류: 필수 파일을 찾을 수 없습니다. '{e.filename}'")
        print("먼저 KRX 주식 목록과 네이버 테마 상세 데이터가 생성되었는지 확인해주세요.")
        return None
    except Exception as e:
        print(f"\n오류: 데이터 처리 중 문제가 발생했습니다: {e}")
        return None

if __name__ == "__main__":
    print("="*50)
    print("주식과 테마 데이터 병합 분석을 시작합니다.")
    print("="*50)
    analyze_stocks_with_themes()
    print("\n분석이 종료되었습니다.")