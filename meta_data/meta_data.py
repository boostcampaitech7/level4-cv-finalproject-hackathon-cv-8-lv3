import urllib.parse
import difflib
import requests
import json
import signal
import sys

# 설정할 프로그램 실행 제한 시간 (초)
PROGRAM_TIMEOUT = 30  # 30초 후 강제 종료

# 프로그램 실행 제한 초과 시 호출될 핸들러
def timeout_handler(signum, frame):
    print("\nProgram execution timed out! Exiting...")
    sys.exit(1)

# 프로그램 타임아웃 적용
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(PROGRAM_TIMEOUT)  # PROGRAM_TIMEOUT 초 후 SIGALRM 발생

# TMDB API를 사용하여 영화 제목과 연도를 기반으로 영화 ID를 검색
def get_movie_id(api_key, movie_title, movie_year=None):
    if not movie_title:
        return None
    
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": api_key, "query": movie_title}
    if movie_year:
        params["year"] = movie_year

    try:
        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                return results[0]['id']
    except requests.exceptions.Timeout:
        print("Request timed out while fetching movie ID.")
    except requests.exceptions.RequestException:
        print("Request failed while fetching movie ID.")
    
    return None

# TMDB API를 사용하여 영화의 출연진 및 제작진 정보를 가져옴
def get_cast_and_crew(api_key, movie_id):
    if not movie_id:
        return [], []
    
    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
    params = {"api_key": api_key}
    
    try:
        response = requests.get(credits_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            cast_list = [f"{actor['name']} as {actor['character']}" for actor in data.get('cast', [])]
            crew_list = [f"{member['job']}: {member['name']}" for member in data.get('crew', []) if member['job'] in ['Director', 'Producer', 'Writer', 'Cinematographer', 'Original Music Composer']]
            return cast_list, crew_list
    except requests.exceptions.Timeout:
        print("Request timed out while fetching cast and crew.")
    except requests.exceptions.RequestException:
        print("Request failed while fetching cast and crew.")
    
    return [], []

# JSON 파일에서 대사를 읽고 QuoDB API를 사용하여 영화 제목을 검색
def search_movie_by_quotes(json_file_path, similarity_threshold=0.8): 
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        # 대사 목록 추출
        quotes_list = [segment["stt_caption"].strip() for segment in data.get("segments", []) if segment.get("stt_caption", "").strip() and segment["stt_caption"].strip() != '.']
        
        if not quotes_list:
            return None, None
        
        for idx, current_quote in enumerate(quotes_list):
            next_quote = quotes_list[idx + 1].strip() if idx + 1 < len(quotes_list) else ""
            
            # QuoDB API를 사용하여 대사 검색
            search_url = f"https://api.quodb.com/search/{urllib.parse.quote(current_quote)}?advance-search=false&titles_per_page=5&phrases_per_title=1&page=1"
            try:
                api_response = requests.get(search_url, timeout=10).json()
            except requests.exceptions.Timeout:
                print("Request timed out while searching for movie by quotes.")
                continue
            except requests.exceptions.RequestException:
                continue
            
            response_movies = api_response.get('docs', [])
            if not response_movies:
                continue
            
            for response_movie in response_movies:
                search_quote_url = f"https://api.quodb.com/quotes/{response_movie['title_id']}/{response_movie['phrase_id']}"
                try:
                    api_title_quote = requests.get(search_quote_url, timeout=10).json()
                    next_dialogue = api_title_quote.get("docs", [{}])[3].get("phrase", "")
                except (requests.exceptions.Timeout, requests.exceptions.RequestException, IndexError, KeyError):
                    next_dialogue = ""
                
                try:
                    similarity = difflib.SequenceMatcher(None, next_dialogue or "", next_quote or "").ratio()
                except TypeError:
                    similarity = 0

                if similarity >= similarity_threshold:
                    return response_movie['title'], response_movie.get("year")
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None
    
    return None, None

# 대사를 기반으로 영화 정보를 검색하고 TMDB에서 출연진 및 제작진 정보를 가져옴
def fetch_movie_info(json_path, api_key):
    movie_title, movie_year = search_movie_by_quotes(json_path)
    if not movie_title:
        return None, None, [], []
    
    movie_id = get_movie_id(api_key, movie_title, movie_year)
    if not movie_id:
        return movie_title, movie_year, [], []
    
    cast, crew = get_cast_and_crew(api_key, movie_id)
    return movie_title, movie_year, cast, crew

# 사용예시
if __name__ == "__main__":
    API_KEY = 'ff315049f0603ced165f84b648338838' 
    json_path = "/data/ephemeral/home/jseo/C4MVQby0InQ.json"
    
    movie_title, movie_year, cast, crew = fetch_movie_info(json_path, API_KEY)
    
    if movie_title:
        print(f"Movie: {movie_title} ({movie_year})")
        print("\nCast:")
        for actor in cast:
            print(actor)
        print("\nCrew:")
        for crew_member in crew:
            print(crew_member)
    else:
        print("No movie found from quotes.")
