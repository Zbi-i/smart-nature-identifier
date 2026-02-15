import axios from 'axios';

// 从环境变量读取
const BASE_URL = import.meta.env.VITE_PYTHON_BACKEND_URL;

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000, // 60秒超时
});

export const api = {
  // 获取推荐列表
  getRecommendations: () => {
    return apiClient.get('/api/recommendations');
  },

  // 上传识别
  identifyImage: (file: File) => {
    const formData = new FormData();
    formData.append('image', file);
    return apiClient.post('/api/identify', formData);
  },

  // 语音合成 (供 VoiceReader 组件使用)
  // 注意：VoiceReader 内部直接用了 axios，之后最好也改成调这个方法，或者传 BaseURL 进去
  getBackendUrl: () => BASE_URL
};
