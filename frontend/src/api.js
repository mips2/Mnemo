// frontend/src/api.js
import axios from 'axios';

const API_URL = "http://localhost:8000"; // Backend URL

const getToken = () => {
    return localStorage.getItem("token");
}

const api = axios.create({
    baseURL: API_URL,
});

api.interceptors.request.use(
    config => {
        const token = getToken();
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    response => response,
    error => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;
