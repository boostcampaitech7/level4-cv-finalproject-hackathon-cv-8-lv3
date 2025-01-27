import styled from 'styled-components';
import { TextToVideo, VideoToText } from '../components';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: ${({ theme }) => theme.spacing.large};
`;

const Title = styled.h1`
  font-size: ${({ theme }) => theme.fontSizes.xlarge};
  text-align: center;
  margin-bottom: ${({ theme }) => theme.spacing.xlarge};
`;

const ComponentWrapper = styled.div`
  margin-bottom: ${({ theme }) => theme.spacing.xlarge};
`;

function Home() {
  return (
    <Container>
      <Title>Video Query to Frames Demo</Title>
      <ComponentWrapper>
        <VideoToText />
      </ComponentWrapper>
      <ComponentWrapper>
        <TextToVideo />
      </ComponentWrapper>
    </Container>
  );
}

export default Home;
