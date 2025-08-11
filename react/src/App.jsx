import './App.css';
import './bootstrap.min.css';
import Display from './display/Display';
import { GameProvider } from './GameContext';

function App() {
  return (
    <GameProvider>
      <Display />
    </GameProvider>
  );
}

export default App;