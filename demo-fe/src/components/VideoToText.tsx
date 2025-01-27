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

const ResultContainer = styled.div`
  margin-top: ${({ theme }) => theme.spacing.large};
  padding: ${({ theme }) => theme.spacing.medium};
  background-color: ${({ theme }) => theme.colors.background};
  border-radius: ${({ theme }) => theme.borderRadius};
`;

const ResultText = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.medium};
  line-height: 1.5;
`;

const Image = styled.img`
  width: 100%;
  height: auto;
  max-height: 200px;
  object-fit: cover;
  border-radius: ${({ theme }) => theme.borderRadius};
  margin-top: ${({ theme }) => theme.spacing.medium};
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

function VideoToText() {
  const [videoId, setVideoId] = useState('');
  const [timestamp, setTimestamp] = useState('');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [results, setResults] = useState<
    {
      videoId: string;
      timestamp: string;
      resultText: string;
      frameUrl: string;
    }[]
  >([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setVideoFile(e.target.files[0]);
    }
  };

  const handleSearch = () => {
    const currentVideoId = videoFile ? videoFile.name : videoId;

    if (!currentVideoId || !timestamp) {
      alert('Please provide both a video ID and timestamp.');
      return;
    }

    console.log('Video to Text:', currentVideoId, timestamp, videoFile);

    const newResult = {
      videoId: currentVideoId,
      timestamp,
      resultText: `Lorem ipsum dolor sit amet, consectetur adipiscing elit. Timestamp: ${timestamp}.`,
      frameUrl: `https://picsum.photos/seed/${timestamp}/300/200`,
    };

    setResults((prevResults) => [...prevResults, newResult]);

    setVideoId('');
    setTimestamp('');
  };

  return (
    <Container>
      <Title>Video to Text</Title>

      <Input
        type="text"
        placeholder="Enter Video ID"
        value={videoId}
        onChange={(e) => setVideoId(e.target.value)}
      />
      <Input
        type="text"
        placeholder="Enter Timestamp"
        value={timestamp}
        onChange={(e) => setTimestamp(e.target.value)}
      />

      <FileInputWrapper htmlFor="fileInput">
        {videoFile ? videoFile.name : 'Select a video file'}
      </FileInputWrapper>
      <FileInput
        id="fileInput"
        type="file"
        onChange={handleFileChange}
        accept="video/mp4, video/mpeg"
      />

      <Button onClick={handleSearch} disabled={!videoId || !timestamp}>
        Search
      </Button>

      {results.length > 0 ? (
        <div>
          <Title>Results</Title>
          {results.map((result) => (
            <ResultContainer key={`${result.videoId}-${result.timestamp}`}>
              <ResultText>
                <strong>Video ID:</strong>
                {result.videoId}
                <br />
                <strong>Timestamp:</strong>
                {result.timestamp}
                <br />
                <strong>Result:</strong>
                {result.resultText}
              </ResultText>
              <Image
                src={result.frameUrl}
                alt={`Frame for ${result.timestamp}`}
              />
            </ResultContainer>
          ))}
        </div>
      ) : (
        <p>No results yet</p>
      )}
    </Container>
  );
}

export default VideoToText;
