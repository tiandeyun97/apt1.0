// 消耗记录提醒功能
$(document).ready(function() {
    // 显示消耗记录提醒
    function showConsumptionReminder() {
        // 检查本地存储是否已经今天提醒过
        const today = new Date().toISOString().split('T')[0]; // 获取当前日期，格式为YYYY-MM-DD
        const dontShowAgainToday = localStorage.getItem('dontShowConsumptionReminderToday') === today;
        
        // 如果今天设置了不再提醒，则不显示提醒
        if (dontShowAgainToday) {
            return;
        }
        
        // 显示提醒弹窗
        const reminderModal = new bootstrap.Modal(document.getElementById('consumptionReminderModal'));
        reminderModal.show();
    }
    
    // 定时检查是否需要显示提醒
    function checkReminderTime() {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        
        // 提醒时间窗口：13:30到14:30之间
        const isReminderTimeWindow = 
            (hours === 13 && minutes >= 30) || (hours === 14 && minutes < 30);
        
        if (!isReminderTimeWindow) {
            return; // 不在提醒时间窗口内
        }
        
        // 获取上次提醒时间
        const lastReminderTime = localStorage.getItem('lastConsumptionReminderTime');
        const today = new Date().toISOString().split('T')[0];
        
        if (lastReminderTime) {
            const lastReminder = new Date(lastReminderTime);
            const timeDiff = now.getTime() - lastReminder.getTime();
            const hoursDiff = timeDiff / (1000 * 60 * 60);
            
            // 如果距离上次提醒不足1小时，则不提醒
            if (hoursDiff < 1) {
                return;
            }
        }
        
        // 记录本次提醒时间
        localStorage.setItem('lastConsumptionReminderTime', now.toISOString());
        
        // 显示提醒
        showConsumptionReminder();
    }
    
    // 页面加载时立即检查一次
    checkReminderTime();
    
    // 每分钟检查一次时间
    setInterval(checkReminderTime, 60000); // 60000毫秒 = 1分钟
    
    // 保存用户设置 - 今日不再提醒
    $('#dontShowAgainToday').change(function() {
        const today = new Date().toISOString().split('T')[0];
        if ($(this).is(':checked')) {
            localStorage.setItem('dontShowConsumptionReminderToday', today);
        } else {
            localStorage.removeItem('dontShowConsumptionReminderToday');
        }
    });
    
    // 手动预览按钮效果
    $('#previewReminderButton').hover(
        function() {
            $(this).css({
                'transform': 'translateY(-3px) scale(1.05)',
                'box-shadow': '0 6px 16px rgba(37, 99, 235, 0.6)'
            });
        },
        function() {
            $(this).css({
                'transform': 'translateY(0) scale(1)',
                'box-shadow': '0 4px 12px rgba(37, 99, 235, 0.4)'
            });
        }
    ).click(function() {
        // 手动触发提醒弹窗预览
        const reminderModal = new bootstrap.Modal(document.getElementById('consumptionReminderModal'));
        reminderModal.show();
    });
}); 