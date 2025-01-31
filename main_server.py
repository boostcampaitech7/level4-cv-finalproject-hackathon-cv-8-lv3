from flask import Flask, request, jsonify
import os
import json
from video_to_text.scene_detect import scene_detect
import requests
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

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
    비디오 파일과 타임스탬프를 받아서 오디오/비디오/STT 캡션을 생성하는 API
    ---
    tags:
      - 비디오 처리
    consumes:
      - multipart/form-data
    parameters:
      - name: video
        in: formData
        type: file
        required: false
        description: 처리할 비디오 파일
      - name: video_id
        in: formData
        type: string
        required: false
        description: 서버에 저장된 비디오의 고유 ID
      - name: timestamps
        in: formData
        type: string
        required: true
        description: |
          처리할 구간의 시작/종료 시간이 담긴 JSON 배열
          예시:
          [
              {
                  "start": 0.0,  # 시작 시간(초)
                  "end": 10.5    # 종료 시간(초) 
              }
          ]
    responses:
      200:
        description: 캡션 생성 성공
        schema:
          type: object
          properties:
            segments:
              type: array
              description: 각 구간별 캡션 정보
              items:
                type: object
                properties:
                  timestamps:
                    type: object
                    description: 구간의 시작/종료 시간
                    properties:
                      start_time: 
                        type: number
                        description: 시작 시간(초)
                      end_time:
                        type: number
                        description: 종료 시간(초)
                  video_id:
                    type: string
                    description: 비디오 고유 ID
                  audio_caption:
                    type: string
                    description: 오디오 기반 캡션
                  video_caption:
                    type: string
                    description: 비디오 기반 캡션
                  stt_caption:
                    type: string
                    description: 음성인식(STT) 기반 캡션
      400:
        description: 잘못된 요청
        schema:
          type: object
          properties:
            error:
              type: string
              description: 오류 메시지
              example: "비디오 파일 또는 video_id가 필요합니다"
      500:
        description: 서버 내부 오류
        schema:
          type: object
          properties:
            error:
              type: string
              description: 오류 메시지
              example: "서버 처리 중 오류가 발생했습니다"
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
                print("1번 서버 비디오 파일 저장 성공")
            except Exception as e:
                return jsonify({"error": f"1번 서버 비디오 파일 저장 실패: {str(e)}"}), 500
            
            try:
                response = requests.post("http://10.28.224.34:30742/upload_video", files={"video": video_file})
                response.raise_for_status()
                video_path = response.json()["video_path"]
                print("2번 서버 비디오 파일 저장 성공")
            except Exception as e:
                return jsonify({"error": f"2번 서버 비디오 파일 저장 실패: {str(e)}"}), 500
            
            try:
                response = requests.post("http://10.28.224.75:30870/upload_video", files={"video": video_file})
                response.raise_for_status()
                video_path = response.json()["video_path"]
                print("4번 서버 비디오 파일 저장 성공")
            except Exception as e:
                return jsonify({"error": f"4번 서버 비디오 파일 저장 실패: {str(e)}"}), 500
        else:
            # video_id를 사용하는 경우
            video_path = f"/data/ephemeral/home/movie_clips/{video_id}.mp4"

        # 장면 전환 감지로 타임스탬프 생성
        try:
            timestamps = scene_detect(video_path)
            formatted_timestamps = [{"start_time": start, "end_time": end} for start, end in timestamps]
            print(timestamps)
        except Exception as e:
            return jsonify({"error": f"장면 전환 감지 실패: {str(e)}"}), 500

        # 모든 API 호출을 병렬로 실행
        try:
            # audio, video, stt API 호출
            audio_output = requests.post(
                "http://10.28.224.194:30076/entire_video",
                json={
                    "video_path": video_path,
                    "timestamps": formatted_timestamps
                }
            )
            video_output = requests.post(
                "http://10.28.224.34:30742/entire_video",
                json={
                    "video_path": video_path,
                    "timestamps": formatted_timestamps
                }
            )
            stt_output = requests.post(
                "http://10.28.224.75:30870/entire_video",
                json={
                    "video_path": video_path,
                    "timestamps": formatted_timestamps
                }
            )

            # 모든 응답을 기다림
            audio_response = audio_output
            video_response = video_output
            stt_response = stt_output

            # 각 응답의 상태 확인
            try:
                audio_response.raise_for_status()
            except Exception as e:
                return jsonify({"error": f"오디오 API 호출 실패: {str(e)}"}), 500
                
            try:
                video_response.raise_for_status()
            except Exception as e:
                return jsonify({"error": f"비디오 API 호출 실패: {str(e)}"}), 500
                
            try:
                stt_response.raise_for_status()
            except Exception as e:
                return jsonify({"error": f"STT API 호출 실패: {str(e)}"}), 500

            # 결과 취합
            audio_data = audio_response.json()["segments"]
            video_data = video_response.json()["segments"]
            stt_data = stt_response.json()["segments"]

            # 타임스탬프별로 결과 통합
            combined_segments = []
            for audio_seg, video_seg, stt_seg in zip(audio_data, video_data, stt_data):
                combined_segment = {
                    "timestamps": {
                        "start_time": audio_seg["timestamps"]["start"],
                        "end_time": audio_seg["timestamps"]["end"]
                    },
                    "video_id": audio_seg["video_id"],
                    "audio_caption": audio_seg["audio_caption"],
                    "video_caption": video_seg["captions"],
                    "stt_caption": stt_seg["stt_caption"]
                }
                combined_segments.append(combined_segment)

            return jsonify({"segments": combined_segments})

        except Exception as e:
            return jsonify({"error": f"API 호출 중 알 수 없는 오류 발생: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"처리 중 오류 발생: {str(e)}"}), 500





if __name__ == "__main__":
    app.run(host='0.0.0.0', port=30862, debug=True)
