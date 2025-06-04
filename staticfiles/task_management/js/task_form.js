$(document).ready(function() {
    // 初始化项目选择器的Select2
    $('.select2-project').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: '请输入项目名称搜索...',
        allowClear: true,
        minimumInputLength: 1,
        language: {
            inputTooShort: function() {
                return "请输入至少1个字符开始搜索";
            },
            noResults: function() {
                return "没有找到匹配的项目";
            },
            searching: function() {
                return "搜索中...";
            }
        },
        escapeMarkup: function(markup) {
            return markup;
        },
        templateResult: formatProject,
        templateSelection: formatProjectSelection
    });

    // 初始化优化师Select2
    $('#optimizer').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: '请选择优化师',
        allowClear: true,
        language: {
            noResults: function() {
                return "没有找到匹配的结果";
            }
        }
    });
    
    // 如果是编辑模式，在页面加载时自动加载项目信息
    if ($('#task-id').length > 0) {
        // 在编辑模式下，相关信息已经由后端提供，无需AJAX请求
        // 但为了显示项目的其他信息，我们仍需要填充这些字段
        $('#mediaChannel').val($('#media-channel-data').val());
        $('#taskType').val($('#task-type-data').val());
        $('#kpi').val($('#kpi-data').val());
        $('#manager').val($('#manager-data').val());
        $('#dailyReport').val($('#daily-report-data').val());
        $('#status2').val($('#status2-data').val());
        $('#productBackend').val($('#product-backend-data').val());
        $('#projectTimezone').val($('#project-timezone-data').val());
    }
    
    // 监听项目选择变化
    $('#project').on('select2:select', function(e) {
        var projectId = $(this).val();
        if (projectId) {
            // 发送AJAX请求获取项目信息
            fetchProjectInfo(projectId);
        } else {
            // 清空所有字段
            $('#mediaChannel, #taskType, #kpi, #manager, #dailyReport, #status2, #productBackend, #projectTimezone').val('-');
        }
    });

    // 表单验证
    $('#taskForm').submit(function(e) {
        var isValid = true;
        $(this).find('[required]').each(function() {
            if (!$(this).val()) {
                isValid = false;
                $(this).addClass('is-invalid');
            } else {
                $(this).removeClass('is-invalid');
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            $('html, body').animate({
                scrollTop: $('.is-invalid').first().offset().top - 100
            }, 500);
        }
    });
});

// 格式化项目搜索结果
function formatProject(project) {
    if (project.loading) return project.text;
    if (!project.id) return project.text;
    
    var $container = $(
        `<div class="select2-result-project">
            <div class="select2-result-project__title">${project.text}</div>
        </div>`
    );
    
    return $container;
}

// 格式化选中的项目
function formatProjectSelection(project) {
    return project.text || project.id;
}

// 获取项目信息并填充到表单
function fetchProjectInfo(projectId) {
    if (!projectId) return;
    
    fetch(`${getProjectInfoUrl}?project_id=${projectId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 填充项目信息
                document.getElementById('mediaChannel').value = data.media_channel;
                document.getElementById('taskType').value = data.task_type;
                document.getElementById('dailyReport').value = data.daily_report_url;
                document.getElementById('kpi').value = data.kpi;
                document.getElementById('manager').value = data.manager;
                document.getElementById('status2').value = data.status2;
                document.getElementById('productBackend').value = data.product_backend;
                document.getElementById('projectTimezone').value = data.timezone;
                
                // 只有在没有时区值或编辑模式下的新建任务时才自动填充时区
                const timezoneSelect = document.getElementById('timezone');
                if (timezoneSelect && (timezoneSelect.value === '' || !document.getElementById('task-id'))) {
                    // 查找匹配的option并设置选中
                    const options = timezoneSelect.options;
                    for (let i = 0; i < options.length; i++) {
                        if (options[i].value === data.timezone) {
                            timezoneSelect.selectedIndex = i;
                            break;
                        }
                    }
                }
                
                // 将产品后台信息自动填充到任务的后台字段
                const backendInput = document.getElementById('backend');
                if (backendInput && backendInput.value === '') {
                    backendInput.value = data.product_backend;
                }
                
                // 显示项目信息区域
                document.getElementById('projectInfoSection').style.display = 'block';
            } else {
                console.error('获取项目信息失败:', data.message);
            }
        })
        .catch(error => {
            console.error('请求错误:', error);
        });
} 