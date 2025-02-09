# Meta data DB 

메타 데이터의 테이블을 저장하는 부분



## DB에 데이터 삽입하기

```python 
from db_input_data import *

#특정 json 한 개만 삽입하기
#   movie_json : json 파일
#   filename: 파일 이름
insert_movie_data(movie_json, filename)

#특정 경로에 있는 데이터 전부 삽입하기
#   folder_path : json들이 있는 경로
insert_all_movies_from_folder(folder_path)
```


## DB에서 데이터 검색하기


```python
from db_search_data import *
#DB에서 쿼리를 통해 해당되는 영화 가져오기
#해당되는 영상이 없는 경우 [] (빈 배열) 반환
# queries : 리스트 형태의 검색어 ex) ["DiCaprio", "Titanic"]

#결과 형식 : [{'id': 'o4Cm2uYymW0', 'title': 'Avengers: Age of Ultron'}, {'id': 'H0AnJKKwhQ0', 'title': 'Half Baked'}]
# -> 딕셔너리 배열
search_movies_like(queries)

