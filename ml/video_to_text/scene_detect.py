from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

def scene_detect(video_path):
    """
    Detect scenes in the video and return the start and end times of each scene in seconds as floats.
    If no scenes are detected, returns a single scene covering the entire video.
    
    Args:
        video_path (str): Path to the video file.
        
    Returns:
        list: A list of tuples containing the start and end times of each scene in seconds.
              e.g. [(0.0, 150.65)]
    """
    # Initialize VideoManager and SceneManager
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    
    # Add a ContentDetector (adjust the threshold as needed)
    scene_manager.add_detector(ContentDetector(threshold=50.0))
    
    # Optionally apply downscale factor for faster processing
    video_manager.set_downscale_factor()
    video_manager.start()
    
    # Retrieve the total duration of the video
    # (Depending on the version, this may return a FrameTimecode object or a tuple)
    total_duration = video_manager.get_duration()
    
    # Perform scene detection
    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list()
    
    # Release VideoManager resources
    video_manager.release()
    
    # If no scenes are detected, return the entire video as a single scene
    if not scene_list:
        # If total_duration is a tuple, extract the seconds from the first element
        if isinstance(total_duration, tuple):
            # Use get_seconds() if the first element is a FrameTimecode object
            if hasattr(total_duration[0], "get_seconds"):
                total_seconds = total_duration[0].get_seconds()
            else:
                total_seconds = total_duration[0]
        else:
            total_seconds = total_duration.get_seconds() if hasattr(total_duration, "get_seconds") else total_duration

        scene_times = [(0.0, total_seconds)]
    else:
        # Convert the start and end times of each detected scene to seconds as floats
        scene_times = [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]
    
    return scene_times

# Example usage
if __name__ == "__main__":
    video_path = '/data/ephemeral/home/data/03NoI9KiZOk.mp4'
    scenes = scene_detect(video_path)
    print("Scene times (in seconds):", scenes)
