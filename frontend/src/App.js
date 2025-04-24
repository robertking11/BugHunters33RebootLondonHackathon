import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Joy from './pages/Joy';
import Conversations from './pages/Conversations';
import Home from './pages/Home';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <div className="side-menu">
          <h2>Menu</h2>
          <ul>
            <li>
              <NavLink
                to="/"
                className={({ isActive }) => (isActive ? 'active-link' : '')}
              >
                Home
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/joy"
                className={({ isActive }) => (isActive ? 'active-link' : '')}
              >
                Talk to Joy
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/conversations"
                className={({ isActive }) => (isActive ? 'active-link' : '')}
              >
                Conversations
              </NavLink>
            </li>
          </ul>
        </div>
        <div className="content-container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/joy" element={<Joy />} />
            <Route path="/conversations" element={<Conversations />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;