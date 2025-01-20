from scenedetect import VideoManager
from scenedetect import SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg

def scene_detect(video_path):
    """
    Detect scenes in a video and return their start and end times in seconds.

    Args:
        video_path (str): Path to the video file.

    Returns:
        list: A list of tuples containing start and end times of each scene in seconds.
    """
    # Initialize VideoManager and SceneManager
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()

    # Add ContentDetector for scene detection
    scene_manager.add_detector(ContentDetector(threshold=50.0))

    # Prepare and start VideoManager
    video_manager.set_downscale_factor()
    video_manager.start()

    # Perform scene detection
    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list()

    # Release the VideoManager
    video_manager.release()

    # Extract start and end times of each scene in seconds
    scene_times = [(scene[0].get_seconds(), scene[1].get_seconds()) for scene in scene_list]

    return scene_times

# Example usage
# if __name__ == "__main__":
#     video_path = '/data/ephemeral/home/jseo/scene_detect/Thanos_eng_sub.mp4'
#     scenes = scene_detect(video_path)

#     print(f"Detected {len(scenes)} scenes.")
#     for i, (start, end) in enumerate(scenes):
#         print(f"Scene {i+1}: Start {start:.2f} seconds End {end:.2f} seconds")
    
#     print(scenes)
