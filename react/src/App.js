import React from 'react';
import { Routes, Route } from 'react-router-dom';

import Display from './display/Display';

const App = () => {
  return (
      <Routes>
        <Route exact path='/' element={<Display/>}></Route>
      </Routes>
  );
}

export default App;