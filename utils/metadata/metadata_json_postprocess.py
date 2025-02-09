import json
import re
import glob
import os

# JSON 파일이 있는 경로 설정
directory = "/Users/kimhyungjun/chromaTest/meta_data/meta_data/movie_info"  # 원하는 경로로 변경

# 정규 표현식을 사용하여 배우와 역할을 분리하는 함수
def process_cast(cast_list):
    processed_cast = []
    pattern = re.compile(r"(.*?)\s+as\s+(.*)")  # 'as' 기준으로 분리
    
    for entry in cast_list:
        match = pattern.match(entry)
        if match:
            actor, role = match.groups()
            role = re.sub(r"\s*\(uncredited\)", "", role).strip()  # (uncredited) 제거
            processed_cast.append({"actor": actor.strip(), "role": role})
    
    return processed_cast

# 디렉토리 내 모든 JSON 파일 처리
json_files = glob.glob(os.path.join(directory, "*.json"))

for json_file in json_files:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if "cast" in data:
        data["cast"] = process_cast(data["cast"])
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Processed {len(json_files)} JSON files.")
