from transformers import AutoModelForVision2Seq, AutoTokenizer, AutoImageProcessor, LogitsProcessor
import torch
import json
import numpy as np
import torchvision
import torchvision.io
import math
from flask import Flask, request, jsonify
from scene_detect import scene_detect
import os
from flasgger import Swagger
import logging
import hashlib

CACHE_DIR = "json_cached"
model_name_or_path = "Salesforce/xgen-mm-vid-phi3-mini-r-v1.5-128tokens-8frames"
model = AutoModelForVision2Seq.from_pretrained(model_name_or_path, trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=True, use_fast=False, legacy=False)
image_processor = AutoImageProcessor.from_pretrained(model_name_or_path, trust_remote_code=True)
tokenizer = model.update_special_tokens(tokenizer)

model = model.to('cuda')
model.eval()
tokenizer.padding_side = "left"
tokenizer.eos_token = "<|end|>"

app = Flask(__name__)
swagger = Swagger(app)

def get_file_hash(video_file):
    """파일 내용을 SHA-256 해시로 변환"""
    hasher = hashlib.sha256()
    video_file.seek(0)  # 파일 포인터를 처음으로 이동
    while chunk := video_file.read(8192):  # 8KB씩 읽기
        hasher.update(chunk)
    video_file.seek(0)  # 다시 처음으로 이동 (중요!)
    return hasher.hexdigest()

def sample_frames(vframes, num_frames):
    print('len vframe: ', len(vframes), 'num_frames: ', num_frames)
    if len(vframes) < num_frames:
        frame_indice = [i for i in range(len(vframes))]
    else:
        frame_indice = np.linspace(int(num_frames/2), len(vframes) - int(num_frames/2), num_frames, dtype=int)
    print(frame_indice)
    video = vframes[frame_indice]
    video_list = []
    for i in range(len(video)):
        video_list.append(torchvision.transforms.functional.to_pil_image(video[i]))

    return video_list

def generate(messages, images):
    image_sizes = [image.size for image in images]
    image_tensor = [image_processor([img])["pixel_values"].to(model.device, dtype=torch.float32) for img in images]

    image_tensor = torch.stack(image_tensor, dim=1)
    image_tensor = image_tensor.squeeze(2)
    inputs = {"pixel_values": image_tensor}

    full_conv = "<|system|>\nA chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.<|end|>\n"
    for msg in messages:
        msg_str = "<|{role}|>\n{content}<|end|>\n".format(
            role=msg["role"], content=msg["content"]
        )
        full_conv += msg_str

    full_conv += "<|assistant|>\n"
    print(full_conv)
    language_inputs = tokenizer([full_conv], return_tensors="pt")
    for name, value in language_inputs.items():
        language_inputs[name] = value.to(model.device)
    inputs.update(language_inputs)

    with torch.inference_mode():
        generated_text = model.generate(
            **inputs,
            image_size=[image_sizes],
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            temperature=1.0,
            do_sample=False,
            max_new_tokens=1024,
            top_p=0.9,
            num_beams=5,
            no_repeat_ngram_size=3,
        )

    outputs = (
        tokenizer.decode(generated_text[0], skip_special_tokens=True)
        .split("<|end|>")[0]
        .strip()
    )
    return outputs

def predict(vframes, num_frames=8):
    total_frames = len(vframes)
    images = sample_frames(vframes, num_frames)
    print('image length :', len(images))
    prompt = ""
    prompt = prompt + "<image>\n"
    prompt = prompt + "For each scene in this video, create a caption that describes the scene. Voice is not considered at this time."
    messages = [{"role": "user", "content": prompt}]
    return generate(messages, images)

