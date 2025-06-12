/**
 * 完成对账页面脚本
 */

// 全局变量，用于存储模态框实例
let detailModalInstance = null;
let attachmentModalInstance = null;

// DOM 加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM已加载，初始化脚本...');
    
    try {
        // 预先创建模态框实例
        initModals();
        
        // 初始化查看详情按钮事件
        initViewDetailButtons();
        
        // 初始化附件按钮事件
        initAttachmentButtons();
        
        // 初始化刷新按钮
        initRefreshButton();
        
        // 初始化导出Excel按钮
        initExportButton();
        
        console.log('所有初始化完成');
    } catch (error) {
        console.error('初始化过程中发生错误:', error);
    }
});

/**
 * 初始化模态框实例
 */
function initModals() {
    console.log('初始化模态框实例...');
    const detailModalElement = document.getElementById('detailModal');
    const attachmentModalElement = document.getElementById('attachmentModal');
    
    try {
        if (detailModalElement) {
            detailModalInstance = new bootstrap.Modal(detailModalElement);
            console.log('详情模态框实例化成功');
        } else {
            console.error('未找到详情模态框元素');
        }
        
        if (attachmentModalElement) {
            attachmentModalInstance = new bootstrap.Modal(attachmentModalElement);
            console.log('附件模态框实例化成功');
        } else {
            console.error('未找到附件模态框元素');
        }
    } catch (error) {
        console.error('模态框实例化失败:', error);
    }
}

/**
 * 初始化查看详情按钮事件
 */
function initViewDetailButtons() {
    console.log('初始化查看详情按钮...');
    const viewDetailButtons = document.querySelectorAll('.btn-view-detail');
    console.log(`找到 ${viewDetailButtons.length} 个查看详情按钮`);
    
    if (viewDetailButtons.length === 0) {
        console.log('没有找到查看详情按钮，跳过初始化');
        return;
    }
    
    if (!detailModalInstance) {
        console.error('详情模态框实例未初始化，跳过绑定查看详情按钮事件');
        return;
    }
    
    viewDetailButtons.forEach(button => {
        button.addEventListener('click', function() {
            try {
                console.log('点击了查看详情按钮');
                const recordId = this.getAttribute('data-id');
                console.log('记录ID:', recordId);
                const row = this.closest('tr');
                
                if (!row) {
                    console.error('未找到行元素');
                    return;
                }
                
                // 获取基本信息
                const period = row.querySelector('td:nth-child(2)')?.textContent || '';
                const project = row.querySelector('.project-name')?.textContent || '';
                const task = row.querySelector('.task-name')?.textContent || '';
                const actualConsumption = row.querySelector('td:nth-child(5)')?.textContent || '';
                const fbConsumption = row.querySelector('td:nth-child(6)')?.textContent || '';
                
                // 获取差异值
                const diffElement = row.querySelector('td:nth-child(7)');
                const difference = diffElement ? diffElement.textContent.trim() : '';
                
                // 填充模态框数据
                const detailProjectElement = document.getElementById('detail-project');
                const detailTaskElement = document.getElementById('detail-task');
                const detailPeriodElement = document.getElementById('detail-period');
                const detailActualConsumptionElement = document.getElementById('detail-actual-consumption');
                const detailFbConsumptionElement = document.getElementById('detail-fb-consumption');
                const detailCreatedAtElement = document.getElementById('detail-created-at');
                
                if (detailProjectElement) detailProjectElement.textContent = project;
                if (detailTaskElement) detailTaskElement.textContent = task;
                if (detailPeriodElement) detailPeriodElement.textContent = period;
                if (detailActualConsumptionElement) detailActualConsumptionElement.textContent = actualConsumption;
                if (detailFbConsumptionElement) detailFbConsumptionElement.textContent = fbConsumption;
                if (detailCreatedAtElement) detailCreatedAtElement.textContent = new Date().toLocaleDateString();
                
                if (difference) {
                    const diffMatch = difference.match(/¥\s*([\d\.]+)/);
                    const percentMatch = difference.match(/\(([\d\.\-\+]+%)\)/);
                    
                    const detailDifferenceElement = document.getElementById('detail-difference');
                    const detailDifferencePercentageElement = document.getElementById('detail-difference-percentage');
                    
                    if (diffMatch && detailDifferenceElement) {
                        detailDifferenceElement.textContent = diffMatch[0];
                    }
                    
                    if (percentMatch && detailDifferencePercentageElement) {
                        detailDifferencePercentageElement.textContent = percentMatch[1];
                    }
                }
                
                // 加载历史记录
                if (recordId) {
                    loadHistoryRecords(recordId);
                }
                
                // 加载附件列表
                loadAttachments(recordId);
                
                // 显示模态框
                detailModalInstance.show();
                console.log('成功显示详情模态框');
            } catch (error) {
                console.error('显示详情模态框失败:', error);
            }
        });
    });
    console.log('查看详情按钮初始化完成');
}

