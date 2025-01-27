import json
import numpy as np
import torchvision
import librosa
from transformers import Qwen2AudioForConditionalGeneration, AutoProcessor
from flask import Flask, request, jsonify
from flasgger import Swagger
from scene_detect import scene_detect
import os
import uuid
# 모델과 프로세서 초기화
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-Audio-7B-Instruct")
model = Qwen2AudioForConditionalGeneration.from_pretrained("Qwen/Qwen2-Audio-7B-Instruct", device_map="auto", torch_dtype="auto")
model.tie_weights()

app = Flask(__name__)
swagger = Swagger(app)

def sample_frames(vframes, num_frames):
    print('len vframe: ', len(vframes), 'num_frames: ', num_frames)
    frame_indice = np.linspace(int(num_frames/2), len(vframes) - int(num_frames/2), num_frames, dtype=int)
    print(frame_indice)
    video = vframes[frame_indice]
    video_list = []
    for i in range(len(video)):
        video_list.append(torchvision.transforms.functional.to_pil_image(video[i]))

    return video_list

def get_audio_caption(video_path, time_ranges):   
    # time_ranges는 [(start1, end1), (start2, end2), ...] 형태의 리스트
    
    all_responses = []
    
    # 대화 템플릿 설정
    conversation = [
    {
        "role": "system",
        "content": "You are an AI assistant specialized in extracting detailed information from audio data. Provide comprehensive descriptions of all audio elements, including background music, sound effects, environmental sounds, and emotional tones."
    },
    {
        "role": "user",
        "content": [
            {
                "type": "audio",
                "audio_url": video_path
            },
            {
                "type": "text",
                "text": "Extract all audio elements. Describe background music, its emotional tone, tempo, and possible genre. Detect sound effects, such as sirens, alarms, or footsteps."
            }
        ]
    },
    {
        "role": "user",
        "content": [
            {
                "type": "audio",
                "audio_url": video_path
            },
            {
                "type": "text",
                "text": "Identify all environmental sounds, such as traffic noise, animal sounds, or nature sounds, and explain their intensity and potential location."
            }
        ]
    },
    {
        "role": "user",
        "content": [
            {
                "type": "audio",
                "audio_url": video_path
            },
            {
                "type": "text",
                "text": "Detect any changes in audio dynamics, such as volume shifts or sudden silences, and explain their significance in the context of the audio."
            }
        ]
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Summarize all extracted audio information , including background music, sound effects, environmental sounds, and any notable audio patterns. Provide only important information. and do not repeat the same information. if there is no useful information, just say 'no information'"
            }
        ],
    }
    ]

    # 텍스트 처리
    text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
    
    for start_time, end_time in time_ranges:
        # 오디오 로드 및 처리
        audios = []
        for message in conversation:
            if isinstance(message["content"], list):
                for ele in message["content"]:
                    if ele["type"] == "audio":
                        # 지정된 시간 범위의 오디오 로드
                        audio, sr = librosa.load(ele['audio_url'], 
                                              sr=processor.feature_extractor.sampling_rate,
                                              offset=start_time,
                                              duration=end_time-start_time)
                        audios.append(audio)

        # 입력 처리
        inputs = processor(text=text, audios=audios, return_tensors="pt", padding=True, 
                          sampling_rate=processor.feature_extractor.sampling_rate)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        # 텍스트 생성
        generate_ids = model.generate(**inputs, max_length=2048)
        generate_ids = generate_ids[:, inputs["input_ids"].size(1):]

        # 결과 디코딩 및 반환
        response = processor.batch_decode(generate_ids, skip_special_tokens=True, 
                                        clean_up_tokenization_spaces=False)[0]
        
        all_responses.append({
            "start_time": start_time,
            "end_time": end_time,
            "caption": response
        })
    
    return all_responses

