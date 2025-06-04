$(document).ready(function() {
    console.log('项目表单JS初始化...');
    
    // 表单字段初始化
    function initFormFields() {
        // 给所有表单控件添加Bootstrap类
        $('#project-form input[type="text"], #project-form input[type="url"], #project-form input[type="date"]').addClass('form-control');
        $('#project-form select').addClass('form-select');
        $('#project-form textarea').addClass('form-control');
        
        // 设置必填字段标记
        $('#id_ProjectName, #id_ManagerID, #id_StartDate').closest('.form-group').find('label').addClass('required');
    }
    
    // 初始化日期选择器
    function initDatePickers() {
        // 确保日期字段有正确的类型
        $('#id_StartDate, #id_EndDate').attr('type', 'date');
        
        // 设置结束日期不能早于开始日期
        $('#id_StartDate').on('change', function() {
            var startDate = $(this).val();
            $('#id_EndDate').attr('min', startDate);
        });
        
        // 如果已有开始日期，设置结束日期的最小值
        if ($('#id_StartDate').val()) {
            $('#id_EndDate').attr('min', $('#id_StartDate').val());
        }
    }
    
    // 监听项目状态变化
    function setupStatusChangeAlert() {
        // 保存原始状态值
        var originalStatus = $('#id_Status2').val();
        
        // 监听状态字段变化
        $('#id_Status2').on('change', function() {
            var selectedValue = $(this).val();
            
            // 如果选择了ID为6的状态（已结束完成对账）
            if (selectedValue === '6') {
                // 显示确认对话框
                if (!confirm('您选择了"已结束完成对账"状态，保存后将自动更新该项目下所有任务的状态为相同状态。\n\n请确认该项目下的所有任务是否已全部结束？')) {
                    // 如果用户点击取消，恢复原始状态值
                    $(this).val(originalStatus);
                } else {
                    // 用户确认了，更新原始状态值
                    originalStatus = selectedValue;
                }
            } else {
                // 更新原始状态值
                originalStatus = selectedValue;
            }
        });
    }
    
    // 表单提交前验证
    function setupFormValidation() {
        $('#project-form').on('submit', function(e) {
            var isValid = true;
            
            // 验证必填字段
            if (!$('#id_ProjectName').val().trim()) {
                $('#id_ProjectName').addClass('is-invalid');
                if (!$('#id_ProjectName').next('.invalid-feedback').length) {
                    $('#id_ProjectName').after('<div class="invalid-feedback">项目名称不能为空</div>');
                }
                isValid = false;
            } else {
                $('#id_ProjectName').removeClass('is-invalid');
                $('#id_ProjectName').next('.invalid-feedback').remove();
            }
            
            if (!$('#id_ManagerID').val()) {
                $('#id_ManagerID').addClass('is-invalid');
                if (!$('#id_ManagerID').next('.invalid-feedback').length) {
                    $('#id_ManagerID').after('<div class="invalid-feedback">请选择项目负责人</div>');
                }
                isValid = false;
            } else {
                $('#id_ManagerID').removeClass('is-invalid');
                $('#id_ManagerID').next('.invalid-feedback').remove();
            }
            
            if (!$('#id_StartDate').val()) {
                $('#id_StartDate').addClass('is-invalid');
                if (!$('#id_StartDate').next('.invalid-feedback').length) {
                    $('#id_StartDate').after('<div class="invalid-feedback">请选择开始日期</div>');
                }
                isValid = false;
            } else {
                $('#id_StartDate').removeClass('is-invalid');
                $('#id_StartDate').next('.invalid-feedback').remove();
            }
            
            // 验证日期逻辑
            var startDate = $('#id_StartDate').val();
            var endDate = $('#id_EndDate').val();
            
            if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
                $('#id_EndDate').addClass('is-invalid');
                if (!$('#id_EndDate').next('.invalid-feedback').length) {
                    $('#id_EndDate').after('<div class="invalid-feedback">结束日期不能早于开始日期</div>');
                }
                isValid = false;
            } else if (endDate) {
                $('#id_EndDate').removeClass('is-invalid');
                $('#id_EndDate').next('.invalid-feedback').remove();
            }
            
            return isValid;
        });
        
        // 字段变化时移除错误提示
        $('#project-form input, #project-form select, #project-form textarea').on('input change', function() {
            $(this).removeClass('is-invalid');
            $(this).next('.invalid-feedback').remove();
        });
    }
    
    // 重置按钮处理
    function setupResetButton() {
        $('button[type="reset"]').click(function(e) {
            e.preventDefault();
            
            if (confirm('确定要重置表单吗？所有未保存的更改将丢失。')) {
                $('#project-form')[0].reset();
                
                // 移除所有验证错误提示
                $('.is-invalid').removeClass('is-invalid');
                $('.invalid-feedback').remove();
            }
        });
    }
    
    // 初始化所有功能
    initFormFields();
    initDatePickers();
    setupStatusChangeAlert(); // 添加状态变化监听
    setupFormValidation();
    setupResetButton();
}); 