/**
 * 加载记录详情
 * @param {string} recordId 记录ID
 * @param {Function} callback 回调函数
 */
function loadRecordDetails(recordId, callback) {
    console.log('加载记录详情，记录ID:', recordId);
    // 这里应该发送AJAX请求获取详情数据
    // 为了演示，直接获取表格中的数据
    const row = document.querySelector(`tr[data-id="${recordId}"]`);
    
    if (row) {
        const cells = row.querySelectorAll('td');
        const diffText = cells[6].textContent.trim();
        const difference = diffText.split('(')[0].trim();
        const percentageMatch = diffText.match(/\((.*?)\)/);
        const differencePercentage = percentageMatch ? percentageMatch[1] : '0%';
        const statusBadge = cells[7].querySelector('.badge');
        const isManuallyConfirmed = statusBadge && statusBadge.classList.contains('bg-info');
        
        const data = {
            id: recordId,
            period: cells[1].textContent,
            project: row.querySelector('.project-name').textContent,
            task: row.querySelector('.task-name').textContent,
            actualConsumption: cells[4].textContent,
            fbConsumption: cells[5].textContent,
            difference: difference,
            differencePercentage: differencePercentage,
            status: isManuallyConfirmed ? '手动确认' : '完成对账',
            isManuallyConfirmed: isManuallyConfirmed,
            createdAt: new Date().toLocaleString(),
            confirmedBy: '系统',
            confirmedAt: new Date().toLocaleString()
        };
        
        callback(data);
    }
}

/**
 * 填充详情模态框
 * @param {Object} data 详情数据
 */
function fillDetailModal(data) {
    document.getElementById('detail-project').textContent = data.project;
    document.getElementById('detail-task').textContent = data.task;
    document.getElementById('detail-period').textContent = data.period;
    document.getElementById('detail-created-at').textContent = data.createdAt;
    document.getElementById('detail-actual-consumption').textContent = data.actualConsumption;
    document.getElementById('detail-fb-consumption').textContent = data.fbConsumption;
    document.getElementById('detail-difference').textContent = data.difference;
    document.getElementById('detail-difference-percentage').textContent = data.differencePercentage;
    
    // 确认方式
    document.getElementById('detail-confirm-type').textContent = data.isManuallyConfirmed ? '手动确认' : '自动确认';
    
    // 如果是手动确认，显示确认人
    const confirmRow = document.getElementById('detail-confirm-row');
    if (data.isManuallyConfirmed) {
        confirmRow.style.display = '';
        document.getElementById('detail-confirmed-by').textContent = data.confirmedBy;
    } else {
        confirmRow.style.display = 'none';
    }
}

/**
 * 加载历史记录
 * @param {string} recordId 记录ID
 */
