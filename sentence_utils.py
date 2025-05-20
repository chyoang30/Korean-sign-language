# sentence_utils.py

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_gloss_from_video(file):     # /upload 역할을 수행하는 함수
    files = {'file': (file.filename, file.stream, file.mimetype)}
    try:
        resp = requests.post("https://d354-218-150-183-121.ngrok-free.app/upload", files=files)
        return resp.json()
    except Exception as e:
        return {"error": f"로컬 추론 서버 호출 실패: {e}"}

def gloss_to_sentence(gloss_list):      # /to_speech 역할을 수행하는 함수
    if not gloss_list or not isinstance(gloss_list, list):
        return {"error": "유효한 gloss 리스트가 필요합니다."}

    prompt = f"다음은 청각장애인이 역무원에게 수어로 표현한 단어(GLOSS) 리스트야 {gloss_list}\n이 단어들을 바탕으로, 역무원에게 전달할 수 있는 자연스러운 한국어 문장으로 바꿔줘."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.0,
            messages=[
                {"role": "system", "content": "입력된 단어들을 바탕으로 가장 자연스러운 존댓말 한국어 문장을 하나 생성하세요. 오직 문장만 출력하세요. 인사말이나 설명은 하지 마세요. 예: ['배', '아프다'] → 배가 아파요"},
                {"role": "user", "content": prompt}
            ]
        )

        sentence = response.choices[0].message.content.strip().strip('"')

        return {"sentence": sentence}
    
    except Exception as e:
        return {"error": str(e)}
