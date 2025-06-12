/**
 * 异常对账页面脚本
 */

// 全局变量，用于存储模态框实例
let detailModalInstance = null;
let solveModalInstance = null;

// DOM 加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM已加载，初始化脚本...');
    
    try {
        // 预先创建模态框实例
        initModals();
        
        // 初始化修改FB消耗按钮事件
        initEditFbButtons();
        
        // 初始化手动确认按钮事件
        initManualConfirmButtons();
        
        // 初始化查看详情按钮事件
        initViewDetailButtons();
        
        // 初始化刷新按钮
        initRefreshButton();
        
        // 初始化导出Excel按钮
        initExportButton();
        
        // 初始化解决异常对账按钮事件 - 来自详情模态框
        initSolveModalButton();
        
        // 初始化解决方式切换事件
        initSolutionTypeChange();
        
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
    const solveModalElement = document.getElementById('solveExceptionModal');
    
    try {
        if (detailModalElement) {
            detailModalInstance = new bootstrap.Modal(detailModalElement);
            console.log('详情模态框实例化成功');
        } else {
            console.error('未找到详情模态框元素');
        }
        
        if (solveModalElement) {
            solveModalInstance = new bootstrap.Modal(solveModalElement);
            console.log('解决异常模态框实例化成功');
        } else {
            console.error('未找到解决异常模态框元素');
        }
    } catch (error) {
        console.error('模态框实例化失败:', error);
    }
}

/**
 * 初始化修改FB消耗按钮事件
 */
function initEditFbButtons() {
    console.log('初始化修改FB消耗按钮...');
    const editFbButtons = document.querySelectorAll('.btn-edit-fb');
    
    if (editFbButtons.length === 0) {
        console.log('没有找到修改FB消耗按钮，跳过初始化');
        return;
    }
    
    const fbConsumptionModalElement = document.getElementById('fbConsumptionModal');
    
    if (!fbConsumptionModalElement) {
        console.error('未找到ID为fbConsumptionModal的元素，跳过初始化');
        return;
    }
    
    try {
        const fbConsumptionModal = new bootstrap.Modal(fbConsumptionModalElement);
        console.log('FB消耗模态框实例化成功');
        
        const saveButton = document.getElementById('save-fb-consumption');
        
        editFbButtons.forEach(button => {
            button.addEventListener('click', function() {
                const recordId = this.getAttribute('data-id');
                const row = this.closest('tr');
                const taskName = row.querySelector('.task-name').textContent;
                const actualConsumption = row.querySelectorAll('td')[4].textContent;
                const fbConsumption = row.querySelectorAll('td')[5].textContent;
                
                // 填充模态框数据
                document.getElementById('record-id').value = recordId;
                
                const taskNameElement = document.getElementById('task-name');
                if (taskNameElement) taskNameElement.value = taskName;
                
                const actualConsumptionElement = document.getElementById('actual-consumption');
                if (actualConsumptionElement) actualConsumptionElement.value = actualConsumption;
                
                const fbConsumptionElement = document.getElementById('fb-consumption');
                if (fbConsumptionElement) fbConsumptionElement.value = fbConsumption;
                
                const consumptionNoteElement = document.getElementById('consumption-note');
                if (consumptionNoteElement) consumptionNoteElement.value = '';
                
                // 显示模态框
                fbConsumptionModal.show();
            });
        });
        
        // 保存FB消耗按钮事件
        if (saveButton) {
            saveButton.addEventListener('click', function() {
                const recordId = document.getElementById('record-id').value;
                const fbConsumptionElement = document.getElementById('fb-consumption');
                const noteElement = document.getElementById('consumption-note');
                
                if (!fbConsumptionElement) {
                    console.error('未找到FB消耗输入框');
                    return;
                }
                
                const fbConsumption = fbConsumptionElement.value;
                const note = noteElement ? noteElement.value : '';
                
                // 表单验证
                if (!fbConsumption) {
                    alert('请输入FB消耗');
                    return;
                }
                
                // 发送更新请求
                saveFbConsumption(recordId, fbConsumption, note, () => {
                    fbConsumptionModal.hide();
                    window.location.reload();
                });
            });
        }
    } catch (error) {
        console.error('初始化FB消耗模态框失败:', error);
    }
}