function loadHistoryRecords(recordId) {
    console.log('加载历史记录，记录ID:', recordId);
    const historyList = document.getElementById('history-list');
    const noHistory = document.getElementById('no-history');
    
    if (!historyList) {
        console.error('未找到ID为history-list的元素');
        return;
    }
    
    // 清空历史记录
    historyList.innerHTML = '';
    
    // 显示加载中
    historyList.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">加载历史记录中...</p></div>';
    
    // 获取CSRF令牌
    const csrfToken = getCsrfToken();
    
    // 发送AJAX请求获取历史记录
    fetch(`/reconciliation/api/record/${recordId}/history/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('获取历史记录失败');
        }
        return response.json();
    })
    .then(data => {
        console.log('获取到历史记录数据:', data);
        
        if (data.histories && data.histories.length > 0) {
            // 清空历史记录列表
            historyList.innerHTML = '';
            
            // 添加历史记录
            data.histories.forEach(history => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                
                // 根据操作类型设置不同的徽章颜色
                let badgeClass = 'bg-info';
                if (history.action === 'confirm') {
                    badgeClass = 'bg-success';
                } else if (history.action === 'create') {
                    badgeClass = 'bg-primary';
                }
                
                historyItem.innerHTML = `
                    <div class="history-action">
                        <span class="badge ${badgeClass}">${history.action_display}</span>
                    </div>
                    <div class="history-content">
                        <div class="history-title">${history.note || '无备注'}</div>
                        <div class="history-detail">
                            ${history.old_status ? `<div>旧状态: <span class="badge bg-secondary">${history.old_status_display}</span></div>` : ''}
                            <div>新状态: <span class="badge bg-info">${history.new_status_display}</span></div>
                        </div>
                        <div class="history-footer">
                            <span class="history-user">${history.operated_by}</span>
                            <span class="history-time">${history.operated_at}</span>
                        </div>
                    </div>
                `;
                
                historyList.appendChild(historyItem);
            });
            
            // 隐藏无历史记录提示
            if (noHistory) {
                noHistory.classList.add('d-none');
            }
        } else {
            // 显示无历史记录提示
            historyList.innerHTML = '';
            if (noHistory) {
                noHistory.classList.remove('d-none');
            } else {
                historyList.innerHTML = `
                    <div class="text-center p-4">
                        <i class="fas fa-history text-muted mb-2" style="font-size: 2rem;"></i>
                        <p class="mb-0 text-muted">暂无历史记录</p>
                    </div>
                `;
            }
        }
    })
    .catch(error => {
        console.error('获取历史记录出错:', error);
        historyList.innerHTML = `
            <div class="text-center p-4">
                <i class="fas fa-exclamation-circle text-danger mb-2" style="font-size: 2rem;"></i>
                <p class="mb-0 text-danger">加载历史记录失败</p>
                <button class="btn btn-sm btn-outline-primary mt-2" onclick="loadHistoryRecords('${recordId}')">重试</button>
            </div>
        `;
    });
}

/**
 * 加载附件列表
 * @param {string} recordId 记录ID
 */
function loadAttachments(recordId) {
    const attachmentsList = document.getElementById('attachments-list');
    const attachmentsLoading = document.getElementById('attachments-loading');
    const noAttachments = document.getElementById('no-attachments');
    const attachmentCount = document.getElementById('attachment-count');
    const attachmentsContainer = document.getElementById('attachments-container');
    
    // 显示容器
    attachmentsContainer.classList.remove('d-none');
    
    // 显示加载中，隐藏其他
    attachmentsLoading.classList.remove('d-none');
    attachmentsList.classList.add('d-none');
    noAttachments.classList.add('d-none');
    
    // 获取CSRF令牌
    const csrfToken = getCsrfToken();
    
    // 发送AJAX请求获取附件列表
    fetch(`/reconciliation/api/record/${recordId}/attachments/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('获取附件列表失败');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 隐藏加载中
            attachmentsLoading.classList.add('d-none');
            
            // 更新计数
            attachmentCount.textContent = data.count;
            
            if (data.attachments.length > 0) {
                // 显示附件列表
                attachmentsList.classList.remove('d-none');
                
                // 清空附件列表
                attachmentsList.innerHTML = '';
                
                // 创建附件网格
                const attachmentsGrid = document.createElement('div');
                attachmentsGrid.className = 'attachments-grid';
                
                // 添加附件
                data.attachments.forEach(attachment => {
                    const attachmentCard = createAttachmentCard(attachment);
                    attachmentsGrid.appendChild(attachmentCard);
                });
                
                attachmentsList.appendChild(attachmentsGrid);
            } else {
                // 显示暂无附件
                noAttachments.classList.remove('d-none');
            }
        } else {
            alert('获取附件列表失败: ' + data.message);
            attachmentsLoading.classList.add('d-none');
            noAttachments.classList.remove('d-none');
        }
    })
    .catch(error => {
        console.error('获取附件列表出错:', error);
        attachmentsLoading.classList.add('d-none');
        noAttachments.classList.remove('d-none');
        attachmentCount.textContent = '0';
    });
}