@app.route('/entire_video', methods=['POST'])
def entire_video():
    """
    전체 비디오의 오디오 캡션을 생성합니다.
    ---
    tags:
      - Audio Caption API
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
                    description: 시작 시간(초)
                  end:
                    type: number
                    description: 종료 시간(초)
    responses:
      200:
        description: 성공적으로 캡션이 생성됨
        schema:
          type: object
          properties:
            video_path:
              type: string
              description: 입력받은 비디오 파일 경로
            segments:
              type: array
              description: 구간별 오디오 캡션 정보
              items:
                type: object
                properties:
                  video_id:
                    type: string
                    description: 구간별 고유 ID
                  audio_caption:
                    type: string
                    description: 생성된 오디오 캡션 텍스트
                  timestamps:
                    type: object
                    description: 구간의 시작/종료 시간 정보
                    properties:
                      start:
                        type: number
                        description: 시작 시간(초)
                      end:
                        type: number
                        description: 종료 시간(초)
      400:
        description: 잘못된 요청
        schema:
          type: object
          properties:
            error:
              type: string
              description: 에러 메시지
      500:
        description: 서버 에러
        schema:
          type: object
          properties:
            error:
              type: string
              description: 에러 메시지
    """
    try:
        video_path = request.json.get('video_path')
        timestamps = request.json.get('timestamps')
        
        if not video_path:
            return jsonify({"error": "missing video_path"}), 400
            
        if not timestamps or len(timestamps) == 0:
            return jsonify({"error": "missing timestamps or empty timestamps list"}), 400
        
        video_id = video_path.split('/')[-1].split('.')[0]

        # timestamps 리스트를 이용해 오디오 캡션 생성
        scenes = [(ts['start_time'], ts['end_time']) for ts in timestamps]
        if not scenes:
            return jsonify({"error": "invalid timestamps format"}), 400
            
        audio_captions = get_audio_caption(video_path, scenes)
        
        if not audio_captions:
            return jsonify({"error": "failed to generate audio captions"}), 500
            
        res = []
        for i, caption_data in enumerate(audio_captions):
            res.append({
                'video_id': f"{video_id}_{i}",
                'audio_caption': caption_data['caption'],
                'timestamps': {
                    'start': caption_data['start_time'],
                    'end': caption_data['end_time']
                }
            })

        response_data = {
            'video_path': video_path,
            'segments': res
        }

        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/short_video', methods=['POST'])
def short_video():
    """
    지정된 구간의 비디오 오디오 캡션을 생성합니다.
    ---
    tags:
      - Audio Caption API
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
        description: 성공적으로 캡션이 생성됨
        schema:
          type: object
          properties:
            result:
              type: string
            start:
              type: number
            end:
              type: number
      400:
        description: 잘못된 요청
      500:
        description: 서버 에러
    """
    try:
        video_path = request.json.get('video_path')
        if not video_path:
            return jsonify({"error": 'missing video_path'}), 400
        start = request.json.get('start')
        end = request.json.get('end')
        
        if start is None or end is None:
            return jsonify({"error": "missing start or end time"}), 400
            
        # 단일 구간에 대한 오디오 캡션 생성
        audio_captions = get_audio_caption(video_path, [(start, end)])
        
        if audio_captions:
            result = audio_captions[0]['caption']
        else:
            result = "No audio information available"
            
        return jsonify({
            'result': result,
            'start': start,
            'end': end
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        description: 비디오 업로드 성공
        schema:
          type: object
          properties:
            video_path:
              type: string
              description: 저장된 비디오 파일 경로
              example: "/home/edddd/data/video.mp4"
      400:
        description: 잘못된 요청
        schema:
          type: object
          properties:
            error:
              type: string
              description: 에러 메시지
              example: "비디오 파일이 필요합니다"
      500:
        description: 서버 에러
        schema:
          type: object
          properties:
            error:
              type: string
              description: 에러 메시지
              example: "Internal server error"
    """
    try:
        if 'video' not in request.files:
            return jsonify({"error": "비디오 파일이 필요합니다"}), 400
            
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({"error": "선택된 파일이 없습니다"}), 400
            
        # 파일 저장 경로 설정
        save_dir = '/data/ephemeral/home/data/'
        os.makedirs(save_dir, exist_ok=True)
        
        # UUID를 사용하여 고유한 파일명 생성
        
        file_extension = os.path.splitext(video_file.filename)[1]
        filename = str(uuid.uuid4()) + file_extension
        file_path = os.path.join(save_dir, filename)
        
        # 파일 저장
        video_file.save(file_path)
        
        return jsonify({
            "video_path": file_path
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500



#change to available port
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30076)