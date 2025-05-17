# 1. Python 3.9 환경 + 용량 적은 Debian 기반 이미지 사용
FROM python:3.9-slim

# 2. FFmpeg 설치
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# 3. 프로젝트 파일 복사
WORKDIR /app
COPY . /app
COPY model_best.pth.tar .

# 4. Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 5. 포트 설정 (Railway에서 8080 사용)
ENV PORT=8080
EXPOSE 8080

# 6. Flask 앱 실행
CMD ["python", "app.py"]