/**
 * 创建附件卡片
 * @param {Object} attachment 附件数据
 * @returns {HTMLElement} 附件卡片元素
 */
function createAttachmentCard(attachment) {
    const attachmentCard = document.createElement('div');
    attachmentCard.className = 'attachment-card';
    
    // 构建HTML
    let cardContent = '';
    
    if (attachment.is_image) {
        // 图片附件
        cardContent = `
            <div class="attachment-img-container">
                <img src="${attachment.file_url}" alt="${attachment.file_name}" class="attachment-img">
            </div>
        `;
    } else {
        // 非图片附件
        cardContent = `
            <div class="attachment-img-container d-flex align-items-center justify-content-center">
                <i class="fas fa-file fa-3x text-muted"></i>
            </div>
        `;
    }
    
    // 添加附件信息
    cardContent += `
        <div class="attachment-info">
            <div class="attachment-name" title="${attachment.file_name}">${attachment.file_name}</div>
            <div class="attachment-meta">
                <span>${attachment.file_size} KB</span>
                <span title="${attachment.uploaded_at}"><i class="fas fa-clock me-1"></i>${formatDate(attachment.uploaded_at)}</span>
            </div>
            <div class="attachment-actions">
                <a href="${attachment.file_url}" class="btn btn-sm btn-outline-primary" target="_blank" download>
                    <i class="fas fa-download"></i>
                </a>
                ${attachment.is_image ? `
                <button type="button" class="btn btn-sm btn-outline-info view-image" data-url="${attachment.file_url}" data-filename="${attachment.file_name}">
                    <i class="fas fa-search-plus"></i>
                </button>
                ` : ''}
            </div>
        </div>
    `;
    
    attachmentCard.innerHTML = cardContent;
    
    // 添加查看图片事件
    const viewImageButton = attachmentCard.querySelector('.view-image');
    if (viewImageButton) {
        viewImageButton.addEventListener('click', function() {
            const imageUrl = this.getAttribute('data-url');
            const fileName = this.getAttribute('data-filename');
            
            // 设置全屏图片
            document.getElementById('fullscreen-image').src = imageUrl;
            document.getElementById('fullscreenImageModalLabel').textContent = fileName;
            document.getElementById('download-image').href = imageUrl;
            document.getElementById('download-image').setAttribute('download', fileName);
            
            // 显示模态框
            const fullscreenImageModal = new bootstrap.Modal(document.getElementById('fullscreenImageModal'));
            fullscreenImageModal.show();
        });
    }
    
    return attachmentCard;
}

/**
 * 格式化日期
 * @param {string} dateString 日期字符串
 * @returns {string} 格式化后的日期
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

/**
 * 初始化附件按钮事件
 */
