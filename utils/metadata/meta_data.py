import urllib.parse
import difflib
import requests
import json
import signal
import sys

# 특정 함수에만 타임아웃 적용하는 함수
# def run_with_timeout(func, timeout, *args, **kwargs):
#     """ 특정 함수 실행을 지정된 시간(초) 동안 제한하는 래퍼 함수 """
#     def timeout_handler(signum, frame):
#         raise TimeoutError
    
#     signal.signal(signal.SIGALRM, timeout_handler)  # 타임아웃 핸들러 설정
#     signal.alarm(timeout)  # timeout 초 후 SIGALRM 발생
    
#     try:
#         result = func(*args, **kwargs)  # 원래 함수 실행
#     except TimeoutError:
#         return None, None, [], []  # 타임아웃 발생 시 None 반환
#     finally:
#         signal.alarm(0)  # 함수 실행이 끝나면 타이머 해제 (필수)
    
#     return result
import threading

def run_with_timeout(func, timeout, *args, **kwargs):
    """ 특정 함수 실행을 지정된 시간(초) 동안 제한하는 래퍼 함수 """
    result = [None]  # 리스트로 감싸서 내부에서 변경 가능하도록 함
    exception = [None]  # 예외 저장용

    def wrapper():
        try:
            result[0] = func(*args, **kwargs)  # 원래 함수 실행
        except Exception as e:
            exception[0] = e  # 예외 저장

    thread = threading.Thread(target=wrapper)
    thread.start()
    thread.join(timeout)  # 타임아웃 시간 동안 대기

    if thread.is_alive():  # 타임아웃이 발생하면
        return None, None, [], []  # 타임아웃 시 None 반환

    if exception[0]:  # 내부에서 예외 발생 시 다시 던지기
        raise exception[0]

    return result[0]

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
            # cast_list = [f"{actor['name']} as {actor['character']}" for actor in data.get('cast', [])]
            # cast_list = [{"actor":f"{actor['name']}", "role": f"{actor['character']}"} for actor in data.get('cast', [])]
            cast_list = [{"actor":actor['name'], "role": actor['character']} for actor in data.get('cast', [])]
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
    """ 대사를 기반으로 영화 정보를 검색하고 TMDB에서 출연진 및 제작진 정보를 가져옴 """
    result = run_with_timeout(search_movie_by_quotes, 30, json_path)

    if result is None:  # 타임아웃 발생 시
        return None, None, [], []

    movie_title, movie_year = result  # search_movie_by_quotes가 항상 2개 반환

    if movie_title is None:  # 검색 결과 없음
        return None, None, [], []

    movie_id = get_movie_id(api_key, movie_title, movie_year)
    if not movie_id:
        return movie_title, movie_year, [], []

    cast, crew = get_cast_and_crew(api_key, movie_id)
    return movie_title, movie_year, cast, crew  # 항상 4개 반환


# 사용예시
if __name__ == "__main__":
    API_KEY = 'ff315049f0603ced165f84b648338838' 
    json_path = "/Users/kimhyungjun/level4-cv-finalproject-hackathon-cv-8-lv3/test.json"
    
    try:
        movie_title, movie_year, cast, crew = run_with_timeout(fetch_movie_info, 30, json_path, API_KEY)
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
    except TimeoutError:
        print("fetch_movie_info execution timed out!")
