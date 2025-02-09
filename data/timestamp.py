import json
import os

def convert_timestamp_to_seconds(timestamp):
    # 빈 문자열 처리
    if not timestamp:
        return 0
        
    # 문자열 타입 체크
    if not isinstance(timestamp, str):
        timestamp = str(timestamp)
        
    # 00:00:00 형식
    if len(timestamp.split(':')) == 3:
        h, m, s = map(int, timestamp.split(':'))
        return h * 3600 + m * 60 + s
        
    # 00:00 형식 
    elif len(timestamp.split(':')) == 2:
        m, s = map(int, timestamp.split(':'))
        return m * 60 + s
        
    # 0:00 형식
    elif ':' in timestamp:
        m, s = map(int, timestamp.split(':'))
        return m * 60 + s
        
    # 00 형식 (초)
    else:
        return int(timestamp) if timestamp else 0

def parse_timestamp(timestamp, next_timestamp=None, is_last=False, video_duration=None):
    # 문자열 타입 체크
    if not isinstance(timestamp, str):
        timestamp = str(timestamp)
        
    # 01:15-01:16 형식
    if '-' in timestamp:
        start, end = timestamp.split('-')
        start_seconds = convert_timestamp_to_seconds(start)
        end_seconds = convert_timestamp_to_seconds(end)
        
    # 단일 시간 형식 (00:00 등)
    else:
        start_seconds = convert_timestamp_to_seconds(timestamp)
        if is_last and video_duration:
            end_seconds = video_duration
        elif next_timestamp:
            end_seconds = convert_timestamp_to_seconds(next_timestamp)
        else:
            end_seconds = start_seconds + 1
        
    # 초를 hh:mm:ss 형식으로 변환
    def seconds_to_hhmmss(seconds):
        if isinstance(seconds, float):
            seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
        
    return {
        "start_time": seconds_to_hhmmss(start_seconds),
        "end_time": seconds_to_hhmmss(end_seconds)
    }

def convert_json_timestamps(input_file):
    # 입력 JSON 파일 읽기
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 모든 비디오에 대해 처리
    for video_info in data.values():
        video_duration = video_info.get('duration')
        
        # captions 키가 없으면 빈 리스트로 초기화
        if 'captions' not in video_info:
            video_info['captions'] = []
            
        # captions가 딕셔너리인 경우 리스트로 변환
        if isinstance(video_info['captions'], dict):
            # 딕셔너리의 모든 리스트 값을 하나의 리스트로 합침
            all_captions = []
            for value in video_info['captions'].values():
                if isinstance(value, list):
                    all_captions.extend(value)
            video_info['captions'] = all_captions
            
        # 각 캡션의 timecode를 start_time과 end_time으로 변환
        for i, caption in enumerate(video_info['captions']):
            if 'timecode' in caption:
                next_timestamp = None
                is_last = i == len(video_info['captions']) - 1
                
                if not is_last:
                    next_timestamp = video_info['captions'][i+1].get('timecode')
                    
                times = parse_timestamp(caption['timecode'], 
                                     next_timestamp,
                                     is_last,
                                     video_duration)
                caption['start_time'] = times['start_time']
                caption['end_time'] = times['end_time']
                del caption['timecode']
    
    # 출력 파일명 생성
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_converted{ext}"
    
    # 변환된 데이터를 새 JSON 파일로 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return output_file

if __name__ == "__main__":
    input_file = "/data/ephemeral/home/level4-cv-finalproject-hackathon-cv-8-lv3/dataset/annotation.json"
    output_file = convert_json_timestamps(input_file)
    print(f"변환된 파일이 {output_file}에 저장되었습니다.")
