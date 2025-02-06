import styled from "styled-components";

export const StyledButton = styled.button`
  --background:rgb(76, 175, 80);
  --text: #fff;
  --font-size: 16px;
  --duration: 0.44s;
  --move-hover: -4px;
  --shadow: 0 2px 8px -1px rgba(76, 175, 80, 0.32);
  --shadow-hover: 0 4px 20px -2px rgba(76, 175, 80, 0.5);
  --font-shadow: var(--font-size);
  
  padding: 16px 32px;
  font-family: 'Roboto', sans-serif;
  font-weight: 500;
  line-height: var(--font-size);
  border-radius: 24px;
  display: inline-block;
  outline: none;
  appearance: none;
  border: none;
  text-decoration: none;
  font-size: var(--font-size);
  letter-spacing: 0.5px;
  background: var(--background);
  color: var(--text);
  box-shadow: var(--shadow);
  transform: translateY(var(--y, 0)) translateZ(0);
  transition: transform var(--duration) ease, box-shadow var(--duration) ease;
  cursor: pointer;

  &:hover {
    --y: var(--move-hover);
    --shadow: var(--shadow-hover);
    div span {
      --m: calc(var(--font-size) * -1);
    }
  }
`;
