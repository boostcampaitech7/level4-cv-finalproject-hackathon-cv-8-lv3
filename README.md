#코드 실행 방법
현재 모든 서버가 켜져있는 상태입니다.
ssh로 10.28.224.136:30936로 들어오신 다음 터미널에
tmux attach -t frontend-0 명령어를 이용하여 세션에 들어갑니다.
tmux attach -t front-vid-server-0명령어를 이용하여 들어갑니다.
브라우저에서 localhost:3000으로 들어가서 원하는 기능을 선택합니다.

##Video_to_Text
1. 이미 movieclips에 있는 영상의 경우
기존 비디오를 누르고 /data/ephemeral/home/movie_clips에 있는 영상의 아이디를 입력하고 타임스탬프를 입력합니다.

2. 직접 영상을 업로드 하는 경우
영상을 업로드하고 타임스탬프를 입력합니다.

##Text_to_Video
검색어 입력합니다.

