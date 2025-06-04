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
        $('#mediaChannel').val(decodeHtmlEntities($('#media-channel-data').val()));
        $('#taskType').val(decodeHtmlEntities($('#task-type-data').val()));
        $('#kpi').val(decodeHtmlEntities($('#kpi-data').val()));
        $('#manager').val(decodeHtmlEntities($('#manager-data').val()));
        $('#dailyReport').val(decodeHtmlEntities($('#daily-report-data').val()));
        $('#status2').val(decodeHtmlEntities($('#status2-data').val()));
        $('#productBackend').val(decodeHtmlEntities($('#product-backend-data').val()));
        $('#projectTimezone').val(decodeHtmlEntities($('#project-timezone-data').val()));
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

// 解码HTML实体和特殊字符
function decodeHtmlEntities(text) {
    if (!text) return '';
    
    // 创建一个临时元素来解码HTML实体
    var textArea = document.createElement('textarea');
    textArea.innerHTML = text;
    var decodedText = textArea.value;
    
    // 手动处理一些特殊的Unicode字符
    decodedText = decodedText.replace(/\\u([0-9a-fA-F]{4})/g, function(match, hex) {
        return String.fromCharCode(parseInt(hex, 16));
    });
    
    // 特殊处理换行符
    decodedText = decodedText.replace(/\\r\\n|\\n|\\r/g, '\n');
    
    // 特殊处理时区格式
    decodedText = decodedText.replace(/\\u002D(\d+)/g, '-$1');
    
    return decodedText;
}

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
                // 填充项目信息，处理特殊字符
                document.getElementById('mediaChannel').value = decodeHtmlEntities(data.media_channel);
                document.getElementById('taskType').value = decodeHtmlEntities(data.task_type);
                document.getElementById('dailyReport').value = decodeHtmlEntities(data.daily_report_url);
                document.getElementById('kpi').value = decodeHtmlEntities(data.kpi);
                document.getElementById('manager').value = decodeHtmlEntities(data.manager);
                document.getElementById('status2').value = decodeHtmlEntities(data.status2);
                document.getElementById('productBackend').value = decodeHtmlEntities(data.product_backend);
                document.getElementById('projectTimezone').value = decodeHtmlEntities(data.timezone);
                
                // 只有在没有时区值或编辑模式下的新建任务时才自动填充时区
                const timezoneSelect = document.getElementById('timezone');
                if (timezoneSelect && (timezoneSelect.value === '' || !document.getElementById('task-id'))) {
                    timezoneSelect.value = decodeHtmlEntities(data.timezone);
                }
                
                // 将产品后台信息自动填充到任务的后台字段
                const backendInput = document.getElementById('backend');
                if (backendInput && backendInput.value === '') {
                    backendInput.value = decodeHtmlEntities(data.product_backend);
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