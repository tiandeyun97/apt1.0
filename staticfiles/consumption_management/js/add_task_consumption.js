document.addEventListener('DOMContentLoaded', function() {
    var existingDates = [];
    var datesCount = {};  // 记录每个日期的记录数量
    var optimizersCount = 0;  // 存储优化师数量
    var taskId = document.getElementById('task-id').value;
    
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
        
        // 默认设置为今天日期
        var today = new Date().toISOString().split('T')[0];
        document.getElementById('date').value = today;
        
        // 清空表单数据
        document.getElementById('consumption_id').value = '';
        document.getElementById('daily_consumption').value = '';
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
        
        // 验证当日消耗是否大于0
        var dailyConsumption = parseFloat(document.getElementById('daily_consumption').value);
        if (dailyConsumption <= 0) {
            alert('当日消耗必须大于0');
            return false;
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
                alert('该日期记录数已达到优化师人数上限(' + optimizersCount + '人)');
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
                alert('保存成功');
                
                // 刷新页面以显示新数据
                window.location.reload();
            },
            error: function(xhr) {
                var errorMessage = '保存失败';
                if(xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage += ': ' + xhr.responseJSON.error;
                }
                alert(errorMessage);
            }
        });
    });
});

// 删除消耗记录函数
function deleteConsumption(taskId, consumptionId) {
    if (!confirm('确定要删除此记录吗？')) {
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
            alert('删除成功');
            // 刷新页面以更新数据
            window.location.reload();
        },
        error: function(xhr) {
            var errorMessage = '删除失败';
            if(xhr.responseJSON && xhr.responseJSON.error) {
                errorMessage += ': ' + xhr.responseJSON.error;
            }
            alert(errorMessage);
        }
    });
} 