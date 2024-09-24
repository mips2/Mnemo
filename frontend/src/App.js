import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Chat from './components/Chat';
import Login from './components/Login';
import Register from './components/Register';

function App() {
    const isAuthenticated = !!localStorage.getItem('token');

    return (
        <Router>
            <Routes>
                <Route path="/" element={isAuthenticated ? <Navigate to="/chat" /> : <Navigate to="/login" />} />
                <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/chat" />} />
                <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/chat" />} />
                <Route path="/chat" element={isAuthenticated ? <Chat /> : <Navigate to="/login" />} />
            </Routes>
        </Router>
    );
}

export default App;
