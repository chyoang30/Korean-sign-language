# app.py 테스트 서버 열어보기

from flask import Flask, send_file, request, make_response, jsonify, after_this_request
from urllib.parse import unquote
from moviepy.editor import VideoFileClip, concatenate_videoclips
import uuid
import tempfile
import pandas as pd
import os
import json
import numpy as np
import logging
logging.basicConfig(level=logging.DEBUG)
# import whisper
# import requests
from datetime import datetime
#from konlpy.tag import Okt
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

df = pd.read_csv('NIA_SEN_ALL.csv', encoding='cp949')

word_to_file = dict(zip(df['Kor'], df['Filename']))

VIDEO_FOLDER = 'videos'

@app.route('/ping')     # 테스트
def ping():
    return 'pong'

@app.route('/get_video')    # 영상 조회
def get_video():
    word = request.args.get('word')
    word = unquote(word)

    print(f"[요청 받은 단어] {word}")
    
    if word in word_to_file:
        filename = word_to_file[word] + '.mp4'
        file_path = os.path.join(VIDEO_FOLDER, filename)

        print(f"[찾은 파일명] {filename}")
        print(f"[파일 경로] {file_path}")

        if os.path.exists(file_path):
            print("[파일 있음! 전송 시작]")
            return send_file(file_path, mimetype='video/mp4')
        else:
            print("[파일 없음 404]")
            response_data = {'error': '파일이 없습니다.'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response, 404
    else:
        print("[단어 없음 404]")
        response_data = {'error': '단어가 없습니다.'}
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 404
    
@app.route('/get_video_sequence', methods=['POST'])
def get_video_sequence():
    data = request.get_json()
    words = data.get("words", [])
    
    if not words or not isinstance(words, list):
        return jsonify({"error": "단어 리스트가 필요합니다."}), 400

    video_urls = []

    for word in words:
        word = unquote(word)
        if word in word_to_file:
            filename = word_to_file[word] + '.mp4'
            file_path = os.path.join(VIDEO_FOLDER, filename)
            if os.path.exists(file_path):
                # 정적 URL을 리턴 (프론트가 이 URL로 각 영상 요청 가능)
                video_urls.append(f"/get_video?word={word}")

    if not video_urls:
        return jsonify({"error": "일치하는 영상이 없습니다."}), 404

    return jsonify({"videos": video_urls})

@app.route('/combine_videos', methods=['POST'])
def combine_videos():
    try:
        data = request.get_json()
        words = data.get("words", [])

        if not words or not isinstance(words, list):
            return {"error": "단어 리스트가 필요합니다."}, 400

        video_paths = []
        for word in words:
            filename = word_to_file.get(word)
            if not filename:
                print(f"[단어 없음] {word}")
                continue
            path = os.path.join(VIDEO_FOLDER, filename + ".mp4")
            if os.path.exists(path):
                video_paths.append(path)
            else:
                print(f"[파일 없음] {path}")

        if not video_paths:
            return {"error": "영상이 없습니다."}, 404

        print(f"[병합할 파일들] {video_paths}")

        clips = [VideoFileClip(p) for p in video_paths]
        final = concatenate_videoclips(clips)
        output_path = f"/tmp/merged_{uuid.uuid4().hex[:8]}.mp4"
        final.write_videofile(output_path, codec="libx264", audio_codec="aac")

        @after_this_request
        def remove_file(response):
            try:
                os.remove(output_path)
            except Exception as e:
                print(f"[파일 삭제 실패] {e}")
            return response

        return send_file(output_path, mimetype="video/mp4")

    except Exception as e:
        print(f"[서버 에러] {str(e)}")
        return {"error": str(e)}, 500


@app.route('/to_speech', methods=['POST'])  # 자연어처리 GLOSS >> 구어
def to_speech():
    data = request.get_json()
    words = data.get('words')  # ['화장실', '어디']

    joined = " ".join(words)
    
    if not words or not isinstance(words, list):
        return {'error': 'words는 리스트여야 합니다.'}, 400

    # 요청
    prompt = f"다음은 청각장애인이 역무원에게 수어로 표현한 단어(GLOSS) 리스트야 {words}\n이 단어들을 바탕으로, 역무원에게 전달할 수 있는 자연스러운 한국어 문장으로 바꿔줘."
    
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
        
        # 테스트용 출력 저장
        with open("output_log.jsonl", "a", encoding="utf-8") as f:
            log_entry = {
                "input_words": words,
                "generated_sentence": sentence,
                "timestamp": datetime.now().isoformat()
            }
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            
        return jsonify({"sentence": sentence})

    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/log', methods=['GET']) # 자연어처리 로그
def get_log():
    log_path = "output_log.jsonl"

    if not os.path.exists(log_path):
        return jsonify({"message": "로그 파일이 없습니다."}), 404

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            logs = [json.loads(line) for line in f.readlines()]
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 음성 인식 기능
# 서버 기준 실행 경로
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# AUDIO_DIR = os.path.join(BASE_DIR, "temp_audio")
# os.makedirs(AUDIO_DIR, exist_ok=True)
# model = whisper.load_model("base")

# @app.route('/to_text', methods=['POST'])
# def speech_to_text():
#     if 'audio' not in request.files:    # audio 파일이 없을 때
#         return {'error': 'Audio file must be exist.'}, 400

#     audio_file = request.files['audio']
#     filename = audio_file.filename or "temp.wav"
#     save_path = os.path.join(AUDIO_DIR, filename)
#     audio_file.save(save_path)

#     try:   # 음성 인식
#         result = model.transcribe(save_path)
#         text = result["text"].strip()

#         # GLOSS 자동 요청
#         gloss = []
#         try:
#             res = requests.post("http://localhost:5000/to_gloss", json={"text": text})
#             if res.status_code == 200:
#                 gloss = res.json().get("gloss", [])
#         except:
#             gloss = ["GLOSS 변환 실패"]

#         # 로그 기록
#         with open("speech_log.jsonl", "a", encoding="utf-8") as f:
#             log = {
#                 "input_file": filename,
#                 "output_text": text,
#                 "gloss:": gloss,
#                 "timestamp": datetime.now().isoformat()
#             }
#             f.write(json.dumps(log, ensure_ascii=False) + "\n")

#         return jsonify({"text": text})
    
#     except Exception as e:  # 음성 인식 실패(예외 처리)  
#         return {'error': str(e)}, 500


# okt = Okt()

# @app.route('/to_gloss', methods=['POST'])
# def to_gloss():
#     try:
#         data = request.get_json()
#         text = data.get("text", "")

#         if not text:
#             return jsonify({"error": "텍스트가 제공되지 않았습니다."}), 400

#         # 형태소 분석 후 명사/동사/형용사만 추출
#         tokens = okt.pos(text, stem=True)
#         gloss = [word for word, tag in tokens if tag in ['Noun', 'Verb', 'Adjective']]

#         return jsonify({"gloss": gloss})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # 기본값 5000, 환경변수 우선
    app.run(debug=False, host='0.0.0.0', port=port)
