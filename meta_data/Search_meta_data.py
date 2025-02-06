from selenium import webdriver
import geckodriver_autoinstaller
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import urllib.parse
import difflib
import re
import requests

# TMDb API 키를 여기에 입력하세요.
API_KEY = 'ff315049f0603ced165f84b648338838'

# Geckodriver 자동 설치
# geckodriver_autoinstaller.install()

# Firefox 옵션 설정 (User-Agent 변경 및 headless 모드)
options = webdriver.FirefoxOptions()
options.add_argument('--headless')
options.set_preference("general.useragent.override", 
                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Firefox 드라이버 실행
driver = webdriver.Firefox(options=options)

# 검색할 대사 목록
quotes = [
    " I have but lost a thousand pounds. You asked me to risk another.",
    " My lord, the money was stolen from me and from you.",
    " I am no part of your incompetence, MacGregor.",
    " You signed a paper.",
    " And I will honor it."
]

# 유사도 임계값 설정
SIMILARITY_THRESHOLD = 0.6

# 타임스탬프 패턴 정의
timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2}\s-\s')

def get_movie_id(api_key, movie_title):
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": api_key, "query": movie_title}
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results')
        if results:
            return results[0]['id']
        else:
            print(f"'{movie_title}'에 대한 결과를 찾을 수 없습니다.")
            return None
    else:
        print(f"검색 요청 실패: {response.status_code}")
        return None

def get_cast_and_crew(api_key, movie_id):
    """
    출연진과 제작진 정보를 반환합니다.
    반환 형식:
    {
        "cast": ["Actor Name as Character", ...],
        "crew": ["Job: Name", ...]
    }
    """
    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
    params = {"api_key": api_key}
    response = requests.get(credits_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        cast_list = [f"{actor['name']} as {actor['character']}" for actor in data.get('cast', [])]
        crew_list = [f"{member['job']}: {member['name']}" for member in data.get('crew', []) if member['job'] in ['Director', 'Producer', 'Writer', 'Cinematographer', 'Original Music Composer']]
        
        return {
            "cast": cast_list,
            "crew": crew_list
        }
    else:
        print(f"크레딧 요청 실패: {response.status_code}")
        return {
            "cast": [],
            "crew": []
        }

def search_quotes(driver, quotes):
    for idx, quote in enumerate(quotes):
        next_quote = quotes[idx + 1].strip() if idx + 1 < len(quotes) else None
        print(f"Searching for quote: {quote.strip()}")
        encoded_quote = urllib.parse.quote(quote.strip())
        search_url = f"https://www.quodb.com/search/{encoded_quote}?advance-search=false&keywords='{encoded_quote}'"
        driver.get(search_url)

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//tr[@data-title]")))
            data_rows = driver.find_elements(By.XPATH, "//tr[@data-title]")

            if data_rows:
                for row in data_rows:
                    movie_title = row.get_attribute('data-title')
                    print(f"Found Movie: {movie_title}")
                    return movie_title  # 첫 번째로 찾은 영화 제목 반환
            else:
                print(f"No matching quote found for: {quote.strip()}")

            print("=" * 70)
            time.sleep(2)

        except TimeoutException:
            print(f"Timeout occurred while searching for: {quote.strip()}")
            print("=" * 70)

# 대사 검색 실행
movie_title = search_quotes(driver, quotes)

# 브라우저 종료
driver.quit()

# TMDb에서 영화 정보 검색 및 출력
if movie_title:
    movie_id = get_movie_id(API_KEY, movie_title)
    if movie_id:
        cast_and_crew = get_cast_and_crew(API_KEY, movie_id)
        
        print("\n출연진 (Cast):")
        for actor in cast_and_crew['cast']:
            print(actor)

        print("\n제작진 (Crew):")
        for crew_member in cast_and_crew['crew']:
            print(crew_member)
else:
    print("No movie found from quotes.")
