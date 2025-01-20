from scenedetect import VideoManager
from scenedetect import SceneManager
from scenedetect.detectors import ContentDetector
from moviepy import *

# 비디오 파일 경로 설정
video_path = '/data/ephemeral/home/jseo/scene_detect/The_Hunter.mp4'
output_dir = '/data/ephemeral/home/jseo/scene_detect/split_video/'

# 비디오 매니저 및 장면 매니저 초기화
video_manager = VideoManager([video_path])
scene_manager = SceneManager()

# ContentDetector 추가 (콘텐츠 기반 장면 감지)
scene_manager.add_detector(ContentDetector(threshold=66.0))

# 비디오 매니저와 장면 매니저 준비
video_manager.set_downscale_factor()
video_manager.start()

# 장면 감지 수행
scene_manager.detect_scenes(frame_source=video_manager)
scene_list = scene_manager.get_scene_list()

print(f"Detected {len(scene_list)} scenes.")

# 각 장면의 시작과 끝 시간 출력 및 저장
for i, scene in enumerate(scene_list):
    start_time, end_time = scene
    print(f"Scene {i+1}: Start {start_time.get_timecode()} End {end_time.get_timecode()}")

    # moviepy를 사용하여 비디오를 자르고 저장
    try:
        # VideoFileClip 열기
        with VideoFileClip(video_path) as clip:
            # 비디오를 장면별로 자르기
            scene_clip = clip.subclipped(start_time.get_seconds(), end_time.get_seconds())
            output_file = f"{output_dir}scene_{i+1}.mp4"
            # 비디오 파일 저장
            scene_clip.write_videofile(output_file, codec='libx264', audio_codec='aac')
    except Exception as e:
        print(f"Error processing scene {i+1}: {e}")

# 비디오 매니저 해제
video_manager.release()
