import sqlite3
import json
import os
import glob

def extract_movie_id(filename):
    """
    파일명에서 `_meta_data.json` 앞에 있는 부분을 movie_id로 추출
    :param filename: 원본 파일명
    :return: 추출된 movie_id
    """
    base_name = os.path.basename(filename)  # 경로 제거
    movie_id = base_name.split("_meta_data.json")[0]  # `_meta_data.json` 앞의 문자열 추출
    return movie_id

def insert_movie_data(movie_json, filename):
    """
    JSON 데이터를 받아 SQLite에 저장하는 함수
    :param movie_json: 영화 데이터 (title, cast 목록 포함)
    :param filename: 원본 파일명 (영화 ID 추출용)
    """
    conn = sqlite3.connect("/data/ephemeral/home/level4-cv-finalproject-hackathon-cv-8-lv3/backend/metadata_db/movies.db")
    cursor = conn.cursor()

    # 1️⃣ 파일명에서 movie_id 추출
    movie_id = extract_movie_id(filename)

    # 2️⃣ title이 None이면 무시
    title = movie_json.get("title")
    if not title:
        print(f"❌ Skipping invalid movie (title is null) [File: {filename}]")
        conn.close()
        return

    # 3️⃣ 영화 데이터 삽입 (중복 방지)
    cursor.execute("INSERT OR IGNORE INTO movies (id, title) VALUES (?, ?)", (movie_id, title))

    # 4️⃣ 배우 및 역할 데이터 삽입
    cast_list = movie_json.get("cast", [])
    for cast in cast_list:
        actor = cast.get("actor")
        role = cast.get("role")

        if actor and role:
            cursor.execute("INSERT INTO movie_cast (movie_id, actor, role) VALUES (?, ?, ?)", (movie_id, actor, role))

    # 변경 사항 저장
    conn.commit()
    conn.close()
    print(f"✅ Movie '{title}' inserted successfully with ID {movie_id}")


def insert_all_movies_from_folder(folder_path):
    """
    지정된 폴더 내 모든 JSON 파일을 찾아 `insert_movie_data()` 실행
    :param folder_path: JSON 파일이 있는 폴더 경로
    """
    json_files = glob.glob(os.path.join(folder_path, "*.json"))  # 폴더 내 모든 JSON 파일 찾기

    if not json_files:
        print("❌ No JSON files found in the specified folder.")
        return

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                movie_json = json.load(f)  # JSON 파일 읽기
                insert_movie_data(movie_json, json_file)  # 데이터 삽입
        except Exception as e:
            print(f"❌ Failed to process {json_file}: {e}")


def insert_movie_from_file(json_file_path):
    """
    지정된 JSON 파일을 읽어 `insert_movie_data()` 실행
    :param json_file_path: JSON 파일 경로
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            movie_json = json.load(f)  # JSON 파일 읽기
            insert_movie_data(movie_json, json_file_path)  # 데이터 삽입
    except Exception as e:
        print(f"❌ Failed to process {json_file_path}: {e}")

if __name__=="__main__":
    # 🔍 실행: 특정 폴더 내 모든 JSON 파일 삽입
    json_folder = "/Users/kimhyungjun/chromaTest/meta_data/meta_data/movie_info"  # 메타 데이터 JSON 파일이 있는 폴더 경로
    # insert_all_movies_from_folder(json_folder)
    insert_movie_from_file('/Users/kimhyungjun/level4-cv-finalproject-hackathon-cv-8-lv3/utils/metadata/json_metadata/BPNUN_aCFAc_meta_data.json')
