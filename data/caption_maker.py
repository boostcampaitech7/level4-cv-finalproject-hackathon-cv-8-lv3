import google.generativeai as genai
import time
import json


def generate_video_captions(video_file_path, api_key): 
    """
    비디오 파일로부터 자막을 생성하는 함수
    
    Args:
        video_file_path (str): 비디오 파일 경로
        api_key (str): Gemini API 키
        
    Returns:
        str: 생성된 자막 텍스트
    """
    # API 키 설정
    genai.configure(api_key=api_key)

    # 비디오 파일 업로드
    print(f"파일 업로드 중...")
    video_file = genai.upload_file(path=video_file_path)
    print(f"업로드 완료: {video_file.uri}")

    # 파일 처리 상태 확인
    while video_file.state.name == "PROCESSING":
        print('.', end='')
        time.sleep(10)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(video_file.state.name)

    # 프롬프트 생성
    prompt = "For each scene in this video, create a caption that describes the scene. Voice is not considered at this time. Places each caption in an object sent to set_timecodes along with the video caption's timecode. And it only outputs in json format."

    # Gemini 모델 선택
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")

    # LLM 요청 실행
    print("LLM 추론 요청 중...")
    response = model.generate_content([video_file, prompt],
                                    request_options={"timeout": 600})

    json_str = response.text.split('```json')[1].split('```')[0]
    captions = json.loads(json_str)
    return captions

if __name__ == "__main__":
    video_path = "/data/ephemeral/home/YouTube-8M/youtube_1.mp4"
    api_key = "AIzaSyCuadcShzS4VInscqtEX2lOaUAwxAyU1uc"
    
    result = generate_video_captions(video_path, api_key)
    print(result)