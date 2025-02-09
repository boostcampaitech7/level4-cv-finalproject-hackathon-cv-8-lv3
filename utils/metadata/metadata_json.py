import json
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.metadata.meta_data import fetch_movie_info, run_with_timeout

#서버에서 절대 경로로 수정하기
def process_movie_data(json_data: dict, cache_folder: str = '/data/ephemeral/home/level4-cv-finalproject-hackathon-cv-8-lv3/utils/metadata/temp', timeout: int = 30):
    """
    This function processes a given JSON object containing movie data.
    It saves the JSON data as a temporary file, retrieves movie information
    from the TMDB API using the file path, and stores the extracted metadata as a JSON file.
    
    :param json_data: Dictionary containing movie-related data, including video file path.
    :param cache_folder: Directory where the temporary JSON file will be stored before processing.
    :param timeout: Maximum time allowed (in seconds) for the API request before timing out.
    """
    output_folder = '/data/ephemeral/home/level4-cv-finalproject-hackathon-cv-8-lv3/utils/metadata/json_metadata'
    api_key = API_KEY = 'ff315049f0603ced165f84b648338838'
    try:
        # Ensure necessary folders exist
        os.makedirs(cache_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
        
        # Extract video title from the JSON data
        video_filename = os.path.basename(json_data.get("video_path", "unknown"))
        video_title = os.path.splitext(video_filename)[0]
        
        # Save JSON data to a temporary file
        temp_filename = "temp_movie_data.json"
        temp_filepath = os.path.join(cache_folder, temp_filename)
        with open(temp_filepath, "w", encoding="utf-8") as temp_file:
            json.dump(json_data, temp_file, indent=4, ensure_ascii=False)
        # Fetch movie information with timeout protection
        movie_title, movie_year, cast, crew = run_with_timeout(fetch_movie_info, timeout, temp_filepath, api_key)
        
        # Prepare JSON data
        movie_data = {
            "title": movie_title,
            "year": movie_year,
            "cast": cast,
            "crew": crew
        }
        print(movie_data)
        # Define output filename
        output_filename = f"{video_title}_meta_data.json"
        output_filepath = os.path.join(output_folder, output_filename)
        
        # Save movie information to output JSON file
        with open(output_filepath, "w", encoding="utf-8") as output_file:
            json.dump(movie_data, output_file, indent=4, ensure_ascii=False)
        
        # Optionally, remove the temporary file
        os.remove(temp_filepath)
        
        print(f"Saved metadata: {output_filepath}")
        return output_filepath
        
        
    except TimeoutError:
        print("Timeout occurred while processing movie data")
    except Exception as e:
        print(f"Error processing movie data: {e}")

if __name__ == "__main__":
    with open('/Users/kimhyungjun/level4-cv-finalproject-hackathon-cv-8-lv3/test.json', "r", encoding="utf-8") as file:
        sample_json = json.load(file)  # 파일에서 JSON 데이터를 읽어와 Python 딕셔너리로 변환

    print(process_movie_data(sample_json))
