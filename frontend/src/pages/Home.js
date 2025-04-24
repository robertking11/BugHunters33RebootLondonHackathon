import React from 'react';
import './Home.css';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Joy from './Joy';

function Home() {
  //TODO: Research for what wording to use to make it more palatable to stressed people
  //TODO: 
  return (
    <div>
      <h1 className="home-title">Welcome to the Lloyds Banking Group Financial Helppage</h1>
      <div className="home-container">
        <h1 className="home-title">Financial Help</h1>
        <h1 className="home-text">Lloyds has dedicated support for customers facing financial difficulties or money worries. They encourage customers to get in touch sooner rather than later.</h1>
      </div>
      <div className="home-container">
        <h1 className="home-title">Mental Help</h1>
      </div>
      <div className="home-container">
        <h1 className="home-title">Talk to Joy</h1>
        <h1 className="home-text">Speak to Joy, our latest AI chatbot.</h1>
        <div className="home-button-wrapper">
          <Link className="home-button" to="/joy">Talk to Joy</Link>
          <Routes>
            <Route className="home-button" path="/joy" element={<Joy />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default Home;