import type React from 'react';
import { useState } from 'react';
import {
  Container,
  Title,
  Input,
  Button,
  FileInputWrapper,
  FileInput,
} from '../styles/SharedStyles';
import styled from 'styled-components';

const SERVER_URL = import.meta.env.VITE_SERVER_URL;

const ResultContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.medium};
  margin-top: ${({ theme }) => theme.spacing.large};
`;

const VideoWrapper = styled.div`
  border: 1px solid ${({ theme }) => theme.colors.primary};
  border-radius: ${({ theme }) => theme.borderRadius};
  padding: ${({ theme }) => theme.spacing.medium};
  text-align: center;
`;

const Timestamp = styled.p`
  bottom: 0;
  left: 0;
  right: 0;
  background-color: rgba(0, 0, 0, 0.7);
  color: ${({ theme }) => theme.colors.text};
  padding: ${({ theme }) => theme.spacing.small};
  margin-top: ${({ theme }) => theme.spacing.large};
  font-size: ${({ theme }) => theme.fontSizes.small};
  text-align: center;
`;

const VideoClip = styled.video`
  width: 100%;
  max-width: 640px;
  height: auto;
  margin-top: ${({ theme }) => theme.spacing.large};
  border-radius: ${({ theme }) => theme.borderRadius};
`;

const VideoId = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.medium};
  line-height: 1.5;
  margin-top: ${({ theme }) => theme.spacing.medium};
  margin-bottom: ${({ theme }) => theme.spacing.medium};
  color: ${({ theme }) => theme.colors.text};
`;

const Caption = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.medium};
  line-height: 1.5;
  margin: 0;
  color: ${({ theme }) => theme.colors.text};
`;

function TextToVideoSearch() {
  const [query, setQuery] = useState('');
  const [videoFiles, setVideoFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<{ video_id: string, metadata: any, distance: number }[]>([]);

  const handleFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const file = e.target.files[0];
      if (file.size > 100 * 1024 * 1024) {
        alert('파일 크기는 100MB를 초과할 수 없습니다.');
        return;
      }
      setVideoFiles([file]);
      setError(null);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('검색어를 입력하세요.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log('Searching for:', query, videoFiles);

      const response = await fetch(`${SERVER_URL}/search_videos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: query }),
      });

      if (!response.ok) {
        throw new Error(`서버 오류 : ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Server response in T2V:', data);
      setResults(data.results);

    } catch (error) {
      setError(error instanceof Error ? error.message : '검색 실패');
    } finally {
      setIsLoading(false);
    }
  };

  // video_path를 이용해서 Express 서버에서 제공하는 URL로 변환하는 함수
  const getVideoURL = (video_path: string): string => {
    // movie_clips 경로로 시작하면
    if (video_path.startsWith('/data/ephemeral/home/movie_clips')) {
      const filename = video_path.replace('/data/ephemeral/home/movie_clips/', '');
      return `http://localhost:3002/videos/movie_clips/${filename}`;
    }
    // new-data 경로로 시작하면
    if (video_path.startsWith('/data/ephemeral/home/new-data')) {
      const filename = video_path.replace('/data/ephemeral/home/new-data/', '');
      return `http://localhost:3002/videos/new-data/${filename}`;
    }
    // 그 외의 경우 빈 문자열 반환
    return '';
  };

  return (
    <Container>
      <Title>Text to Video Search</Title>
      <Input
        type="text"
        placeholder="Enter your search query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <FileInputWrapper htmlFor="videoFiles">
        {videoFiles.length > 0
          ? `${videoFiles.length} files selected`
          : 'Select video files'}
      </FileInputWrapper>
      <FileInput
        id="videoFiles"
        type="file"
        onChange={handleFilesChange}
        multiple
        accept="video/mp4, video/mpeg"
      />
      <Button onClick={handleSearch} disabled={isLoading}>
        {isLoading ? 'Searching...' : 'Search'}
      </Button>

      {error && <p style={{ color: 'red', marginTop: '1rem' }}>{error}</p>}

      {results.length > 0 && (
        <div>
          <Title>Search Results</Title>
          <ResultContainer>
            {results.map((result, index) => {
              const { captions, start, end, video_path } = result.metadata;
              const formattedStart = new Date(start * 1000)
                .toISOString()
                .substr(11, 8);
              const formattedEnd = new Date(end * 1000)
                .toISOString()
                .substr(11, 8);

              // video_path에 따라 동영상 URL을 동적으로 생성
              const videoURL = getVideoURL(video_path);

              return (
                <VideoWrapper key={result.video_id}>
                  <VideoId>
                    <strong>Video ID: </strong> {result.video_id}
                  </VideoId>
                  <Caption>
                    <strong>Scene {index + 1}:</strong> {captions}
                  </Caption>
                  <Timestamp>
                    ⏱ {formattedStart} - {formattedEnd}
                  </Timestamp>
                  <VideoClip
                    controls
                    // 동영상 메타데이터가 로드되면 시작 시간으로 이동
                    onLoadedMetadata={(e) => {
                      // 재생 시작 시간을 검색 결과의 start 값으로 설정
                      e.currentTarget.currentTime = start;
                    }}
                    // 현재 재생 시간이 end 시간 이상이면 정지
                    onTimeUpdate={(e) => {
                      if (e.currentTarget.currentTime >= end) {
                        e.currentTarget.pause();
                      }
                    }}
                  >
                    <source src={videoURL} type="video/mp4" />
                  </VideoClip>
                </VideoWrapper>
              );
            })}
          </ResultContainer>
        </div>
      )}
    </Container>
  );
}

export default TextToVideoSearch;
