import json
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

def get_stt_caption(video_path: str) -> list:
    """
    비디오의 STT 캡션을 생성합니다.
    
    Args:
        video_path (str): 비디오 파일 경로
        
    Returns:
        list: STT 캡션 정보를 담은 리스트
    """
    try:
        audio = load_audio(video_path)
        # 전체 오디오 길이(초)를 계산
        sample_rate = 16000  # whisper의 기본 sample rate
        duration = len(audio) / sample_rate
        
        # STT 수행
        result = model.transcribe(
            audio=audio,
            logprob_threshold=-2.0,
            no_speech_threshold=0.95
        )
        print(f"디버그 - STT 결과: {result}")  # 디버그용 출력
        
        # segments 배열 생성
        segments = []
        
        # result의 segments에서 필요한 정보 추출
        for segment in result["segments"]:
            segments.append({
                "start_time": segment["start"],
                "end_time": segment["end"], 
                "caption": segment["text"]
            })
            
        return segments
            
    except Exception as e:
        print(f"STT 처리 중 오류 발생: {str(e)}")
        return []

@app.route('/save_captions', methods=['POST'])
def save_captions():
    """
    비디오의 STT 캡션을 JSON 파일로 저장합니다.
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
    responses:
      200:
        description: 캡션 저장 성공
      400:
        description: 잘못된 요청
      500:
        description: 서버 오류
    """
    try:
        video_path = request.json.get('video_path')
        
        # 입력값 검증
        if not video_path:
            return jsonify({"error": "비디오 경로가 필요합니다"}), 400
            
        # 비디오 ID 생성
        video_id = video_path.split('/')[-1].split('.')[0]
            
        # STT 캡션 생성
        stt_captions = get_stt_caption(video_path)
        
        if not stt_captions:
            return jsonify({"error": "STT 캡션 생성에 실패했습니다"}), 500
            
        # 캡션만 추출
        captions = []
        for caption_data in stt_captions:
            captions.append(caption_data['caption'])
            
        # JSON 데이터 생성
        json_data = {
            'video_id': video_id,
            'captions': captions
        }
        
        # JSON 파일 저장 경로
        save_dir = '/data/ephemeral/home/captions/'
        os.makedirs(save_dir, exist_ok=True)
        json_path = os.path.join(save_dir, f'{video_id}_captions.json')
        
        # JSON 파일 저장
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
            
        return jsonify({
            'message': '캡션이 성공적으로 저장되었습니다',
            'file_path': json_path
        })
        
    except Exception as e:
        return jsonify({'error': f"캡션 저장 중 오류가 발생했습니다: {str(e)}"}), 500

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
        
        # 입력값 검증
        if not video_path:
            return jsonify({"error": "비디오 경로가 누락되었습니다"}), 400
            
        video_id = video_path.split('/')[-1].split('.')[0]
            
        stt_captions = get_stt_caption(video_path)
        
        if not stt_captions:
            return jsonify({"error": "STT 캡션 생성에 실패했습니다"}), 500
            
        res = []
        for i, caption_data in enumerate(stt_captions):
            res.append({
                'video_id': f"{video_id}_{i}",
                'stt_caption': caption_data['caption'],
                'timestamp': {
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
            
        stt_captions = get_stt_caption(video_path)
        
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
            
        # 허용된 비디오 확장자 검사
        allowed_extensions = {'.mp4', '.avi', '.mov', '.wmv'}
        file_extension = os.path.splitext(video_file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            return jsonify({"error": "지원하지 않는 비디오 형식입니다. mp4, avi, mov, wmv 파일만 허용됩니다."}), 400
            
        # 저장 디렉토리 설정 및 생성
        save_dir = '/data/ephemeral/home/new-data/'
        os.makedirs(save_dir, exist_ok=True)
        
        # 고유한 파일명 생성 (확장자 중복 제거)
        filename = str(uuid.uuid4()) + file_extension
        file_path = os.path.join(save_dir, filename)
        
        # 파일 저장 전 용량 체크
        video_file.seek(0, 2)  # 파일 끝으로 이동
        file_size = video_file.tell()  # 현재 위치(파일 크기) 확인
        video_file.seek(0)  # 파일 포인터를 다시 처음으로
        
        # 파일 크기 제한 (예: 500MB)
        if file_size > 500 * 1024 * 1024:
            return jsonify({"error": "파일 크기가 500MB를 초과합니다"}), 400
            
        video_file.save(file_path)
        
        # 파일이 실제로 저장되었는지 확인
        if not os.path.exists(file_path):
            return jsonify({"error": "파일 저장에 실패했습니다"}), 500
            
        return jsonify({
            "video_path": file_path,
            "message": "파일이 성공적으로 업로드되었습니다",
            "file_size": f"{file_size / (1024 * 1024):.2f}MB"
        })
        
    except Exception as e:
        # 에러 발생 시 상세 로그 기록
        print(f"파일 업로드 에러: {str(e)}")
        return jsonify({"error": f"파일 업로드 중 오류가 발생했습니다: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30076)
