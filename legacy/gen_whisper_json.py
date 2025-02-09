import os
import json

import numpy as np

from whisper import load_model
from whisper.audio import load_audio

from scene_detect import scene_detect, scene_detect_frame

def gen_clip_list(
    video_array: np.array,
    scenes: list
) -> list:
    total_frame_num = scenes[-1][-1]
    video_length = len(video_array)
    frame_ratio = video_length / total_frame_num

    clip_list = [] 
    for start_frame, end_frame in scenes:
        start_idx = int(start_frame * frame_ratio)
        end_idx = int(end_frame * frame_ratio)
        clip_list.append(video_array[start_idx:end_idx])
    
    return clip_list

def gen_stt_segments(
    clip_list: list, 
    timestamps: list,
    video_id: str,
) -> None:
    model = load_model("turbo", device="cuda", download_root=None)
    clip_text_list = []
    for clip in clip_list:
        result = model.transcribe(
            audio=clip,
            logprob_threshold=-2.0,
            no_speech_threshold=0.95
        )
        clip_text_list.append(result["text"])
    
    segments = []
    for i, (clip_text, timestamp) in enumerate(zip(clip_text_list, timestamps)):
        segments.append({
            "video_id": f"{video_id}_{i}",
            "captions": clip_text,
            "timestamp": {
                "start": timestamp[0],
                "end": timestamp[1]
            }
        })

    return segments


def stt(
    video_path: str,
    output_dir: str,
) -> None:
    video_array = load_audio(video_path)
    video_id = video_path.split('/')[-1].split('.')[0] 

    scenes = scene_detect_frame(video_path)
    timestamps = scene_detect(video_path)

    clip_list = gen_clip_list(
        video_array=video_array,
        scenes=scenes
    )

    segments = gen_stt_segments(
        clip_list=clip_list,
        timestamps=timestamps,
        video_id=video_id
    )

    stt_dict = {
       "video_path": video_path,
       "segments": segments
    }

    output_file = os.path.join(output_dir, f'{video_id}.json')
    with open(output_file, "w") as f:
        json.dump(stt_dict, f, indent=4)
        

if __name__ == "__main__":
    video_path = "/data/ephemeral/home/movie_clips/kRZDSvsdZ8A.mp4"
    output_dir = "./whisper_json"
    stt(
        video_path=video_path, 
        output_dir=output_dir
    )