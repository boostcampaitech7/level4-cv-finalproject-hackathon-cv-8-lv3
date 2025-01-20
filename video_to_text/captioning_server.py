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


def sample_frames(vframes, num_frames):
    print('len vframe: ', len(vframes), 'num_frames: ', num_frames)
    frame_indice = np.linspace(int(num_frames/2), len(vframes) - int(num_frames/2), num_frames, dtype=int)
    print(frame_indice)
    video = vframes[frame_indice]
    video_list = []
    for i in range(len(video)):
        video_list.append(torchvision.transforms.functional.to_pil_image(video[i]))

    return video_list


def generate(messages, images):
    # img_bytes_list = [base64.b64decode(image.encode("utf-8")) for image in images]
    # images = [Image.open(BytesIO(img_bytes)) for img_bytes in img_bytes_list]

    image_sizes = [image.size for image in images]
    # Similar operation in model_worker.py
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
    # print(inputs)

    with torch.inference_mode():
        generated_text = model.generate(
            **inputs,
            image_size=[image_sizes],
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            temperature=0.05,
            do_sample=False,
            max_new_tokens=1024,
            top_p=None,
            num_beams=1,
        )

    outputs = (
        tokenizer.decode(generated_text[0], skip_special_tokens=True)
        .split("<|end|>")[0]
        .strip()
    )
    return outputs



def predict(vframes, num_frames=8):
    # vframes, _, _ = torchvision.io.read_video(
    #     filename=video_file, pts_unit="sec", output_format="TCHW",
    # )

    total_frames = len(vframes)
    images = sample_frames(vframes, num_frames)
    print('image length :', len(images)) # 8 Frame을 sampling 해서 출력함
    prompt = ""
    prompt = prompt + "<image>\n"
    # prompt = prompt + "What's the main gist of the video ?"
    prompt = prompt + "For each scene in this video, create a caption that describes the scene. Voice is not considered at this time. Places each caption in an object sent to set_timecodes along with the video caption's timecode. And it only outputs in json format." #"Please describe the primary object or subject in the video, capturing their attributes, actions, positions, and movements."
    messages = [{"role": "user", "content": prompt}]
    return generate(messages, images)




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
                'captions':result,
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
    try:
        video_path = request.json.get('video_path')
        if not video_path:
            return jsonify({"error": 'missing video_path'}), 400
        start = request.json.get('start')
        print(start)
        # print(start.dtype)
        end = request.json.get('end')
        # 이부분 float나 int인지 체크 코드 
        # if not start:
        #     return jsonify({"error": "missing start."}), 400
        # if not end:
        #     return jsonify({"error": "missing end."}), 400
        
        vframes, _, _ = torchvision.io.read_video(
            filename=video_path, pts_unit='sec', output_format='TCHW', 
            start_pts=start, end_pts=end
        )
        
        result = predict(vframes)
        
        
        return jsonify({'result':result, 'start': start, 'end': end})
    except Exception as e:
        return jsonify({'error' : str(e)}), 500



#change to available port
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30742)