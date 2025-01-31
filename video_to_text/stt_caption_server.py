import json
import numpy as np
from flask import Flask, request, jsonify
from flasgger import Swagger
import os
import uuid
from whisper import load_model
from whisper.audio import load_audio

# 모델 초기화 
model = load_model("turbo", device="cuda", download_root=None)

app = Flask(__name__)
swagger = Swagger(app)

def get_stt_caption(video_path: str, time_ranges: list) -> list:
    """
    비디오의 특정 시간 범위에서 STT 캡션을 생성합니다.
    
    Args:
        video_path (str): 비디오 파일 경로
        time_ranges (list): 시작/종료 시간 튜플의 리스트
        
    Returns:
        list: 각 구간별 STT 캡션 정보를 담은 리스트
    """
    all_responses = []
    
    try:
        audio = load_audio(video_path)
        # 전체 오디오 길이(초)를 계산
        sample_rate = 16000  # whisper의 기본 sample rate
        duration = len(audio) / sample_rate
        
        for start_time, end_time in time_ranges:
            # 시간(초)을 샘플 인덱스로 변환
            start_idx = int(start_time * sample_rate)
            end_idx = int(end_time * sample_rate)
            
            # 인덱스가 유효한지 확인
            if start_idx >= len(audio) or end_idx > len(audio):
                print(f"경고: 요청한 시간 범위({start_time}-{end_time}초)가 오디오 길이({duration}초)를 초과합니다")
                continue
                
            audio_segment = audio[start_idx:end_idx]
            
            if len(audio_segment) == 0:
                print(f"경고: {start_time}-{end_time}초 구간의 오디오가 비어있습니다")
                continue
            
            # STT 수행
            result = model.transcribe(
                audio=audio_segment,
                logprob_threshold=-2.0,
                no_speech_threshold=0.95
            )
            print(f"디버그 - STT 결과: {result}")  # 디버그용 출력 추가
            
            all_responses.append({
                "start_time": start_time,
                "end_time": end_time,
                "caption": result["text"]
            })
            
    except Exception as e:
        print(f"STT 처리 중 오류 발생: {str(e)}")
        return []
        
    return all_responses

@app.route('/entire_video', methods=['POST'])
def entire_video():
    """
    전체 비디오의 STT 캡션을 생성합니다.
    ---
    tags:
      - STT Caption API
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            video_path:
              type: string
              description: 비디오 파일의 경로
            timestamps:
              type: array
              description: 시작/종료 시간 리스트
              items:
                type: object
                properties:
                  start:
                    type: number
                  end:
                    type: number
    responses:
      200:
        description: STT 캡션 생성 성공
      400:
        description: 잘못된 요청
      500:
        description: 서버 오류
    """
    try:
        video_path = request.json.get('video_path')
        timestamps = request.json.get('timestamps')
        
        # 입력값 검증
        if not video_path:
            return jsonify({"error": "비디오 경로가 누락되었습니다"}), 400
            
        if not timestamps or len(timestamps) == 0:
            return jsonify({"error": "타임스탬프가 누락되었거나 비어있습니다"}), 400
        
        video_id = video_path.split('/')[-1].split('.')[0]
        scenes = [(ts['start_time'], ts['end_time']) for ts in timestamps]
        
        if not scenes:
            return jsonify({"error": "타임스탬프 형식이 잘못되었습니다"}), 400
            
        stt_captions = get_stt_caption(video_path, scenes)
        
        if not stt_captions:
            return jsonify({"error": "STT 캡션 생성에 실패했습니다"}), 500
            
        res = []
        for i, caption_data in enumerate(stt_captions):
            res.append({
                'video_id': f"{video_id}_{i}",
                'stt_caption': caption_data['caption'],
                'timestamps': {
                    'start': caption_data['start_time'],
                    'end': caption_data['end_time']
                }
            })

        return jsonify({
            'video_path': video_path,
            'segments': res
        })
    
    except Exception as e:
        return jsonify({'error': f"처리 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route('/short_video', methods=['POST'])
def short_video():
    """
    지정된 구간의 비디오 STT 캡션을 생성합니다.
    ---
    tags:
      - STT Caption API
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            video_path:
              type: string
              description: 비디오 파일의 경로
            start:
              type: number
              description: 시작 시간(초)
            end:
              type: number
              description: 종료 시간(초)
    responses:
      200:
        description: STT 캡션 생성 성공
      400:
        description: 잘못된 요청
      500:
        description: 서버 오류
    """
    try:
        video_path = request.json.get('video_path')
        start = request.json.get('start')
        end = request.json.get('end')
        
        # 입력값 검증
        if not video_path:
            return jsonify({"error": '비디오 경로가 누락되었습니다'}), 400
            
        if start is None or end is None:
            return jsonify({"error": "시작 또는 종료 시간이 누락되었습니다"}), 400
            
        if start >= end:
            return jsonify({"error": "시작 시간이 종료 시간보다 크거나 같습니다"}), 400
            
        stt_captions = get_stt_caption(video_path, [(start, end)])
        
        if stt_captions:
            result = stt_captions[0]['caption']
        else:
            result = "음성이 감지되지 않았습니다"
            
        return jsonify({
            'result': result,
            'start': start,
            'end': end
        })
        
    except Exception as e:
        return jsonify({'error': f"처리 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """
    비디오 파일을 업로드하고 저장하는 API
    ---
    tags:
      - name: 비디오 업로드
        description: 비디오 파일 업로드 관련 API
    consumes:
      - multipart/form-data
    produces:
      - application/json
    parameters:
      - in: formData
        name: video
        type: file
        required: true
        description: 업로드할 비디오 파일
    responses:
      200:
        description: 파일 업로드 성공
      400:
        description: 잘못된 요청
      500:
        description: 서버 오류
    """
    try:
        if 'video' not in request.files:
            return jsonify({"error": "비디오 파일이 필요합니다"}), 400
            
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({"error": "선택된 파일이 없습니다"}), 400
            
        # 저장 디렉토리 설정 및 생성
        save_dir = '/data/ephemeral/home/data/'
        os.makedirs(save_dir, exist_ok=True)
        
        # 고유한 파일명 생성
        file_extension = os.path.splitext(video_file.filename)[1]
        filename = str(uuid.uuid4()) + file_extension
        file_path = os.path.join(save_dir, filename)
        
        video_file.save(file_path)
        
        return jsonify({
            "video_path": file_path,
            "message": "파일이 성공적으로 업로드되었습니다"
        })
        
    except Exception as e:
        return jsonify({"error": f"파일 업로드 중 오류가 발생했습니다: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30870)
