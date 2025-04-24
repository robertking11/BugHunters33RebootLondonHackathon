import React, { useState } from 'react';
import './App.css';

function App() {
  const [phoneInput, setPhoneInput] = useState('');
  const [flashMessage, setFlashMessage] = useState('');
  const [flashCategory, setFlashCategory] = useState('');
  const [statusMsg, setStatusMsg] = useState('');
  const [callStatus, setCallStatus] = useState('');
  const [pollResult, setPollResult] = useState([]);

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Form submitted with phone number:', phoneInput);
  };

  return (
    <div className="app-container">
      <div className="form-container">
        <h1 className="form-title">Voice Agent Outbound Call</h1>
        <form onSubmit={handleSubmit} className="form">
          <label className="form-label">UK Phone Number</label>
          <input
            type="text"
            name="phone_number"
            value={phoneInput}
            onChange={(e) => setPhoneInput(e.target.value)}
            placeholder="e.g. 07xxxxxxxxx or +447xxxxxxxxx"
            className="form-input"
          />
          <button type="submit" className="form-button">
            Call
          </button>
        </form>
        {flashMessage && (
          <div className="flash-message">
            <div
              className={`flash-message-content ${
                flashCategory === 'error' ? 'flash-error' : 'flash-success'
              }`}
            >
              {flashMessage}
            </div>
          </div>
        )}
        {statusMsg && (
          <div className="status-message">
            <strong>API Response:</strong> {statusMsg}
          </div>
        )}
        {callStatus && (
          <div className="call-status">
            <strong>Call Status:</strong> {callStatus}
          </div>
        )}
        {pollResult.length > 0 && (
          <div className="poll-result">
            Status history: {pollResult.join(', ')}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;