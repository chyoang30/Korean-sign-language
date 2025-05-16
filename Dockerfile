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
COPY . .  # 여기에 model_best.pth.tar도 포함되므로 아래 COPY 생략 가능

# 4. Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 5. 환경변수 및 포트 설정
ENV PORT=8080
EXPOSE 8080

# 6. Flask 앱 실행
CMD ["python", "app.py"]