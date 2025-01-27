import type React from 'react';
import { useState } from 'react';
import {
  Container,
  Title,
  Input,
  Button,
  FileInputWrapper,
  FileInput,
  RadioGroup,
  RadioLabel,
  RadioInput,
} from '../styles/SharedStyles';
import styled from 'styled-components';

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

function VideoToTextSearch() {
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
  const [videoType, setVideoType] = useState<'unseen' | 'seen'>('unseen');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setVideoFile(e.target.files[0]);
    }
  };

  const handleSearch = () => {
    const currentVideoId = videoType === 'unseen' ? 'unseen' : videoId;

    if (
      !timestamp ||
      (videoType === 'seen' && !videoId) ||
      (videoType === 'unseen' && !videoFile)
    ) {
      alert('Please provide all required information.');
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
      <Title>Video to Text Search</Title>

      <RadioGroup>
        <RadioLabel>
          <RadioInput
            type="radio"
            value="unseen"
            checked={videoType === 'unseen'}
            onChange={() => setVideoType('unseen')}
          />
          Unseen Video
        </RadioLabel>
        <RadioLabel>
          <RadioInput
            type="radio"
            value="seen"
            checked={videoType === 'seen'}
            onChange={() => setVideoType('seen')}
          />
          Seen Video
        </RadioLabel>
      </RadioGroup>

      {videoType === 'seen' && (
        <Input
          type="text"
          placeholder="Enter Video ID"
          value={videoId}
          onChange={(e) => setVideoId(e.target.value)}
        />
      )}

      <Input
        type="text"
        placeholder="Enter Timestamp"
        value={timestamp}
        onChange={(e) => setTimestamp(e.target.value)}
      />

      {videoType === 'unseen' && (
        <FileInputWrapper htmlFor="fileInput">
          {videoFile ? videoFile.name : 'Select a video file'}
        </FileInputWrapper>
      )}
      {videoType === 'unseen' && (
        <FileInput
          id="fileInput"
          type="file"
          onChange={handleFileChange}
          accept="video/mp4, video/mpeg"
        />
      )}

      <Button
        onClick={handleSearch}
        disabled={
          !timestamp ||
          (videoType === 'seen' && !videoId) ||
          (videoType === 'unseen' && !videoFile)
        }>
        Search
      </Button>

      {results.length > 0 ? (
        <div>
          <Title>Results</Title>
          {results.map((result) => (
            <ResultContainer key={`${result.videoId}-${result.timestamp}`}>
              <ResultText>
                <strong>Video ID:</strong> {result.videoId}
                <br />
                <strong>Timestamp:</strong> {result.timestamp}
                <br />
                <strong>Result:</strong> {result.resultText}
              </ResultText>
              <Image
                src={result.frameUrl || '/placeholder.svg'}
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

export default VideoToTextSearch;
