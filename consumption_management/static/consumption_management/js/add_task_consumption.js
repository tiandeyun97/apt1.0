document.addEventListener('DOMContentLoaded', function() {
    var existingDates = [];
    var datesCount = {};  // 记录每个日期的记录数量
    var optimizersCount = 0;  // 存储优化师数量
    var taskId = document.getElementById('task-id').value;
    
    // 添加实际消耗和当日消耗变化监听，自动计算回流
    function setupAutoCalculation() {
        // 监听当日消耗和实际消耗输入框的变化
        document.getElementById('daily_consumption').addEventListener('input', calculateReturnFlow);
        document.getElementById('actual_consumption').addEventListener('input', calculateReturnFlow);
        
        // 计算回流值的函数
        function calculateReturnFlow() {
            const dailyConsumption = parseFloat(document.getElementById('daily_consumption').value) || 0;
            const actualConsumption = parseFloat(document.getElementById('actual_consumption').value) || 0;
            
            // 验证实际消耗不小于当日消耗
            if (actualConsumption < dailyConsumption) {
                document.getElementById('actual_consumption_warning').style.display = 'block';
                document.getElementById('return_flow').value = '0.00';
                return;
            } else {
                document.getElementById('actual_consumption_warning').style.display = 'none';
                const returnFlow = (actualConsumption - dailyConsumption).toFixed(2);
                document.getElementById('return_flow').value = returnFlow;
            }
        }
    }
    
    // 初始化自动计算
    setupAutoCalculation();
    
    // 检查任务状态是否为"已结束完成对账"
    function isTaskLocked() {
        // 通过模板中的状态徽章来检查
        const statusBadge = document.querySelector('.badge.status-ended-reconciliation-complete');
        return statusBadge !== null;
    }
    
    // 获取任务的优化师数量
    function getOptimizersCount() {
        $.ajax({
            url: '/consumption/task/' + taskId + '/get-optimizers-count/',
            type: 'GET',
            success: function(data) {
                if (data.success) {
                    optimizersCount = data.count;
                    console.log('优化师数量:', optimizersCount);
                }
            },
            error: function() {
                console.error('获取优化师数量失败');
            }
        });
    }
    
    // 调用获取优化师数量函数
    getOptimizersCount();
    
    // 预加载日期数据
    const consumptionRows = document.querySelectorAll('tr[data-date]');
    consumptionRows.forEach(function(row) {
        const date = row.getAttribute('data-date');
        if (date) {
            existingDates.push(date);
            // 统计每个日期的记录数量
            if (datesCount[date]) {
                datesCount[date]++;
            } else {
                datesCount[date] = 1;
            }
        }
    });
    
    var originalDate = '';
    
    // 模态窗口显示时设置日期默认值和表单action
    $('#addConsumptionModal').on('show.bs.modal', function (e) {
        // 设置表单提交地址
        var form = document.getElementById('consumptionForm');
        form.action = '/consumption/task/' + taskId + '/add/';
        
        // 设置默认日期为前一天
        var yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        var yesterdayStr = yesterday.toISOString().split('T')[0];
        document.getElementById('date').value = yesterdayStr;
        
        // 清空表单数据
        document.getElementById('consumption_id').value = '';
        document.getElementById('daily_consumption').value = '';
        document.getElementById('actual_consumption').value = '';
        document.getElementById('return_flow').value = '0';
        document.getElementById('impressions').value = '0';
        document.getElementById('clicks').value = '0';
        document.getElementById('registrations').value = '0';
        document.getElementById('first_deposits').value = '0';
        
        // 重置原始日期
        originalDate = '';
        
        // 如果是编辑模式，则填充数据
        var button = e.relatedTarget;
        if (button && button.classList.contains('edit-consumption')) {
            var consumptionId = button.getAttribute('data-consumption-id');
            document.getElementById('consumption_id').value = consumptionId;
            
            // 修改表单提交地址为编辑接口
            form.action = '/consumption/task/' + taskId + '/edit/' + consumptionId + '/';
            
            // 发送Ajax请求获取消耗记录数据
            $.ajax({
                url: '/consumption/task/' + taskId + '/get-consumption/' + consumptionId + '/',
                type: 'GET',
                success: function(data) {
                    if (data.success) {
                        document.getElementById('date').value = data.data.date;
                        originalDate = data.data.date; // 保存原始日期，用于后续验证
                        document.getElementById('daily_consumption').value = data.data.daily_consumption;
                        
                        // 计算并填充实际消耗
                        const dailyConsumption = parseFloat(data.data.daily_consumption) || 0;
                        const returnFlow = parseFloat(data.data.return_flow) || 0;
                        const actualConsumption = (dailyConsumption + returnFlow).toFixed(2);
                        document.getElementById('actual_consumption').value = actualConsumption;
                        
                        document.getElementById('return_flow').value = data.data.return_flow;
                        document.getElementById('impressions').value = data.data.impressions;
                        document.getElementById('clicks').value = data.data.clicks;
                        document.getElementById('registrations').value = data.data.registrations;
                        document.getElementById('first_deposits').value = data.data.first_deposits;
                    } else {
                        alert('获取数据失败: ' + data.message);
                    }
                },
                error: function() {
                    alert('获取数据请求失败');
                }
            });
        }
    });
    
    // 表单验证与提交
    document.getElementById('consumptionForm').addEventListener('submit', function(e) {
        e.preventDefault(); // 阻止默认提交行为
        
        // 验证当日消耗是否为有效数字
        var dailyConsumption = parseFloat(document.getElementById('daily_consumption').value);
        if (isNaN(dailyConsumption)) {
            showToast('当日消耗必须是有效数字', 'error');
            return false;
        }
        
        // 验证实际消耗是否小于当日消耗
        if (document.getElementById('actual_consumption').value) {
            var actualConsumption = parseFloat(document.getElementById('actual_consumption').value);
            if (actualConsumption < dailyConsumption) {
                showToast('实际消耗不能小于当日消耗', 'error');
                return false;
            }
        }
        
        // 验证每日记录数不超过优化师人数
        var date = document.getElementById('date').value;
        var isEdit = document.getElementById('consumption_id').value !== '';
        
        // 如果是编辑且日期没变，跳过日期验证
        if (!(isEdit && date === originalDate)) {
            // 计算当前日期的记录数量
            var currentDateCount = datesCount[date] || 0;
            
            // 检查是否超过优化师数量
            if (currentDateCount >= optimizersCount && optimizersCount > 0) {
                showToast('该日期记录数已达到优化师人数上限(' + optimizersCount + '人)', 'error');
                return false;
            }
        }
        
        // 获取表单数据
        var formData = new FormData(this);
        
        // Ajax提交表单
        $.ajax({
            url: this.action,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                // 关闭模态窗口
                $('#addConsumptionModal').modal('hide');
                
                // 显示成功消息
                showToast('保存成功', 'success');
                
                // 刷新页面以显示新数据
                window.location.reload();
            },
            error: function(xhr) {
                var errorMessage = '保存失败';
                if(xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage += ': ' + xhr.responseJSON.error;
                }
                showToast(errorMessage, 'error');
            }
        });
    });
    
    // 为日期单元格添加工具提示，显示完整日期格式
    $('.date-cell').each(function() {
        let dateText = $(this).text().trim();
        if (dateText !== '合计') {
            let dateParts = dateText.split('-');
            if (dateParts.length === 3) {
                let year = dateParts[0];
                let month = dateParts[1];
                let day = dateParts[2];
                let formattedDate = `${year}年${month}月${day}日`;
                $(this).attr('title', formattedDate);
                $(this).attr('data-bs-toggle', 'tooltip');
                $(this).attr('data-bs-placement', 'top');
            }
        }
    });
    
    // 初始化所有工具提示
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // 处理返回任务列表按钮
    $('#backToTaskListBtn').on('click', function(e) {
        e.preventDefault();
        
        // 获取上一个页面的URL（来源页面）
        const referer = document.referrer;
        
        // 检查referer是否包含task_list
        if (referer && referer.includes('/task_management/task/')) {
            // 使用来源页面的URL返回
            window.location.href = referer;
        } else {
            // 默认返回任务列表页
            window.location.href = '/admin/task_management/task/';
        }
    });
    
    // 处理实际消耗字段的内联编辑
    $(document).on('click', '.edit-actual-consumption-btn', function(e) {
        e.preventDefault();
        const container = $(this).closest('.editable-field');
        container.find('.editable-text, .edit-actual-consumption-btn').addClass('d-none');
        container.find('.edit-form').removeClass('d-none');
        container.find('.actual-consumption-input').focus();
    });
    
    // 取消编辑按钮
    $(document).on('click', '.cancel-edit-btn', function() {
        const container = $(this).closest('.editable-field');
        container.find('.edit-form').addClass('d-none');
        container.find('.editable-text, .edit-actual-consumption-btn').removeClass('d-none');
        
        // 恢复原始值
        const originalValue = container.find('.editable-text').text().trim();
        container.find('.actual-consumption-input').val(originalValue);
    });
    
    // 保存实际消耗编辑
    $(document).on('click', '.save-actual-consumption-btn', function() {
        const container = $(this).closest('.editable-field');
        const consumptionId = container.data('consumption-id');
        const newActualConsumption = parseFloat(container.find('.actual-consumption-input').val());
        
        // 显示加载指示器
        $(this).html('<i class="fas fa-spinner fa-spin"></i>');
        $(this).prop('disabled', true);
        
        // 发送AJAX请求更新实际消耗值
        $.ajax({
            url: '/consumption/consumption/' + consumptionId + '/update-return-flow/',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ actual_consumption: newActualConsumption }),
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    // 更新显示的值（数据已从后端格式化为两位小数）
                    container.find('.editable-text').text(response.consumption.actual_consumption);
                    container.find('.edit-form').addClass('d-none');
                    container.find('.editable-text, .edit-actual-consumption-btn').removeClass('d-none');
                    
                    // 更新相关字段，显示两位小数
                    $('#return-flow-ratio-' + consumptionId).text(response.consumption.return_flow_ratio + '%');
                    
                    // 显示成功提示
                    showToast('实际消耗更新成功', 'success');
                } else {
                    showToast('更新失败: ' + response.error, 'error');
                }
            },
            error: function(xhr) {
                let errorMessage = '更新失败';
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.error) {
                        errorMessage = response.error;
                    }
                } catch(e) {}
                showToast(errorMessage, 'error');
            },
            complete: function() {
                // 恢复按钮状态
                container.find('.save-actual-consumption-btn').html('<i class="fas fa-save"></i>');
                container.find('.save-actual-consumption-btn').prop('disabled', false);
            }
        });
    });
    
    // 回车键保存
    $(document).on('keydown', '.actual-consumption-input', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            $(this).closest('.editable-field').find('.save-actual-consumption-btn').click();
        }
        else if (e.key === 'Escape') {
            e.preventDefault();
            $(this).closest('.editable-field').find('.cancel-edit-btn').click();
        }
    });
});

