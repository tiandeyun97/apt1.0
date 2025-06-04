/**
 * 账户及信用卡列表管理
 */
$(document).ready(function() {
    // 获取CSRF令牌
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // 获取数据URL
    const dataUrl = $('#data-url').data('url');
    
    // 获取用户权限
    const hasChangePermission = $('#user-perms').data('has-change-perm') === true;
    const hasViewPermission = $('#user-perms').data('has-view-perm') === true;
    
    // 获取用户角色
    const userRoles = $('#user-roles').data('roles') || '';
    const userRolesArray = userRoles.split(',').filter(Boolean);
    
    // 检查用户是否有特定角色
    const isOptimizer = userRolesArray.includes('优化师') && 
                         !userRolesArray.includes('部门主管') && 
                         !userRolesArray.includes('小组长');
    const isTeamLeader = userRolesArray.includes('小组长') && 
                          !userRolesArray.includes('部门主管');
    const isDepartmentManager = userRolesArray.includes('部门主管');
    
    // 获取当前用户名
    let currentUsername = '';
    if (document.querySelector('.role-info')) {
        // 尝试从页面获取用户名
        const userLinks = document.querySelectorAll('header .dropdown-toggle');
        if (userLinks.length > 0) {
            const userText = userLinks[userLinks.length - 1].textContent.trim();
            if (userText) {
                // 假设格式是 "用户名 (其他信息)"
                const match = userText.match(/([^\s\(]+)/);
                if (match && match[1]) {
                    currentUsername = match[1];
                }
            }
        }
    }
    
    // 初始化查询条件元素
    const filters = {
        cardNumber: $('#card-number-search'),
        responsiblePerson: $('#responsible-person-search'),
        accountId: $('#account-id-search'),
        searchBtn: $('#search-btn'),
        resetBtn: $('#reset-filters')
    };
    
    // 初始化DataTable
    const table = $('#account-card-table').DataTable({
        processing: true,
        serverSide: true,
        ajax: {
            url: dataUrl,
            type: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            data: function(d) {
                // 添加查询参数
                d.card_number = filters.cardNumber.val();
                d.responsible_person = filters.responsiblePerson.val();
                d.account_id = filters.accountId.val();
                return d;
            }
        },
        columns: [
            { 
                // 序号列
                data: null,
                render: function(data, type, row, meta) {
                    return meta.row + meta.settings._iDisplayStart + 1;
                },
                orderable: false,
                width: '60px',
                className: 'text-center'
            },
            { 
                data: 'card_number',
                render: function(data) {
                    // 显示完整卡号
                    return `<span class="card-number">${data}</span>`;
                }
            },
            { 
                data: 'expiry_date',
                render: function(data) {
                    return `<span class="expiry-date">${data}</span>`;
                }
            },
            { 
                data: 'cvc',
                render: function(data) {
                    // 隐藏CVC，点击显示
                    return `<span class="mask-info" data-value="${data}" data-type="cvc">***</span>`;
                }
            },
            { 
                data: 'full_info',
                render: function(data) {
                    // 隐藏完整信息，点击显示
                    return `<span class="mask-info" data-value="${data}" data-type="full">***** <i class="fas fa-eye-slash fa-xs"></i></span>`;
                }
            },
            { 
                data: 'responsible_person',
                render: function(data) {
                    // 如果是当前用户，突出显示
                    if (data === currentUsername) {
                        return `<span class="responsible-person font-weight-bold text-primary">${data} <i class="fas fa-user-check text-success"></i></span>`;
                    }
                    return `<span class="responsible-person">${data}</span>`;
                }
            },
            { data: 'serial_number' },
            { 
                data: 'bm_name',
                render: function(data) {
                    return `<span class="bm-name">${data}</span>`;
                }
            },
            { 
                data: 'has_limit',
                render: function(data) {
                    return data === '是' ? 
                        '<span class="badge bg-warning"><i class="fas fa-exclamation-circle me-1"></i>是</span>' : 
                        '<span class="badge bg-success"><i class="fas fa-check-circle me-1"></i>否</span>';
                }
            },
            { 
                data: 'account_id',
                render: function(data) {
                    return data ? `<span class="account-id">${data}</span>` : '-';
                }
            },
            { 
                data: 'account_status',
                render: function(data) {
                    let badgeClass = 'bg-secondary';
                    let icon = 'fas fa-circle';
                    
                    if (data === '正常') {
                        badgeClass = 'bg-success';
                        icon = 'fas fa-check-circle';
                    } else if (data === '待激活') {
                        badgeClass = 'bg-info';
                        icon = 'fas fa-clock';
                    } else if (data === '已冻结') {
                        badgeClass = 'bg-danger';
                        icon = 'fas fa-ban';
                    } else if (data === '已关闭') {
                        badgeClass = 'bg-dark';
                        icon = 'fas fa-times-circle';
                    }
                    
                    return `<span class="badge ${badgeClass}"><i class="${icon} me-1"></i>${data}</span>`;
                }
            },
            { 
                data: 'card_platform',
                render: function(data) {
                    let icon = '';
                    
                    if (data === 'Visa') {
                        icon = '<i class="fab fa-cc-visa me-1"></i>';
                    } else if (data === 'Mastercard') {
                        icon = '<i class="fab fa-cc-mastercard me-1"></i>';
                    } else if (data === '美国运通') {
                        icon = '<i class="fab fa-cc-amex me-1"></i>';
                    } else {
                        icon = '<i class="fas fa-credit-card me-1"></i>';
                    }
                    
                    return `<span class="card-platform">${icon}${data}</span>`;
                }
            },
            { 
                // 最近消耗数据列
                data: 'recent_consumptions',
                render: function(data) {
                    if (!data || data.length === 0) {
                        return '<span class="text-muted"><i class="fas fa-info-circle me-1"></i>暂无消耗记录</span>';
                    }
                    
                    let html = '<div class="recent-consumption-data">';
                    data.forEach(function(item) {
                        html += `
                            <div class="consumption-item">
                                <span class="consumption-month"><i class="far fa-calendar-alt me-1"></i>${item.month_display}</span>
                                <span class="consumption-amount"><i class="fas fa-dollar-sign me-1"></i>${item.amount}</span>
                            </div>
                        `;
                    });
                    html += '</div>';
                    
                    return html;
                }
            },
            { 
                data: 'id',
                orderable: false,
                render: function(data, type, row) {
                    let buttons = `<div class="btn-group btn-group-sm">`;
                    
                    // 查看按钮 - 所有人都可以查看
                    buttons += `<button type="button" class="btn btn-outline-primary btn-action view-btn" data-id="${data}" title="查看详情">
                                <i class="fas fa-eye"></i>
                            </button>`;
                    
                    // 编辑按钮 - 只有有更改权限的用户才能看到
                    if (hasChangePermission) {
                        buttons += `<button type="button" class="btn btn-outline-success btn-action edit-btn" data-id="${data}" title="编辑信息">
                                    <i class="fas fa-edit"></i>
                                </button>`;
                    }
                    
                    // 添加消耗按钮 - 所有用户都可以看到
                    buttons += `<button type="button" class="btn btn-outline-info btn-action consumption-btn" data-id="${data}" title="添加消耗">
                                <i class="fas fa-dollar-sign"></i>
                            </button>`;
                    
                    buttons += `</div>`;
                    return buttons;
                }
            }
        ],
        order: [[1, 'desc']], // 按卡号排序，序号列是第0列
        language: {
            processing: '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">处理中...</span></div>',
            search: "搜索:",
            lengthMenu: '<i class="fas fa-list me-1"></i> 每页 _MENU_ 条',
            info: '<i class="fas fa-info-circle me-1"></i> 第 _START_ 至 _END_ 条，共 _TOTAL_ 条记录',
            infoEmpty: '<i class="fas fa-info-circle me-1"></i> 暂无数据',
            infoFiltered: "(从 _MAX_ 条数据中过滤)",
            infoPostFix: "",
            loadingRecords: '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">载入中...</span></div>',
            zeroRecords: '<div class="alert alert-info">没有匹配结果</div>',
            emptyTable: '<div class="alert alert-info">暂无数据</div>',
            paginate: {
                first: '<i class="fas fa-angle-double-left"></i>',
                previous: '<i class="fas fa-angle-left"></i>',
                next: '<i class="fas fa-angle-right"></i>',
                last: '<i class="fas fa-angle-double-right"></i>'
            }
        },
        responsive: true,
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        dom: '<"table-responsive"rt><"pagination-row mt-3"<"row align-items-center"<"col-md-6 d-flex align-items-center"li><"col-md-6 d-flex justify-content-end"p>>>',
        pagingType: 'simple_numbers',
        pageLength: 10,
        drawCallback: function() {
            // 表格绘制完成后，绑定工具提示
            $('[title]').tooltip();
            
            // 自定义分页信息样式
            customizePaginationInfo();
            
            // 限制显示的页码数量
            limitPageNumbers(4);
            
            // 高亮当前用户的行
            highlightUserRows();
        },
        initComplete: function() {
            // 自定义分页大小选择器
            customizePageLengthSelect();
            
            // 添加表格加载完成的动画效果
            $('.dataTable').addClass('fade-in');
        }
    });
    
    // 高亮显示当前用户相关的行
    function highlightUserRows() {
        if (currentUsername) {
            $('#account-card-table tbody tr').each(function() {
                const responsiblePerson = $(this).find('td:nth-child(6)').text().trim();
                if (responsiblePerson === currentUsername) {
                    $(this).addClass('table-primary');
                }
            });
        }
    }
    
    // 绑定查询按钮点击事件
    filters.searchBtn.on('click', function() {
        table.ajax.reload();
        
        // 高亮显示已使用的查询条件
        highlightActiveFilters();
    });
    
    // 绑定重置按钮点击事件
    filters.resetBtn.on('click', function() {
        // 清空所有查询条件
        filters.cardNumber.val('');
        filters.responsiblePerson.val('');
        filters.accountId.val('');
        
        // 移除高亮样式
        $('.form-control').removeClass('border-primary bg-light');
        
        // 重新加载表格数据
        table.ajax.reload();
    });
    
    // 绑定输入框回车键查询
    filters.cardNumber.add(filters.responsiblePerson).add(filters.accountId).on('keypress', function(e) {
        if (e.which === 13) { // 回车键
            filters.searchBtn.click();
        }
    });
    
    // 高亮显示已使用的查询条件
    function highlightActiveFilters() {
        $('.form-control').each(function() {
            const $input = $(this);
            if ($input.val()) {
                $input.addClass('border-primary bg-light');
            } else {
                $input.removeClass('border-primary bg-light');
            }
        });
    }
    
    // 限制显示的页码数量
    function limitPageNumbers(maxPages) {
        const paginateContainer = $('.dataTables_paginate');
        const pageBtns = paginateContainer.find('.paginate_button:not(.previous):not(.next)');
        
        if (pageBtns.length > maxPages) {
            // 获取当前页码
            const currentPage = paginateContainer.find('.paginate_button.current').text();
            const currentPageNum = parseInt(currentPage);
            
            // 隐藏多余的页码
            pageBtns.each(function(index) {
                const pageNum = parseInt($(this).text());
                
                // 显示当前页附近的页码
                const shouldShow = (
                    pageNum === 1 || // 始终显示第一页
                    pageNum === parseInt(pageBtns.last().text()) || // 始终显示最后一页
                    (pageNum >= currentPageNum - 1 && pageNum <= currentPageNum + 2) // 显示当前页及其前后页
                );
                
                if (!shouldShow) {
                    $(this).hide();
                }
            });
            
            // 确保显示的页码不超过maxPages
            let visiblePages = paginateContainer.find('.paginate_button:not(.previous):not(.next):visible');
            if (visiblePages.length > maxPages) {
                // 按照优先级隐藏页码
                visiblePages.each(function(index) {
                    if (index >= maxPages) {
                        $(this).hide();
                    }
                });
            }
        }
    }
    
    // 自定义分页信息样式函数
    function customizePaginationInfo() {
        // 添加图标到分页信息
        const infoElement = $('.dataTables_info');
        if (!infoElement.find('i.fas').length) {
            infoElement.html(infoElement.html());
        }
        
        // 美化分页按钮
        $('.paginate_button.previous').attr('title', '上一页');
        $('.paginate_button.next').attr('title', '下一页');
        
        $('[title]').tooltip();
    }
    
    // 美化分页大小选择器
    function customizePageLengthSelect() {
        const lengthSelect = $('.dataTables_length select');
        
        // 添加包装元素
        if (!$('.dataTables_length').find('i.fas').length) {
            $('.dataTables_length label').prepend('<i class="fas fa-list-ol me-1"></i>');
            
            // 将"显示"文本替换为"每页显示"
            const lengthLabel = $('.dataTables_length label');
            let labelHtml = lengthLabel.html();
            labelHtml = labelHtml.replace('显示', '每页显示');
            lengthLabel.html(labelHtml);
        }
    }
    
    // 绑定敏感信息显示/隐藏功能
    $(document).on('click', '.mask-info', function() {
        const $this = $(this);
        const value = $this.data('value');
        const type = $this.data('type');
        
        if ($this.hasClass('revealed')) {
            // 如果已经显示，则隐藏
            if (type === 'cvc') {
                $this.html('***');
            } else {
                $this.html('***** <i class="fas fa-eye-slash fa-xs"></i>');
            }
            $this.removeClass('revealed');
        } else {
            // 如果已经隐藏，则显示
            $this.text(value);
            $this.addClass('revealed');
            
            // 5秒后自动隐藏
            setTimeout(function() {
                if (type === 'cvc') {
                    $this.html('***');
                } else {
                    $this.html('***** <i class="fas fa-eye-slash fa-xs"></i>');
                }
                $this.removeClass('revealed');
            }, 5000);
        }
    });
    
    // 绑定查看按钮事件
    $(document).on('click', '.view-btn', function() {
        const id = $(this).data('id');
        // 显示加载提示
        $(this).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
        // 页面跳转
        window.location.href = '/admin/account_consumption/accountconsumption/' + id + '/change/';
    });
    
    // 绑定编辑按钮事件
    $(document).on('click', '.edit-btn', function() {
        const id = $(this).data('id');
        // 显示加载提示
        $(this).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
        // 页面跳转
        window.location.href = '/admin/account_consumption/accountconsumption/' + id + '/change/';
    });
    
    // 绑定添加消耗按钮事件
    $(document).on('click', '.consumption-btn', function() {
        const id = $(this).data('id');
        // 显示加载提示
        $(this).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
        // 页面跳转
        window.location.href = '/admin/account_consumption/accountconsumption/' + id + '/add_monthly_consumption/';
    });
    
    // 添加页面加载动画
    $(document).ready(function() {
        setTimeout(function() {
            $('.card').addClass('fade-in');
        }, 100);
    });
}); 