@app.route('/entire_video', methods=['POST'])
def entire_video():
    """
    전체 비디오를 분석하여 각 장면별 캡션을 생성하는 API
    ---
    tags:
      - name: 비디오 분석
        description: 비디오 분석 관련 API
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            video_path:
              type: string
              description: 분석할 비디오 파일 경로
    responses:
      200:
        description: 비디오 분석 성공
        schema:
          type: object
          properties:
            video_path:
              type: string
            segments:
              type: array
              items:
                type: object
                properties:
                  video_id:
                    type: string
                  video_caption_en:
                    type: string
                  timestamps:
                    type: object
                    properties:
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
            return jsonify({"error: missing video_path"}), 400
        
        video_id = video_path.split('/')[-1].split('.')[0]
        cache_file = os.path.join(CACHE_DIR, f"{video_id}.json")

        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            return jsonify(cached_data)

        res = []
        scenes = scene_detect(video_path)
        print(scenes)
        for i, (start, end) in enumerate(scenes):
            vframes, _, _ = torchvision.io.read_video(
                filename=video_path, pts_unit='sec', output_format='TCHW', 
                start_pts=start, end_pts=end
            )
            result = predict(vframes)
            res.append({
                'video_id': f"{video_id}_{i}",
                'video_caption_en':result,
                'timestamps':{
                    'start': start,
                    'end': end
                } 
            })
        
        response_data = {
                'video_path':video_path,
                'segments':res
            }
        
        with open(cache_file, 'w') as f:
            json.dump(response_data, f)

        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error' : str(e)}), 500

@app.route('/short_video', methods=['POST'])
def short_video():
    """
    특정 구간의 비디오를 분석하여 캡션을 생성하는 API
    ---
    tags:
      - name: 비디오 분석
        description: 비디오 분석 관련 API
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            video_path:
              type: string
              description: 분석할 비디오 파일 경로
            start:
              type: number
              description: 시작 시간(초)
            end:
              type: number
              description: 종료 시간(초)
    responses:
      200:
        description: 비디오 분석 성공
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
        print(start)
        end = request.json.get('end')
        
        vframes, _, _ = torchvision.io.read_video(
            filename=video_path, pts_unit='sec', output_format='TCHW', 
            start_pts=start, end_pts=end
        )
        
        result = predict(vframes)
        
        return jsonify({'result':result, 'start': start, 'end': end})
    except Exception as e:
        return jsonify({'error' : str(e)}), 500


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """
    비디오 파일을 업로드하고 저장하는 API
    """
    try:
        logger.info("📢 파일 업로드 요청 수신됨")

        if 'video' not in request.files:
            logger.error("❌ 비디오 파일이 요청에 없음")
            return jsonify({"error": "비디오 파일이 필요합니다"}), 400

        video_file = request.files['video']
        filename = request.form.get('file_name')
        logger.info(f"전달 받은 filename: ${filename}")
        if video_file.filename == '':
            logger.error("❌ 선택된 파일이 없음")
            return jsonify({"error": "선택된 파일이 없습니다"}), 400

        logger.info(f"✅ 업로드된 파일명: {video_file.filename}")

        # 저장 디렉토리 확인
        save_dir = '/data/ephemeral/home/new-data/'
        os.makedirs(save_dir, exist_ok=True)

        file_extension = os.path.splitext(video_file.filename)[1]
        
        if not filename:
          logger.info('전달받은 filename이 없습니다.')
          filename = str(get_file_hash(video_file)) + file_extension
        elif not filename.endswith(file_extension):
          filename += file_extension
          
        file_path = os.path.join(save_dir, filename)

        logger.info(f"💾 파일 저장 경로: {file_path}")

        video_file.seek(0)
        video_file.save(file_path)
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
          os.remove(file_path)
          return jsonify({"error": "파일이 비어있습니다. 다시 업로드 해주세요."})

        logger.info("✅ 파일 저장 완료")

        return jsonify({
            "video_path": file_path,
            "message": "파일이 성공적으로 업로드되었습니다"
        })

    except Exception as e:
        logger.error(f"❌ 파일 업로드 중 오류 발생: {str(e)}")
        return jsonify({"error": f"파일 업로드 중 오류가 발생했습니다: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30742)