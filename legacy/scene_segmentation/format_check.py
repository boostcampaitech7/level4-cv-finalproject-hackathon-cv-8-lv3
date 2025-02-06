import json
from datetime import datetime

path = "/data/ephemeral/home/level4-cv-finalproject-hackathon-cv-8-lv3/dataset/annotation_converted.json"
with open(path, 'r', encoding="utf-8") as f:
    data = json.load(f)

for video_id, anno in data.items():
    captions = anno.get('captions', [])
    for i, cap in enumerate(captions):
        # 1) end_time, start_time 누락 여부 체크
        if 'end_time' not in cap:
            print(f"[MISSING] {video_id}의 captions[{i}]에 'end_time'이 없습니다. 내용: {cap}")
        if 'start_time' not in cap:
            print(f"[MISSING] {video_id}의 captions[{i}]에 'start_time'이 없습니다. 내용: {cap}")
        
        # 2) HH:MM:SS 형식 체크
        # start_time
        if 'start_time' in cap:
            try:
                datetime.strptime(cap['start_time'], '%H:%M:%S')
            except ValueError:
                print(f"[FORMAT] {video_id}의 captions[{i}] start_time='{cap['start_time']}' 가 'HH:MM:SS' 형식이 아님.")
        
        # end_time
        if 'end_time' in cap:
            try:
                datetime.strptime(cap['end_time'], '%H:%M:%S')
            except ValueError:
                print(f"[FORMAT] {video_id}의 captions[{i}] end_time='{cap['end_time']}' 가 'HH:MM:SS' 형식이 아님.")
