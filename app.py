from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger, swag_from
from video_to_text.scene_detect import scene_detect
from db_search import search_movies_like

import requests
import json
import logging

# Flask 앱 설정
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Swagger 설정
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "비디오 캡션 생성 및 검색 API",
        "description": """
        # 비디오 분석 및 캡션 생성 API 문서
        
        이 API는 비디오를 분석하여 장면별 캡션을 생성하고 검색할 수 있는 기능을 제공합니다.
        
        ## 주요 기능
        
        ### 1. 비디오 처리
        - 비디오 파일 업로드 및 처리
        - 자동 장면 감지(Scene Detection)
        - 장면별 캡션 생성
        
        ### 2. 음성 처리
        - STT(Speech-to-Text) 처리
        - 음성 내용의 텍스트 변환
        
        ### 3. 다국어 지원
        - 영어/한국어 번역 지원
        - 자동 번역 기능
        
        ### 4. 검색 기능
        - 벡터 DB 기반 의미론적 검색
        - 텍스트 기반 비디오 구간 검색
        
        ## 기술 스택
        - Scene Detection
        - Video Captioning
        - Speech-to-Text
        - Neural Machine Translation
        - Vector Database
        """,
        "version": "1.0.0",
        "contact": {
            "email": "admin@example.com"
        }
    },
    "tags": [
        {
            "name": "비디오 처리",
            "description": "비디오 업로드 및 캡션 생성 관련 API 엔드포인트"
        },
        {
            "name": "비디오 검색",
            "description": "생성된 캡션 기반 비디오 검색 API 엔드포인트"
        }
    ],
    "schemes": ["http", "https"],
    "consumes": ["multipart/form-data", "application/json"],
    "produces": ["application/json"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT 토큰을 입력하세요. 예: Bearer {token}"
        }
    },
    "definitions": {
        "Error": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "description": "에러 메시지"
                }
            }
        },
        "VideoSegment": {
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "number",
                    "description": "시작 시간(초)"
                },
                "end_time": {
                    "type": "number", 
                    "description": "종료 시간(초)"
                },
                "caption_eng": {
                    "type": "string",
                    "description": "영어 캡션"
                },
                "caption_kor": {
                    "type": "string",
                    "description": "한국어 캡션"
                }
            }
        }
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)


# API 엔드포인트 설정
API_ENDPOINTS = {
    'video': "http://10.28.224.34:30742",
    'stt': "http://10.28.224.194:30076", 
    'vectordb': "http://localhost:1234",
    'llm': "http://10.28.224.27:30896"
}

# 유틸리티 함수
def translate_text(text: str) -> str:
    """텍스트 번역 함수
    
    Args:
        text (str): 번역할 영어 텍스트
        
    Returns:
        str: 번역된 한국어 텍스트. 오류 발생시 원본 텍스트 반환
    """
    DEEPL_API_KEY = "e002ea00-6062-41c7-8382-2e2bb6039b24:fx"  # DeepL API 키를 여기에 입력하세요
    DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"  # 무료 API의 경우. Pro 버전은 다른 URL 사용
    
    if not text or not isinstance(text, str):
        return ""
        
    try:
        response = requests.post(
            DEEPL_API_URL,
            headers={"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"},
            data={
                "text": text,
                "source_lang": "EN",  # 영어에서
                "target_lang": "KO"   # 한국어로
            }
        )
        response.raise_for_status()
        
        translated_text = response.json()["translations"][0]["text"]
        return translated_text
            
    except Exception as e:
        logger.error(f"DeepL 번역 중 오류 발생: {str(e)}")
        return text

def upload_video_to_server(server_url: str, video_file) -> str:
    """비디오 업로드 함수"""
    try:
        files = {
            "video": (video_file.filename, video_file, video_file.content_type)
        }
        response = requests.post(f"{server_url}/upload_video", files=files)
        response.raise_for_status()
        print(response.json())
        return response.json()["video_path"]
    except Exception as e:
        raise Exception(f"비디오 업로드 실패: {e}")

