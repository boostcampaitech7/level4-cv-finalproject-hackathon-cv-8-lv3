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

const ImageContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: ${({ theme }) => theme.spacing.medium};
  margin-top: ${({ theme }) => theme.spacing.large};
`;

const ImageWrapper = styled.div`
  position: relative;
`;

const Image = styled.img`
  width: 100%;
  height: 100px;
  object-fit: cover;
  border-radius: ${({ theme }) => theme.borderRadius};
`;

const Timestamp = styled.p`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: rgba(0, 0, 0, 0.7);
  color: ${({ theme }) => theme.colors.text};
  padding: ${({ theme }) => theme.spacing.small};
  margin: 0;
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

function TextToVideoSearch() {
  const [query, setQuery] = useState('');
  const [videoFiles, setVideoFiles] = useState<File[]>([]);
  const [frames, setFrames] = useState<string[]>([]);
  const [timestamps, setTimestamps] = useState<string[]>([]);
  const [videoClip, setVideoClip] = useState<string | null>(null);

  const handleFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setVideoFiles(Array.from(e.target.files));
    }
  };

  const handleSearch = () => {
    console.log('Searching for:', query, videoFiles);

    setFrames([
      'https://picsum.photos/seed/1/300/200',
      'https://picsum.photos/seed/2/300/200',
      'https://picsum.photos/seed/3/300/200',
      'https://picsum.photos/seed/4/300/200',
      'https://picsum.photos/seed/5/300/200',
    ]);
    setTimestamps(['00:01:10', '00:02:20', '00:03:30', '00:04:40', '00:05:50']);
    setVideoClip('/mov_bbb.mp4');
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
      <Button
        onClick={handleSearch}
        disabled={!query || videoFiles.length === 0}>
        Search
      </Button>

      {frames.length > 0 && (
        <div>
          <Title>Search Results</Title>
          <ImageContainer>
            {frames.map((frame, index) => (
              <ImageWrapper key={frame}>
                <Image
                  src={frame || '/placeholder.svg'}
                  alt={`Frame ${index + 1}`}
                />
                <Timestamp>{timestamps[index]}</Timestamp>
              </ImageWrapper>
            ))}
          </ImageContainer>

          {videoClip && (
            <VideoClip src={videoClip} controls>
              <track kind="captions" />
            </VideoClip>
          )}
        </div>
      )}
    </Container>
  );
}

export default TextToVideoSearch;
