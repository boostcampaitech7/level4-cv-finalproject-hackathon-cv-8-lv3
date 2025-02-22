from flask import Flask, request, jsonify
import json
import re
from flasgger import Swagger
import google.generativeai as genai
from typing import List
import time

# Flask 앱 초기화  
app = Flask(__name__)
swagger = Swagger(app)

# 기본 응답 템플릿
DEFAULT_RESPONSE = {
    "video_keywords": [],
    "stt_keywords": [],
    "unique_keywords": [],
    "unique_keywords_importance": 1,
    "video_keywords_importance": 1,
    "stt_keywords_importance": 1
}

# API 키 관리를 위한 클래스 추가
class APIKeyManager:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.last_request_time = 0
        self.requests_per_minute = 60  # 분당 요청 제한

    def get_next_key(self) -> str:
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return self.api_keys[self.current_key_index]

    def get_current_key(self) -> str:
        return self.api_keys[self.current_key_index]

    def handle_rate_limit(self):
        current_time = time.time()
        time_diff = current_time - self.last_request_time
        
        if time_diff < 60/self.requests_per_minute:
            time.sleep(60/self.requests_per_minute - time_diff)
        
        self.last_request_time = time.time()

# API 키 목록 설정
API_KEYS = ['API_KEY']

# API 키 매니저 초기화
key_manager = APIKeyManager(API_KEYS)

def create_prompt(query_text):
    return f"""Query Text에서 다음 세 분야의 정보를 추출하고 중요도를 평가하세요:

Query Text: {query_text}

1. 비디오 분야 (시각적 요소)
   - 시각적 요소 관련 문장만 추출
   - 대화/음성 관련 문장 무조건 제외
   - 고유명사(배우 이름/등장인물 이름)는 무조건 대명사로 변경
   - 하나의 연결된 문장으로 만들기
   - 영어로 번역
   중요도: 1-5점

2. STT 분야 (대화/음성)
   - 대화/음성 관련 문장만 추출
   - 화자 정보 제외
   - 각 문장을 "..." 형식으로 분리
   - 영어로 번역
   중요도: 1-5점

3. 고유명사 (배우 이름/등장인물 이름)
   - 배우 이름/등장인물 이름만 추출
   - 영어로 번역
   - 각각 "..." 형식으로 분리
   중요도: 1-5점

응답 형식 (JSON):
{{
    "video_field": ["..."],
    "video_field_importance": N,
    "stt_field": ["...", "..."],
    "stt_field_importance": N,
    "unique_field": ["...", "..."],
    "unique_field_importance": N
}}

주의사항:
- 모든 필드의 텍스트는 무조건 영어로 번역해서 출력할 것
- 키워드가 없는 경우 중요도 1점 부여
- "~장면" 형태의 표현은 제외
"""


def create_translation_prompt(english_text):
    return f"""Please translate the following English text to Korean:

English: {english_text}

important:
- json으로 translation:... 형식으로만 알려줄 것
- 번역된 텍스트는 한국어로 번역되어야 함
- 중국어는 절대 쓰지 않아야 하고 최종 출력애 나와서는 안됨"""

def analyze_query(query_text):
    try:
        key_manager.handle_rate_limit()
        genai.configure(api_key=key_manager.get_current_key())
        
        model = genai.GenerativeModel('gemini-pro')
        prompt = create_prompt(query_text)
        
        try:
            response = model.generate_content(prompt)
            
            if not response.text:
                key_manager.get_next_key()
                return analyze_query(query_text)
            
            json_pattern = r'\{[^{}]*\}'
            json_match = re.search(json_pattern, response.text)
            
            if json_match:
                try:
                    json_str = json_match.group()
                    print(json_str)
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    return DEFAULT_RESPONSE
                    
        except Exception as e:
            print(f"현재 API 키에서 오류 발생: {str(e)}")
            key_manager.get_next_key()
            return analyze_query(query_text)
            
    except Exception as e:
        print(f"분석 중 오류 발생: {str(e)}")
        return DEFAULT_RESPONSE