def process_api_request(api_url: str, video_path: str, timestamps: list) -> dict:
    """API 요청 처리 함수"""
    try:
        response = requests.post(
            f"{api_url}/entire_video",
            json={"video_path": video_path, "timestamps": timestamps}
        )
        response.raise_for_status()
        return response.json()["segments"]
    except Exception as e:
        raise Exception(f"API 요청 실패: {e}")

def text_to_timestamps(model, input_text: str, top_k: int = 3) -> list:
    """텍스트 기반 타임스탬프 검색 함수"""
    try:
        query_embedding = model.encode(input_text, normalize_embeddings=True).tolist()
        response = requests.post(
            f"{API_ENDPOINTS['vectordb']}/search",
            json={
                'query_embedding': query_embedding,
                'top_k': top_k
            }
        )
        return response.json()['results']
    except Exception as e:
        raise Exception(f"검색 실패: {e}")

def _save_to_vectordb(translated_data: dict, video_path: str):
    """벡터 DB 저장 함수"""
    try:
        # 비디오 캡션 저장
        video_segments = []
        for segment in translated_data.get("video_caption", []):
            video_id = f"{translated_data['video_id']}_{len(video_segments)}"
            
            video_segments.append({
                "segments": {
                    "timestamps": {
                        "start": segment["start_time"],
                        "end": segment["end_time"]
                    },
                    "video_id": video_id,
                    "video_caption_eng": segment["caption_eng"]
                },
                "video_path": video_path
            })
            
        if video_segments:
            requests.post(f"{API_ENDPOINTS['vectordb']}/add_json", 
                        files={"file": json.dumps(video_segments)})

        # STT 캡션 저장  
        audio_segments = []
        for segment in translated_data.get("stt", []):
            audio_id = f"{translated_data['video_id']}_{len(audio_segments)}"
            
            audio_segments.append({
                "segments": {
                    "timestamps": {
                        "start": segment["start_time"],
                        "end": segment["end_time"]
                    },
                    "video_id": audio_id,
                    "stt_caption_eng": segment["caption_eng"]
                },
                "video_path": video_path
            })

        if audio_segments:
            requests.post(f"{API_ENDPOINTS['vectordb']}/add_json_audio",
                        files={"file": json.dumps(audio_segments)})

    except Exception as e:
        logger.error(f"벡터 DB 저장 실패: {e}")
        raise

