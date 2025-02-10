# 🚀 코드 실행 방법
현재 모든 서버가 켜져 있는 상태입니다.
아래 절차에 따라 서버에 접속하고 기능을 사용할 수 있습니다.

<br />

## 🔗 서버 접속 방법
1. SSH로 서버에 접속

```
ssh -i cv-08.pem -p 31578 root@10.28.224.136
```

<br />

2. tmux 세션에 접속

터미널 2개를 열고 각각의 서버에 접속합니다.

- 터미널 1번 : Frontend 서버 접속

```
tmux attach -t frontend-0
```

- 터미널 2번 : Frontend Video 서버 접속

```
tmux attach -t front-vid-server-0
```

<br />

3. 웹 인터페이스 접속

브라우저에서 다음 주소로 이동

```
http://localhost:3000
```

원하는 기능을 선택하여 사용

<br />

## 🎥 기능 설명

<br />

### 1️⃣ Video to Text

<img width="628" alt="image" src="https://github.com/user-attachments/assets/ee019a20-ae51-4df8-8924-8d3ff6b14c20" />

기존 비디오를 선택하거나 직접 업로드한 후 타임스탬프를 입력하여 텍스트 변환을 수행합니다.

<br />

✅ 기존 비디오 활용

/data/ephemeral/home/movie_clips에 저장된 영상의 ID를 입력 (e.g, _8LrZ4NhPmk) <br />
타임스탬프를 입력하여 원하는 부분을 선택

<br />

📤 새로운 영상 업로드
파일 업로드 버튼을 클릭하여 새로운 영상을 업로드 <br />
타임스탬프를 입력하여 변환할 부분을 지정

<br />

### 2️⃣ Text to Video

<img width="624" alt="image" src="https://github.com/user-attachments/assets/85483b29-1b8e-4c75-97d5-1682958dfcc5" />


사용자가 검색어를 입력하면 해당 검색어와 관련된 비디오 클립을 찾아 출력합니다.

<br />

## 🔍 사용 방법

검색창에 원하는 키워드 입력
관련 비디오 장면(프레임) 및 타임스탬프가 포함된 결과 확인
