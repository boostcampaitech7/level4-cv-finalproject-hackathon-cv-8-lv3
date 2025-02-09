from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import json
import re
from flasgger import Swagger

# Flask 앱 초기화
app = Flask(__name__)
swagger = Swagger(app)

# 모델 설정
class ModelConfig:
    def __init__(self):
        self.quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
        self.model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
        
    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            device_map="auto",
            quantization_config=self.quantization_config
        )
        return self.tokenizer, self.model

# 기본 응답 템플릿
DEFAULT_RESPONSE = {
    "video_keywords": [],
    "stt_keywords": [],
    "unique_keywords": [],
    "unique_keywords_importance": 1,
    "video_keywords_importance": 1,
    "stt_keywords_importance": 1
}

# 모델 및 토크나이저 초기화
model_config = ModelConfig()
tokenizer, model = model_config.load_model()

def create_prompt(query_text):
    return f"""Query Text에서 정확한 단어와 구문을 추출하고, 추출된 키워드의 수와 중요성에 따라 중요도를 평가하세요:

Query Text: {query_text}

1. 비디오 키워드: 시각적 요소와 관련된거로만 한 문장으로 출력
   중요도: [키워드 수와 중요성에 따라 1-5 사이 점수 부여]

2. STT 키워드: [대화나 음성과 관련된 키워드만 추출]
   중요도: [키워드 수와 중요성에 따라 1-5 사이 점수 부여]

4. 고유명사: [Query Text 내의 인물, 장소, 작품명 등 고유명사만 추출]
   중요도: [고유명사의 중요성에 따라 1-5 사이 점수 부여]

중요:
- Query Text에서 정확한 단어만 추출
- 키워드는 대괄호 안에 쉼표로 구분하여 나열
- json으로 video_keywords: ..., stt_keywords: ..., unique_keywords: ..., unique_keywords_importance: ..., video_keywords_importance: ..., stt_keywords_importance: ...의 형식으로 알려줄 것
- vide_keywords는 하나의 문장으로만 출력
- 추출된 키워드의 수와 중요성을 고려하여 중요도 평가
- 중국어는 절대 쓰지 않아야 하고 최종 출력애 나와서는 안됨
- 키워드가 없는 경우 1점 부여"""

def create_translation_prompt(english_text):
    return f"""Please translate the following English text to Korean:

English: {english_text}

important:
- json으로 translation:... 형식으로만 알려줄 것
- 번역된 텍스트는 한국어로 번역되어야 함
- 중국어는 절대 쓰지 않아야 하고 최종 출력애 나와서는 안됨"""

def analyze_query(query_text):
    # 프롬프트 생성 및 모델 입력
    prompt = create_prompt(query_text)
    inputs = tokenizer(prompt, return_tensors="pt", padding=True).to(model.device)
    
    # 모델 추론
    outputs = model.generate(
        **inputs,
        max_new_tokens=1024,
        temperature=0.8,
        do_sample=True,
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
            return json.loads(json_str)
        except json.JSONDecodeError:
            return DEFAULT_RESPONSE
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
    app.run(host='0.0.0.0', port=30896)