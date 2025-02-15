# 🎬 비디오 내 장면 탐색을 위한 Video-to-Text 모델과 검색

<br />

본 프로젝트는 **OTT(Over-the-Top) 플랫폼(예: 티빙)** 에서 자연어(한국어) 검색을 통해 특정 장면을 빠르고 정확하게 찾을 수 있는 검색 시스템을 구현하는 것을 목표로 합니다.  
이를 위해 크게 **Video-to-Text**와 **Text-to-Video**라는 두 가지 모듈로 나누어 개발했습니다.

- **Video-to-Text**  
  입력된 영상을 장면별로 분할하고, 시각 정보를 캡션(xGen-MM-Vid 모델)으로 생성하며, 음성 정보를 (Whisper)로 STT하여 텍스트 형태로 타임스탬프와 함께 저장합니다.

- **Text-to-Video**  
  사용자가 자연어 쿼리를 입력하면, 시각 캡션과 오디오 캡션, 그리고 영화 메타데이터를 함께 활용하여 해당 장면의 비디오 ID와 타임스탬프를 빠르게 검색합니다.

<br />

## 📌 프로젝트 개요

<br />

### 🔷 배경
- OTT 서비스에서 방대한 양의 영상 콘텐츠를 보유하고 있으며, 이를 **효율적으로 검색·추천**해야 하는 필요성이 있습니다.
- 특정 영화나 드라마에서 원하는 장면을 **자연어로 검색하여 즉시 찾아보려는 요구**가 증가하고 있습니다.
- 본 프로젝트는 영상의 **시각 정보**와 **음성(발화) 정보**, 그리고 **메타데이터**(영화 제목·출연진·제작진 등)를 결합하여, 사용자가 자연어로 묘사한 장면을 **빠르고 정확하게 매핑**할 수 있는 시스템을 구현하는 것을 목표로 합니다.

<br />

### 📄 프로젝트 주제 (Abstract)
- **프로젝트명**: 비디오 내 장면 탐색을 위한 Video-to-Text 모델과 검색  
- **목표**: 티빙 같은 OTT 플랫폼에서 **사용자의 자유로운 자연어 입력**에 따라 특정 비디오 장면을 빠르고 정확하게 찾는 검색 시스템을 제공  
- **핵심 아이디어**  
  1. **비디오 장면 분할** (PySceneDetect)  
  2. **비디오 캡션 생성** (xGen-MM-Vid, BLIP-3 기반)  
  3. **음성 변환(STT)** (OpenAI Whisper)  
  4. **메타데이터 추출** (TMDB·QuoDB 활용)  
  5. **유사도 검색** (ChromaDB + 임베딩)  
  6. **자연어 쿼리 분석** (Gemini API 활용)

<br />

## 👥 프로젝트 팀 구성 및 역할

네이버 커넥트재단의 **CV-08 “여름엔 쪼꼬만두 호두베리찐빵”** 팀이 진행했습니다.

| 캠퍼 |  이름   | 이메일 | 담당 및 역할 | GitHub |
|:---------:|:------:|:-----------------------------:|:---------------------------------------------------------------------|:--------------------------------------------:|
| **T7103** | 김건수  | kundoo0412@gmail.com         | 팀장, 프로젝트 총괄, STT, 메인 서버 API 제작                          | <a href="https://github.com/kimgeonsu"><img src="https://github.com/kimgeonsu.png" width="40"></a> |
| **T7141** | 김형준  | ruka030809@gmail.com         | VLM 모델 실험 및 API 구현, ChromaDB 구현 및 메타데이터 DB 구현       | <a href="https://github.com/ruka030809"><img src="https://github.com/ruka030809.png" width="40"></a> |
| **T7163** | 서진형  | tjwlssla1@gmail.com          | EILVE/LLAMA 실험, 장면분할 함수, 메타데이터 검색 함수 구현           | <a href="https://github.com/SeoJinHyoung"><img src="https://github.com/SeoJinHyoung.png" width="40"></a> |
| **T7224** | 이시하  | sihari1115@gmail.com         | 평가 지표 구현, DeepL API 및 Gemini 기반 검색어 분할 함수 구현       | <a href="https://github.com/sihari-1115"><img src="https://github.com/sihari-1115.png" width="40"></a> |
| **T7149** | 박민영  | afroralex98@gmail.com        | STT 모델 실험·구현, Data parallel 실험                                | <a href="https://github.com/alexminyoungpark"><img src="https://github.com/alexminyoungpark.png" width="40"></a> |
| **T7255** | 조혜원  | 5876675@gmail.com            | 데모 페이지 구현, New-Data 업로드 구현, VLM/SED 모델 실험            | <a href="https://github.com/One-HyeWon"><img src="https://github.com/One-HyeWon.png" width="40"></a> |