// 删除消耗记录函数
function deleteConsumption(taskId, consumptionId) {
    // 检查任务是否被锁定
    if (document.querySelector('.badge.status-ended-reconciliation-complete')) {
        showToast('任务已结束完成对账，不能删除消耗记录', 'error');
        return;
    }
    
    // 创建一个包含CSRF令牌的表单数据对象
    var formData = new FormData();
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    formData.append('csrfmiddlewaretoken', csrfToken);
    
    // 发送AJAX请求删除记录
    $.ajax({
        url: '/consumption/task/' + taskId + '/delete/' + consumptionId + '/',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            showToast('删除成功', 'success');
            // 刷新页面以更新数据
            window.location.reload();
        },
        error: function(xhr) {
            var errorMessage = '删除失败';
            if(xhr.responseJSON && xhr.responseJSON.error) {
                errorMessage += ': ' + xhr.responseJSON.error;
            }
            showToast(errorMessage, 'error');
        }
    });
}

// 简单的Toast通知系统
function showToast(message, type) {
    // 检查是否已有toast容器
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
    const toastHtml = `
        <div id="${toastId}" class="toast ${bgClass} text-white" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="关闭"></button>
            </div>
        </div>
    `;
    
    // 添加到容器
    toastContainer.innerHTML += toastHtml;
    
    // 初始化并显示toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    toast.show();
    
    // 监听关闭事件，在关闭后移除元素
    toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
    });
} 