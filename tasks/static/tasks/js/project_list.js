$(document).ready(function() {
    // 全选/反选
    $('#action-toggle').click(function() {
        $('.action-select').prop('checked', $(this).prop('checked'));
    });
    
    // 删除选中 - 使用Django删除确认模板
    $('#delete-selected').click(function() {
        var selectedItems = $('input[name="_selected_action"]:checked');
        if (selectedItems.length === 0) {
            // 使用Bootstrap警告而不是alert
            showToast('警告', '请至少选择一个项目', 'warning');
            return;
        }
        
        // 准备表单提交到删除确认页面
        var form = $('#changelist-form');
        
        // 确保表单有正确的action属性
        form.attr('action', deleteConfirmUrl);
        
        // 添加action参数
        var input = $('<input>').attr({
            type: 'hidden',
            name: 'action',
            value: 'delete_selected'
        });
        
        // 移除可能存在的旧参数
        form.find('input[name="action"]').remove();
        form.append(input);
        
        // 提交表单到删除确认页面
        form.submit();
    });
    
    // 搜索按钮点击处理 - 直接提交表单，不拦截默认行为
    $('#filter-form').on('submit', function() {
        return true; // 允许表单正常提交
    });
    
    // 重置按钮
    $('button[type="reset"]').click(function(e) {
        e.preventDefault();
        $('#filter-form')[0].reset();
        window.location.href = resetUrl; // 通过模板变量传递URL
    });
    
    // 表格行悬停效果
    $('.table tbody tr').hover(
        function() {
            $(this).addClass('bg-light');
        },
        function() {
            $(this).removeClass('bg-light');
        }
    );
    
    // 辅助函数：显示Toast通知
    function showToast(title, message, type) {
        // 创建toast元素
        var toast = $('<div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000">');
        var toastHeader = $('<div class="toast-header">');
        var icon = type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
        var color = type === 'warning' ? 'text-warning' : 'text-info';
        
        toastHeader.append('<i class="fas ' + icon + ' ' + color + ' me-2"></i>');
        toastHeader.append('<strong class="me-auto">' + title + '</strong>');
        toastHeader.append('<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>');
        
        var toastBody = $('<div class="toast-body">').text(message);
        
        toast.append(toastHeader).append(toastBody);
        
        // 添加到页面
        var container = $('.toast-container');
        if (container.length === 0) {
            container = $('<div class="toast-container position-fixed top-0 end-0 p-3">');
            $('body').append(container);
        }
        
        container.append(toast);
        
        // 显示toast
        var bsToast = new bootstrap.Toast(toast[0]);
        bsToast.show();
        
        // 自动删除
        toast.on('hidden.bs.toast', function () {
            $(this).remove();
        });
    }
}); 