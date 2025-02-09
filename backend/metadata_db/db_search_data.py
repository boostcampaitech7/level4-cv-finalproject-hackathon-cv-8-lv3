import sqlite3

def search_movies_like(queries):
    """
    여러 개의 검색어를 입력받아 `LIKE` 검색을 수행하여 해당하는 모든 영화 ID와 제목을 반환
    :param queries: 리스트 형태의 검색어 ex) ["DiCaprio", "Titanic"]
    :return: 검색된 영화 ID 및 제목 리스트 (같은 제목의 모든 ID 포함)
    """
    conn = sqlite3.connect("/data/ephemeral/home/level4-cv-finalproject-hackathon-cv-8-lv3/backend/metadata_db/movies.db")
    cursor = conn.cursor()

    # 모든 영화별 데이터를 하나의 문자열로 합쳐서 검색
    sql = """
    SELECT m.title, GROUP_CONCAT(DISTINCT m.id)
    FROM movies m
    JOIN movie_cast c ON m.id = c.movie_id
    GROUP BY m.title
    HAVING {}
    """

    # 검색어 개수만큼 OR 조건 추가 (배우, 역할, 영화 제목 모두 검색)
    conditions = []
    params = []
    for query in queries:
        formatted_query = f"%{query.replace(' ', '').lower()}%"  # 띄어쓰기 제거 후 소문자로 변환
        condition = "(LOWER(REPLACE(GROUP_CONCAT(DISTINCT m.title || c.actor || c.role), ' ', '')) LIKE ?)"
        conditions.append(condition)
        params.append(formatted_query)

    # AND 조건으로 검색어 개수만큼 모든 검색어를 포함해야 함
    sql = sql.format(" AND ".join(conditions))

    cursor.execute(sql, params)
    results = cursor.fetchall()

    conn.close()

    # 결과를 영화 제목별로 모든 ID 포함하여 변환
    output = []
    for row in results:
        movie_title = row[0]
        movie_ids = row[1].split(",")  # 여러 개의 ID 포함
        for movie_id in movie_ids:
            output.append({"id": movie_id, "title": movie_title})

    return output



def select_query(queries):
    """
    여러 개의 검색어를 입력받아, 가능한 모든 조합을 줄여가면서 검색 후 결과를 합쳐서 반환
    :param queries: 리스트 형태의 검색어 ex) ["DiCaprio", "Titanic", "Action"]
    :return: 검색된 영화 ID 및 제목 리스트 (같은 제목의 모든 ID 포함)
    """
    queries_len = len(queries)
    results = set()  # 중복 방지를 위한 set 사용

    # 검색어 개수 줄여가면서 검색 (3개 -> 2개 -> 1개)
    for i in range(queries_len, max(queries_len -3,0) , -1):
        from itertools import combinations

        # i개짜리 검색어 조합 생성
        for combo in combinations(queries, i):
            search_result = search_movies_like(list(combo))

            # 검색 결과가 있으면 추가 (중복 방지)
            for movie in search_result:
                results.add((movie["id"], movie["title"]))
        if results:
            break

    # 결과를 리스트로 변환
    return [{"id": movie_id, "title": title} for movie_id, title in results]
        
# print(select_query(['hulk', 'ironman', 'hulkbuster']))
# print(select_query(['hulk', 'ironman', 'hulkbuster']))
# 🔍 테스트 실행
# print(search_movies_like(["IronMan", "Avengers"]))  # [{'id': 'ZXTUV_pQWER', 'title': 'Avengers'}]
# print(search_movies_like(["IronMan", "robert"]))  # [{'id': 'ZXTUV_pQWER', 'title': 'Avengers'}]
# print(search_movies_like(["DiCaprio", "Titanic"]))  # [{'id': 'NMPQL_dEGRf', 'title': 'Titanic'}]
# print(search_movies_like(["LeonardoDiCaprio"]))  # [{'id': 'BPNUN_aCFAc', 'title': 'Inception'}, {'id': 'NMPQL_dEGRf', 'title': 'Titanic'}]
# print(search_movies_like(["CaptainAmerica"]))  # [{'id': 'ZXTUV_pQWER', 'title': 'Avengers'}]
# print(search_movies_like(["CaptainAmerica", "IronMan"]))  # [{'id': 'ZXTUV_pQWER', 'title': 'Avengers'}]
# print(search_movies_like(["Rose"]))  # [{'id': 'NMPQL_dEGRf', 'title': 'Titanic'}]
# print(search_movies_like(["ChrisEvans"]))  # [{'id': 'ZXTUV_pQWER', 'title': 'Avengers'}]
# print(search_movies_like(["Dicaprio"]))  # [{'id': 'ZXTUV_pQWER', 'title': 'Avengers'}]
# print(search_movies_like(['tom']))  # [{'id': 'ZXTUV_pQWER', 'title': 'Avengers'}]


