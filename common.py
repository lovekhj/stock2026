
import datetime
from file_manager import FileManager

# 파일 관리자 객체를 한 번만 초기화
file_manager = FileManager()

def get_today_str():
    """오늘 날짜를 'YYYYMMDD' 형식의 문자열로 반환합니다."""
    return datetime.datetime.now().strftime("%Y%m%d")

def get_daily_folder_path():
    """오늘 날짜로 된 데이터 폴더의 경로를 반환하고, 필요하면 생성합니다."""
    today = get_today_str()
    return file_manager.make_folder(today)

def get_last_trading_day_str():
    """
    가장 최근의 평일(월-금)을 찾아 'YYYYMMDD' 형식의 문자열로 반환합니다.
    (공휴일은 고려하지 않음)
    """
    today = datetime.date.today()
    
    # 오늘이 토요일(5)이면 1일을 빼서 금요일로
    if today.weekday() == 5:
        last_trading_day = today - datetime.timedelta(days=1)
    # 오늘이 일요일(6)이면 2일을 빼서 금요일로
    elif today.weekday() == 6:
        last_trading_day = today - datetime.timedelta(days=2)
    # 평일이면 오늘 날짜 그대로 사용
    else:
        last_trading_day = today
        
    return last_trading_day.strftime("%Y%m%d")


# --- KRX 관련 상수들 (getKrxStockList.py에서 가져옴) ---
KRX_OTP_GENERATE_URL = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
KRX_DATA_DOWNLOAD_URL = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'

DEFAULT_HEADERS = {
    "user-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Refer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101",
    "Connection": "keep-alive"
}
