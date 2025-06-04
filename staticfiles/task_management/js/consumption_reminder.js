$(document).ready(function() {
    // 调试模式开关（设置为true可以随时触发提醒进行测试）
    const DEBUG_MODE = false;
    
    // 初始化提醒系统
    initConsumptionReminder();

    // 初始化提醒系统的函数
    function initConsumptionReminder() {
        console.log('初始化消耗记录提醒系统');
        
        // 获取今天的日期作为key
        const today = new Date().toISOString().split('T')[0];
        const reminderDisabledKey = 'consumption_reminder_disabled_' + today;
        
        // 检查用户是否已经选择了今天不再提醒
        if (localStorage.getItem(reminderDisabledKey) === 'true' && !DEBUG_MODE) {
            console.log('用户已选择今天不再提醒');
            return;
        }
        
        // 调试模式下，立即显示提醒
        if (DEBUG_MODE) {
            console.log('调试模式：立即显示提醒');
            setTimeout(function() {
                showConsumptionReminder();
            }, 2000);
            return;
        }
        
        // 立即检查一次时间
        checkTimeAndRemind();
        
        // 每分钟检查一次时间（是否在提醒时间范围内）
        setInterval(checkTimeAndRemind, 60000);
    }
    
    // 检查当前时间并在满足条件时显示提醒
    function checkTimeAndRemind() {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        
        console.log(`当前时间: ${hours}:${minutes}`);
        
        // 在13:00到15:00之间提醒
        if (hours >= 13 && hours <= 15) {
            // 获取今天的日期和当前小时数
            const today = now.toISOString().split('T')[0];
            const currentHour = hours;
            
            // 上次提醒的小时
            const lastReminderKey = 'last_consumption_reminder_' + today;
            const lastReminderHour = parseInt(localStorage.getItem(lastReminderKey) || '0');
            
            console.log(`上次提醒时间: ${lastReminderHour}:00, 当前时间: ${currentHour}:${minutes}`);
            
            // 如果距离上次提醒已经过了至少1小时，或者是新的小时
            if (!lastReminderHour || (currentHour !== lastReminderHour)) {
                console.log('显示提醒');
                // 显示提醒
                showConsumptionReminder();
                
                // 更新上次提醒时间
                localStorage.setItem(lastReminderKey, currentHour.toString());
            } else {
                console.log(`本小时已经提醒过，下一次提醒将在 ${lastReminderHour + 1}:00`);
            }
        } else {
            console.log('当前不在提醒时间范围内(13:00-15:00)');
        }
    }
    
    // 显示提醒弹窗
    function showConsumptionReminder() {
        // 如果已经有提醒弹窗，则不再显示
        if ($('#consumptionReminderModal').length > 0) {
            console.log('已有提醒弹窗存在，不重复显示');
            return;
        }
        
        // 创建提醒弹窗
        const modalHtml = `
            <div class="modal fade" id="consumptionReminderModal" tabindex="-1" aria-labelledby="consumptionReminderModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <div class="reminder-title-container">
                                <div class="reminder-icon-wrapper">
                                    <i class="fas fa-bell"></i>
                                </div>
                                <h5 class="modal-title" id="consumptionReminderModalLabel">消耗记录提醒</h5>
                            </div>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="reminder-content">
                                <div class="reminder-icon">
                                    <i class="fas fa-exclamation-circle"></i>
                                </div>
                                <div class="reminder-message">
                                    <h5>请记得填写今日消耗记录</h5>
                                    <p>及时填写有助于跟踪项目进度和优化广告效果</p>
                                </div>
                            </div>
                            <div class="reminder-checkbox">
                                <input class="form-check-input" type="checkbox" id="doNotRemindToday">
                                <label class="form-check-label" for="doNotRemindToday">
                                    今日不再提醒
                                </label>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-close-reminder" data-bs-dismiss="modal">关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 添加到页面并显示
        $('body').append(modalHtml);
        
        // 初始化并显示模态框
        const reminderModal = new bootstrap.Modal(document.getElementById('consumptionReminderModal'));
        reminderModal.show();
        
        // 处理"今日不再提醒"选项
        $('#doNotRemindToday').on('change', function() {
            if ($(this).is(':checked')) {
                const today = new Date().toISOString().split('T')[0];
                localStorage.setItem('consumption_reminder_disabled_' + today, 'true');
                console.log('用户选择了今日不再提醒');
            } else {
                const today = new Date().toISOString().split('T')[0];
                localStorage.removeItem('consumption_reminder_disabled_' + today);
                console.log('用户取消了今日不再提醒');
            }
        });
        
        // 监听模态框关闭事件，关闭后删除DOM
        $('#consumptionReminderModal').on('hidden.bs.modal', function() {
            $(this).remove();
        });
    }
}); 