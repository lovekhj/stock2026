
### stock project

### 가상환경
python3 -m venv venv
source venv/bin/activate
deactivate



# install
# pip3 install datetime time requests beautifulsoup4 pandas openpyxl
# pip3 freeze : 설치된 패키지 확인
# pip3 freeze > requirements.txt : requirements.txt에 설치된 패키지 설치
# pip3 install -r requirements.txt : requirements.txt에 기록된 패키지 설치
# pip3 install konlpy

# 구글드라이브 - 구글스플데시트에 파일 읽어서 넣기
# pip3 install pandas gspread google-auth-oauthlib google-auth-httplib2

## 2. 개별 컴포넌트 실행 방법 (How to Run Components)
프로젝트 루트 디렉토리에서 `-m` 옵션을 사용하여 모듈 형태로 실행합니다.

예시:
```bash
# 네이버 뉴스 크롤링 실행
python3 -m component.navernews.getNaverNewsList

# 주식 분석 (테마 포함)
python3 -m component.stockanalysis.daily_analysis_stocks

# 주식 차트 URL 생성
python3 -m component.naverstock.getStockChart
```
