# 1. Python 3.9 환경 + 용량 적은 Debian 기반 이미지 사용
FROM python:3.9-slim

# 2. 시스템 패키지 설치 (FFmpeg + OpenCV용 의존성)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. 프로젝트 디렉토리 설정 및 파일 복사
WORKDIR /app
COPY app.py .
COPY requirements.txt .
COPY lib/ lib/
COPY vocab.txt .

# 모델 파일 다운로드 (Google Drive 링크 사용)
RUN curl -L -o model_best.pth.tar "https://drive.google.com/uc?export=download&id=1I9ZRRzUUpb8i1cW0Q5vtVxebhuBdO8f5"

# 4. Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 5. 환경변수 및 포트 설정
ENV PORT=8080
EXPOSE 8080

# 6. Flask 앱 실행
CMD ["python", "app.py"]