function initAttachmentButtons() {
    console.log('初始化附件按钮事件...');
    const attachmentButtons = document.querySelectorAll('.btn-add-attachment');
    console.log(`找到 ${attachmentButtons.length} 个附件按钮`);
    
    if (attachmentButtons.length === 0) {
        console.log('没有找到附件按钮，跳过初始化');
        return;
    }
    
    if (!attachmentModalInstance) {
        console.error('附件模态框实例未初始化，跳过绑定附件按钮事件');
        return;
    }
    
    attachmentButtons.forEach(button => {
        button.addEventListener('click', function() {
            try {
                console.log('点击了附件按钮');
                const recordId = this.getAttribute('data-id');
                console.log('记录ID:', recordId);
                const row = this.closest('tr');
                
                if (!row) {
                    console.error('未找到行元素');
                    return;
                }
                
                const taskName = row.querySelector('.task-name')?.textContent || '';
                
                // 填充模态框数据
                const recordIdElement = document.getElementById('attachment-record-id');
                const taskNameElement = document.getElementById('attachment-task-name');
                const fileInputElement = document.getElementById('attachment-file');
                
                if (recordIdElement) recordIdElement.value = recordId;
                if (taskNameElement) taskNameElement.value = taskName;
                if (fileInputElement) fileInputElement.value = '';
                
                // 加载已上传附件
                loadModalAttachments(recordId);
                
                // 显示模态框
                attachmentModalInstance.show();
                console.log('成功显示附件模态框');
            } catch (error) {
                console.error('显示附件模态框失败:', error);
            }
        });
    });
    
    // 上传附件按钮事件
    const saveButton = document.getElementById('save-attachment');
    if (saveButton) {
        console.log('初始化保存附件按钮');
        saveButton.addEventListener('click', function() {
            try {
                console.log('点击了保存附件按钮');
                const recordIdElement = document.getElementById('attachment-record-id');
                const fileInputElement = document.getElementById('attachment-file');
                
                if (!recordIdElement || !fileInputElement) {
                    console.error('未找到必要的表单元素');
                    return;
                }
                
                const recordId = recordIdElement.value;
                
                // 表单验证
                if (!fileInputElement.files.length) {
                    alert('请选择文件');
                    return;
                }
                
                // 文件大小验证（最大5MB）
                const file = fileInputElement.files[0];
                if (file.size > 5 * 1024 * 1024) {
                    alert('文件大小不能超过5MB');
                    return;
                }
                
                // 发送上传请求
                uploadAttachment(recordId, file, () => {
                    // 重新加载附件列表
                    loadModalAttachments(recordId);
                    
                    // 清空文件输入框
                    fileInputElement.value = '';
                });
            } catch (error) {
                console.error('保存附件失败:', error);
            }
        });
    } else {
        console.error('未找到ID为save-attachment的元素');
    }
}

/**
 * 加载模态框中的附件列表
 * @param {string} recordId 记录ID
 */
function loadModalAttachments(recordId) {
    console.log('加载模态框附件列表，记录ID:', recordId);
    const attachmentTable = document.getElementById('modal-attachment-list');
    
    if (!attachmentTable) {
        console.error('未找到附件列表元素');
        return;
    }
    
    // 清空附件列表
    attachmentTable.innerHTML = '<tr><td colspan="5" class="text-center py-3"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">加载附件中...</p></td></tr>';
    
    // 获取CSRF令牌
    const csrfToken = getCsrfToken();
    
    // 这里应该发送AJAX请求获取附件列表
    // 为了演示，添加一条示例记录
    setTimeout(() => {
        attachmentTable.innerHTML = `
            <tr>
                <td><i class="fas fa-file-pdf me-2"></i>对账单.pdf</td>
                <td>258 KB</td>
                <td>系统管理员</td>
                <td>${new Date().toLocaleString()}</td>
                <td>
                    <a href="#" class="btn btn-sm btn-outline-primary"><i class="fas fa-download me-1"></i>下载</a>
                    <button type="button" class="btn btn-sm btn-outline-danger ms-1" onclick="deleteAttachment('12345')"><i class="fas fa-trash-alt"></i></button>
                </td>
            </tr>
        `;
    }, 500);
}

