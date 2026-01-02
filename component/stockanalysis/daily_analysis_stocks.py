import pandas as pd
import os
import sys

from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter
from collections import Counter
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

        # 조건별 마스크 생성
        mask_fluctuation = df_krx['등락률'] >= min_fluctuation_rate
        mask_transaction = (df_krx['거래대금'] >= min_trading_amount) & (df_krx['변동폭'] >= min_range_rate)

        # 선정사유 컬럼 추가
        # 기본적으로 None 또는 빈 문자열
        df_krx['선정사유'] = ''
        
        # 거래대금 조건 만족 시 'B'
        df_krx.loc[mask_transaction, '선정사유'] = 'B'
        
        # 등락률 조건 만족 시 'A' (중복 시 'A'가 우선하거나 덮어씌움 - 사용자 요청: 등락률일때 'A')
        # 만약 둘 다 표시하고 싶다면: df_krx.loc[mask_fluctuation & mask_transaction, '선정사유'] = 'A,B' 등의 로직 가능
        # 여기서는 등락률이 우선시되는 구조로 'A'를 나중에 할당
        df_krx.loc[mask_fluctuation, '선정사유'] = 'A'

        # 필터링 적용 (선정사유가 있는 종목만)
        df_krx_filtered = df_krx[mask_fluctuation | mask_transaction].copy()
        
        print(f"\n필터링 적용: 1. 등락률 {min_fluctuation_rate}% 이상 (A) OR 2. (거래대금 {min_trading_amount/1e8:.0f}억 이상 AND 변동폭 {min_range_rate}% 이상 (B))")
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
        # [교육용 주석: 람다(Lambda) 함수]
        # 람다 함수는 'lambda 입력변수 : 리턴값' 형태로 쓰는 익명(이름 없는) 함수입니다.
        # 여기서는 종목코드별로 묶인(grouped) 데이터(x)를 받아서,
        # NaN(빈 값)을 제거(.dropna())하고 리스트로 변환(.tolist())하는 역할을 합니다.
        themes_grouped_series = merged_df.groupby('종목코드')['테마'].apply(lambda x: x.dropna().tolist())
        
        # 3. 테마 리스트를 '테마_1', '테마_2', ... 컬럼으로 분리합니다.
        themes_expanded_df = themes_grouped_series.apply(pd.Series)
        
        # [교육용 주석: 람다(Lambda) 함수와 f-string]
        # rename 함수 안에서 lambda x는 기존 컬럼 이름(여기서는 숫자 인덱스 0, 1, 2...)을 입력(x)으로 받습니다.
        # f'테마_{x+1}'은 x에 1을 더해 '테마_1', '테마_2'와 같은 문자열을 만들어 리턴합니다.
        themes_expanded_df = themes_expanded_df.rename(columns=lambda x: f'테마_{x+1}')
        
        # 4. 종목 정보와 확장된 테마 데이터를 '종목코드'를 기준으로 합칩니다.
        final_df = stock_info_df.join(themes_expanded_df).reset_index()

        print("데이터 재구성이 완료되었습니다.")

        # 6. 최종 컬럼 선택 및 순서 재정렬
        # 선정사유 컬럼 추가
        base_cols = ['종목코드', '종목명', '선정사유', '시장구분','종가','고가','저가','등락률','거래량','거래대금']
        theme_cols = sorted([col for col in final_df.columns if col.startswith('테마_')])
        
        # 최종적으로 저장할 컬럼 리스트
        final_output_cols = base_cols + theme_cols
        
        # final_df에 있는 컬럼만으로 최종 리스트를 다시 필터링 (오류 방지)
        final_output_cols = [col for col in final_output_cols if col in final_df.columns]
        
        output_df = final_df[final_output_cols]

        # 7. 재구성 및 정렬된 데이터 저장
        pivoted_output_filepath = os.path.join(daily_folder_path, f'00_stock_analysis_pivoted_{today_str}.xlsx')

        # --- 추가 로직 적용 ---
        # 1. 거래대금 억원 단위로 변환
        output_df['거래대금'] = (output_df['거래대금'] / 100000000).round(1)

        # 2. 정렬: 선정사유(오름차순), 거래대금(내림차순)
        output_df = output_df.sort_values(by=['선정사유', '거래대금'], ascending=[True, False])

        # 테마별 요약 정보 생성 (excel_utils 모듈 사용)
        # create_theme_summary 함수는 '테마' 컬럼을 기준으로 종목 수를 세어 반환합니다.
        from component.excel_utils import create_theme_summary, apply_conditional_formatting, auto_adjust_column_width
        
        theme_summary_df = create_theme_summary(output_df)

        # 4. Excel 파일로 저장 및 서식 적용
        # with 구문을 사용하여 파일을 안전하게 열고 작성 후 자동으로 닫습니다.
        with pd.ExcelWriter(pivoted_output_filepath, engine='openpyxl') as writer:
            # 원본 데이터와 테마 요약 데이터를 각각 다른 시트에 저장
            output_df.to_excel(writer, sheet_name='종목분석', index=False)
            theme_summary_df.to_excel(writer, sheet_name='테마별분석', index=False)

            # --- 엑셀 서식 적용 (공통 유틸리티 사용) ---
            
            # 1. 조건부 서식 적용 (색상 강조)
            # 선정사유(A/B)와 테마 빈도수에 따라 셀 색상을 변경하는 함수 호출
            apply_conditional_formatting(writer, '종목분석', output_df)

            # 2. 컬럼 너비 자동 조정
            # 엑셀의 모든 시트에 대해 글자 수에 맞춰 열 너비를 최적화하는 함수 호출
            auto_adjust_column_width(writer)
            
        print(f"\n성공: 최종 데이터가 다음 파일로 저장되었습니다:\n{pivoted_output_filepath}")

        # 간단한 결과 미리보기
        # print("\n--- 최종 데이터 샘플 (상위 5개) ---")
        # print(output_df.head())
        
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