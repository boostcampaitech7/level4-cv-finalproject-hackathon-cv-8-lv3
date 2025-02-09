import json

def convert_predictions_format(input_file_path, output_file_path):
    # 입력 파일 읽기
    with open(input_file_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # 새로운 형식으로 변환
    converted_data = []
    
    # segments 배열을 순회하면서 새로운 형식으로 변환
    for idx, segment in enumerate(original_data['segments']):
        converted_item = {
            "image_id": str(idx),  # 인덱스를 문자열로 변환
            "caption": segment['captions']
        }
        converted_data.append(converted_item)
    
    # 결과를 파일로 저장
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(converted_data, f)

# 사용 예시
input_file = "blip-3_predictions.json"
output_file = "blip-3_predictions_fin.json"
convert_predictions_format(input_file, output_file)
