// frontend/src/components/Login.js
import React, { useState } from 'react';
import axios from 'axios';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const response = await axios.post('http://localhost:8000/login', {
        email,
        password,
      });
      localStorage.setItem('token', response.data.access_token);
      window.location.href = '/';
    } catch (error) {
      alert('Login failed. Please check your credentials.');
    }
  };

  return (
    <div>
      <h2>Login</h2>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      /><br/>
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      /><br/>
      <button onClick={handleLogin}>Login</button>
    </div>
  );
}

export default Login;