# API 엔드포인트
@app.route('/process_entire_video', methods=['POST'])
@swag_from({
    'tags': ['비디오 처리'],
    'parameters': [
        {
            'name': 'video',
            'in': 'formData',
            'type': 'file',
            'required': False,
            'description': '처리할 비디오 파일'
        },
        {
            'name': 'video_id',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': '처리할 비디오 ID'
        }
    ],
    'responses': {
        200: {
            'description': '비디오 처리 성공',
            'schema': {
                'type': 'object',
                'properties': {
                    'video_id': {'type': 'string'},
                    'stt': {'type': 'array', 'items': {'$ref': '#/definitions/VideoSegment'}},
                    'video_caption': {'type': 'array', 'items': {'$ref': '#/definitions/VideoSegment'}}
                }
            }
        },
        400: {
            'description': '잘못된 요청',
            'schema': {'$ref': '#/definitions/Error'}
        },
        500: {
            'description': '서버 오류',
            'schema': {'$ref': '#/definitions/Error'}
        }
    }
})
def process_entire_video():
    """전체 비디오 처리 API"""
    video_file = request.files.get('video')
    video_id = request.form.get('video_id')
    
    if not video_file and not video_id:
        return jsonify({"error": "비디오 파일 또는 video_id가 필요합니다"}), 400

    try:
        video_path = upload_video_to_server(API_ENDPOINTS['video'], video_file) if video_file else f"/data/ephemeral/home/movie_clips/{video_id}.mp4"
        timestamps = scene_detect(video_path)
        formatted_timestamps = [{"start_time": start, "end_time": end} for start, end in timestamps]
        
        # 비디오 캡션 처리
        video_results = process_api_request(API_ENDPOINTS['video'], video_path, formatted_timestamps)
        
        # STT 처리
        stt_segments = []
        try:
            stt_response = requests.post(
                f"{API_ENDPOINTS['stt']}/entire_video",
                json={"video_path": video_path}
            )
            stt_response.raise_for_status()
            stt_segments = stt_response.json().get('segments', [])
        except Exception as e:
            logger.error(f"STT 처리 실패: {e}")

        # 결과 처리
        video_segments = []
        for segment in video_results:
            try:
                # 'captions' 키에서 캡션 값을 안전하게 가져옴
                video_caption_en = segment.get("video_caption_en", "")
                if not video_caption_en:
                    logger.warning(f"caption이 없거나 비어있습니다: {segment}")
                    continue
                    
                video_segments.append({
                    "start_time": segment["timestamps"]["start"],
                    "end_time": segment["timestamps"]["end"],
                    "caption_eng": video_caption_en,
                    "caption_kor": translate_text(video_caption_en)
                })
            except KeyError as e:
                logger.error(f"세그먼트 처리 중 키 오류: {e}, 세그먼트: {segment}")
                continue

        # STT 번역 처리: stt API 반환 결과의 구조에 맞게 수정
        stt_translated = []
        for segment in stt_segments:
            stt_caption = segment.get("stt_caption")
            if not stt_caption:
                logger.warning(f"STT segment에 stt_caption이 없습니다: {segment}")
                continue
            timestamp = segment.get("timestamp", {})
            start = timestamp.get("start", 0)
            end = timestamp.get("end", 0)
            stt_translated.append({
                "caption_eng": stt_caption,
                "caption_kor": translate_text(stt_caption),
                "start_time": start,
                "end_time": end
            })

        result = {
            "video_id": video_id,
            "stt": stt_translated,
            "video_caption": video_segments
        }
        
        try:
            _save_to_vectordb(result, video_path)
        except Exception as e:
            logger.error(f"vectorDB 저장 실패: {e}")
        
        return jsonify(result)

    except Exception as e:
        error_msg = f"처리 중 오류 발생: {e}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500

@app.route('/process_video_without_translation', methods=['POST'])
@swag_from({
    'tags': ['비디오 처리'],
    'parameters': [
        {
            'name': 'video',
            'in': 'formData',
            'type': 'file',
            'required': False,
            'description': '처리할 비디오 파일'
        },
        {
            'name': 'video_id',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': '처리할 비디오 ID'
        }
    ],
    'responses': {
        200: {
            'description': '비디오 처리 성공',
            'schema': {
                'type': 'object',
                'properties': {
                    'video_id': {'type': 'string'},
                    'stt': {'type': 'array', 'items': {'$ref': '#/definitions/VideoSegment'}},
                    'video_caption': {'type': 'array', 'items': {'$ref': '#/definitions/VideoSegment'}}
                }
            }
        },
        400: {
            'description': '잘못된 요청',
            'schema': {'$ref': '#/definitions/Error'}
        },
        500: {
            'description': '서버 오류',
            'schema': {'$ref': '#/definitions/Error'}
        }
    }
})
def process_video_without_translation():
    """전체 비디오 처리 API (번역 제외)"""
    video_file = request.files.get('video')
    video_id = request.form.get('video_id')
    
    if not video_file and not video_id:
        return jsonify({"error": "비디오 파일 또는 video_id가 필요합니다"}), 400

    try:
        video_path = upload_video_to_server(API_ENDPOINTS['video'], video_file) if video_file else f"/data/ephemeral/home/movie_clips/{video_id}.mp4"
        timestamps = scene_detect(video_path)
        formatted_timestamps = [{"start_time": start, "end_time": end} for start, end in timestamps]
        
        # 비디오 캡션 처리
        video_results = process_api_request(API_ENDPOINTS['video'], video_path, formatted_timestamps)
        
        # STT 처리
        stt_segments = []
        try:
            stt_response = requests.post(
                f"{API_ENDPOINTS['stt']}/entire_video",
                json={"video_path": video_path}
            )
            stt_response.raise_for_status()
            stt_segments = stt_response.json().get('segments', [])
        except Exception as e:
            logger.error(f"STT 처리 실패: {e}")

        # 결과 처리
        video_segments = []
        for segment in video_results:
            try:
                video_caption_en = segment.get("video_caption_en", "")
                if not video_caption_en:
                    logger.warning(f"caption이 없거나 비어있습니다: {segment}")
                    continue
                    
                video_segments.append({
                    "start_time": segment["timestamps"]["start"],
                    "end_time": segment["timestamps"]["end"],
                    "caption_eng": video_caption_en
                })
            except KeyError as e:
                logger.error(f"세그먼트 처리 중 키 오류: {e}, 세그먼트: {segment}")
                continue

        # STT 처리
        stt_processed = []
        for segment in stt_segments:
            stt_caption = segment.get("stt_caption")
            if not stt_caption:
                logger.warning(f"STT segment에 stt_caption이 없습니다: {segment}")
                continue
            timestamp = segment.get("timestamp", {})
            start = timestamp.get("start", 0)
            end = timestamp.get("end", 0)
            stt_processed.append({
                "caption_eng": stt_caption,
                "start_time": start,
                "end_time": end
            })

        result = {
            "video_id": video_id,
            "stt": stt_processed,
            "video_caption": video_segments
        }
        
        try:
            _save_to_vectordb(result, video_path)
        except Exception as e:
            logger.error(f"vectorDB 저장 실패: {e}")
        
        return jsonify(result)

    except Exception as e:
        error_msg = f"처리 중 오류 발생: {e}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500



