import json
import numpy as np
import torchvision
import librosa
from transformers import Qwen2AudioForConditionalGeneration, AutoProcessor

from flask import Flask, request, jsonify

from scene_detect import scene_detect
import os

CACHE_DIR = "json_cached"

# 모델과 프로세서 초기화
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-Audio-7B-Instruct")
model = Qwen2AudioForConditionalGeneration.from_pretrained("Qwen/Qwen2-Audio-7B-Instruct", device_map="auto", torch_dtype="auto")
model.tie_weights()

app = Flask(__name__)


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
    try:
        video_path = request.json.get('video_path')
        if not video_path:
            return jsonify({"error: missing video_path"}), 400
        
        video_id = video_path.split('/')[-1].split('.')[0]
        cache_file = os.path.join(CACHE_DIR, f"{video_id}.json")

        # 캐싱된 파일이 있는지 확인
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            return jsonify(cached_data)

        scenes = scene_detect(video_path)
        print(scenes)
        
        # 각 장면에 대한 오디오 캡션 생성
        audio_captions = get_audio_caption(video_path, scenes)
        
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

        with open(cache_file, 'w') as f:
            json.dump(response_data, f)

        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/short_video', methods=['POST'])
def short_video():
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



#change to available port
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30742)