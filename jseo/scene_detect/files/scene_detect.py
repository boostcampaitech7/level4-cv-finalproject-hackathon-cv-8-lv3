from scenedetect import VideoManager
from scenedetect import SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg

# 비디오 파일 경로 설정
video_path = '/data/ephemeral/home/jseo/scene_detect/Thanos_eng_sub.mp4'

# 비디오 매니저 및 장면 매니저 초기화
video_manager = VideoManager([video_path])
scene_manager = SceneManager()

# ContentDetector 추가 (콘텐츠 기반 장면 감지)
scene_manager.add_detector(ContentDetector(threshold=50.0))

# 비디오 매니저와 장면 매니저 준비
video_manager.set_downscale_factor()
video_manager.start()

# 장면 감지 수행
scene_manager.detect_scenes(frame_source=video_manager)
scene_list = scene_manager.get_scene_list()

print(f"Detected {len(scene_list)} scenes.")

# 각 장면의 시작과 끝 시간 출력
for i, scene in enumerate(scene_list):
    start_time, end_time = scene
    print(f"Scene {i+1}: Start {start_time.get_timecode()} End {end_time.get_timecode()}")

# # 감지된 장면별로 비디오 자르기 (ffmpeg 사용)
# try:
#     split_video_ffmpeg(video_path, scene_list, output_dir='/data/ephemeral/home/jseo/scene_detect/split_video', show_progress=True)
# except Exception as e:
#     print(f"Error during split: {e}")



# 비디오 매니저 해제
video_manager.release()
