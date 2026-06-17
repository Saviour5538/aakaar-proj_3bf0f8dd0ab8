import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

const baseURL = import.meta.env.VITE_API_URL || '';

const api: AxiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface RegisterResponse {
  token: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

export interface User {
  id: string;
  name: string;
  email: string;
  createdAt: string;
  updatedAt: string;
}

export interface UploadExcelRequest {
  file: File;
  chunkSize?: number;
  overlapPercentage?: number;
}

export interface UploadExcelResponse {
  sessionId: string;
  fileName: string;
  fileSize: number;
  chunkCount: number;
  message: string;
}

export interface Session {
  id: string;
  userId: string;
  fileName: string;
  fileSize: number;
  chunkCount: number;
  status: 'processing' | 'completed' | 'failed';
  createdAt: string;
  updatedAt: string;
}

export interface QueryRequest {
  sessionId: string;
  query: string;
}

export interface QueryResponse {
  answer: string;
  sources: Array<{
    chunkId: string;
    content: string;
    score: number;
  }>;
}

export const login = (data: LoginRequest): Promise<AxiosResponse<LoginResponse>> => {
  return api.post('/api/auth/login', data);
};

export const register = (data: RegisterRequest): Promise<AxiosResponse<RegisterResponse>> => {
  return api.post('/api/auth/register', data);
};

export const getCurrentUser = (): Promise<AxiosResponse<User>> => {
  return api.get('/api/users/me');
};

export const uploadExcel = (data: FormData): Promise<AxiosResponse<UploadExcelResponse>> => {
  return api.post('/api/upload/excel', data, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const getSessions = (): Promise<AxiosResponse<Session[]>> => {
  return api.get('/api/upload/sessions');
};

export const getSession = (sessionId: string): Promise<AxiosResponse<Session>> => {
  return api.get(`/api/upload/sessions/${sessionId}`);
};

export const deleteSession = (sessionId: string): Promise<AxiosResponse<void>> => {
  return api.delete(`/api/upload/sessions/${sessionId}`);
};

export const querySession = (data: QueryRequest): Promise<AxiosResponse<QueryResponse>> => {
  return api.post('/api/upload/query', data);
};