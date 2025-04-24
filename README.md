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
- gloss 형태의 단어 리스트(예: `["배", "아프다"]`)를 받아 자연어 문장(예: `"배가 아파요"`)으로 변환합니다.

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

### 2. 자연어처리 문장 생성 API
#### 요청
- **Method**: POST  
- **Endpoint**: `/to_speech`  
- **Request Body (JSON)**:  
  ```json
  {
    "words": ["배", "아프다"]
  }
  ```
  ```bash
  curl -X POST https://flask-sign-language-api-production.up.railway.app/to_speech -H "Content-Type: application/json" -d "@test.json"
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
  - 400: 요청 형식 오류
  - 500: OpenAI 처리 중 오류

---

## 주의사항
- API의 `word` 파라미터는 한글 문자열로 정확히 입력하고, URL 인코딩에 유의하세요.  
  (예: `위험` → `word=위험`)
- 제공되는 모든 수어 영상은 연구 및 학습용으로만 사용 가능합니다.
- - `/to_speech` 요청은 JSON 형식의 단어 리스트를 POST 방식으로 보내야 합니다.
- 단어 리스트는 공백 없는 단일 형태소 단어 기준으로 구성되어야 정확한 문장 변환이 가능합니다.

---

## 팀 정보
- **팀명**: (비공개 / 팀명 없음)
- **프로젝트 기간**: 2025년 졸업작품 프로젝트

---

## License
이 프로젝트는 오픈소스가 아니며, 비상업적 연구 및 교육 목적에 한해 사용 가능합니다.  
영상 데이터는 [한국지능정보사회진흥원](https://aihub.or.kr)의 라이선스를 따릅니다.
