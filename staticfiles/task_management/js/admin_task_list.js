$(document).ready(function() {
    // 初始化所有工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // 自动隐藏消息提示
    $('.alert').delay(3000).fadeOut(500);

    // 为任务列表的每一行添加双击事件
    $('.task-row').dblclick(function() {
        const taskId = $(this).data('task-id');
        showTaskDetail(taskId);
    });
    
    // 处理点击编辑按钮
    $(document).on('click', '#task-detail-edit-btn', function(e) {
        e.preventDefault();
        const taskId = $(this).data('task-id');
        window.location.href = "/admin/task_management/task/create/?id=" + taskId;
    });
    
    // 初始化弹窗
    const taskDetailModal = new bootstrap.Modal(document.getElementById('taskDetailModal'));
    
    // 加载任务详情的函数
    function showTaskDetail(taskId) {
        // 发送AJAX请求获取任务详情
        $.ajax({
            url: "/admin/task_management/get-task-detail/",
            data: {
                task_id: taskId
            },
            dataType: 'json',
            success: function(data) {
                if (data.success) {
                    // 任务ID
                    $('#task-detail-id').text(data.id);
                    
                    // 标题和基本信息
                    $('#task-detail-title').text(data.name);
                    $('#task-detail-name').text(data.name);
                    $('#task-detail-advert-name').text(data.advert_name);
                    $('#task-detail-product-info').text(data.product_info);
                    $('#task-detail-backend').text(data.backend);
                    
                    // 项目信息
                    $('#task-detail-project').text(data.project.name);
                    $('#task-detail-media-channel').text(data.project.media_channel);
                    $('#task-detail-task-type').text(data.project.task_type);
                    $('#task-detail-kpi').text(data.project.kpi);
                    $('#task-detail-manager').text(data.project.manager);
                    $('#task-detail-timezone').text(data.timezone || '-');
                    
                    // 状态信息
                    $('#task-detail-status').text(data.status.name);
                    $('#task-detail-created-at').text(data.created_at);
                    $('#task-detail-start-date').text(data.start_date);
                    $('#task-detail-end-date').text(data.end_date);
                    
                    // 日报链接
                    if (data.project.daily_report_url && data.project.daily_report_url !== '-') {
                        $('#task-detail-daily-report-link').attr('href', data.project.daily_report_url);
                        $('#task-detail-daily-report-link .link-text').text(data.project.daily_report_url);
                        $('#task-detail-daily-report-link').show();
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
                        $optimizerContainer.text('-');
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
                    
                    // 显示模态框
                    taskDetailModal.show();
                } else {
                    alert(data.message || '获取任务详情失败');
                }
            },
            error: function() {
                alert('网络错误，请稍后重试');
            }
        });
    }
}); 