<br />

## 🔄 프로젝트 수행 절차 및 방법

<br />

### 🔄 전반적인 프로세스
1️⃣ **데이터 준비 및 장면 분할**  
   - PySceneDetect 활용, `ContentDetector`로 비디오를 **장면 단위** 로 분할  
   - threshold 조정(예: 50) 등으로 장면 변화 검출

2️⃣ **비디오 캡션 생성 (Video-to-Text)**  
   - **xGen-MM-Vid(BLIP-3-Video)** 모델로 분할된 각 장면을 **캡션**  
   - 영어로 캡션 생성 후, **DeepL API** 등으로 **한국어 번역**  
   - 장면별 타임스탬프와 함께 **JSON** 형태로 저장

3️⃣ **음성 변환(STT)**  
   - **OpenAI Whisper** 를 활용하여 영상 오디오 → 텍스트 변환  
   - 중복·불필요 문장 등 후처리  
   - 타임스탬프와 함께 STT 결과를 관리

4️⃣ **메타데이터 추출**  
   - QuoDB API로 영화 제목·개봉연도 추정  
   - TMDB API로 ID 조회 후 출연진, 캐릭터, 제작진 정보 획득  
   - DB에 메타데이터 저장

5️⃣ **DB(ChromaDB) 구축**  
   - Video Caption(시각정보), Audio Caption(오디오 정보)을 각각 임베딩 (paraphrase-multilingual-mpnet-base-v2) → **ChromaDB**에 저장  
   - 메타데이터는 일반 DB(sqlite 등)에 저장

6️⃣ **쿼리 분석 및 Text-to-Video 검색**  
   - 사용자 **자연어 쿼리** → **Gemini API**로 비디오/오디오/메타데이터 키워드 등으로 분류  
   - 분류된 키워드를 ChromaDB, 메타데이터 DB에 각각 질의  
   - 결과(비디오 ID, 타임스탬프 등)를 규칙 기반으로 통합, 사용자에게 반환

7️⃣ **평가**  
   - **Video-to-Text**: 키워드 기반 / Gemini API 활용 정량·정성 평가  
   - **Text-to-Video**: 사람이 작성한 장면 캡션과 모델 예측 장면(타임스탬프) 비교  
   - 일부 장면에서 타임스탬프 범위가 넓게 잡히거나 잡음이 포함되는 문제 발견

<br />

## 🚀 코드 실행 방법

~~현재 모든 서버가 켜져 있습니다.~~
<br />
~~아래 절차에 따라 서버에 접속하고 기능을 사용할 수 있습니다.~~

### 🔗 서버 접속 방법

1. **SSH로 서버에 접속**
    ```bash
    ssh -i cv-08.pem -p 31578 root@10.28.224.136
    ```

2. **tmux 세션에 접속**  
   터미널 2개를 열고 각각의 서버에 접속:
    - **터미널 1번**: Frontend 서버
      ```bash
      tmux attach -t frontend-0
      ```
    - **터미널 2번**: Frontend Video 서버
      ```bash
      tmux attach -t front-vid-server-0
      ```

