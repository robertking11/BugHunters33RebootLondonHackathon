import React, { useState } from 'react';
import './Joy.css';

function Joy() {
  const [phoneInput, setPhoneInput] = useState('');
  const [flashMessage, setFlashMessage] = useState('');
  const [flashCategory, setFlashCategory] = useState('');
  const [statusMsg, setStatusMsg] = useState('');
  const [callStatus, setCallStatus] = useState('');
  const [pollResult, setPollResult] = useState([]);

  const apiUrl = 'https://bhbackend.whitecliff-47e35800.uksouth.azurecontainerapps.io';

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('Form submitted with phone number:', phoneInput);
    try {
      const response = await fetch(`${apiUrl}/call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phoneInput }),
      });

      const data = await response.json();

      if (response.ok) {
        setFlashMessage('Call initiated successfully!');
        setFlashCategory('success');
        setStatusMsg(data.status_msg);
        setCallStatus(data.call_status);
        setPollResult(data.poll_result || []);
      } else {
        setFlashMessage(data.error || 'Something went wrong.');
        setFlashCategory('error');
      }
    } catch (error) {
      setFlashMessage('Failed to connect to the server.');
      setFlashCategory('error');
    }
  };

  return (
    <div className="form-container">
      <h1 className="form-title">Talk to Joy ✨</h1>
      <form onSubmit={handleSubmit} className="form">
        <label className="form-label">Enter a UK Phone Number</label>
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
  );
}

export default Joy;