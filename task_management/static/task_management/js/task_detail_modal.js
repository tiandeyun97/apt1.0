document.addEventListener('DOMContentLoaded', function() {
    // 复制按钮功能
    if (typeof ClipboardJS !== 'undefined') {
        new ClipboardJS('.btn-copy-code').on('success', function(e) {
            const originalTitle = e.trigger.getAttribute('title');
            e.trigger.setAttribute('title', '已复制！');
            
            // 恢复原始标题
            setTimeout(function() {
                e.trigger.setAttribute('title', originalTitle);
            }, 1500);
            
            e.clearSelection();
        });
    }
    
    // 任务详情数据加载
    function loadTaskDetails(taskId) {
        // 显示加载状态
        showLoading();
        
        // 发送AJAX请求获取任务详情
        fetch(`/task_management/api/tasks/${taskId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络响应异常');
                }
                return response.json();
            })
            .then(data => {
                // 控制台打印数据，用于调试
                console.log('任务详情数据:', data);
                // 填充任务详情数据
                populateTaskDetails(data);
                hideLoading();
            })
            .catch(error => {
                console.error('获取任务详情失败:', error);
                showError('无法加载任务详情，请稍后重试');
                hideLoading();
            });
    }
    
    // 填充任务详情
    function populateTaskDetails(task) {
        // 设置标题
        document.getElementById('task-detail-title').textContent = `任务详情: ${task.name}`;
        
        // 基本信息
        document.getElementById('task-detail-name').textContent = task.name || '-';
        document.getElementById('task-detail-advert-name').textContent = task.advert_name || '-';
        document.getElementById('task-detail-product-info').textContent = task.product_info || '-';
        document.getElementById('task-detail-backend').textContent = task.backend || '-';
        document.getElementById('task-detail-timezone-basic').textContent = task.timezone || '-';
        
        // 项目信息
        if (task.project) {
            // 项目信息使用嵌套对象属性
            const project = task.project;
            document.getElementById('task-detail-project').textContent = project.name || '-';
            document.getElementById('task-detail-media-channel').textContent = project.media_channel || '-';
            document.getElementById('task-detail-task-type').textContent = project.task_type || '-';
            document.getElementById('task-detail-kpi').textContent = project.kpi || '-';
            document.getElementById('task-detail-manager').textContent = project.manager || '-';
            document.getElementById('task-detail-status2').textContent = project.status2 || '-';
            document.getElementById('task-detail-product-backend').textContent = project.product_backend || '-';
            document.getElementById('task-detail-timezone').textContent = project.timezone || '-';
        
            // 日报链接处理
        const dailyReportLink = document.getElementById('task-detail-daily-report-link');
        const dailyReportText = document.querySelector('#task-detail-daily-report-link .link-text');
        
            if (project.daily_report_url && project.daily_report_url !== '-') {
                dailyReportLink.href = project.daily_report_url;
                dailyReportText.textContent = project.daily_report_url;
            document.getElementById('task-detail-daily-report').style.display = 'block';
            } else {
                document.getElementById('task-detail-daily-report').style.display = 'none';
            }
        } else {
            // 如果没有项目信息，所有项目相关字段显示默认值
            document.getElementById('task-detail-project').textContent = '-';
            document.getElementById('task-detail-media-channel').textContent = '-';
            document.getElementById('task-detail-task-type').textContent = '-';
            document.getElementById('task-detail-kpi').textContent = '-';
            document.getElementById('task-detail-manager').textContent = '-';
            document.getElementById('task-detail-status2').textContent = '-';
            document.getElementById('task-detail-product-backend').textContent = '-';
            document.getElementById('task-detail-timezone').textContent = '-';
            document.getElementById('task-detail-daily-report').style.display = 'none';
        }
        
        // 状态信息
        const statusElement = document.getElementById('task-detail-status');
        
        // 为状态添加样式
        if (task.status) {
            const statusName = task.status.name || '-';
            const statusId = task.status.id || '';
            statusElement.innerHTML = getStatusBadge(statusId, statusName);
        } else {
            statusElement.textContent = '-';
        }
        
        document.getElementById('task-detail-created-at').textContent = formatDateTime(task.created_at) || '-';
        document.getElementById('task-detail-start-date').textContent = formatDate(task.start_date) || '-';
        document.getElementById('task-detail-end-date').textContent = formatDate(task.end_date) || '-';
        
        // 广告信息
        const pixelElement = document.getElementById('task-detail-pixel');
        pixelElement.textContent = task.pixel || '-';
        
        // 投放链接
        const publishUrlLink = document.getElementById('task-detail-publish-url-link');
        const publishUrlText = document.querySelector('#task-detail-publish-url-link .link-text');
        
        if (task.publish_url) {
            publishUrlLink.href = task.publish_url;
            publishUrlText.textContent = task.publish_url;
        } else {
            publishUrlText.textContent = '-';
            publishUrlLink.removeAttribute('href');
        }
        
        // 其他信息
        if (task.optimizers && task.optimizers.length > 0) {
            const optimizerNames = task.optimizers.map(opt => opt.username).join(', ');
            document.getElementById('task-detail-optimizer').textContent = optimizerNames;
        } else {
            document.getElementById('task-detail-optimizer').textContent = '-';
        }
        document.getElementById('task-detail-notes').textContent = task.notes || '-';
        
        // 设置编辑按钮链接
        document.getElementById('task-detail-edit-btn').href = `/task_management/tasks/${task.id}/change/`;
    }
    
    // 获取状态徽章HTML
    function getStatusBadge(status, text) {
        const statusClasses = {
            'draft': 'badge-draft',
            'active': 'badge-active',
            'paused': 'badge-paused',
            'completed': 'badge-completed',
            'cancelled': 'badge-cancelled'
        };
        
        const badgeClass = statusClasses[status] || 'badge-secondary';
        return `<span class="badge badge-status ${badgeClass}">${text}</span>`;
    }
    
    // 格式化日期时间
    function formatDateTime(dateTimeStr) {
        if (!dateTimeStr) return '-';
        
        const date = new Date(dateTimeStr);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    // 格式化日期
    function formatDate(dateStr) {
        if (!dateStr) return '-';
        
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    }
    
    // 显示加载状态
    function showLoading() {
        // 可以添加加载动画或遮罩
    }
    
    // 隐藏加载状态
    function hideLoading() {
        // 移除加载动画或遮罩
    }
    
    // 显示错误信息
    function showError(message) {
        alert(message);
    }
    
    // 监听模态框打开事件
    const taskDetailModal = document.getElementById('taskDetailModal');
    if (taskDetailModal) {
        taskDetailModal.addEventListener('show.bs.modal', function(event) {
            // 添加安全检查，防止button未定义错误
            const button = event.relatedTarget;
            
            // 只有当存在触发元素时才从其获取任务ID
            if (button && button.getAttribute) {
                const taskId = button.getAttribute('data-task-id');
            if (taskId) {
                loadTaskDetails(taskId);
            }
            }
            // 如果是通过JS代码直接打开模态框，data-task-id会由task_list.js处理
        });
        
        // 监听模态框隐藏事件，确保背景遮罩被完全清除
        taskDetailModal.addEventListener('hidden.bs.modal', function () {
            // 移除所有可能残留的模态框背景
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => {
                backdrop.remove();
            });
            
            // 移除body上的modal类，确保滚动恢复正常
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        });
    }
}); 