import React, { useState } from 'react';
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
  display: flex;
  justify-content: center;
  gap: ${({ theme }) => theme.spacing.medium};
`;

const ResultText = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.medium};
  line-height: 1.5;
  margin: 0;
`;

const CaptionItem = styled.div`
  padding: ${({ theme }) => theme.spacing.medium};
  margin-bottom: ${({ theme }) => theme.spacing.small};
  border: 1px solid #f5f5f5;
  border-radius: ${({ theme }) => theme.borderRadius};
  line-height: 1.5;
`;

const ScrollableContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.medium};
  max-height: 600px;
  overflow-y: auto;
  padding: ${({ theme }) => theme.spacing.medium};
  background-color: ${({ theme }) => theme.colors.background};
  border-radius: ${({ theme }) => theme.borderRadius};
  &::-webkit-scrollbar {
    width: 8px;
  }
  &::-webkit-scrollbar-thumb {
    background-color: ${({ theme }) => theme.colors.primary};
  }
  &::-webkit-scrollbar-track {
    background-color: ${({ theme }) => theme.colors.background};
  }
  scrollbar-width: thin;
  scrollbar-color: ${({ theme }) => theme.colors.primary} ${({ theme }) => theme.colors.background};
`;

const ResultTimestamp = styled.div`
  margin-top: ${({ theme }) => theme.spacing.xsmall};
  font-size: ${({ theme }) => theme.fontSizes.small};
  color: ${({ theme }) => theme.colors.textSecondary};
  display: flex;
  gap: ${({ theme }) => theme.spacing.small};
`;

function VideoToTextSearch() {
  const [videoId, setVideoId] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoCaptions, setVideoCaptions] = useState<any[]>([]);
  const [sttCaptions, setSttCaptions] = useState<any[]>([]);
  const [videoType, setVideoType] = useState<'unseen' | 'seen'>('unseen');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const file = e.target.files[0];
      if (file.size > 100 * 1024 * 1024) {
        alert('파일 크기는 100MB를 초과할 수 없습니다.');
        return;
      }
      setVideoFile(file);
      setError(null);
    }
  };

  const handleSearch = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const formData = new FormData();
      const timestamps = [
        {
          start: parseFloat(startTime),
          end: parseFloat(endTime)
        }
      ];

      if (parseFloat(startTime) >= parseFloat(endTime)) {
        throw new Error('시작 시간은 종료 시간보다 작아야 합니다.');
      }

      formData.append('timestamps', JSON.stringify(timestamps));

      if (videoType === 'seen') {
        formData.append('video_id', videoId);
      } else if (videoFile) {
        formData.append('video', videoFile);
      }

      const response = await fetch(
        `${process.env.REACT_APP_SERVER_URL}/process_video_with_timestamps`,
        {
          method: 'POST',
          body: formData
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '서버 오류가 발생했습니다.');
      }

      const data = await response.json();
      console.log('Server response:', data);

      // API 응답에 video_caption 데이터가 없으면 에러 처리
      if (!data.video_caption || data.video_caption.length === 0) {
        throw new Error('처리된 결과가 없습니다.');
      }

      // video_caption과 stt 데이터를 각각 상태에 저장합니다.
      setVideoCaptions(data.video_caption);
      setSttCaptions(data.stt || []);

      setVideoId('');
      setStartTime('');
      setEndTime('');
      setVideoFile(null);
    } catch (error) {
      console.error('Error:', error);
      setError(
        error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'
      );
    } finally {
      setIsLoading(false);
    }
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
          새로운 비디오
        </RadioLabel>
        <RadioLabel>
          <RadioInput
            type="radio"
            value="seen"
            checked={videoType === 'seen'}
            onChange={() => setVideoType('seen')}
          />
          기존 비디오
        </RadioLabel>
      </RadioGroup>

      {videoType === 'seen' && (
        <Input
          type="text"
          placeholder="비디오 ID를 입력하세요"
          value={videoId}
          onChange={(e) => setVideoId(e.target.value)}
        />
      )}

      <Input
        type="number"
        placeholder="시작 시간 (초)"
        value={startTime}
        onChange={(e) => setStartTime(e.target.value)}
        min="0"
        step="0.1"
      />

      <Input
        type="number"
        placeholder="종료 시간 (초)"
        value={endTime}
        onChange={(e) => setEndTime(e.target.value)}
        min="0"
        step="0.1"
      />

      {videoType === 'unseen' && (
        <FileInputWrapper htmlFor="fileInput">
          {videoFile ? videoFile.name : '비디오 파일을 선택하세요'}
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

      {error && (
        <ResultContainer style={{ backgroundColor: '#ffebee' }}>
          <ResultText style={{ color: '#c62828' }}>{error}</ResultText>
        </ResultContainer>
      )}

      <Button
        onClick={handleSearch}
        disabled={
          isLoading ||
          !startTime ||
          !endTime ||
          (videoType === 'seen' && !videoId) ||
          (videoType === 'unseen' && !videoFile)
        }
      >
        {isLoading ? '처리 중...' : '검색'}
      </Button>

      {videoCaptions.length > 0 || sttCaptions.length > 0 ? (
        <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
          {videoCaptions.length > 0 && (
            <div style={{ flex: 1 }}>
              <Title>비디오 캡션</Title>
              <ScrollableContainer>
                {videoCaptions.map((vc, index) => (
                  <CaptionItem key={index}>
                    <p>{vc.caption_kor}</p>
                    <p style={{ color: '#666' }}>{vc.caption_eng}</p>
                    <ResultTimestamp>
                      <span>
                        <strong>시작 시간:</strong> {vc.start_time}초
                      </span>
                      <span>
                        <strong>종료 시간:</strong> {vc.end_time}초
                      </span>
                    </ResultTimestamp>
                  </CaptionItem>
                ))}
              </ScrollableContainer>
            </div>
          )}

          {sttCaptions.length > 0 && (
            <div style={{ flex: 1 }}>
              <Title>STT 캡션</Title>
              <ScrollableContainer>
                {sttCaptions.map((stt, index) => (
                  <CaptionItem key={index}>
                    <p>{stt.caption_kor}</p>
                    <p style={{ color: '#666' }}>{stt.caption_eng}</p>
                    <ResultTimestamp>
                      <span>
                        <strong>시작 시간:</strong> {stt.start_time}초
                      </span>
                      <span>
                        <strong>종료 시간:</strong> {stt.end_time}초
                      </span>
                    </ResultTimestamp>
                  </CaptionItem>
                ))}
              </ScrollableContainer>
            </div>
          )}
        </div>
      ) : (
        <p>아직 결과가 없습니다</p>
      )}
    </Container>
  );
}

export default VideoToTextSearch;
