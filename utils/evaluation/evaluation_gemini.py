import google.generativeai as genai
import json
import time
from google.api_core import exceptions

class GeminiAPI:
    def __init__(self):
        self.api_keys = ['API_KEY']
        self.current_key_index = 0
        self.setup_api()

    def setup_api(self):
        genai.configure(api_key=self.api_keys[self.current_key_index])
        self.model = genai.GenerativeModel('gemini-pro')
        print(f"API 키 {self.current_key_index + 1} 사용 중")

    def switch_to_next_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.setup_api()

    def compare_captions(self, caption1, caption2, retry_delay=1):
        max_retries = len(self.api_keys)  # API 키 개수만큼 재시도
        for attempt in range(max_retries):
            try:
                prompt = f"""
                Please rate the semantic similarity between these two sentences on a scale of 1-5:
                Sentence 1: {caption1}
                Sentence 2: {caption2}
                
                Scale:
                1: Strongly Disagree (Completely different content)
                2: Disagree (Somewhat different content)
                3: Neutral (Partially similar)
                4: Agree (Mostly similar)
                5: Strongly Agree (Almost identical)
                
                Please respond with only the number.
                """
                
                response = self.model.generate_content(prompt)
                similarity_score = int(response.text.strip())
                time.sleep(retry_delay)
                return similarity_score
                
            except exceptions.ResourceExhausted:
                print(f"API 키 {self.current_key_index + 1} 할당량 초과. 다음 키로 전환...")
                self.switch_to_next_key()
            except ValueError:
                print("유효하지 않은 응답")
                return None
        
        print("모든 API 키의 할당량이 초과되었습니다.")
        return None

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_total_score(results):
    # 모든 similarity 값 추출
    similarities = [item['similarity'] for item in results.values()]
    
    # 총점 계산
    total_similarity = sum(similarities)
    
    # 최대 가능 점수 계산 (항목 수 * 최대 점수 5)
    max_possible = len(similarities) * 5
    
    # 100점 기준으로 환산
    final_score = (total_similarity / max_possible) * 100
    
    return round(final_score, 2)  # 소수점 둘째자리까지 반올림

def main():
    references = load_json_file('gemini_predictions_fin.json')
    blip_predictions = load_json_file('blip-3_predictions_fin.json')
    
    results = {}
    gemini_api = GeminiAPI()  # API 관리자 인스턴스 생성
    
    for image in references['images']:
        image_id = image['id']
        print(f"처리 중인 이미지 ID: {image_id}")
        
        ref_caption = None
        for annotation in references['annotations']:
            if annotation['image_id'] == image_id:
                ref_caption = annotation['caption']
                break
                
        blip_caption = None
        for prediction in blip_predictions:
            if prediction['image_id'] == image_id:
                blip_caption = prediction['caption']
                break
        
        if ref_caption and blip_caption:
            similarity = gemini_api.compare_captions(ref_caption, blip_caption)
            if similarity is not None:
                results[image_id] = {
                    'reference': ref_caption,
                    'prediction': blip_caption,
                    'similarity': similarity
                }
            else:
                print(f"이미지 ID {image_id}의 유사도 계산 실패")
    
    # 결과 저장 전에 총점 계산
    total_score = calculate_total_score(results)
    
    # 결과에 총점 추가
    final_results = {
        'items': results,
        'total_items': len(results),
        'total_similarity': sum(item['similarity'] for item in results.values()),
        'score_100': total_score
    }
    
    with open('similarity_results4.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n총 항목 수: {len(results)}")
    print(f"100점 기준 점수: {total_score}점")

if __name__ == "__main__":
    main()
