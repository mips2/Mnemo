import React, { useState, useEffect } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';

function Chat() {
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState('');
    const [feedback, setFeedback] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        fetchChatHistory();
    }, []);

    const fetchChatHistory = async () => {
        try {
            const res = await api.get('/chat-history');
            setChatHistory(res.data);
        } catch (error) {
            handleError(error);
        }
    };

    const handleGenerate = async () => {
        if (!query.trim()) return;
        setLoading(true);
        try {
            const res = await api.post('/generate', { user_input: query });
            setResponse(res.data.response);
            setChatHistory([...chatHistory, { user_input: query, ai_response: res.data.response }]);
            setQuery('');
        } catch (error) {
            handleError(error);
        } finally {
            setLoading(false);
        }
    };

    const handleFeedback = async () => {
        if (!feedback.trim()) return;
        try {
            const lastChat = chatHistory[chatHistory.length - 1];
            await api.post('/feedback', {
                user_input: lastChat.user_input,
                ai_response: lastChat.ai_response,
                corrected_response: feedback
            });
            alert("Feedback submitted and model fine-tuned successfully.");
            setFeedback('');
        } catch (error) {
            handleError(error);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    const handleError = (error) => {
        if (error.response && error.response.status === 401) {
            navigate('/login');
        } else {
            alert("Error: " + (error.response?.data?.detail || "An error occurred."));
        }
    };

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2>Chat Interface</h2>
                <button onClick={handleLogout}>Logout</button>
            </div>

            <div style={{ height: '400px', overflowY: 'auto', border: '1px solid #ccc', padding: '10px', marginBottom: '20px' }}>
                {chatHistory.map((chat, index) => (
                    <div key={index} style={{ marginBottom: '10px' }}>
                        <p><strong>You:</strong> {chat.user_input}</p>
                        <p><strong>AI:</strong> {chat.ai_response}</p>
                    </div>
                ))}
            </div>

            <div style={{ display: 'flex', marginBottom: '20px' }}>
                <textarea
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    placeholder="Enter your query here..."
                    rows="3"
                    style={{ flex: 1, marginRight: '10px' }}
                />
                <button onClick={handleGenerate} disabled={loading || !query.trim()}>
                    {loading ? 'Generating...' : 'Generate Response'}
                </button>
            </div>

            <div style={{ marginTop: '20px' }}>
                <h3>Provide Feedback</h3>
                <textarea
                    value={feedback}
                    onChange={e => setFeedback(e.target.value)}
                    placeholder="Provide your corrected response here..."
                    rows="3"
                    style={{ width: '100%', marginBottom: '10px' }}
                />
                <button onClick={handleFeedback} disabled={!feedback.trim()}>Submit Feedback</button>
            </div>
        </div>
    );
}

export default Chat;
