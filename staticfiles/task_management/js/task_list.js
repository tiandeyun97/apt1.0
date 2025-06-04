$(document).ready(function() {
    // 初始化所有工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // 自动隐藏消息提示
    $('.alert').delay(3000).fadeOut(500);
    
    // 处理点击编辑按钮
    $(document).on('click', '#task-detail-edit-btn', function(e) {
        e.preventDefault();
        const taskId = $(this).data('task-id');
        window.location.href = taskCreateUrl + "?id=" + taskId;
    });
    
    // 初始化弹窗
    const taskDetailModal = new bootstrap.Modal(document.getElementById('taskDetailModal'));
    
    // 监听模态框关闭事件，确保清除背景
    $('#taskDetailModal').on('hidden.bs.modal', function() {
        // 清除所有模态框背景
        $('.modal-backdrop').remove();
        // 恢复body样式
        $('body').removeClass('modal-open').css({
            'overflow': '',
            'padding-right': ''
        });
    });
    
    // 打印任务行数量，确认DOM元素存在
    const taskRowCount = $('.task-row').length;
    console.log('找到任务行数量:', taskRowCount);
    
    // 绑定任务行的双击事件
    $(document).on('dblclick', '.task-row', function() {
        const taskId = $(this).data('task-id');
        console.log('双击任务行，任务ID:', taskId);
        if (taskId) {
            showTaskDetail(taskId);
        } else {
            console.error('错误：无法获取任务ID，任务行:', this);
        }
    });
    
    // 也直接绑定到现有元素上，以防事件委托失效
    $('.task-row').on('dblclick', function() {
        const taskId = $(this).data('task-id');
        console.log('直接绑定-双击任务行，任务ID:', taskId);
        if (taskId) {
            showTaskDetail(taskId);
        } else {
            console.error('错误：无法获取任务ID，任务行:', this);
        }
    });

    // === 任务状态编辑功能 ===
    // 点击任务状态显示编辑控件
    $(document).on('click', '.editable-status .status-display', function() {
        // 隐藏所有其他打开的编辑控件
        $('.status-edit-controls, .date-edit-controls').not($(this).siblings('.status-edit-controls')).hide();
        $('.status-display, .date-display').show();
        
        // 隐藏当前状态显示，显示编辑控件
        $(this).hide();
        $(this).siblings('.status-edit-controls').show();
    });

    // 保存状态变更
    $(document).on('click', '.save-status', function() {
        const statusContainer = $(this).closest('.editable-status');
        const taskId = statusContainer.data('task-id');
        const statusId = statusContainer.find('.status-select').val();
        const statusText = statusContainer.find('.status-select option:selected').text();
        
        // 构建CSRF令牌
        const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
        
        // 显示加载状态
        $(this).prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
        
        // 发送AJAX请求更新状态
        $.ajax({
            url: '/task_management/update-status/',
            type: 'POST',
            data: {
                'task_id': taskId,
                'status_id': statusId,
                'csrfmiddlewaretoken': csrfToken
            },
            success: function(response) {
                if (response.success) {
                    // 判断状态颜色类
                    let statusClass = 'bg-secondary';
                    if (statusText === '进行中') {
                        statusClass = 'status-in-progress';
                    } else if (statusText === '包下架待对账') {
                        statusClass = 'status-pending-reconciliation';
                    } else if (statusText === '待开始') {
                        statusClass = 'status-waiting-to-start';
                    } else if (statusText === '暂停' || statusText === '已暂停') {
                        statusClass = 'status-paused';
                    } else if (statusText === '以结束待对账') {
                        statusClass = 'status-ended-pending-reconciliation';
                    } else if (statusText === '已结束完成对账') {
                        statusClass = 'status-ended-reconciliation-complete';
                    } else if (statusText === '稍等，等通知就开启') {
                        statusClass = 'status-waiting-for-notification';
                    }
                    
                    // 更新显示
                    const statusDisplay = statusContainer.find('.status-display');
                    statusDisplay.html(`<span class="badge ${statusClass}">${statusText}</span>`);
                    statusDisplay.show();
                    statusContainer.find('.status-edit-controls').hide();
                    
                    // 显示成功提示
                    showNotification('success', response.message);
                } else {
                    // 显示错误提示
                    showNotification('danger', response.error || '更新失败');
                }
            },
            error: function(xhr) {
                let errorMsg = '更新失败';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                showNotification('danger', errorMsg);
            },
            complete: function() {
                // 恢复按钮状态
                statusContainer.find('.save-status').prop('disabled', false).html('保存');
            }
        });
    });

    // 取消状态编辑
    $(document).on('click', '.cancel-status', function() {
        const statusContainer = $(this).closest('.editable-status');
        statusContainer.find('.status-display').show();
        statusContainer.find('.status-edit-controls').hide();
    });

    // === 结束日期编辑功能 ===
    // 点击结束日期显示编辑控件
    $(document).on('click', '.editable-date .date-display', function() {
        // 隐藏所有其他打开的编辑控件
        $('.status-edit-controls, .date-edit-controls').not($(this).siblings('.date-edit-controls')).hide();
        $('.status-display, .date-display').show();
        
        // 隐藏当前日期显示，显示编辑控件
        $(this).hide();
        $(this).siblings('.date-edit-controls').show();
    });

    // 保存日期变更
    $(document).on('click', '.save-date', function() {
        const dateContainer = $(this).closest('.editable-date');
        const taskId = dateContainer.data('task-id');
        const endDate = dateContainer.find('.end-date-input').val();
        
        // 如果没有选择日期，提示并返回
        if (!endDate) {
            showNotification('warning', '请选择结束日期');
            return;
        }
        
        // 构建CSRF令牌
        const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
        
        // 显示加载状态
        $(this).prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
        
        // 发送AJAX请求更新结束日期
        $.ajax({
            url: '/task_management/update-end-date/',
            type: 'POST',
            data: {
                'task_id': taskId,
                'end_date': endDate,
                'csrfmiddlewaretoken': csrfToken
            },
            success: function(response) {
                if (response.success) {
                    // 更新显示
                    const dateDisplay = dateContainer.find('.date-display');
                    dateDisplay.text(endDate);
                    dateDisplay.removeClass('text-muted');
                    dateDisplay.show();
                    dateContainer.find('.date-edit-controls').hide();
                    
                    // 显示成功提示
                    showNotification('success', response.message);
                } else {
                    // 显示错误提示
                    showNotification('danger', response.error || '更新失败');
                }
            },
            error: function(xhr) {
                let errorMsg = '更新失败';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                showNotification('danger', errorMsg);
            },
            complete: function() {
                // 恢复按钮状态
                dateContainer.find('.save-date').prop('disabled', false).html('保存');
            }
        });
    });

    // 取消日期编辑
    $(document).on('click', '.cancel-date', function() {
        const dateContainer = $(this).closest('.editable-date');
        dateContainer.find('.date-display').show();
        dateContainer.find('.date-edit-controls').hide();
    });

    // 通知显示函数
    function showNotification(type, message) {
        // 创建通知元素
        const notification = $(`
            <div class="alert alert-${type} alert-dismissible fade show notify-alert" role="alert">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `);
        
        // 添加到页面顶部
        $('.main-container').prepend(notification);
        
        // 3秒后自动隐藏
        setTimeout(function() {
            notification.alert('close');
        }, 3000);
    }
    
    // 加载任务详情的函数
    function showTaskDetail(taskId) {
        console.log('正在加载任务详情，任务ID:', taskId);
        // 发送AJAX请求获取任务详情
        $.ajax({
            url: getTaskDetailUrl,
            data: {
                task_id: taskId
            },
            dataType: 'json',
            success: function(data) {
                console.log('获取任务详情成功:', data);
                if (data.success) {
                    // 任务ID
                    $('#task-detail-id').text(data.id);
                    
                    // 标题和基本信息
                    $('#task-detail-title').text(data.name);
                    $('#task-detail-name').text(data.name);
                    $('#task-detail-advert-name').text(data.advert_name);
                    $('#task-detail-product-info').text(data.product_info);
                    $('#task-detail-backend').text(data.backend);
                    $('#task-detail-timezone-basic').text(data.timezone || '-');
                    
                    // 项目信息
                    $('#task-detail-project').text(data.project.name);
                    $('#task-detail-media-channel').text(data.project.media_channel);
                    $('#task-detail-task-type').text(data.project.task_type);
                    $('#task-detail-kpi').text(data.project.kpi);
                    $('#task-detail-manager').text(data.project.manager);
                    $('#task-detail-status2').text(data.project.status2 || '-');
                    $('#task-detail-product-backend').text(data.project.product_backend || '-');
                    $('#task-detail-timezone').text(data.project.timezone || '-'); // 确保显示项目时区
                    
                    // 状态信息
                    $('#task-detail-status').text(data.status.name);
                    $('#task-detail-created-at').text(data.created_at);
                    $('#task-detail-start-date').text(data.start_date);
                    $('#task-detail-end-date').text(data.end_date);
                    
                    // 日报链接
                    if (data.project.daily_report_url && data.project.daily_report_url !== '-') {
                        $('#task-detail-daily-report-link').attr('href', data.project.daily_report_url);
                        $('#task-detail-daily-report-link .link-text').text(data.project.daily_report_url);
                        $('#task-detail-daily-report').show();
                    } else {
                        $('#task-detail-daily-report').text('-');
                    }
                    
                    // 设置像素代码
                    $('#task-detail-pixel').text(data.pixel || '');
                    
                    // 投放链接
                    if (data.publish_url && data.publish_url !== '-') {
                        $('#task-detail-publish-url-link').attr('href', data.publish_url);
                        $('#task-detail-publish-url-link .link-text').text(data.publish_url);
                        $('#task-detail-publish-url-link').show();
                    } else {
                        $('#task-detail-publish-url').text('-');
                    }
                    
                    // 备注
                    $('#task-detail-notes').text(data.notes || '');
                    
                    // 优化师列表
                    const $optimizerContainer = $('#task-detail-optimizer');
                    $optimizerContainer.empty();
                    
                    if (data.optimizers && data.optimizers.length > 0) {
                        data.optimizers.forEach(function(optimizer) {
                            $optimizerContainer.append(
                                $('<span class="user-tag"></span>').text(optimizer.username)
                            );
                        });
                    } else {
                        // 当没有优化师时，显示一个灰色的占位标签
                        $optimizerContainer.append(
                            $('<span class="user-tag user-tag-empty"></span>').text('-')
                        );
                    }
                    
                    // 对于单个优化师的情况，单独处理
                    if (data.optimizer && !data.optimizers) {
                        $optimizerContainer.empty();
                        $optimizerContainer.append(
                            $('<span class="user-tag"></span>').text(data.optimizer)
                        );
                    }
                    
                    // 设置编辑按钮的任务ID
                    $('#task-detail-edit-btn').data('task-id', data.id);
                    
                    // 根据用户权限显示或隐藏编辑按钮
                    const hasChangePermission = $('#has-change-task-permission').val() === 'true';
                    if (hasChangePermission) {
                        $('#task-detail-edit-btn').show();
                    } else {
                        $('#task-detail-edit-btn').hide();
                    }
                    
                    // 初始化复制按钮
                    if (typeof ClipboardJS !== 'undefined') {
                        new ClipboardJS('.btn-copy-code').on('success', function(e) {
                            const $btn = $(e.trigger);
                            const originalTitle = $btn.attr('title');
                            $btn.attr('title', '已复制!').addClass('btn-success');
                            
                            setTimeout(function() {
                                $btn.attr('title', originalTitle).removeClass('btn-success');
                            }, 1500);
                            
                            e.clearSelection();
                        });
                    }
                    
                    // 使用jQuery方式直接显示模态框，避免依赖event.relatedTarget
                    const modal = document.getElementById('taskDetailModal');
                    
                    // 先确保关闭已存在的模态框和背景
                    $('.modal-backdrop').remove();
                    $('body').removeClass('modal-open').css({
                        'overflow': '',
                        'padding-right': ''
                    });
                    
                    // 使用原生Bootstrap方式显示，避免jQuery和Bootstrap混用导致的问题
                    const modalInstance = new bootstrap.Modal(modal, {
                        backdrop: true,
                        keyboard: true,
                        focus: true
                    });
                    modalInstance.show();
                } else {
                    console.error('获取任务详情失败:', data.message);
                    alert(data.message || '获取任务详情失败');
                }
            },
            error: function(xhr, status, error) {
                console.error('获取任务详情失败:', error);
                console.error('响应:', xhr.responseText);
                console.error('状态:', status);
                console.error('XHR详情:', xhr);
                alert('网络错误，请稍后重试');
            }
        });
    }
    
    // 在DOM加载完成后进行额外检查
    $(window).on('load', function() {
        console.log('页面完全加载完成，再次检查任务行数量');
        console.log('任务行数量(window.load):', $('.task-row').length);
        
        // 确保双击事件绑定
        $('.task-row').off('dblclick').on('dblclick', function() {
            const taskId = $(this).data('task-id');
            console.log('window.load后-双击任务行，任务ID:', taskId);
            if (taskId) {
                showTaskDetail(taskId);
            }
        });
    });

    // === 表格排序功能 ===
    let currentSort = {
        column: null,
        direction: 'asc'
    };

    // 排序函数
    function sortTable(column, direction) {
        const tbody = $('.table tbody');
        const rows = tbody.find('tr').toArray();
        
        // 更新排序状态
        $('.sortable').removeClass('sort-asc sort-desc');
        $(`.sortable[data-sort="${column}"]`).addClass(`sort-${direction}`);
        
        // 排序行
        rows.sort((a, b) => {
            let aVal, bVal;
            
            // 获取要比较的值
            switch(column) {
                case 'index':
                    aVal = parseInt($(a).find('td:first').text());
                    bVal = parseInt($(b).find('td:first').text());
                    break;
                case 'name':
                    aVal = $(a).find('td[data-label="任务名称"]').text().trim();
                    bVal = $(b).find('td[data-label="任务名称"]').text().trim();
                    break;
                case 'project':
                    aVal = $(a).find('td[data-label="所属项目"]').text().trim();
                    bVal = $(b).find('td[data-label="所属项目"]').text().trim();
                    break;
                case 'media_channel':
                    aVal = $(a).find('td[data-label="媒体渠道"]').text().trim();
                    bVal = $(b).find('td[data-label="媒体渠道"]').text().trim();
                    break;
                case 'task_type':
                    aVal = $(a).find('td[data-label="任务类型"]').text().trim();
                    bVal = $(b).find('td[data-label="任务类型"]').text().trim();
                    break;
                case 'status':
                    aVal = $(a).find('td[data-label="任务状态"] .badge').text().trim();
                    bVal = $(b).find('td[data-label="任务状态"] .badge').text().trim();
                    break;
                case 'kpi':
                    aVal = $(a).find('td[data-label="KPI"]').text().trim();
                    bVal = $(b).find('td[data-label="KPI"]').text().trim();
                    break;
                case 'timezone':
                    aVal = $(a).find('td[data-label="时区"]').text().trim();
                    bVal = $(b).find('td[data-label="时区"]').text().trim();
                    break;
                case 'optimizer':
                    aVal = $(a).find('td[data-label="优化师"]').text().trim();
                    bVal = $(b).find('td[data-label="优化师"]').text().trim();
                    break;
                case 'manager':
                    aVal = $(a).find('td[data-label="运营负责人"]').text().trim();
                    bVal = $(b).find('td[data-label="运营负责人"]').text().trim();
                    break;
                case 'start_date':
                    aVal = $(a).find('td[data-label="开始日期"]').text().trim();
                    bVal = $(b).find('td[data-label="开始日期"]').text().trim();
                    break;
                case 'end_date':
                    aVal = $(a).find('td[data-label="结束日期"]').text().trim();
                    bVal = $(b).find('td[data-label="结束日期"]').text().trim();
                    break;
                default:
                    return 0;
            }
            
            // 处理空值
            if (aVal === '-') aVal = '';
            if (bVal === '-') bVal = '';
            
            // 比较值
            if (direction === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
        
        // 重新添加排序后的行
        tbody.empty().append(rows);
        
        // 更新当前排序状态
        currentSort.column = column;
        currentSort.direction = direction;
    }

    // 点击表头排序
    $('.sortable').on('click', function() {
        const column = $(this).data('sort');
        let direction = 'asc';
        
        // 如果点击当前排序列，切换排序方向
        if (currentSort.column === column) {
            direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        }
        
        sortTable(column, direction);
    });
});