3. **웹 인터페이스 접속**  
   - 브라우저에서 아래 주소로 접속  
     ```
     http://localhost:3000
     ```
   - 원하는 기능을 선택하여 사용

<br />

## 📌 기능 설명

### 🎞️ Video to Text

<img width="628" alt="image" src="https://github.com/user-attachments/assets/ee019a20-ae51-4df8-8924-8d3ff6b14c20" />

- **기존 비디오**를 선택하거나 **직접 업로드**하여 **타임스탬프**를 지정하면 텍스트 변환을 수행합니다.

  - **기존 비디오 활용**  
    - `/data/ephemeral/home/movie_clips` 디렉터리에 있는 영상의 **ID** 입력 (예: `_8LrZ4NhPmk`)
    - 타임스탬프 범위를 입력하여 캡션·STT 결과 추출

  - **새로운 비디오 업로드**
    - 파일 업로드 버튼 클릭 → 영상 업로드
    - 원하는 구간(타임스탬프)을 지정해 변환 요청

### 🔎 Text to Video

<img width="624" alt="image" src="https://github.com/user-attachments/assets/85483b29-1b8e-4c75-97d5-1682958dfcc5" />

- 사용자가 **검색어**를 입력하면, 관련된 비디오 장면(프레임)을 찾아 출력합니다.

#### 사용 방법
1. 검색창에 **자연어**로 키워드 입력  
2. **결과 목록**에서 프레임·타임스탬프 확인  

<br />

## 📂 간단 아키텍처/파이프라인 요약

1. **STT 서버**  
   - Whisper 모델로 STT 수행 (`POST /entire_video`, `POST /short_video`, `POST /upload_video` 등)

2. **Video Captioning 서버**  
   - xGen-MM-Vid(BLIP-3-Video)로 장면 단위 캡션 생성 (`POST /entire_video`, `POST /short_video`)

3. **ChromaDB 서버**  
   - 비디오 캡션·오디오 캡션을 임베딩 후 벡터 저장/검색  
   - (`POST /add_json`, `POST /add_json_audio`, `POST /query`, `POST /query_audio` 등)

4. **LLM 서버**  
   - Gemini API를 통해 자연어 쿼리 분석 (시각·청각·메타데이터 영역)  
   - (`POST /analyze_query`, `POST /translate` 등)

5. **Main 서버**  
   - 장면분할, 전체 결과 취합  
   - `POST /process_entire_video`: 비디오 업로드 → STT + Caption 서버 호출 → 결과 병합 후 ChromaDB 저장  
   - `POST /search_videos`: 쿼리 분석 → ChromaDB/메타데이터 DB 조회 → 최종 결과 반환

<br />

## 🔮 결론 및 앞으로의 과제

- **결론**  
  - Video-to-Text와 Text-to-Video 모듈을 효과적으로 결합하여, 자연어 검색으로 특정 비디오 장면을 찾아내는 시스템을 구현했습니다.  
  - 장면 분할, 음성 분석, LLM 쿼리 분석 정확도 등의 한계가 있으나, 시각·청각 정보와 메타데이터를 융합한 구조를 통해 **확장 가능성**을 확인했습니다.

- **향후 과제**  
  1. **맥락 기반 장면 분할**(PySceneDetect 고도화 혹은 대안)  
  2. **오디오·비디오 통합 모델**(멀티모달)로 더 풍부한 영상 캡션 생성  
  3. **LLM 프롬프트 튜닝**으로 검색 정확도 향상  
  4. **데이터셋 확장** 및 **모델 재학습** 등을 통한 성능 개선

<br />

## 7. 랩업 리포트

[[랩업]비디오 내 장면 탐색을 위한 Video-to-Text 모델과 검색.pdf](https://github.com/user-attachments/files/18811561/Video-to-Text.pdf)
