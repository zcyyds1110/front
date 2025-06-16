/**
 * 认证相关功能
 * 处理用户登录、登出和认证状态
 */

const auth = {
    /**
     * 检查用户是否已认证
     * @returns {boolean} 是否已认证
     */
    isAuthenticated() {
        return !!localStorage.getItem('token');
    },
    
    /**
     * 获取当前用户角色
     * @returns {string|null} 用户角色或null
     */
    getCurrentUserRole() {
        const token = localStorage.getItem('token');
        if (!token) return null;
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.role;
        } catch (e) {
            console.error('解析token失败:', e);
            return null;
        }
    },
    
    /**
     * 登录成功后处理
     * @param {string} token - JWT token
     */
    handleLoginSuccess(token) {
        localStorage.setItem('token', token);
        
        // 根据角色重定向
        const role = this.getCurrentUserRole();
        if (role === 'ADMIN') {
            window.location.href = 'dashboard.html';
        } else {
            window.location.href = 'papers.html';
        }
    },
    
    /**
     * 登出
     */
    logout() {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
    },
    
    /**
     * 保护路由，未认证用户重定向到登录页
     */
    protectRoute() {
        if (!this.isAuthenticated() && !window.location.pathname.endsWith('login.html')) {
            window.location.href = 'login.html';
        }
    },
    
    /**
     * 检查用户权限
     * @param {string} requiredRole - 需要的角色
     * @returns {boolean} 是否有权限
     */
    checkPermission(requiredRole) {
        const role = this.getCurrentUserRole();
        if (!role) return false;
        
        // 管理员有所有权限
        if (role === 'ADMIN') return true;
        
        return role === requiredRole;
    },
    
    /**
     * 初始化导航栏
     */
    initNavigation() {
        const navElement = document.getElementById('nav');
        if (!navElement) return;
        
        const role = this.getCurrentUserRole();
        let navItems = '';
        
        if (this.isAuthenticated()) {
            navItems += `
                <li><a href="papers.html">论文列表</a></li>
                <li><a href="#" id="logoutBtn">退出</a></li>
            `;
            
            if (role === 'ADMIN') {
                navItems = `
                    <li><a href="dashboard.html">仪表盘</a></li>
                    <li><a href="papers.html">论文管理</a></li>
                    ${navItems}
                `;
            }
        } else {
            navItems = '<li><a href="login.html">登录</a></li>';
        }
        
        navElement.innerHTML = `<ul>${navItems}</ul>`;
        
        // 添加登出事件
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }
    }
};

// 全局可用
window.auth = auth;

// 页面加载时执行保护检查
document.addEventListener('DOMContentLoaded', () => {
    auth.protectRoute();
    auth.initNavigation();
});