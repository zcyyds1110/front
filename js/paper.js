/**
 * 论文管理功能
 * 处理论文列表、详情等操作
 */

const paperManager = {
    /**
     * 加载论文列表
     */
    async loadPapers() {
        try {
            const response = await api.papers.getAll();
            this.renderPapers(response.data);
        } catch (error) {
            console.error('加载论文列表失败:', error);
            alert('加载论文列表失败: ' + error.message);
        }
    },
    
    /**
     * 渲染论文列表
     * @param {Array} papers - 论文数组
     */
    renderPapers(papers) {
        const container = document.getElementById('papersContainer');
        if (!container) return;
        
        if (papers.length === 0) {
            container.innerHTML = '<p>暂无论文数据</p>';
            return;
        }
        
        let html = `
            <table>
                <thead>
                    <tr>
                        <th>标题</th>
                        <th>作者</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        papers.forEach(paper => {
            const statusClass = this.getStatusClass(paper.status);
            const actions = this.getPaperActions(paper);
            
            html += `
                <tr>
                    <td>${paper.title}</td>
                    <td>${paper.author}</td>
                    <td><span class="${statusClass}">${paper.status}</span></td>
                    <td>${actions}</td>
                </tr>
            `;
        });
        
        html += `
                </tbody>
            </table>
        `;
        
        container.innerHTML = html;
        
        // 添加查看详情事件
        document.querySelectorAll('.view-paper').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const paperId = btn.getAttribute('data-id');
                window.location.href = `review.html?id=${paperId}`;
            });
        });
    },
    
    /**
     * 获取论文状态对应的CSS类
     * @param {string} status - 论文状态
     * @returns {string} CSS类名
     */
    getStatusClass(status) {
        const statusMap = {
            'PENDING': 'status-pending',
            'ASSIGNED': 'status-assigned',
            'REVIEWED': 'status-reviewed'
        };
        return statusMap[status] || '';
    },
    
    /**
     * 获取论文操作按钮
     * @param {Object} paper - 论文对象
     * @returns {string} 操作按钮HTML
     */
    getPaperActions(paper) {
        const role = auth.getCurrentUserRole();
        let actions = '';
        
        if (role === 'EXPERT' && paper.status === 'ASSIGNED') {
            actions += `<a href="review.html?id=${paper.id}" class="btn">评审</a> `;
        }
        
        actions += `<a href="#" class="btn view-paper" data-id="${paper.id}">查看</a>`;
        
        return actions;
    },
    
    /**
     * 加载论文详情
     * @param {string} paperId - 论文ID
     */
    async loadPaperDetails(paperId) {
        try {
            const response = await api.papers.getById(paperId);
            this.renderPaperDetails(response.data);
            
            // 如果是管理员，加载评审结果
            if (auth.getCurrentUserRole() === 'ADMIN') {
                this.loadPaperReviews(paperId);
            }
        } catch (error) {
            console.error('加载论文详情失败:', error);
            alert('加载论文详情失败: ' + error.message);
        }
    },
    
    /**
     * 渲染论文详情
     * @param {Object} paper - 论文对象
     */
    renderPaperDetails(paper) {
        const container = document.getElementById('paperDetails');
        if (!container) return;
        
        container.innerHTML = `
            <div class="card">
                <h3>${paper.title}</h3>
                <p><strong>作者:</strong> ${paper.author}</p>
                <p><strong>状态:</strong> <span class="${this.getStatusClass(paper.status)}">${paper.status}</span></p>
                ${paper.score ? `<p><strong>平均分:</strong> ${paper.score.toFixed(1)}</p>` : ''}
                <p><strong>摘要:</strong></p>
                <p>${paper.abstractText}</p>
                <a href="${paper.fileUrl}" class="btn" target="_blank">下载论文</a>
            </div>
        `;
    },
    
    /**
     * 加载论文评审结果
     * @param {string} paperId - 论文ID
     */
    async loadPaperReviews(paperId) {
        try {
            const response = await api.reviews.getByPaperId(paperId);
            this.renderPaperReviews(response.data);
        } catch (error) {
            console.error('加载评审结果失败:', error);
        }
    },
    
    /**
     * 渲染论文评审结果
     * @param {Array} reviews - 评审数组
     */
    renderPaperReviews(reviews) {
        const container = document.getElementById('paperReviews');
        if (!container || reviews.length === 0) return;
        
        let html = `
            <h3>评审结果</h3>
            <table>
                <thead>
                    <tr>
                        <th>评审专家</th>
                        <th>评分</th>
                        <th>评审意见</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        reviews.forEach(review => {
            html += `
                <tr>
                    <td>${review.reviewerName}</td>
                    <td>${review.score}</td>
                    <td>${review.comments || '无'}</td>
                </tr>
            `;
        });
        
        html += `
                </tbody>
            </table>
        `;
        
        container.innerHTML = html;
    }
};

// 全局可用
window.paperManager = paperManager;