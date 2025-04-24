import React, { useEffect, useState } from 'react';
import './Conversations.css';

function Conversations() {
  const [conversations, setConversations] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const response = await fetch('/conversations');
        const data = await response.json();
        if (response.ok) {
          setConversations(data.conversations || []);
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
      <h1>Conversations</h1>
      {error && <p className="error-message">{error}</p>}
      <ul>
        {conversations.map((conversation) => (
          <li key={conversation.id}>
            <strong>ID:</strong> {conversation.id} <br />
            <strong>Details:</strong> {conversation.details}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Conversations;