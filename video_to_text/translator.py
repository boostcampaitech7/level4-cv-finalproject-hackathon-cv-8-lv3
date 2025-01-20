from transformers import pipeline
import json

def translate_captions(json_path):
    translator = pipeline('translation', model='facebook/nllb-200-distilled-600M', device=0, src_lang='eng_Latn', tgt_lang='kor_Hang', max_length=512)
    
    # JSON 파일 읽기
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # 각 세그먼트의 캡션 번역
    for segment in data['segments']:
        caption = segment['captions']
        # 번역 수행
        translated = translator(caption, max_length=512)[0]['translation_text']
        # 번역된 텍스트로 교체
        segment['captions'] = translated
        
    # 번역된 JSON 저장
    output_path = json_path.replace('.json', '_korean.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f'번역이 완료되었습니다. 결과가 {output_path}에 저장되었습니다.')

if __name__ == '__main__':
    json_path = 'final_json_format.json'
    translate_captions(json_path)
