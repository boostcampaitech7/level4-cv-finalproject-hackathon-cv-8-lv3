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

const ResultGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: ${({ theme }) => theme.spacing.medium};
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

const Caption = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.medium};
  line-height: 1.5;
  margin: 0;
  color: ${({ theme }) => theme.colors.text};
  overflow: hidden;
  transition: max-height 0.3s ease-in-out;
`;

const CaptionText = styled.p`
  margin: 0;
  padding: ${({ theme }) => theme.spacing.small} 0;
`;

const ExpandButton = styled.button`
  background: none;
  border: none;
  color: ${({ theme }) => theme.colors.primary};
  cursor: pointer;
  padding: ${({ theme }) => theme.spacing.small};
  font-size: ${({ theme }) => theme.fontSizes.small};
  
  &:hover {
    text-decoration: underline;
  }
`;

function TextToVideoSearch() {
  const [query, setQuery] = useState('');
  const [videoFiles, setVideoFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<{ video_id: string, metadata: any, distance: number }[]>([]);
  const [expandedCaptions, setExpandedCaptions] = useState<{[key: string]: boolean}>({});

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

  const toggleCaption = (videoId: string) => {
    setExpandedCaptions(prev => ({
      ...prev,
      [videoId]: !prev[videoId]
    }));
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

  const getVideoURL = (video_path: string): string => {
    if (video_path.startsWith('/data/ephemeral/home/movie_clips')) {
      const filename = video_path.replace('/data/ephemeral/home/movie_clips/', '');
      return `http://localhost:3002/videos/movie_clips/${filename}`;
    }
    if (video_path.startsWith('/data/ephemeral/home/new-data')) {
      const filename = video_path.replace('/data/ephemeral/home/new-data/', '');
      return `http://localhost:3002/videos/new-data/${filename}`;
    }
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
          <ResultGrid>
            {results.map((result, index) => {
              const { captions, start, end, video_path } = result.metadata;
              const computedVideoId = video_path.split('/').pop()?.replace('.mp4', '') || result.video_id;
              const formattedStart = new Date(start * 1000)
                .toISOString()
                .substr(11, 8);
              const formattedEnd = new Date(end * 1000)
                .toISOString()
                .substr(11, 8);
              const videoURL = getVideoURL(video_path);
              const isExpanded = expandedCaptions[result.video_id];

              return (
                <VideoWrapper key={result.video_id}>
                  <VideoId>
                    <strong>Video ID: </strong> {computedVideoId}
                  </VideoId>
                  <Caption>
                    <CaptionText>
                      <strong>Scene {index + 1}:</strong>{' '}
                      {isExpanded ? captions : captions.slice(0, 100) + '...'}
                    </CaptionText>
                    <ExpandButton onClick={() => toggleCaption(result.video_id)}>
                      {isExpanded ? '접기' : '펼치기'}
                    </ExpandButton>
                  </Caption>
                  <Timestamp>
                    ⏱ {formattedStart} - {formattedEnd}
                  </Timestamp>
                  <VideoClip
                    controls
                    onLoadedMetadata={(e) => {
                      e.currentTarget.currentTime = start;
                    }}
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
          </ResultGrid>
        </div>
      )}
    </Container>
  );
}

export default TextToVideoSearch;
