import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Joy from './pages/Joy';
import Conversations from './pages/Conversations';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <div className="side-menu">
          <h2>Menu</h2>
          <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/joy">Talk to Joy</Link></li>
            <li><Link to="/conversations">Conversations</Link></li>
          </ul>
        </div>
        <div className="content-container">
          <Routes>
            <Route path="/" element={<h1>Welcome to the Voice Agent App</h1>} />
            <Route path="/joy" element={<Joy />} />
            <Route path="/conversations" element={<Conversations />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;