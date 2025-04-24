import React from 'react';
import './Home.css';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Joy from './Joy';

function Home() {
  //Wording follows ISO 9241-110:2020 – Ergonomics of human-system interaction
  //https://www.gov.uk/service-manual/design/writing-for-user-interfaces
  //TODO: Research for what wording to use to make it more palatable to stressed people
  // Acknowledge the emotion (without being dramatic)
  // Don’t use metaphors or idioms (can be misinterpreted)
  // Be clear and direct (no euphemisms)  
  // Avoid passive voice — use active verbs so users know what to do next
  // Minimize steps — simplify interactions
  
  return (
    <div>
      <h1 className="home-title">Welcome to the Lloyds Banking Group Financial Helppage</h1>
      <div className="home-container">
        <h1 className="home-title">Financial Help</h1>
        <h1 className="home-text">Many people face financial stress, but you are not alone. We have dedicated support for customers facing financial difficulties or money worries. Users in any stage of financial stress are encouraged to use them.</h1>
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