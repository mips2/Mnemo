// frontend/src/components/Register.js
import React, { useState } from 'react';
import axios from 'axios';

function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleRegister = async () => {
    try {
      await axios.post('http://localhost:8000/register', {
        email,
        password,
      });
      alert('Registration successful. Please login.');
      window.location.href = '/login';
    } catch (error) {
      alert('Registration failed. Email may already be in use.');
    }
  };

  return (
    <div>
      <h2>Register</h2>
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
      <button onClick={handleRegister}>Register</button>
    </div>
  );
}

export default Register;
