import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect("movies.db")
cursor = conn.cursor()

# 1️⃣ 영화 테이블 (고유 ID 포함, 영화 제목 중복 가능)
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id TEXT PRIMARY KEY,  -- 고유 식별자 (예: 'BPNUN_aCFAc')
    title TEXT NOT NULL   -- 영화 제목 (중복 가능)
)
""")

# 2️⃣ 배우 및 역할 테이블 (1:N 관계)
cursor.execute("""
CREATE TABLE IF NOT EXISTS movie_cast (
    movie_id TEXT,        -- 영화 ID (movies 테이블과 연결)
    actor TEXT,           -- 배우 이름
    role TEXT,            -- 역할 이름
    FOREIGN KEY (movie_id) REFERENCES movies(id)
)
""")

# 변경 사항 저장 및 종료
conn.commit()
conn.close()
print("✅ Database and tables created successfully!")
