import { Route, Routes } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';

import theme from './styles/theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <Routes>
        <Route path="/" element={<App />} />
      </Routes>
    </ThemeProvider>
  );
}

export default App;
