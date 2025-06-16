/**
 * 评审管理功能
 * 处理论文评审相关操作
 */

const reviewManager = {
    /**
     * 初始化评审表单
     */
    initReviewForm() {
        const form = document.getElementById('reviewForm');
        if (!form) return;
        
        // 获取URL中的论文ID
        const urlParams = new URLSearchParams(window.location.search);
        const paperId = urlParams.get('id');
        
        if (!paperId) {
            alert('无效的论文ID');
            window.location.href = 'papers.html';
            return;
        }
        
        // 加载论文信息
        paperManager.loadPaperDetails(paperId);
        
        // 表单提交处理
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const score = document.getElementById('score').value;
            const comments = document.getElementById('comments').value;
            
            if (!score || score < 0 || score > 100) {
                alert('请输入0-100之间的有效分数');
                return;
            }
            
            try {
                await api.reviews.submit(paperId, parseInt(score), comments);
                alert('评审提交成功！');
                window.location.href = 'papers.html';
            } catch (error) {
                console.error('提交评审失败:', error);
                alert('提交评审失败: ' + error.message);
            }
        });
    },
    
    /**
     * 加载专家待评审论文
     */
    async loadAssignedReviews() {
        try {
            const response = await api.reviews.getAssigned();
            this.renderAssignedReviews(response.data);
        } catch (error) {
            console.error('加载待评审论文失败:', error);
            alert('加载待评审论文失败: ' + error.message);
        }
    },
    
    /**
     * 渲染待评审论文列表
     * @param {Array} reviews - 评审任务数组
     */
    renderAssignedReviews(reviews) {
        const container = document.getElementById('reviewsContainer');
        if (!container) return;
        
        if (reviews.length === 0) {
            container.innerHTML = '<p>当前没有待评审的论文</p>';
            return;
        }
        
        let html = `
            <table>
                <thead>
                    <tr>
                        <th>论文标题</th>
                        <th>作者</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        reviews.forEach(review => {
            const paper = review.paper;
            html += `
                <tr>
                    <td>${paper.title}</td>
                    <td>${paper.author}</td>
                    <td><span class="${paperManager.getStatusClass(paper.status)}">${paper.status}</span></td>
                    <td><a href="review.html?id=${paper.id}" class="btn">开始评审</a></td>
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
window.reviewManager = reviewManager;