from flask import Flask, request, jsonify
import os
import json
from video_to_text.scene_detect import scene_detect
import requests

app = Flask(__name__)

def check_video_exists(video_id):
    try:
        if not video_id:
            return False
            
        # DB에서 비디오 ID 확인
        video = Video.query.get(video_id)
        
        return video is not None
            
    except Exception as e:
        print(f"비디오 확인 중 오류 발생: {str(e)}")
        return False
    


@app.route('/process_video_with_timestamps', methods=['POST'])
def process_video_with_timestamps():
    """
    비디오 파일(또는 video_id)과 타임스탬프를 받아서 오디오 캡션을 생성하는 엔드포인트
    
    Request body (multipart/form-data):
    - video: 비디오 파일 (선택적)
    - video_id: 서버에 있는 비디오의 ID (선택적)
    - timestamps: 타임스탬프 JSON 문자열
        [
            {
                "start": float,  # 시작 시간(초)
                "end": float     # 종료 시간(초)
            }
        ]
    """
    # 비디오 파일 또는 video_id 확인
    video_file = request.files.get('video')
    video_id = request.form.get('video_id')
    
    if not video_file and not video_id:
        return jsonify({"error": "비디오 파일 또는 video_id가 필요합니다"}), 400

    # 타임스탬프 확인 
    if 'timestamps' not in request.form:
        return jsonify({"error": "timestamps가 필요합니다"}), 400

    try:
        timestamps = json.loads(request.form['timestamps'])
    except json.JSONDecodeError:
        return jsonify({"error": "timestamps JSON 형식이 잘못되었습니다"}), 400

    if not timestamps:
        return jsonify({"error": "timestamps가 비어있습니다"}), 400

    try:
        if video_file:
            # 새로운 비디오 파일이 업로드된 경우
            # 비디오 파일 저장 API 호출
            try:
                response = requests.post("http://10.28.224.194:30076/upload_video", files={"video": video_file})
                response.raise_for_status()
                video_path = response.json()["video_path"]
            except Exception as e:
                return jsonify({"error": f"1번 서버 비디오 파일 저장 실패: {str(e)}"}), 500
            
            try:
                response = requests.post("http://10.28.224.34:30742/upload_video", files={"video": video_file})
                response.raise_for_status()
                video_path = response.json()["video_path"]
            except Exception as e:
                return jsonify({"error": f"2번 서버 비디오 파일 저장 실패: {str(e)}"}), 500
            
            try:
                response = requests.post("http://10.28.224.75:30822/upload_video", files={"video": video_file})
                response.raise_for_status()
                video_path = response.json()["video_path"]
            except Exception as e:
                return jsonify({"error": f"4번 서버 비디오 파일 저장 실패: {str(e)}"}), 500
        else:
            # video_id를 사용하는 경우
            video_path = f"/data/ephemeral/home/movie_clips/{video_id}.mp4"

        # 장면 전환 감지로 타임스탬프 생성
        try:
            timestamps = scene_detect(video_path)
            formatted_timestamps = [{"start_time": start, "end_time": end} for start, end in timestamps]
        except Exception as e:
            return jsonify({"error": f"장면 전환 감지 실패: {str(e)}"}), 500

        # audio : entire_video API 호출
        try:
            audio_response = requests.post(
                "http://10.28.224.194:30076/entire_video",
                json={
                    "video_path": video_path,
                    "timestamps": formatted_timestamps
                }
            )
            audio_response.raise_for_status()
            return jsonify(audio_response.json())
        except Exception as e:
            return jsonify({"error": f"오디오 캡션 생성 실패: {str(e)}"}), 500
        
        # video : entire_video API 호출
        try:
            video_response = requests.post(
                "http://10.28.224.34:30742/entire_video",
                json={
                    "video_path": video_path,
                    "timestamps": formatted_timestamps
                }
            )
            video_response.raise_for_status()
            return jsonify(video_response.json())
        except Exception as e:
            return jsonify({"error": f"비디오 캡션 생성 실패: {str(e)}"}), 500
        
        # stt : entire_video API 호출
        try:
            stt_response = requests.post(
                "http://127.0.0.1:30076/entire_video",
                json={
                    "video_path": video_path,
                    "timestamps": formatted_timestamps
                }
            )
            stt_response.raise_for_status()
            return jsonify(stt_response.json())
        except Exception as e:
            return jsonify({"error": f"stt 캡션 생성 실패: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"처리 중 오류 발생: {str(e)}"}), 500





if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