@app.route('/process_video_with_timestamps', methods=['POST'])
@swag_from({
    'tags': ['비디오 처리'],
    'parameters': [
        {
            'name': 'video',
            'in': 'formData',
            'type': 'file',
            'required': False,
            'description': '처리할 비디오 파일'
        },
        {
            'name': 'video_id',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': '처리할 비디오 ID'
        },
        {
            'name': 'timestamps',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': '''JSON 형식의 타임스탬프 배열. 각 타임스탬프는 start와 end 시간을 포함해야 합니다.
            예시: [{"start": 0, "end": 10}, {"start": 20, "end": 30}]
            - start: 시작 시간(초 단위)
            - end: 종료 시간(초 단위)
            '''
        }
    ],
    'responses': {
        200: {
            'description': '비디오 처리 성공',
            'schema': {
                'type': 'object',
                'properties': {
                    'video_id': {'type': 'string'},
                    'stt': {'type': 'array', 'items': {'$ref': '#/definitions/VideoSegment'}},
                    'video_caption': {'type': 'array', 'items': {'$ref': '#/definitions/VideoSegment'}}
                }
            }
        },
        400: {
            'description': '잘못된 요청',
            'schema': {'$ref': '#/definitions/Error'}
        },
        500: {
            'description': '서버 오류',
            'schema': {'$ref': '#/definitions/Error'}
        }
    }
})
def process_video_with_timestamps():
    """타임스탬프 기반 비디오 처리 API"""
    video_file = request.files.get('video')
    video_id = request.form.get('video_id')
    
    if not video_file and not video_id:
        return jsonify({"error": "비디오 파일 또는 video_id가 필요합니다"}), 400

    try:
        timestamps = json.loads(request.form.get('timestamps', '[]'))
    except json.JSONDecodeError as e:
        return jsonify({"error": f"timestamps JSON 형식이 잘못되었습니다: {e}"}), 400

    if not timestamps:
        return jsonify({"error": "timestamps가 비어있습니다"}), 400

    try:
        video_path = upload_video_to_server(API_ENDPOINTS['video'], video_file) if video_file else f"/data/ephemeral/home/movie_clips/{video_id}.mp4"
        detected_timestamps = scene_detect(video_path)
        
        filtered_timestamps = [
            {"start_time": start, "end_time": end}
            for start, end in detected_timestamps
            for ts in timestamps
            if not (ts["end"] < start or ts["start"] > end)
        ]

        if not filtered_timestamps:
            return jsonify({"error": "지정된 타임스탬프 구간 내에서 감지된 장면이 없습니다"}), 400

        # 비디오 캡션 처리
        video_results = process_api_request(API_ENDPOINTS['video'], video_path, filtered_timestamps)
        
        # STT 처리
        stt_segments = []
        try:
            stt_response = requests.post(
                f"{API_ENDPOINTS['stt']}/entire_video",
                json={"video_path": video_path}
            )
            stt_response.raise_for_status()
            stt_segments = stt_response.json().get('segments', [])
        except Exception as e:
            logger.error(f"STT 처리 실패: {e}")

        # 비디오 캡션 결과 처리
        video_segments = []
        for segment in video_results:
            try:
                video_caption_en = segment.get("video_caption_en", "")
                if not video_caption_en:
                    logger.warning(f"caption이 없거나 비어있습니다: {segment}")
                    continue
                    
                start_time = segment["timestamps"]["start"]
                end_time = segment["timestamps"]["end"]
                
                # 사용자가 지정한 타임스탬프와 겹치는지 확인
                for ts in timestamps:
                    if not (ts["end"] < start_time or ts["start"] > end_time):
                        video_segments.append({
                            "start_time": start_time,
                            "end_time": end_time,
                            "caption_eng": video_caption_en,
                            "caption_kor": translate_text(video_caption_en)
                        })
                        break
                        
            except KeyError as e:
                logger.error(f"세그먼트 처리 중 키 오류: {e}, 세그먼트: {segment}")
                continue

        # STT 번역 처리
        stt_translated = []
        for segment in stt_segments:
            stt_caption = segment.get("stt_caption")
            if not stt_caption:
                logger.warning(f"STT segment에 stt_caption이 없습니다: {segment}")
                continue
                
            timestamp = segment.get("timestamp", {})
            start = timestamp.get("start", 0)
            end = timestamp.get("end", 0)
            
            # 사용자가 지정한 타임스탬프와 겹치는지 확인
            for ts in timestamps:
                if not (ts["end"] < start or ts["start"] > end):
                    stt_translated.append({
                        "caption_eng": stt_caption,
                        "caption_kor": translate_text(stt_caption),
                        "start_time": start,
                        "end_time": end
                    })
                    break

        result = {
            "video_id": video_id,
            "stt": stt_translated,
            "video_caption": video_segments
        }
        
        try:
            _save_to_vectordb(result, video_path)
        except Exception as e:
            logger.error(f"vectorDB 저장 실패: {e}")
        
        return jsonify(result)

    except Exception as e:
        error_msg = f"처리 중 오류 발생: {e}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500


@app.route('/search_videos', methods=['POST'])
@swag_from({
    'tags': ['비디오 검색'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'text': {'type': 'string', 'description': '검색할 텍스트'}
                },
                'required': ['text']
            }
        }
    ],
    'responses': {
        200: {
            'description': '검색 성공',
            'schema': {
                'type': 'object',
                'properties': {
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string'},
                                'score': {'type': 'number'},
                                'metadata': {'type': 'object'}
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': '잘못된 요청',
            'schema': {'$ref': '#/definitions/Error'}
        },
        500: {
            'description': '서버 오류',
            'schema': {'$ref': '#/definitions/Error'}
        }
    }
})
def search_videos():
    """비디오 검색 API"""
    try:
        data = request.get_json()
        if not data or 'text' not in data or not data['text'].strip():
            return jsonify({"error": "유효한 검색어를 입력해주세요"}), 400

        # LLM 서버에 쿼리 분석 요청
        try:
            llm_response = requests.post(
                f"{API_ENDPOINTS['llm']}/analyze_query",
                json={"query_text": data['text']}
            )
            llm_response.raise_for_status()
            query_analysis = llm_response.json()['result']
            print("query_analysis", query_analysis)
            
            
            # 비디오 필드와 중요도 추출
            video_field = query_analysis.get('video_field', '')
            video_importance = query_analysis.get('video_field_importance', 0)
            
            # STT 필드와 중요도 추출  
            stt_fields = query_analysis.get('stt_field', [])
            stt_importance = query_analysis.get('stt_field_importance', [])
            
            # 고유 필드와 중요도 추출
            unique_fields = query_analysis.get('unique_field', [])
            unique_importance = query_analysis.get('unique_field_importance', [])
            
            
            # 비디오 검색
            video_results = []
            if video_field:
                response = requests.post(
                    f"{API_ENDPOINTS['vectordb']}/query",
                    json={"input_text": video_field}
                )
                if response.status_code == 200:
                    video_results = response.json()
            
            # STT 검색
            stt_results = []
            if stt_fields:
                stt_search_text = ' '.join(stt_fields)
                response = requests.post(
                    f"{API_ENDPOINTS['vectordb']}/query_audio",
                    json={"input_text": stt_search_text}
                )
                if response.status_code == 200:
                    stt_results = response.json()
            
            meta_results = []
            if unique_fields:
                # unique_fields를 이용하여 메타데이터 검색 수행
                meta_results = search_movies_like(unique_fields)
            

            # 검색 결과 순위 매기기
            final_results = rank_search_results(
                video_results if video_results else [],
                stt_results if stt_results else [],
                meta_results if meta_results else []
            )
            
            return jsonify({"results": final_results})

        except Exception as e:
            logger.warning(f"쿼리 분석 실패, 원본 텍스트로 검색: {e}")
            # 실패 시 원본 텍스트로 양쪽 모두 검색
            video_response = requests.post(
                f"{API_ENDPOINTS['vectordb']}/query",
                json={"input_text": data['text']}
            )
            stt_response = requests.post(
                f"{API_ENDPOINTS['vectordb']}/query_audio",
                json={"input_text": data['text']}
            )
            
            meta_results = []
            if unique_fields:
                meta_results = search_movies_like(unique_fields)
            print("meta_results", meta_results)
            final_results = rank_search_results(video_response.json() if video_response.status_code == 200 else [], stt_response.json() if stt_response.status_code == 200 else [], meta_results if meta_results else [])
            return jsonify({"results": final_results})

    except Exception as e:
        error_msg = f"검색 중 오류 발생: {e}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500

def get_base_video_id(video_id):
    """비디오 ID에서 기본 ID 추출 (숫자 제외)"""
    import re
    # 문자열이 아니라면 문자열로 변환을 시도
    if not isinstance(video_id, str):
        try:
            video_id = str(video_id)
        except Exception:
            return ""
    return re.sub(r'_\d+$', '', video_id)

def rank_search_results(video_results, stt_results, meta_results):
    """검색 결과의 순위를 매기는 함수"""
    
    # video_results와 stt_results에서 ID 추출
    video_ids = set()
    if video_results and 'ids' in video_results and video_results['ids']:
        for id_list in video_results['ids']:
            for id in id_list:
                video_ids.add(get_base_video_id(id))
            
    stt_ids = set()
    if stt_results and 'ids' in stt_results and stt_results['ids']:
        for id_list in stt_results['ids']:
            for id in id_list:
                stt_ids.add(get_base_video_id(id))
            
    meta_ids = set()
    if meta_results:
        meta_ids = set(result['id'] for result in meta_results if isinstance(result, dict) and 'id' in result)
                
    print("video_ids", video_ids)
    print("stt_ids", stt_ids)
    print("meta_ids", meta_ids)
    
    ranked_results = []
    
    # 3개 모두 있는 경우
    if video_ids and stt_ids and meta_ids:
        print("3개 모두 있는 경우")
        # 1. 3개 모두 겹치는 결과
        triple_overlap = video_ids & stt_ids & meta_ids
        # 2. 비디오 + 메타 겹치는 결과 
        video_meta_overlap = video_ids & meta_ids - triple_overlap
        # 3. 비디오 + STT 겹치는 결과
        video_stt_overlap = video_ids & stt_ids - triple_overlap
        # 4. STT + 메타 겹치는 결과
        stt_meta_overlap = stt_ids & meta_ids - triple_overlap
        
        # 결과 순서대로 추가
        for video_id in triple_overlap:
            for i, id_list in enumerate(video_results['ids']):
                for j, vid in enumerate(id_list):
                    if get_base_video_id(vid) == video_id:
                        ranked_results.append({
                            'video_id': vid,
                            'metadata': video_results['metadatas'][i][j] if video_results['metadatas'] else None
                        })
        
        for video_id in video_meta_overlap | video_stt_overlap:
            for i, id_list in enumerate(video_results['ids']):
                for j, vid in enumerate(id_list):
                    if get_base_video_id(vid) == video_id:
                        ranked_results.append({
                            'video_id': vid,
                            'metadata': video_results['metadatas'][i][j] if video_results['metadatas'] else None
                        })
                        
        for video_id in stt_meta_overlap:
            for i, id_list in enumerate(stt_results['ids']):
                for j, vid in enumerate(id_list):
                    if get_base_video_id(vid) == video_id:
                        ranked_results.append({
                            'video_id': vid,
                            'metadata': stt_results['metadatas'][i][j] if stt_results['metadatas'] else None
                        })
                        
        # 5. 나머지 메타 결과
        remaining_meta = meta_ids - triple_overlap - video_meta_overlap - stt_meta_overlap
        for video_id in remaining_meta:
            meta_matches = [r for r in meta_results if isinstance(r, dict) and 'id' in r and r['id'] == video_id]
            if meta_matches:
                ranked_results.append(meta_matches[0])
                
    # 비디오 + 메타만 있는 경우
    elif video_ids and meta_ids and not stt_ids:
        print("비디오 + 메타만 있는 경우")
        overlap = video_ids & meta_ids
        for video_id in overlap:
            for i, id_list in enumerate(video_results['ids']):
                for j, vid in enumerate(id_list):
                    if get_base_video_id(vid) == video_id:
                        ranked_results.append({
                            'video_id': vid,
                            'metadata': video_results['metadatas'][i][j] if video_results['metadatas'] else None
                        })
                        
    # STT + 메타만 있는 경우
    elif stt_ids and meta_ids and not video_ids:
        print("STT + 메타만 있는 경우")
        overlap = stt_ids & meta_ids
        for video_id in overlap:
            for i, id_list in enumerate(stt_results['ids']):
                for j, vid in enumerate(id_list):
                    if get_base_video_id(vid) == video_id:
                        ranked_results.append({
                            'video_id': vid,
                            'metadata': stt_results['metadatas'][i][j] if stt_results['metadatas'] else None
                        })
        remaining_meta = [r for r in meta_results if isinstance(r, dict) and 'id' in r and r['id'] not in overlap]
        ranked_results.extend(remaining_meta[:30])
        
    # 비디오 + STT만 있는 경우
    elif video_ids and stt_ids and not meta_ids:
        print("비디오 + STT만 있는 경우")
        overlap = video_ids & stt_ids
        for video_id in overlap:
            for i, id_list in enumerate(video_results['ids']):
                for j, vid in enumerate(id_list):
                    if get_base_video_id(vid) == video_id:
                        ranked_results.append({
                            'video_id': vid,
                            'metadata': video_results['metadatas'][i][j] if video_results['metadatas'] else None
                        })
                        
    # 하나만 있는 경우
    else:
        print("하나만 있는 경우")
        if video_ids:
            for i, id_list in enumerate(video_results['ids']):
                for j, vid in enumerate(id_list):
                    ranked_results.append({
                        'video_id': vid,
                        'metadata': video_results['metadatas'][i][j] if video_results['metadatas'] else None
                    })
        elif stt_ids:
            for i, id_list in enumerate(stt_results['ids']):
                for j, vid in enumerate(id_list):
                    ranked_results.append({
                        'video_id': vid,
                        'metadata': stt_results['metadatas'][i][j] if stt_results['metadatas'] else None
                    })
        elif meta_ids:
            print("meta_ids만 있는 경우")
            ranked_results = [meta_results[0]]
            
    print("ranked_results 처리 완료")
    return ranked_results
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=30936, debug=True)
