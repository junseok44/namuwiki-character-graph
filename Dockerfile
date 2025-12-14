# Python 3.9 슬림 이미지 사용
FROM python:3.9-slim

# 작업 디렉토리를 /app으로 설정
WORKDIR /app

# requirements.txt 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 소스 코드 복사 (app.py, modules 폴더, templates 폴더 등)
COPY . .

# 컨테이너 실행 명령 (Gunicorn 사용)
# app:app은 app.py 파일 내의 Flask 앱 인스턴스 이름(app)을 지칭합니다.
# --timeout 300: 데이터 로드에 시간이 걸릴 수 있으므로 넉넉하게 설정합니다.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 300 app:app