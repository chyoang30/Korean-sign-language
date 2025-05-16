# app.py 테스트 서버 열어보기

from flask import Flask, send_file, request, make_response, jsonify, after_this_request
from urllib.parse import unquote
import ffmpeg
import uuid
import pandas as pd
import cv2
import shutil
import torch
import os
import json
import numpy as np
import logging
import requests
logging.basicConfig(level=logging.DEBUG)
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
from lib.model.sign_model import SignModel
from lib.dataset.vocabulary import GlossVocabulary
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

df = pd.read_csv('NIA_SEN_ALL.csv', encoding='cp949')

word_to_file = dict(zip(df['Kor'], df['Filename']))

VIDEO_FOLDER = 'videos'

@app.route('/get_video')    # 영상 조회
def get_video():
    word = request.args.get('word')
    word = unquote(word)

    print(f"[요청 받은 단어] {word}")
    
    if word in word_to_file:

        filename = word_to_file[word] + '.mp4'
        file_path = os.path.join(VIDEO_FOLDER, filename)

        if os.path.exists(file_path):
            return send_file(file_path, mimetype='video/mp4')
        
        else:
            response_data = {'error': '파일이 없습니다.'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response, 404
    else:
        response_data = {'error': '단어가 없습니다.'}
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 404

@app.route('/combine_videos', methods=['POST'])
def combine_videos():
    data = request.get_json()
    words = data.get("words", [])

    if not words or not isinstance(words, list):
        return jsonify({"error": "단어 리스트가 필요합니다."}), 400

    input_paths = []
    for word in words:
        filename = word_to_file.get(word)
        if filename:
            path = os.path.join(VIDEO_FOLDER, filename + ".mp4")
            if os.path.exists(path):
                input_paths.append(path)


    if not input_paths:
        return jsonify({"error": "일치하는 영상이 없습니다."}), 404

    # 병합용 리스트 파일 생성
    list_path = f"/tmp/video_list_{uuid.uuid4().hex[:8]}.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for path in input_paths:
            abs_path = os.path.abspath(path)
            f.write(f"file '{abs_path}'\n")

    output_path = f"/tmp/merged_{uuid.uuid4().hex[:8]}.mp4"

    try:
        (
            ffmpeg
            .input(list_path, format='concat', safe=0)
            .output(output_path, c='copy')
            .run(overwrite_output=True)
        )
    except ffmpeg.Error as e:
        err_msg = e.stderr.decode() if e.stderr else "FFmpeg unknown error"
        print(f"[FFmpeg 오류] {err_msg}")
        return jsonify({"error": "영상 병합 실패", "detail": err_msg}), 500

    @after_this_request
    def cleanup(response):
        try:
            os.remove(output_path)
            os.remove(list_path)
        except:
            pass
        return response

    return send_file(output_path, mimetype='video/mp4')


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

@app.route('/to_gloss', methods=['POST'])  # 구어 >> GLOSS
def to_gloss():
    data = request.get_json()
    sentence = data.get('sentence')  # 예: "화장실이 어디예요?"

    if not sentence or not isinstance(sentence, str):
        return {'error': 'sentence는 문자열이어야 합니다.'}, 400

    prompt = f"""
    문장을 의미 중심의 GLOSS 리스트로 바꿔줘. 
    조사, 어미, 인칭, 부가 설명은 전부 제거하고 핵심 단어만 남겨.
    예시처럼 단어만 리스트로 출력해. 예: "배가 아파요" → ["배", "아프다"]

    문장: "{sentence}"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.0,
            messages=[
                {"role": "system", "content": "주어진 문장을 바탕으로 핵심 단어만 남긴 GLOSS 리스트를 출력하세요. 조사, 어미 등은 제거하고, 문법보다 의미 중심으로 구성하세요. 결과는 리스트 형식으로 출력하세요."},
                {"role": "user", "content": prompt}
            ]
        )

        gloss_list_str = response.choices[0].message.content.strip()
        # 문자열을 파이썬 리스트로 안전하게 변환
        gloss_list = json.loads(gloss_list_str)

        return jsonify({"gloss": gloss_list})

    except Exception as e:
        return {'error': str(e)}, 500


AUDIO_DIR = "./uploads"
os.makedirs(AUDIO_DIR, exist_ok=True)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
checkpoint = torch.load("model_best.pth.tar", map_location=DEVICE, weights_only=False)
# vocab_list = checkpoint.get("vocab", None)
with open("vocab.txt", encoding="utf-8") as f:
    vocab_list = [line.strip() for line in f if line.strip()]
vocab = GlossVocabulary(tokens=vocab_list)
model = SignModel(vocab)
model.load_state_dict(checkpoint["state_dict"])
model.to(DEVICE).eval()

# 전처리 함수
def preprocess(frames):
    frames = frames / 255.0
    frames = frames.astype(np.float32)
    frames = np.transpose(frames, (0, 3, 1, 2))  # (T, C, H, W)
    frames = np.expand_dims(frames, axis=0)      # (1, T, C, H, W)
    return torch.tensor(frames).to(DEVICE)

# 프레임 추출 함수
def extract_frames(video_path, fps=30):
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_count = 0
    interval = int(cap.get(cv2.CAP_PROP_FPS) / fps) or 1

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % interval == 0:
            resized = cv2.resize(frame, (224, 224))
            frames.append(resized)
        frame_count += 1

    cap.release()
    return np.array(frames)

# 프레임 이미지 추출 함수
def extract_video_to_images(video_path, output_dir, fps=30):
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(round(original_fps / fps)) if original_fps > fps else 1

    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            filename = os.path.join(output_dir, f"{saved_count:04d}.jpg")
            cv2.imwrite(filename, frame)
            saved_count += 1
        frame_count += 1

    cap.release()
    print(f"Saved {saved_count} frames to {output_dir}")

# 이미지 → 텐서 변환 함수
def load_images_as_tensor(image_dir):
    image_files = sorted([f for f in os.listdir(image_dir) if f.endswith(".jpg")])
    frames = []

    for filename in image_files:
        img_path = os.path.join(image_dir, filename)
        img = Image.open(img_path).convert("RGB")
        img = img.resize((224, 224))
        frame = np.array(img)
        frames.append(frame)

    return preprocess(np.array(frames))

# 추론 함수
def run_inference(model, vocab, video_tensor):
    with torch.no_grad():
        output = model(video_tensor)  # (B, T//4, V)
        print("[DEBUG] output.shape:", output.shape)
        pred = output.argmax(dim=-1).cpu().numpy()[0]  # (T//4,)
        print("[DEBUG] pred indices:", pred)
        glosses = vocab.arrays_to_sentences([pred])[0]
        print("[DEBUG] glosses:", glosses)
        return glosses

@app.route("/upload", methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 필요합니다."}), 400

    file = request.files['file']
    filename = file.filename or "temp.mp4"
    save_path = os.path.join(AUDIO_DIR, filename)
    file.save(save_path)

    try:
        # 1. mp4 → 이미지 프레임 저장
        tmp_dir = os.path.join("temp_frames", uuid.uuid4().hex[:8])
        extract_video_to_images(save_path, tmp_dir)

        # 2. 이미지 폴더 → 텐서 변환
        input_tensor = load_images_as_tensor(tmp_dir)

        # 3. 추론
        glosses = run_inference(model, vocab, input_tensor)

        # 4. 임시 프레임 폴더 정리 (after_this_request)
        @after_this_request
        def cleanup(response):
            try:
                shutil.rmtree(tmp_dir)
                os.remove(save_path)
            except Exception as e:
                print(f"Cleanup error: {e}")
            return response

        return jsonify({
            "message": "file uploaded successfully",
            "filename": filename,
            "glosses": glosses
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":    # 로컬 테스트용
    app.run(debug=True)

# if __name__ == '__main__':  # 배포용
#     port = int(os.environ.get('PORT', 5000))  # 기본값 5000, 환경변수 우선
#     app.run(debug=False, host='0.0.0.0', port=port)
