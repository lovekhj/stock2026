import pandas as pd
import os
import sys
import time

# 프로젝트 루트 디렉토리를 Python 경로에 추가하여 'common' 모듈을 임포트할 수 있도록 함
# (만약 모듈로 실행 시 불필요하지만, 단독 실행 편의성을 위해 남겨두거나, user 요청대로 삭제했다면 common import만 유지)
# User requested removing sys.path hacks, so I will assume running as module.
# However, for safety in this new file, I will rely on standard imports.

from common import file_manager, get_daily_folder_path, get_today_str
from component.excel_utils import auto_adjust_column_width

# -----------------------------------------------------------------------------------------
# [교육용 주석: 주식 차트 이미지 URL 생성기]
# 이 스크립트는 'total_YYYYMMDD.xlsx' 파일에 있는 종목 리스트를 읽어서,
# 네이버 금융의 차트 이미지(3개월, 1년, 3년)에 바로 접근할 수 있는 URL을 생성합니다.
# 
# 이렇게 생성된 엑셀 파일에서 링크를 클릭하면 바로 차트를 볼 수 있어 분석 시간을 단축해줍니다.
# -----------------------------------------------------------------------------------------

def generate_chart_urls():
    """
    메인 실행 함수: 종목 리스트를 읽어 차트 URL을 포함한 엑셀 파일 생성
    """
    print("="*50)
    print("네이버 주식 차트 URL 생성을 시작합니다.")
    print("="*50)

    # 1. 날짜 및 경로 설정
    today = get_today_str()
    folder_path = get_daily_folder_path()
    
    # 2. 입력 파일 확인 (total_YYYYMMDD.xlsx)
    input_filename = f'total_{today}.xlsx'
    input_filepath = os.path.join(folder_path, input_filename)
    
    if not os.path.exists(input_filepath):
        print(f"오류: 입력 파일을 찾을 수 없습니다. ({input_filepath})")
        print("getFileSum.py가 먼저 실행되었는지 확인해주세요.")
        return

    # 3. 엑셀 파일 읽기 (종목분석 시트)
    print(f"입력 파일 로딩 중: {input_filename}")
    try:
        df = pd.read_excel(input_filepath, sheet_name='종목분석')
    except ValueError:
        print("오류: '종목분석' 시트를 찾을 수 없습니다.")
        return

    # 4. 차트 URL 생성
    chart_data = []
    
    # URL 생성을 위한 타임스탬프 (캐시 방지용, 현재 시간 사용)
    sidcode = int(time.time() * 1000)
    
    for idx, row in df.iterrows():
        code = str(row['종목코드']).zfill(6) # 6자리 문자로 변환
        name = row['종목명']
        
        # 3개월 차트
        url_3m = f"https://ssl.pstatic.net/imgfinance/chart/item/area/month3/{code}.png?sidcode={sidcode}"
        # 1년 차트
        url_1y = f"https://ssl.pstatic.net/imgfinance/chart/item/area/year/{code}.png?sidcode={sidcode}"
        # 3년 차트
        url_3y = f"https://ssl.pstatic.net/imgfinance/chart/item/area/year3/{code}.png?sidcode={sidcode}"
        
        chart_data.append({
            '번호': idx + 1,
            '종목코드': code,
            '종목명': name,
            '3개월': url_3m,
            '1년': url_1y,
            '3년': url_3y
        })
        
    # 5. 결과 저장
    output_df = pd.DataFrame(chart_data)
    output_filename = f'naver_stock_chart_{today}.xlsx'
    output_filepath = os.path.join(folder_path, output_filename)
    
    # 기존 파일 삭제
    file_manager.check_and_delete_file(output_filepath)
    
    try:
        with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
            # 시트명: 종목차트
            output_df.to_excel(writer, sheet_name='종목차트', index=False)
            
            # [서식 적용]
            # 1. 자동 컬럼 너비 조정
            auto_adjust_column_width(writer)
            
            # 2. URL 컬럼 너비 조정 (사용자 요청: 작게)
            # '3개월', '1년', '3년' 컬럼의 너비를 15로 고정
            ws = writer.sheets['종목차트']
            
            # 헤더 인덱스 매핑
            col_indices = {cell.value: cell.column_letter for cell in ws[1]}
            
            target_cols = ['3개월', '1년', '3년']
            for col_name in target_cols:
                if col_name in col_indices:
                    ws.column_dimensions[col_indices[col_name]].width = 15
            
            # 번호 컬럼도 작게
            if '번호' in col_indices:
                ws.column_dimensions[col_indices['번호']].width = 10
            
        print(f"\n성공: 차트 URL 파일이 생성되었습니다.")
        print(f"저장 위치: {output_filepath}")
        print(f"총 {len(output_df)}개 종목 처리 완료")
        
    except Exception as e:
        print(f"오류: 파일 저장 중 문제가 발생했습니다: {e}")

if __name__ == "__main__":
    generate_chart_urls()
