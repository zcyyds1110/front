/**
 * API服务封装
 * 提供与后端交互的统一接口
 */

const API_BASE_URL = 'http://localhost:8080/api';

const api = {
    /**
     * 通用请求方法
     * @param {string} endpoint - API端点
     * @param {string} method - HTTP方法
     * @param {object} data - 请求数据
     * @returns {Promise} 返回Promise对象
     */
    async request(endpoint, method = 'GET', data = null) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
        };
        
        // 添加认证token
        const token = localStorage.getItem('token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const config = {
            method,
            headers,
        };
        
        if (data) {
            config.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, config);
            
            // 处理无内容响应（如204）
            if (response.status === 204) {
                return { success: true };
            }
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || '请求失败');
            }
            
            return result;
        } catch (error) {
            console.error(`API请求错误: ${method} ${endpoint}`, error);
            throw error;
        }
    },
    
    // 认证相关API
    auth: {
        login(username, password) {
            return api.request('/auth/login', 'POST', { username, password });
        },
        getCurrentUser() {
            return api.request('/auth/me');
        }
    },
    
    // 论文相关API
    papers: {
        getAll() {
            return api.request('/papers');
        },
        getById(id) {
            return api.request(`/papers/${id}`);
        },
        create(paperData) {
            return api.request('/papers', 'POST', paperData);
        }
    },
    
    // 评审相关API
    reviews: {
        submit(paperId, score, comments) {
            return api.request('/reviews', 'POST', { paperId, score, comments });
        },
        getAssigned() {
            return api.request('/reviews/assigned');
        },
        getByPaperId(paperId) {
            return api.request(`/papers/${paperId}/reviews`);
        }
    },
    
    // 管理员API
    admin: {
        assignPapers() {
            return api.request('/admin/assign', 'POST');
        },
        getAllUsers() {
            return api.request('/admin/users');
        }
    }
};

// 全局可用
window.api = api;