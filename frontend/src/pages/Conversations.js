import React, { useEffect, useState } from 'react';
import './Conversations.css';

function Conversations() {
  const [conversations, setConversations] = useState([]);
  const [error, setError] = useState('');

  const apiUrl = 'https://bhbackend.whitecliff-47e35800.uksouth.azurecontainerapps.io';

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const response = await fetch(`${apiUrl}/latest_transcript_summary`);
        const data = await response.json();
        if (response.ok) {
          setConversations([data] || []);
        } else {
          setError(data.error || 'Failed to fetch conversations.');
        }
      } catch (err) {
        setError('Failed to connect to the server.');
      }
    };

    fetchConversations();
  }, []);

  return (
    <div className="conversations-container">
      <h1>Conversations 📚</h1>
      {error && <p className="error-message">{error}</p>}
      <ul>
        {conversations.map((conversation) => (
          <li key={conversation.id}>
            <strong>Date:</strong> {conversation.time} <br />
            <strong>Summary:</strong> {conversation.transcript_summary} <br />
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Conversations;