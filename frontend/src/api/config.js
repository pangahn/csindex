// API配置
export const API_BASE_URL = 'http://localhost:5001';

// 创建axios实例
import axios from 'axios';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// 请求拦截器
api.interceptors.request.use(
  config => {
    console.log('API请求:', config.method?.toUpperCase(), config.url);
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  response => {
    console.log('API响应:', response.status, response.config.url);
    return response;
  },
  error => {
    console.error('API错误:', error.response?.status, error.config?.url, error.message);
    return Promise.reject(error);
  }
);

export default api;