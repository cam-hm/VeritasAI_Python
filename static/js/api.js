/**
 * API Utility Functions
 * Centralized API calls and token management
 */

const API_BASE_URL = '/api';

// Token management
const TokenManager = {
    getAccessToken() {
        return localStorage.getItem('access_token');
    },
    
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },
    
    setTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
    },
    
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },
    
    isAuthenticated() {
        return !!this.getAccessToken();
    }
};

// API request helper
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = TokenManager.getAccessToken();
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };
    
    if (token && !options.skipAuth) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };
    
    try {
        const response = await fetch(url, config);
        
        // Handle 401 - try refresh token
        if (response.status === 401 && token && !options.skipAuth) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                // Retry request with new token
                config.headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
                const retryResponse = await fetch(url, config);
                return handleResponse(retryResponse);
            } else {
                // Refresh failed, redirect to login
                TokenManager.clearTokens();
                window.location.href = '/login';
                throw new Error('Authentication failed');
            }
        }
        
        return handleResponse(response);
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

async function handleResponse(response) {
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || data.detail || 'Request failed');
        }
        return data;
    } else {
        // Handle streaming response (SSE)
        return response;
    }
}

async function refreshAccessToken() {
    const refreshToken = TokenManager.getRefreshToken();
    if (!refreshToken) return false;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: refreshToken }),
        });
        
        if (response.ok) {
            const data = await response.json();
            TokenManager.setTokens(data.access, refreshToken);
            return true;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
    }
    
    return false;
}

// Authentication API
const AuthAPI = {
    async register(name, email, password, passwordConfirm) {
        const data = await apiRequest('/auth/register/', {
            method: 'POST',
            body: JSON.stringify({
                name,
                email,
                password,
                password_confirm: passwordConfirm,
            }),
            skipAuth: true,
        });
        
        if (data.tokens) {
            TokenManager.setTokens(data.tokens.access, data.tokens.refresh);
            localStorage.setItem('user', JSON.stringify(data.user));
        }
        
        return data;
    },
    
    async login(email, password) {
        const data = await apiRequest('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
            skipAuth: true,
        });
        
        if (data.tokens) {
            TokenManager.setTokens(data.tokens.access, data.tokens.refresh);
            localStorage.setItem('user', JSON.stringify(data.user));
        }
        
        return data;
    },
    
    async logout() {
        const refreshToken = TokenManager.getRefreshToken();
        if (refreshToken) {
            try {
                await apiRequest('/auth/logout/', {
                    method: 'POST',
                    body: JSON.stringify({ refresh: refreshToken }),
                });
            } catch (error) {
                console.error('Logout error:', error);
            }
        }
        TokenManager.clearTokens();
    },
};

// Documents API
const DocumentsAPI = {
    async list(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return apiRequest(`/documents/${queryString ? '?' + queryString : ''}`);
    },
    
    async get(documentId) {
        return apiRequest(`/documents/${documentId}/`);
    },
    
    async upload(file, category = null, tags = []) {
        const url = `${API_BASE_URL}/documents/upload/`;
        
        const formData = new FormData();
        formData.append('file', file);
        if (category) formData.append('category', category);
        if (tags.length) formData.append('tags', JSON.stringify(tags));
        
        // Helper function to make upload request with token
        const makeUploadRequest = async (token) => {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    // Don't set Content-Type, let browser set it with boundary for FormData
                },
                body: formData,
            });
            return response;
        };
        
        let token = TokenManager.getAccessToken();
        let response = await makeUploadRequest(token);
        
        // Handle 401 - try refresh token
        if (response.status === 401 && token) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                // Retry with new token
                token = TokenManager.getAccessToken();
                response = await makeUploadRequest(token);
            } else {
                // Refresh failed, redirect to login
                TokenManager.clearTokens();
                window.location.href = '/login';
                throw new Error('Authentication failed');
            }
        }
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ error: 'Upload failed' }));
            throw new Error(error.error || error.detail || 'Upload failed');
        }
        
        return await response.json();
    },
    
    async delete(documentId) {
        return apiRequest(`/documents/${documentId}/delete/`, {
            method: 'DELETE',
        });
    },
};

// Chat Sessions API
const ChatSessionsAPI = {
    async list() {
        return apiRequest('/chat/sessions/');
    },
    
    async create(title = 'New Conversation') {
        return apiRequest('/chat/sessions/create/', {
            method: 'POST',
            body: JSON.stringify({ title }),
        });
    },
    
    async get(sessionId) {
        return apiRequest(`/chat/sessions/${sessionId}/`);
    },
    
    async update(sessionId, data) {
        return apiRequest(`/chat/sessions/${sessionId}/update/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    },
    
    async delete(sessionId) {
        return apiRequest(`/chat/sessions/${sessionId}/delete/`, {
            method: 'DELETE',
        });
    },
};

// Chat Stream API
const ChatAPI = {
    async stream(messages, sessionId = null, documentId = null) {
        const url = `${API_BASE_URL}/chat/stream/`;
        const token = TokenManager.getAccessToken();
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({
                messages,
                session_id: sessionId ? parseInt(sessionId) : null,
                document_id: documentId ? parseInt(documentId) : null,
            }),
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ error: 'Request failed' }));
            throw new Error(error.error || error.detail || 'Chat request failed');
        }
        
        return response;
    },
};
