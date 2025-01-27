from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from chromadb import HttpClient
import pandas as pd
from tqdm import tqdm
import os

# Flask 애플리케이션 생성
app = Flask(__name__)

# ChromaDB 및 모델 초기화
client = HttpClient(host='localhost', port=8000)
movie_clips = client.get_or_create_collection(name="movie_clips")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def json_to_vectorDB(model, json_path, collections): 
    df = pd.read_json(json_path)
    ids = []
    metadatas = []
    embeddings = []

    for row in tqdm(df.iterrows()):
        video_path = row[1].video_path

        timestamp = row[1].segments['timestamps']
        video_id = row[1].segments['video_id']
        caption = row[1].segments['video_caption_en']

        metadata = {
            "captions": caption,
            "video_path": video_path,
            "start": timestamp['start'],
            "end" : timestamp['end']    
        }

        embedding = model.encode(caption, normalize_embeddings=True)

        ids.append(video_id)
        metadatas.append(metadata)
        embeddings.append(embedding)

    chunk_size = 1024  # 한 번에 처리할 chunk 크기 설정
    total_chunks = len(embeddings) // chunk_size + 1  # 전체 데이터를 chunk 단위로 나눈 횟수
    embeddings = [e.tolist() for e in tqdm(embeddings)]  

    for chunk_idx in tqdm(range(total_chunks)):
        start_idx = chunk_idx * chunk_size
        end_idx = (chunk_idx + 1) * chunk_size

        # chunk 단위로 데이터 자르기
        chunk_embeddings = embeddings[start_idx:end_idx]
        chunk_ids = ids[start_idx:end_idx]
        chunk_metadatas = metadatas[start_idx:end_idx]

        # chunk를 answers에 추가
        collections.add(embeddings=chunk_embeddings, ids=chunk_ids, metadatas=chunk_metadatas)

def text_to_timestamps(model, input, collections):
    input_embedding = model.encode(input, normalize_embeddings=True).tolist()
    result = collections.query(input_embedding, n_results=3)
    return result


@app.route('/add_json', methods=['POST'])
def add_json_to_db():
    """
    JSON 데이터를 받아서 VectorDB에 저장
    """
    try:
        json_file = request.files['file']
        if not json_file:
            return jsonify({"error": "No file provided"}), 400

        file_path = os.path.join("temp.json")
        json_file.save(file_path)

        # JSON 파일 처리
        json_to_vectorDB(model, file_path, movie_clips)
        os.remove(file_path)  # 임시 파일 삭제

        return jsonify({"message": "Data added to VectorDB successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/query', methods=['POST'])
def query_timestamps():
    """
    텍스트 입력을 받아 타임스탬프를 반환
    """
    try:
        data = request.json
        input_text = data.get('input_text')
        if not input_text:
            return jsonify({"error": "Input text is required"}), 400

        # 텍스트를 이용하여 타임스탬프 쿼리
        result = text_to_timestamps(model, input_text, movie_clips)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=1234)
