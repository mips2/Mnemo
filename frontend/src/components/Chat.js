// frontend/src/components/Chat.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Chat() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [feedback, setFeedback] = useState('');

  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token) {
      window.location.href = '/login';
    }
  }, [token]);

  const handleGenerate = async () => {
    try {
      const res = await axios.post(
        'http://localhost:8000/generate',
        { text: query },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResponse(res.data.response);
    } catch (error) {
      alert('Error generating response.');
    }
  };

  const handleFeedback = async () => {
    if (!response) {
      alert('No response to provide feedback for.');
      return;
    }
    try {
      await axios.post(
        'http://localhost:8000/feedback',
        {
          user_input: query,
          model_response: response,
          feedback: feedback,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('Feedback submitted. Thank you!');
      setFeedback('');
    } catch (error) {
      alert('Error submitting feedback.');
    }
  };

  return (
    <div>
      <h1>Dynamic Memory Transformer</h1>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter your query here..."
      /><br/>
      <button onClick={handleGenerate}>Generate Response</button>
      
      {response && (
        <div>
          <h2>Response:</h2>
          <p>{response}</p>
        </div>
      )}

      {response && (
        <div>
          <h2>Provide Feedback</h2>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Provide your feedback here..."
          /><br/>
          <button onClick={handleFeedback}>Submit Feedback</button>
        </div>
      )}
    </div>
  );
}

export default Chat;