def translate_text(english_text):
    # 프롬프트 생성 및 모델 입력
    prompt = create_translation_prompt(english_text)
    inputs = tokenizer(prompt, return_tensors="pt", padding=True).to(model.device)
    
    # 모델 추론
    outputs = model.generate(
        **inputs,
        max_new_tokens=1024,
        temperature=0.7,
        do_sample=True,
        num_beams=1,
        pad_token_id=tokenizer.eos_token_id
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(response)
    # JSON 추출 및 파싱
    json_pattern = r'\{[^{}]*\}'
    json_match = re.search(json_pattern, response)
    
    if json_match:
        try:
            json_str = json_match.group()
            json_data = json.loads(json_str)
            return json_data.get('translation', '')
        except json.JSONDecodeError:
            return ''
    return ''

@app.route('/analyze_query', methods=['POST'])
def query_analysis():
    """
    Query Text를 분석하여 키워드와 중요도를 추출하는 API
    ---
    tags:
      - Query Analysis
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - query_text
          properties:
            query_text:
              type: string
              description: 분석할 쿼리 텍스트
              example: "비오는 소리가 들리며 낮에 바닥은 시멘트이고, 배경에 나무가 있고, 하나의 우산을 청자켓입은 스파이더맨과 여름 교복입은 메리 제인이 같이 쓰고 있는 상태에서 '우리 사귈래?' 라고 말하는 장면"
    responses:
      200:
        description: 성공적으로 분석 완료
        schema:
          type: object
          properties:
            result:
              type: object
              properties:
                video_keywords:
                  type: array
                  items:
                    type: string
                  description: 시각적 요소와 관련된 키워드 목록
                  example: ["바다", "울다"]
                stt_keywords:
                  type: array
                  items:
                    type: string
                  description: 대화나 음성과 관련된 키워드 목록
                  example: []
                unique_keywords:
                  type: array
                  items:
                    type: string
                  description: 고유명사 키워드 목록
                  example: ["주인공"]
                video_keywords_importance:
                  type: integer
                  description: 비디오 키워드의 중요도 (1-5)
                  example: 4
                stt_keywords_importance:
                  type: integer
                  description: STT 키워드의 중요도 (1-5)
                  example: 1
                unique_keywords_importance:
                  type: integer
                  description: 고유명사 키워드의 중요도 (1-5)
                  example: 3
      400:
        description: 잘못된 요청
        schema:
          type: object
          properties:
            error:
              type: string
              description: 오류 메시지
              example: "Content-Type은 application/json이어야 합니다"
      500:
        description: 서버 내부 오류
        schema:
          type: object
          properties:
            error:
              type: string
              description: 오류 메시지
              example: "분석 중 오류 발생: 내부 서버 오류"
    """
    # 요청 검증
    if not request.is_json:
        return jsonify({"error": "Content-Type은 application/json이어야 합니다"}), 400
    
    data = request.get_json()
    query_text = data.get('query_text')
    
    if not query_text:
        return jsonify({"error": "query_text가 필요합니다"}), 400

    # 쿼리 분석 실행
    try:
        result = analyze_query(query_text)
        return jsonify({"result": result}), 200
    except Exception as e:
        return jsonify({"error": f"분석 중 오류 발생: {str(e)}"}), 500

@app.route('/translate', methods=['POST'])
def translate():
    """
    영어 텍스트를 한국어로 번역하는 API
    ---
    tags:
      - Translation
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - english_text
          properties:
            english_text:
              type: string
              description: 번역할 영어 텍스트
              example: "Hello, how are you?"
    responses:
      200:
        description: 성공적으로 번역 완료
        schema:
          type: object
          properties:
            translation:
              type: string
              description: 번역된 한국어 텍스트
              example: "안녕하세요, 어떻게 지내세요?"
      400:
        description: 잘못된 요청
        schema:
          type: object
          properties:
            error:
              type: string
              description: 오류 메시지
              example: "Content-Type은 application/json이어야 합니다"
      500:
        description: 서버 내부 오류
        schema:
          type: object
          properties:
            error:
              type: string
              description: 오류 메시지
              example: "번역 중 오류 발생: 내부 서버 오류"
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type은 application/json이어야 합니다"}), 400
    
    data = request.get_json()
    english_text = data.get('english_text')
    
    if not english_text:
        return jsonify({"error": "english_text가 필요합니다"}), 400

    try:
        translation = translate_text(english_text)
        return jsonify({"translation": translation}), 200
    except Exception as e:
        return jsonify({"error": f"번역 중 오류 발생: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=30896, debug=True)
