import os
import json
import cv2
from caption_maker import generate_video_captions
from tqdm import tqdm

def create_dataset():
    # API 키 설정
    api_key = ['API_KEY']
    # 비디오 파일이 있는 디렉토리 경로
    video_dir = "/data/ephemeral/home/tmp"
    
    # 결과를 저장할 딕셔너리
    dataset = {}
    
    # 기존 annotation.json 파일이 있다면 불러오기
    if os.path.exists("annotation.json"):
        with open("annotation.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
    
    # 비디오 파일 목록 가져오기
    video_files = [f for f in os.listdir(video_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
    
    print(f"\n총 {len(video_files)}개의 비디오 파일을 처리합니다.")
    
    # tqdm으로 진행률 표시
    for video_file in tqdm(video_files, desc="비디오 처리 중"):
        # 이미 처리된 비디오는 건너뛰기
        if video_file in dataset:
            continue
            
        video_path = os.path.join(video_dir, video_file)
        
        # 비디오 메타데이터 추출
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        # 파일 정보 추출
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB 단위
        cap.release()
        
        # 캡션 생성
        success = False
        for i, key in enumerate(api_key):
            try:
                captions = generate_video_captions(video_path, key)
                success = True
                print(f"캡션 생성 성공 ({video_file})")
                # 사용한 API 키를 리스트 맨 뒤로 이동
                api_key.append(api_key.pop(i))
                break
            except Exception as e:
                print(f"\n캡션 생성 중 오류 발생 ({video_file}): {str(e)}")
                if i < len(api_key) - 1:
                    print(f"{video_file}에 대해 {i+2}번째 API 키로 재시도...")
                else:
                    print(f"모든 API 키 시도 실패 ({video_file})")
                    captions = ""
                    with open("failed_videos.txt", "a", encoding="utf-8") as f:
                        f.write(f"{video_file}\n")
            
        # 데이터셋에 추가
        dataset[video_file] = {
            "video_file_name": video_file,
            "captions": captions,
            "width": width,
            "height": height,
            "duration": duration,
            "fps": fps,
            "frame_count": frame_count,
            "file_size_mb": round(file_size, 2),
        }
        
        # 각 비디오 처리 후 JSON 파일 업데이트
        with open("annotation.json", "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=4)
    
    print("\n모든 비디오 처리가 완료되었습니다.")
    print(f"성공적으로 처리된 비디오: {len(dataset)}개")
    
    # 실패한 비디오 수 계산
    try:
        with open("failed_videos.txt", "r", encoding="utf-8") as f:
            failed_count = len(f.readlines())
        print(f"실패한 비디오: {failed_count}개")
    except FileNotFoundError:
        print("실패한 비디오 없음")
    
    print("데이터셋 생성이 완료되었습니다.")

if __name__ == "__main__":
    create_dataset()
