# 1. Python 3.9 환경 + 용량 적은 Debian 기반 이미지 사용
FROM python:3.9-slim

# 2. FFmpeg 설치
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# 3. 프로젝트 파일 복사
WORKDIR /app

# requirements 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Whisper 설치 (requirements에 포함해도 되지만 명시적으로도 가능)
# RUN pip install git+https://github.com/openai/whisper.git

# 앱 코드 복사
COPY . .

# 서버 실행
CMD ["python", "app.py"]