// frontend/src/components/Chat.js
import React, { useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';

function Chat() {
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState('');
    const [feedback, setFeedback] = useState('');
    const navigate = useNavigate();

    const handleGenerate = async () => {
        if (!query) return;
        try {
            const res = await api.post('/generate', { user_input: query, model_response: "" }); // Adjust based on backend
            setResponse(res.data.response);
        } catch (error) {
            if (error.response && error.response.status === 401) {
                navigate('/login');
            } else {
                alert("Error: " + (error.response.data.detail || "An error occurred."));
            }
        }
    }

    const handleFeedback = async () => {
        if (!feedback) return;
        try {
            await api.post('/feedback', {
                user_input: query,
                model_response: response,
                corrected_response: feedback
            });
            alert("Feedback submitted successfully.");
            setFeedback('');
        } catch (error) {
            alert("Feedback submission failed: " + (error.response.data.detail || "An error occurred."));
        }
    }

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    }

    return (
        <div>
            <h2>Chat Interface</h2>
            <button onClick={handleLogout}>Logout</button>
            <br /><br />
            <textarea
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Enter your query here..."
                rows="4"
                cols="50"
            /><br />
            <button onClick={handleGenerate}>Generate Response</button>

            <div>
                <h3>Response:</h3>
                <p>{response}</p>
            </div>

            <div>
                <h3>Provide Feedback</h3>
                <textarea
                    value={feedback}
                    onChange={e => setFeedback(e.target.value)}
                    placeholder="Provide your corrected response here..."
                    rows="4"
                    cols="50"
                /><br />
                <button onClick={handleFeedback}>Submit Feedback</button>
            </div>
        </div>
    );
}

export default Chat;
