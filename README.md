# 교통 약자 응대를 위한 수어 번역기

## 프로젝트 개요
- **프로젝트명**: 교통 약자 응대를 위한 수어 번역기
- **설명**: 교통 약자 고객 응대를 위해 직군별로 특화된 수어 표현 번역과 학습이 가능한 도구입니다.  
  한국어 단어에 대응하는 수어 영상을 제공하고 gloss된 단어 리스트를 구어체로 자연어 처리하는 REST API 서버를 포함합니다.

---

## API 서버 정보
- **서버 명칭**: 수어 영상 조회 및 자연어처리 변환 API  
- **설명**:  
  - 전송된 단어(`word`)에 대응하는 수어 영상을 반환  
  - gloss 형태의 단어 리스트를 자연스러운 한국어 문장으로 변환하는 자연어처리 기능
- **Base URL**: [https://flask-sign-language-api-production.up.railway.app](https://flask-sign-language-api-production.up.railway.app)

---

## 데이터 출처 및 라이선스
본 프로젝트는 한국지능정보사회진흥원(NIA)에서 제공하는 **한국어-수어 영상 데이터셋**을 기반으로 수어 영상을 제공합니다.

- **출처**: [AI Hub - 한국지능정보사회진흥원(NIA)/수어 영상 데이터셋](https://www.aihub.or.kr/aihubdata/data/view.do?currMenu=115&topMenu=100&dataSetSn=103)
- **데이터셋 이름**: 수어 영상
- **데이터 배포 일자**: 2020년 10월
- **라이선스**:  
  AIHub 데이터는 비상업적 연구 및 개발 목적으로 무료 제공됩니다.  
  해당 데이터는 상업적 사용이 제한되며, 원본 제공처의 이용약관을 반드시 준수해야 합니다.

---

## 주요 기능
- 검색어(`word`)에 해당하는 수어 영상을 조회하고 mp4 파일로 반환합니다.
- 여러 단어(`words`)에 해당하는 수어 영상을 병합하여 하나의 mp4 파일로 반환합니다.
- gloss 형태의 단어 리스트(`words`, 예: `["배", "아프다"]`)를 받아 자연어 문장(예: `"배가 아파요"`)으로 변환합니다.
- 일상 한국어 문장(`sentence`)을 입력받아 핵심 의미만 남긴 GLOSS 단어 리스트로 변환합니다.
- 수어 영상(`.mp4`)을 업로드하면 해당 영상에서 GLOSS 단어 리스트를 추출해 반환합니다.
- 수어 영상(`.mp4`)을 업로드하면 GLOSS를 추출하고 자연어 문장으로 자동 변환하여 함께 반환합니다.

---

## 사용 기술 스택
- **백엔드 서버**: Python Flask
  - 영상 조회 및 자연어처리용 API 제공
- **서버 배포**: Railway
  - GitHub 연동으로 자동 배포
- **데이터 저장소**: 
  - 수어 영상: GitHub Repository 내 `/videos` 폴더
  - gloss → 문장 변환 요청 기록: `output_test.json` (로컬 로그)
- **자연어처리(NLP)**: OpenAI GPT-3.5 Turbo API
  - gloss 단어 리스트를 자연어 문장으로 변환

---

## API 명세서
### 1. 수어 영상 조회 API
#### 요청
- **Method**: GET  
- **Endpoint**: `/get_video`  
- **Query Parameters**:  
  - `word` (string): 검색할 한국어 단어 (예: `위험`, `여기`)

#### 응답
- 성공 (200 OK): 해당 단어의 수어 영상 mp4 파일 반환  
- 실패 (404, 502): 오류 메시지 반환  
  - `404`: 단어에 대한 영상 없음  
  - `404`: 파일이 존재하지 않음
  - `502`: 서버 응답 실패

### 2. 수어 영상 병합 API
#### 요청
- **Method**: POST
- **Endpoint**: `\combine_video`
- **Request Body (JSON)**:
```json
{
  "words": ["여기", "위험"]
}
```
- 아래처럼 curl로 요청할 수 있습니다:
  ```bash
  curl -X POST https://flask-sign-language-api-production.up.railway.app/combine_videos \
      -H "Content-Type: application/json" \
      --data-binary "@test.json" --output combined.mp4
  ```

#### 응답
- **성공 (200 OK)**: 병합된 수어 영상(mp4 파일) 반환
- **실패**
  - `400 Bad Request`: 요청 형식 오류
  - `404 Not Found`: 일부 단어에 해당하는 영상이 존재하지 않음
  - `500 Internal Server Error`: 병합 처리 중 오류 발생 (ffmpeg 등)


### 3. 자연어처리 문장 생성 API
#### 요청
- **Method**: POST  
- **Endpoint**: `/to_speech`  
- **Request Body (JSON)**:  
  ```json
  {
    "words": ["배", "아프다"]
  }
  ```
  - 또는 아래처럼 curl로 요청할 수 있습니다:
  ```bash
  curl -X POST https://flask-sign-language-api-production.up.railway.app/to_speech \
      -H "Content-Type: application/json" \
      -d "@test.json"
  ```

#### 응답
- 성공 (200 OK): 자연어 문장 반환
  ```json
  {
    "input_words": [
      "배",
      "아프다"
    ],
    "generated_sentence": "배가 아파요.",
    "timestamp": "YYYY-MM-DDTHH:MM:SS"
  }
  ```

- 실패 (400, 500): 오류 메시지 반환
  - ``400 Bad Request``: 요청 형식 오류
  - `500 Internal Server Error`: OpenAI 처리 중 오류


### 4. GLOSS 변환 API
#### 요청
- **Method**: POST  
- **Endpoint**: `/to_gloss`  
- **Request Body (JSON)**:  
  ```json
  {
    "sentence": "화장실이 어디예요?"
  }
  ```
  - 아래처럼 curl로 요청할 수 있습니다:
  ```bash
  curl -X POST https://flask-sign-language-api-production.up.railway.app/to_gloss -H "Content-Type: application/json" -d "@test.json"
  ```

  #### 응답
- 성공 (200 OK): gloss 형태의 단어 리스트 반환
  ```json
  {
    "gloss": ["화장실", "어디"]
  }
  ```

- 실패 (400, 500): 오류 메시지 반환
  - `400 Bad Request`: 요청 형식 오류
  - `500 Internal Server Error`: OpenAI 처리 중 오류

### 5. GLOSS 추출 API
#### 설명
- 수어 영상(mp4)을 업로드하면 해당 영상에서 GLOSS 단어 리스트를 추출합니다.
#### 요청
- **Method**: POST  
- **Endpoint**: `/upload`  
- **Form-Data**:
  - file: `.mp4` 형식 수어 영상
  - 아래처럼 curl로 요청할 수 있습니다:
  ```bash
  curl -X POST https://flask-sign-language-api-production.up.railway.app/upload \
      -F "file=@test.mp4"
  ```
#### 응답
- 성공 (200 OK): gloss 형태의 단어 리스트 반환
  ```json
  {
    "message": "file uploaded successfully",
    "filename": "test3.mp4",
    "glosses": ["배", "아프다"]
  }
  ```

- 실패 (400, 500): 오류 메시지 반환
  - `400 Bad Request`: 파일 누락
  - `500 Internal Server Error`: 로컬 추론 서버 호출 실패

### 6. 문장 생성 통합 API
#### 설명
- 수어 영상(mp4)을 업로드하면 GLOSS를 추출하고 자연어 문장을 함께 반환합니다.
- (`/upload` + `/to_speech` 결합 기능)
#### 요청
- **Method**: POST  
- **Endpoint**: `/generate_sentence`  
- **Form-Data**:
  - file: `.mp4` 형식 수어 영상
  - 아래처럼 curl로 요청할 수 있습니다:
  ```bash
  curl -X POST https://flask-sign-language-api-production.up.railway.app/generate_sentence \
      -F "file=@test.mp4"
  ```
#### 응답
- 성공 (200 OK): gloss 형태의 단어 리스트와 완성된 sentence 
  ```json
  {
    "gloss": ["배", "아프다"],
    "sentence": "배가 아파요."
  }
  ```

- 실패 (400, 500): 오류 메시지 반환
  - `400 Bad Request`: 파일 누락
  - `500 Internal Server Error`: 로컬 추론 서버 호출 또는 gloss 추출 실패

---

## 주의사항
- `/get_video`, `/combine_videos` API의 `word`, `words` 파라미터는 **정확한 한글 문자열**로 입력해야 하며, **URL 인코딩**에 유의하세요. (예: `위험` → `word=위험`)
- `/to_speech`, `/to_gloss` API는 **JSON 형식의 요청 본문**을 받아야 하며, 필드 이름과 자료형을 정확히 맞춰야 합니다.
- `words` 리스트는 **공백 없는 단일 형태소 단어** 기준으로 구성해야 정확한 문장 생성 및 변환이 가능합니다. (예: `"배가"` → `["배"]`, `"아프다"` → 유지)
- `/upload`, `/generate_sentence` API는 **mp4 형식의 영상 파일**을 `file` 필드로 업로드해야 하며,  
  파일이 없거나 형식이 맞지 않으면 오류가 발생합니다.
- `/generate_sentence`는 내부적으로 `/upload`와 `/to_speech`를 자동 호출하므로, 업로드한 영상의 품질이나 길이에 따라 처리 시간이 다소 소요될 수 있습니다.
- 모든 수어 영상 및 생성 문장은 **비상업적 연구 및 학습용**으로만 사용 가능합니다.

---

## 팀 정보
- **팀명**: (비공개 / 팀명 없음)
- **프로젝트 기간**: 2025년 졸업작품 프로젝트

---

## License
이 프로젝트는 오픈소스가 아니며, 비상업적 연구 및 교육 목적에 한해 사용 가능합니다.  
영상 데이터는 [한국지능정보사회진흥원](https://aihub.or.kr)의 라이선스를 따릅니다.
