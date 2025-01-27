import type React from 'react';
import { useState } from 'react';
import styled from 'styled-components';

const Container = styled.div`
  background-color: ${({ theme }) => theme.colors.inputBg};
  border-radius: ${({ theme }) => theme.borderRadius};
  padding: ${({ theme }) => theme.spacing.large};
`;

const Title = styled.h2`
  font-size: ${({ theme }) => theme.fontSizes.large};
  margin-bottom: ${({ theme }) => theme.spacing.medium};
`;

const Input = styled.input`
  width: 80%;
  padding: ${({ theme }) => theme.spacing.medium};
  margin-bottom: ${({ theme }) => theme.spacing.medium};
  border-radius: ${({ theme }) => theme.borderRadius};
  background-color: ${({ theme }) => theme.colors.background};
  color: ${({ theme }) => theme.colors.text};
  border: 1px solid ${({ theme }) => theme.colors.primary};
`;

const Button = styled.button`
  padding: ${({ theme }) => theme.spacing.medium}
    ${({ theme }) => theme.spacing.large};
  background-color: ${({ theme }) => theme.colors.primary};
  color: ${({ theme }) => theme.colors.text};
  border: none;
  border-radius: ${({ theme }) => theme.borderRadius};
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background-color: ${({ theme }) => theme.colors.secondary};
  }

  &:disabled {
    background-color: ${({ theme }) => theme.colors.disabled};
    cursor: not-allowed;
  }
`;

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

const FileInputWrapper = styled.label`
  display: block;
  width: 80%;
  padding: ${({ theme }) => theme.spacing.medium};
  margin-bottom: ${({ theme }) => theme.spacing.medium};
  border-radius: ${({ theme }) => theme.borderRadius};
  background-color: ${({ theme }) => theme.colors.background};
  color: ${({ theme }) => theme.colors.text};
  border: 1px solid ${({ theme }) => theme.colors.primary};
  cursor: pointer;
  text-align: center;
  font-size: ${({ theme }) => theme.fontSizes.medium};
  margin-bottom: ${({ theme }) => theme.spacing.medium};

  &:hover {
    background-color: ${({ theme }) => theme.colors.primary};
  }

  transition: background-color 0.3s;
`;

const FileInput = styled.input`
  display: none;
`;

function TextToVideo() {
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

    // 임시 데이터
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
      <Title>Text to Video</Title>
      <Input
        type="text"
        placeholder="Enter your search query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <FileInputWrapper htmlFor="videoFiles">
        Select video files
      </FileInputWrapper>
      <FileInput
        id="videoFiles"
        type="file"
        onChange={handleFilesChange}
        multiple
        accept="video/mp4, video/mpeg"
      />
      <Button onClick={handleSearch}>Search</Button>

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

export default TextToVideo;
