import { useNavigate } from "react-router-dom";
import styled from "styled-components";
import { StyledButton } from "../styles/StyledButton";

const PageToggleContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 50px;
  gap: 150px;
`;

const PageToggle = () => {
  const navigate = useNavigate();
  return (
    <PageToggleContainer>
      <StyledButton onClick={() => navigate("/")}>
        Video to Text
      </StyledButton>
      <StyledButton onClick={() => navigate("/text-to-video")} className="reverse">
        Text to Video
      </StyledButton>
    </PageToggleContainer>
  );
};

export default PageToggle;
