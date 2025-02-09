const express = require('express');
const path = require('path');
const app = express();

// '/videos/new-data' 경로로 요청하면 '/data/ephemeral/home/new-data' 폴더 내의 파일을 제공
app.use('/videos/new-data', express.static('/data/ephemeral/home/new-data'));

// '/videos/movie_clips' 경로로 요청하면 '/data/ephemeral/home/movie_clips' 폴더 내의 파일을 제공
app.use('/videos/movie_clips', express.static('/data/ephemeral/home/movie_clips'));

app.listen(3002, () => {
  console.log('Server is running on port 3002');
});
