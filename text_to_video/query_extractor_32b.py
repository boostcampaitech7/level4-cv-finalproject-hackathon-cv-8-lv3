from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from transformers import BitsAndBytesConfig

def analyze_query(query_text):
    # 4비트 양자화 설정
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    # 토크나이저와 모델 로드
    tokenizer = AutoTokenizer.from_pretrained(
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        trust_remote_code=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        trust_remote_code=True,
        device_map="auto",
        quantization_config=quantization_config
    )

    prompt = f"""Query Text에서 정확한 단어와 구문을 추출하고, 추출된 키워드의 수와 중요성에 따라 중요도를 평가하세요:

Query Text: {query_text}

1. 비디오 키워드: [시각적 요소와 관련된 키워드만 추출]
중요도: [키워드 수와 중요성에 따라 1-5 사이 점수 부여]

2. STT 키워드: [대화나 음성과 관련된 키워드만 추출]
중요도: [키워드 수와 중요성에 따라 1-5 사이 점수 부여]

3. SED 키워드: [배경음이나 소리와 관련된 키워드만 추출]
중요도: [키워드 수와 중요성에 따라 1-5 사이 점수 부여]

중요:
- Query Text에서 정확한 단어만 추출
- 키워드는 대괄호 안에 쉼표로 구분하여 나열
- 추출된 키워드의 수와 중요성을 고려하여 중요도 평가
- 키워드가 없는 경우 1점 부여"""

    inputs = tokenizer(prompt, return_tensors="pt", padding=True).to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=10000,
        temperature=0.8,
        do_sample=True
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

if __name__ == "__main__":
    print("Query Text를 입력하세요:")
    user_query = input()
    result = analyze_query(user_query)
    print("\n분석 결과:")
    print(result)