/**
 * 上传附件
 * @param {string} recordId 记录ID
 * @param {File} file 文件
 * @param {Function} callback 回调函数
 */
function uploadAttachment(recordId, file, callback) {
    console.log('上传附件，记录ID:', recordId);
    // 创建FormData对象
    const formData = new FormData();
    formData.append('attachment_file', file);
    
    // 获取CSRF令牌
    const csrfToken = getCsrfToken();
    
    // 显示上传中提示
    const saveButton = document.getElementById('save-attachment');
    const originalText = saveButton.innerHTML;
    saveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>上传中...';
    saveButton.disabled = true;
    
    // 发送AJAX请求
    fetch(`/reconciliation/record/${recordId}/upload/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.ok) {
            // 上传成功
            alert('附件上传成功');
            callback();
        } else {
            // 上传失败
            alert('附件上传失败，请重试');
        }
    })
    .catch(error => {
        console.error('上传附件出错:', error);
        alert('上传附件时出错，请稍后重试');
    })
    .finally(() => {
        // 恢复按钮状态
        saveButton.innerHTML = originalText;
        saveButton.disabled = false;
    });
}

/**
 * 删除附件
 * @param {string} attachmentId 附件ID
 */
function deleteAttachment(attachmentId) {
    console.log('删除附件，附件ID:', attachmentId);
    if (!confirm('确定要删除此附件吗？此操作无法撤销。')) {
        return;
    }
    
    // 获取CSRF令牌
    const csrfToken = getCsrfToken();
    
    // 这里应该发送AJAX请求删除附件
    // 为了演示，直接显示成功消息
    alert('附件删除成功');
    
    // 重新加载附件列表
    const recordId = document.getElementById('attachment-record-id').value;
    loadModalAttachments(recordId);
}

/**
 * 初始化刷新按钮
 */
function initRefreshButton() {
    console.log('初始化刷新按钮...');
    const refreshButton = document.getElementById('btn-refresh');
    
    if (!refreshButton) {
        console.error('未找到ID为btn-refresh的元素');
        return;
    }
    
    refreshButton.addEventListener('click', function() {
        console.log('点击了刷新按钮');
        window.location.reload();
    });
    console.log('刷新按钮初始化完成');
}

/**
 * 初始化导出Excel按钮
 */
function initExportButton() {
    console.log('初始化导出Excel按钮...');
    const exportButton = document.getElementById('btn-export-excel');
    
    if (!exportButton) {
        console.error('未找到ID为btn-export-excel的元素');
        return;
    }
    
    exportButton.addEventListener('click', function() {
        console.log('点击了导出Excel按钮');
        const yearSelect = document.getElementById('year-select');
        const monthSelect = document.getElementById('month-select');
        const projectSelect = document.getElementById('project-select');
        
        const year = yearSelect ? yearSelect.value : new Date().getFullYear();
        const month = monthSelect ? monthSelect.value : (new Date().getMonth() + 1);
        const project = projectSelect ? projectSelect.value : '';
        
        // 获取当前页面的状态（等待对账、异常对账或完成对账）
        let status = 'completed';
        
        // 构建导出URL
        let url = `/reconciliation/export/?year=${year}&month=${month}&status=${status}`;
        if (project) {
            url += `&project=${project}`;
        }
        
        console.log('导出URL:', url);
        window.open(url, '_blank');
    });
    console.log('导出Excel按钮初始化完成');
}

/**
 * 获取CSRF令牌
 * @returns {string} CSRF令牌
 */
function getCsrfToken() {
    // 从cookie中获取CSRF令牌
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
} 