/**
 * 保存FB消耗
 * @param {string} recordId 记录ID
 * @param {string} fbConsumption FB消耗
 * @param {string} note 备注
 * @param {Function} callback 回调函数
 */
function saveFbConsumption(recordId, fbConsumption, note, callback) {
    // 构建表单数据
    const formData = new FormData();
    formData.append('fb_consumption', fbConsumption);
    formData.append('note', note);
    formData.append('redirect_to', 'exception');
    
    // 获取CSRF令牌
    const csrfToken = getCsrfToken();
    
    // 发送AJAX请求
    fetch(`/reconciliation/update-fb-consumption/${recordId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.ok) {
            callback();
        } else {
            alert('更新FB消耗失败，请重试');
        }
    })
    .catch(error => {
        console.error('更新FB消耗出错:', error);
        alert('更新FB消耗时出错，请稍后重试');
    });
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
                const actualConsumption = row.querySelector('td:nth-child(6)')?.textContent || '';
                const fbConsumption = row.querySelector('td:nth-child(7)')?.textContent || '';
                
                // 获取优化师信息
                const optimizerCell = row.querySelector('td:nth-child(5)');
                const optimizerBadges = optimizerCell ? optimizerCell.querySelectorAll('.badge') : [];
                const detailOptimizers = document.getElementById('detail-optimizers');
                
                if (detailOptimizers) {
                    detailOptimizers.innerHTML = '';
                    if (optimizerBadges.length > 0) {
                        optimizerBadges.forEach(badge => {
                            const badgeClone = badge.cloneNode(true);
                            detailOptimizers.appendChild(badgeClone);
                            detailOptimizers.appendChild(document.createTextNode(' '));
                        });
                    } else {
                        detailOptimizers.textContent = '未分配';
                    }
                }
                
                // 获取差异值
                const diffElement = row.querySelector('td:nth-child(8)');
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
 * 初始化手动确认按钮事件
 */
function initManualConfirmButtons() {
    console.log('初始化手动确认按钮...');
    const solveButtons = document.querySelectorAll('.btn-solve');
    console.log(`找到 ${solveButtons.length} 个手动确认按钮`);
    
    if (solveButtons.length === 0) {
        console.log('没有找到手动确认按钮，跳过初始化');
        return;
    }
    
    if (!solveModalInstance) {
        console.error('解决异常模态框实例未初始化，跳过绑定手动确认按钮事件');
        return;
    }
    
    solveButtons.forEach(button => {
        button.addEventListener('click', function() {
            try {
                console.log('点击了手动确认按钮');
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
                const recordIdElement = document.getElementById('record-id');
                const projectTaskNameElement = document.getElementById('project-task-name');
                const reconcilePeriodElement = document.getElementById('reconcile-period');
                const actualConsumptionElement = document.getElementById('actual-consumption');
                const fbConsumptionElement = document.getElementById('fb-consumption');
                const differenceValueElement = document.getElementById('difference-value');
                
                if (recordIdElement) recordIdElement.value = recordId;
                if (projectTaskNameElement) projectTaskNameElement.textContent = `${project} / ${task}`;
                if (reconcilePeriodElement) reconcilePeriodElement.textContent = period;
                if (actualConsumptionElement) actualConsumptionElement.textContent = actualConsumption;
                if (fbConsumptionElement) fbConsumptionElement.textContent = fbConsumption;
                if (differenceValueElement) differenceValueElement.textContent = difference;
                
                // 重置表单
                const solutionTypeElement = document.getElementById('solution-type');
                const solutionNoteElement = document.getElementById('solution-note');
                const adjustAmountGroupElement = document.getElementById('adjust-amount-group');
                
                if (solutionTypeElement) solutionTypeElement.value = '';
                if (solutionNoteElement) solutionNoteElement.value = '';
                if (adjustAmountGroupElement) adjustAmountGroupElement.classList.add('d-none');
                
                // 显示模态框
                solveModalInstance.show();
                console.log('成功显示手动确认模态框');
            } catch (error) {
                console.error('显示手动确认模态框失败:', error);
            }
        });
    });
    console.log('手动确认按钮初始化完成');
    
    // 保存按钮事件处理
    const saveButton = document.getElementById('save-solution');
    if (saveButton) {
        console.log('初始化保存解决方案按钮');
        saveButton.addEventListener('click', function() {
            try {
                console.log('点击了保存解决方案按钮');
                const recordIdElement = document.getElementById('record-id');
                const solutionTypeElement = document.getElementById('solution-type');
                const solutionNoteElement = document.getElementById('solution-note');
                
                if (!recordIdElement || !solutionTypeElement || !solutionNoteElement) {
                    console.error('未找到必要的表单元素');
                    return;
                }
                
                const recordId = recordIdElement.value;
                const solutionType = solutionTypeElement.value;
                const note = solutionNoteElement.value;
                
                if (!recordId) {
                    console.error('记录ID为空');
                    return;
                }
                
                if (!solutionType) {
                    alert('请选择解决方式');
                    return;
                }
                
                if (!note) {
                    alert('请输入解决备注');
                    return;
                }
                
                // 构建表单数据
                const formData = new FormData();
                formData.append('note', note);
                
                // 获取CSRF令牌
                const csrfToken = getCsrfToken();
                
                console.log('准备发送手动确认请求');
                // 发送AJAX请求
                fetch(`/reconciliation/record/${recordId}/confirm/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    credentials: 'same-origin'
                })
                .then(response => {
                    if (response.ok) {
                        // 关闭模态框
                        solveModalInstance.hide();
                        
                        // 刷新页面
                        window.location.reload();
                    } else {
                        alert('手动确认失败，请重试');
                    }
                })
                .catch(error => {
                    console.error('手动确认出错:', error);
                    alert('手动确认时出错，请稍后重试');
                });
            } catch (error) {
                console.error('保存解决方案出错:', error);
            }
        });
    } else {
        console.error('未找到ID为save-solution的元素');
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
        let status = 'exception';
        
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

/**
 * 初始化解决异常对账按钮事件 - 来自详情模态框
 */
function initSolveModalButton() {
    console.log('初始化从详情模态框解决异常按钮...');
    const solveBtnFromModal = document.querySelector('.btn-solve-modal');
    
    if (!solveBtnFromModal) {
        console.error('未找到从详情模态框解决异常按钮，跳过初始化');
        return;
    }
    
    if (!detailModalInstance || !solveModalInstance) {
        console.error('模态框实例未初始化，跳过绑定解决异常按钮事件');
        return;
    }
    
    solveBtnFromModal.addEventListener('click', function() {
        console.log('点击了从详情模态框解决异常按钮');
        // 隐藏详情模态框
        detailModalInstance.hide();
        
        // 延迟显示解决异常模态框，避免模态框冲突
        setTimeout(() => {
            solveModalInstance.show();
            console.log('从详情模态框显示解决异常模态框成功');
        }, 500);
    });
    console.log('从详情模态框解决异常按钮初始化完成');
}

/**
 * 初始化解决方式切换事件
 */
function initSolutionTypeChange() {
    console.log('初始化解决方式切换事件...');
    const solutionTypeSelect = document.getElementById('solution-type');
    const adjustAmountGroup = document.getElementById('adjust-amount-group');
    
    if (!solutionTypeSelect) {
        console.error('未找到解决方式选择框');
        return;
    }
    
    if (!adjustAmountGroup) {
        console.error('未找到调整金额组元素');
        return;
    }
    
    solutionTypeSelect.addEventListener('change', function() {
        const selectedSolutionType = this.value;
        console.log('选择的解决方式:', selectedSolutionType);
        
        // 根据选择的解决方式，显示或隐藏调整金额组
        if (selectedSolutionType === 'adjust') {
            adjustAmountGroup.classList.remove('d-none');
        } else {
            adjustAmountGroup.classList.add('d-none');
        }
    });
    console.log('解决方式切换事件初始化完成');
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