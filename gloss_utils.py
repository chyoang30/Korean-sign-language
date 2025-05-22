# # gloss_utils.py

# import json
# import os
# import uuid
# import ffmpeg
# from flask import send_file
# from dotenv import load_dotenv
# from openai import OpenAI

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# def convert_sentence_to_gloss(sentence, openai_client):
#     prompt = f"""
#     문장을 의미 중심의 GLOSS 리스트로 바꿔줘. 
#     조사, 어미, 인칭, 부가 설명은 전부 제거하고 핵심 단어만 남겨.
#     예시처럼 단어만 리스트로 출력해. 예: "배가 아파요" → ["배", "아프다"]

#     문장: "{sentence}"
#     """

#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             temperature=0.0,
#             messages=[
#                 {"role": "system", "content": "주어진 문장을 바탕으로 핵심 단어만 남긴 GLOSS 리스트를 출력하세요. 조사, 어미 등은 제거하고, 문법보다 의미 중심으로 구성하세요. 결과는 리스트 형식으로 출력하세요."},
#                 {"role": "user", "content": prompt}
#             ]
#         )

#         gloss = json.loads(response.choices[0].message.content.strip())
#         return gloss

#     except Exception as e:
#         raise RuntimeError(f"OpenAI API 호출 실패(변환 실패): {e}")
    

# def generate_video_from_gloss(gloss_list, word_to_file_map, video_dir):
#     input_path = []

#     for word in gloss_list:
#         filename = word_to_file_map.get(word)
#         if filename:
#             path = os.path.join(video_dir, filename + "mp4")
#             if os.path.exists(path):
#                 input_path.append(path)

#     if not input_path:
#         raise FileNotFoundError("GLOSS 리스트에 해당하는 비디오 파일이 없습니다.")
        
#     # 병합용 텍스트 파일 생성
#     list_path = f"/tmp/{uuid.uuid4()}.txt"
#     with open(list_path, 'w') as f:
#         for path in input_path:
#             abs_path = os.path.abspath(path)
#             f.write(f"file '{path}'\n")
#     output_path = f"/tmp/merged_{uuid.uuid4().hex[:8]}.mp4"
#     try:
#         (
#             ffmpeg
#             .input(list_path, format='concat', safe=0)
#             .output(output_path, c='copy')
#             .run(overwrite_output=True)
#         )
#     except ffmpeg.Error as e:
#         err_msg = e.stderr.decode() if e.stderr else "FFmpeg unknown error"
#         raise RuntimeError(f"영상 병합 실패: {err_msg}")
#     finally:
#         os.remove(list_path)

#     return output_path