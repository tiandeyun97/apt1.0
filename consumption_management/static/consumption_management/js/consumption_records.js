$(document).ready(function() {
    // 项目选择时更新任务下拉框
    $('#project').change(function() {
        const projectId = $(this).val();
        const taskSelect = $('#task');
        
        // 清空任务下拉框
        taskSelect.empty();
        taskSelect.append('<option value="">全部任务</option>');
        
        if (projectId) {
            // AJAX获取相关任务
            $.ajax({
                url: '/api/tasks-by-project/',
                data: {
                    'project_id': projectId
                },
                dataType: 'json',
                success: function(data) {
                    $.each(data, function(index, task) {
                        taskSelect.append($('<option></option>')
                            .attr('value', task.id)
                            .text(task.name));
                    });
                }
            });
        }
    });
    
    // 日期验证
    $('#filter-form').submit(function(e) {
        const startDate = new Date($('#start_date').val());
        const endDate = new Date($('#end_date').val());
        
        if (startDate > endDate) {
            alert('开始日期不能大于结束日期');
            e.preventDefault();
            return false;
        }
        
        // 显示加载指示器
        showLoadingIndicator();
        return true;
    });
    
    // 分页链接点击时显示加载指示器
    $('.pagination .page-link').click(function() {
        showLoadingIndicator();
    });
    
    // 显示加载指示器函数
    function showLoadingIndicator() {
        $('body').append('<div class="loading-overlay"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div></div>');
    }
    
    // 重置按钮事件
    $('button[type="reset"]').click(function(e) {
        e.preventDefault();
        $('#filter-form')[0].reset();
        // 重置日期为当前值
        $('#start_date').val(startDateDefault);
        $('#end_date').val(endDateDefault);
        
        // 清空所有查询参数并提交表单
        window.location.href = consumptionRecordsListUrl;
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

    // ========== 视图切换功能 ==========
    
    // 切换到日期视图
    $('#date-view-btn').click(function() {
        $(this).addClass('btn-primary').removeClass('btn-outline-primary');
        $('#project-view-btn').removeClass('btn-primary').addClass('btn-outline-primary');
        $('#date-view-container').removeClass('d-none');
        $('#project-view-container').addClass('d-none');
    });
    
    // 切换到项目视图
    $('#project-view-btn').click(function() {
        $(this).addClass('btn-primary').removeClass('btn-outline-primary');
        $('#date-view-btn').removeClass('btn-primary').addClass('btn-outline-primary');
        $('#project-view-container').removeClass('d-none');
        $('#date-view-container').addClass('d-none');
        
        // 如果还没有加载项目视图数据，则加载数据
        if ($('#projectAccordion').children().length === 0) {
            loadProjectView();
        }
    });
    
    // 加载项目视图数据
    function loadProjectView() {
        showLoadingIndicator();
        
        // 获取当前筛选条件
        const filterParams = $('#filter-form').serialize();
        
        // 通过AJAX请求获取项目列表和汇总数据
        $.ajax({
            url: projectViewDataUrl,
            data: filterParams + '&data_type=summary',
            dataType: 'json',
            success: function(data) {
                renderProjectSummary(data);
                $('.loading-overlay').remove();
            },
            error: function(xhr, status, error) {
                console.error('加载项目视图失败：', error);
                $('#project-view-content').html('<div class="p-5 text-center text-danger"><i class="fas fa-exclamation-circle fa-3x mb-3"></i><p>加载数据失败，请稍后重试</p></div>');
                $('.loading-overlay').remove();
            }
        });
    }
    
    // 渲染项目汇总视图（只显示项目列表和汇总数据，不加载详细内容）
    function renderProjectSummary(data) {
        const projectAccordion = $('#projectAccordion');
        projectAccordion.empty();
        
        if (data.projects.length === 0) {
            projectAccordion.html('<div class="p-5 text-center text-muted"><i class="fas fa-search fa-3x mb-3"></i><p>没有找到符合条件的消耗记录</p><small>请尝试调整筛选条件</small></div>');
            return;
        }
        
        // 创建项目总计行
        const totalRow = $('<div class="card mb-3 bg-light">').html(`
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h5 class="mb-0"><i class="fas fa-calculator me-2"></i>所有项目总计</h5>
                    </div>
                    <div class="col-md-6">
                        <div class="row">
                            <div class="col-4">
                                <div class="d-flex align-items-center">
                                    <strong style="min-width: 90px;">总消耗额：</strong>
                                    <span class="text-primary ms-1">¥${data.total_consumption.toFixed(2)}</span>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="d-flex align-items-center">
                                    <strong style="min-width: 90px;">总注册人数：</strong>
                                    <span class="text-success ms-1">${data.total_registrations}</span>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="d-flex align-items-center">
                                    <strong style="min-width: 90px;">总首充人数：</strong>
                                    <span class="text-warning ms-1">${data.total_first_deposits}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        projectAccordion.append(totalRow);
        
        // 遍历项目数据
        $.each(data.projects, function(index, project) {
            const projectId = 'project-' + project.id;
            const projectCard = $('<div class="accordion-item mb-3 border">');
            
            // 项目标题和汇总数据
            const projectHeader = $('<div class="accordion-header" id="heading-' + projectId + '">').html(`
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-${projectId}" aria-expanded="false" aria-controls="collapse-${projectId}">
                    <div class="container-fluid p-0">
                        <div class="row align-items-center">
                            <div class="col-md-4">
                                <strong><i class="fas fa-folder-open me-2"></i>${project.name}</strong>
                            </div>
                            <div class="col-md-8">
                                <div class="row">
                                    <div class="col-4">
                                        <div class="d-flex align-items-center">
                                            <strong style="min-width: 60px;">消耗：</strong>
                                            <span class="text-primary ms-1">¥${project.total_consumption.toFixed(2)}</span>
                                        </div>
                                    </div>
                                    <div class="col-3">
                                        <div class="d-flex align-items-center">
                                            <strong style="min-width: 60px;">注册：</strong>
                                            <span class="text-success ms-1">${project.total_registrations}</span>
                                        </div>
                                    </div>
                                    <div class="col-3">
                                        <div class="d-flex align-items-center">
                                            <strong style="min-width: 60px;">首充：</strong>
                                            <span class="text-warning ms-1">${project.total_first_deposits}</span>
                                        </div>
                                    </div>
                                    <div class="col-2">
                                        <div class="d-flex align-items-center">
                                            <strong style="min-width: 60px;">任务数：</strong>
                                            <span class="ms-1">${project.task_count}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </button>
            `);
            
            // 项目内容区域 - 初始为空的容器
            const projectContent = $('<div id="collapse-' + projectId + '" class="accordion-collapse collapse" aria-labelledby="heading-' + projectId + '" data-project-id="' + project.id + '" data-loaded="false">');
            const projectBody = $('<div class="accordion-body p-0">').html(`
                <div class="text-center p-4 loading-tasks-placeholder">
                    <div class="spinner-border text-primary mb-2" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="text-muted">加载任务数据中，请稍候...</p>
                </div>
            `);
            
            // 组装项目卡片
            projectContent.append(projectBody);
            projectCard.append(projectHeader);
            projectCard.append(projectContent);
            projectAccordion.append(projectCard);
        });
        
        // 添加项目点击事件，懒加载任务数据
        $('.accordion-collapse').on('show.bs.collapse', function() {
            const projectContainer = $(this);
            const projectId = projectContainer.data('project-id');
            const isLoaded = projectContainer.data('loaded') === true;
            
            // 如果数据已加载，不重复加载
            if (isLoaded) return;
            
            // 获取当前筛选条件
            const filterParams = $('#filter-form').serialize();
            
            // 加载项目任务数据
            $.ajax({
                url: projectViewDataUrl,
                data: filterParams + '&data_type=tasks&project_id=' + projectId,
                dataType: 'json',
                success: function(data) {
                    renderProjectTasks(projectContainer, data);
                    projectContainer.data('loaded', true);
                },
                error: function(xhr, status, error) {
                    projectContainer.find('.accordion-body').html(`
                        <div class="text-center p-4">
                            <i class="fas fa-exclamation-circle text-danger fa-3x mb-3"></i>
                            <p>加载任务数据失败，请稍后再试</p>
                            <button class="btn btn-sm btn-outline-primary reload-tasks-btn" data-project-id="${projectId}">
                                <i class="fas fa-sync-alt me-1"></i>重试
                            </button>
                        </div>
                    `);
                }
            });
        });
        
        // 添加重试加载按钮事件
        $(document).on('click', '.reload-tasks-btn', function(e) {
            e.preventDefault();
            const projectId = $(this).data('project-id');
            const projectContainer = $('#collapse-project-' + projectId);
            
            projectContainer.find('.accordion-body').html(`
                <div class="text-center p-4 loading-tasks-placeholder">
                    <div class="spinner-border text-primary mb-2" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="text-muted">加载任务数据中，请稍候...</p>
                </div>
            `);
            
            // 触发数据重新加载
            projectContainer.data('loaded', false);
            projectContainer.trigger('show.bs.collapse');
        });
    }
    
    // 渲染项目任务数据（当用户展开某个项目时调用）
    function renderProjectTasks(projectContainer, data) {
        const projectBody = projectContainer.find('.accordion-body');
        projectBody.empty();
        
        // 遍历项目下的任务
        $.each(data.tasks, function(taskIndex, task) {
            const taskId = 'task-' + task.id;
            const taskCard = $('<div class="card mb-3 mx-3 mt-3 border border-light">');
            const taskHeader = $('<div class="card-header bg-light task-header" data-task-id="' + task.id + '" data-loaded="false">').html(`
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h6 class="mb-0"><i class="fas fa-tasks me-2"></i>${task.name}</h6>
                    </div>
                    <div class="col-md-4 text-end">
                        <button class="btn btn-sm btn-outline-primary task-details-btn">
                            <i class="fas fa-chevron-down me-1"></i>查看消耗详情
                        </button>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-md-12">
                        <div class="row">
                            <div class="col-4">
                                <div class="d-flex align-items-center">
                                    <strong style="min-width: 60px;">消耗：</strong>
                                    <span class="text-primary ms-1">¥${task.total_consumption.toFixed(2)}</span>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="d-flex align-items-center">
                                    <strong style="min-width: 60px;">注册：</strong>
                                    <span class="text-success ms-1">${task.total_registrations}</span>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="d-flex align-items-center">
                                    <strong style="min-width: 60px;">首充：</strong>
                                    <span class="text-warning ms-1">${task.total_first_deposits}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `);
            
            // 创建任务内容容器（初始为隐藏）
            const taskContent = $('<div class="task-content" style="display: none;">');
            const taskLoadingPlaceholder = $('<div class="text-center p-4">').html(`
                <div class="spinner-border text-primary mb-2" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="text-muted">加载消耗记录中，请稍候...</p>
            `);
            
            taskContent.append(taskLoadingPlaceholder);
            taskCard.append(taskHeader);
            taskCard.append(taskContent);
            projectBody.append(taskCard);
        });
        
        // 添加任务详情按钮点击事件
        projectBody.on('click', '.task-details-btn', function() {
            const taskHeader = $(this).closest('.task-header');
            const taskContent = taskHeader.next('.task-content');
            const taskId = taskHeader.data('task-id');
            const isLoaded = taskHeader.data('loaded') === true;
            const btn = $(this);
            
            // 切换图标和按钮文本
            if (taskContent.is(':visible')) {
                taskContent.slideUp();
                btn.html('<i class="fas fa-chevron-down me-1"></i>查看消耗详情');
                return;
            }
            
            taskContent.slideDown();
            btn.html('<i class="fas fa-chevron-up me-1"></i>隐藏消耗详情');
            
            // 如果数据已加载，不重复加载
            if (isLoaded) return;
            
            // 获取当前筛选条件
            const filterParams = $('#filter-form').serialize();
            
            // 加载任务消耗记录
            $.ajax({
                url: projectViewDataUrl,
                data: filterParams + '&data_type=records&task_id=' + taskId,
                dataType: 'json',
                success: function(data) {
                    renderTaskRecords(taskContent, data);
                    taskHeader.data('loaded', true);
                },
                error: function(xhr, status, error) {
                    taskContent.html(`
                        <div class="text-center p-4">
                            <i class="fas fa-exclamation-circle text-danger fa-3x mb-3"></i>
                            <p>加载消耗记录失败，请稍后再试</p>
                            <button class="btn btn-sm btn-outline-primary reload-records-btn" data-task-id="${taskId}">
                                <i class="fas fa-sync-alt me-1"></i>重试
                            </button>
                        </div>
                    `);
                }
            });
        });
        
        // 添加重试加载消耗记录按钮事件
        projectBody.on('click', '.reload-records-btn', function(e) {
            e.preventDefault();
            const taskId = $(this).data('task-id');
            const taskHeader = $('.task-header[data-task-id="' + taskId + '"]');
            const taskContent = taskHeader.next('.task-content');
            
            taskContent.html(`
                <div class="text-center p-4">
                    <div class="spinner-border text-primary mb-2" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="text-muted">加载消耗记录中，请稍候...</p>
                </div>
            `);
            
            // 触发数据重新加载
            taskHeader.data('loaded', false);
            
            // 获取当前筛选条件
            const filterParams = $('#filter-form').serialize();
            
            // 重新加载任务消耗记录
            $.ajax({
                url: projectViewDataUrl,
                data: filterParams + '&data_type=records&task_id=' + taskId,
                dataType: 'json',
                success: function(data) {
                    renderTaskRecords(taskContent, data);
                    taskHeader.data('loaded', true);
                },
                error: function(xhr, status, error) {
                    taskContent.html(`
                        <div class="text-center p-4">
                            <i class="fas fa-exclamation-circle text-danger fa-3x mb-3"></i>
                            <p>加载消耗记录失败，请稍后再试</p>
                            <button class="btn btn-sm btn-outline-primary reload-records-btn" data-task-id="${taskId}">
                                <i class="fas fa-sync-alt me-1"></i>重试
                            </button>
                        </div>
                    `);
                }
            });
        });
    }
    
    // 渲染任务消耗记录（当用户展开某个任务时调用）
    function renderTaskRecords(taskContent, data) {
        // 创建消耗记录表格
        const taskTable = $('<div class="table-responsive">').html(`
            <table class="table table-hover mb-0">
                <thead>
                    <tr>
                        <th style="width: 120px;">日期</th>
                        <th class="text-end">当日消耗</th>
                        <th class="text-end">实际消耗</th>
                        <th class="text-end">回流</th>
                        <th class="text-end">点击量</th>
                        <th class="text-end">注册人数</th>
                        <th class="text-end">首充人数</th>
                        <th class="text-end">注册成本</th>
                        <th class="text-end">首充成本</th>
                    </tr>
                </thead>
                <tbody>
                </tbody>
            </table>
        `);
        
        // 获取表格body
        const taskTableBody = taskTable.find('tbody');
        
        // 添加任务消耗记录
        if (data.records.length === 0) {
            taskTableBody.html('<tr><td colspan="9" class="text-center py-3 text-muted">该任务在筛选时间范围内无消耗记录</td></tr>');
        } else {
            $.each(data.records, function(recordIndex, record) {
                const recordRow = $('<tr>').html(`
                    <td>${record.date}</td>
                    <td class="text-end"><span class="badge bg-light text-dark">${record.daily_consumption}</span></td>
                    <td class="text-end"><span class="fw-bold text-primary">${record.actual_consumption}</span></td>
                    <td class="text-end">${record.return_flow}</td>
                    <td class="text-end">${record.clicks}</td>
                    <td class="text-end"><span class="badge bg-success text-white">${record.registrations}</span></td>
                    <td class="text-end"><span class="badge bg-warning text-dark">${record.first_deposits}</span></td>
                    <td class="text-end">${record.registration_cost}</td>
                    <td class="text-end">${record.first_deposit_cost}</td>
                `);
                taskTableBody.append(recordRow);
            });
            
            // 小计行已被移除，不再显示
        }
        
        // 更新任务内容
        taskContent.empty().append(taskTable);
    }
}); 