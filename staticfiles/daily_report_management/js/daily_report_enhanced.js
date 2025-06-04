/**
 * 日报数据管理增强功能
 * 添加分页功能和其他交互效果
 */

$(document).ready(function() {
    // 调整布局以适应页面容器
    adjustLayoutToContainer();
    
    // 初始化日期选择器 - 初始化放在第一位确保执行
    initializeDateControls();
    
    // 初始化数据
    loadReportData();
    
    // 行号自动生成
    $(document).on('DOMNodeInserted', '#report-data tr', function() {
        if ($(this).find('.row-number').length > 0) {
            const rowIndex = $(this).index() + 1;
            $(this).find('.row-number').text(rowIndex);
        }
    });
    
    // 添加表格行悬停效果
    $(document).on('mouseenter', '.table tbody tr', function() {
        $(this).addClass('hover-highlight');
    }).on('mouseleave', '.table tbody tr', function() {
        $(this).removeClass('hover-highlight');
    });
    
    // 提示框初始化 (如果需要使用Bootstrap的tooltip)
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // 绑定筛选按钮事件
    $('#filter-btn').click(function() {
        loadReportData();
    });
    
    // 回车触发搜索
    $('#channel-name').keypress(function(e) {
        if(e.which === 13) {
            loadReportData();
            e.preventDefault();
        }
    });
    
    // 绑定重置按钮事件
    $('#reset-btn').click(function() {
        $('#date-from').val('');
        $('#date-to').val('');
        $('#channel-name').val('');
        loadReportData();
    });
    
    // 绑定分页按钮事件
    $('#first-page').click(function() {
        if (!$(this).prop('disabled')) {
            goToPage(1);
        }
    });
    
    $('#prev-page').click(function() {
        if (!$(this).prop('disabled')) {
            const currentPage = parseInt($('#current-page').text());
            if (currentPage > 1) {
                goToPage(currentPage - 1);
            }
        }
    });
    
    $('#next-page').click(function() {
        if (!$(this).prop('disabled')) {
            const currentPage = parseInt($('#current-page').text());
            const totalPages = parseInt($('#total-pages').text());
            if (currentPage < totalPages) {
                goToPage(currentPage + 1);
            }
        }
    });
    
    $('#last-page').click(function() {
        if (!$(this).prop('disabled')) {
            const totalPages = parseInt($('#total-pages').text());
            goToPage(totalPages);
        }
    });
    
    $('#page-size-select').change(function() {
        goToPage(1);
    });
    
    // 检测屏幕尺寸变化，调整UI
    $(window).resize(function() {
        adjustUIForScreenSize();
        adjustLayoutToContainer();
    });
    
    // 初始调整UI
    adjustUIForScreenSize();
});

/**
 * 初始化日期控件
 */
function initializeDateControls() {
    console.log('初始化日期控件...');
    
    // 获取当前日期
    const today = new Date();
    // 设置默认开始日期为当前月第一天
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    
    const formatDate = (date) => {
        let month = '' + (date.getMonth() + 1);
        let day = '' + date.getDate();
        const year = date.getFullYear();
        
        if (month.length < 2) month = '0' + month;
        if (day.length < 2) day = '0' + day;
        
        return [year, month, day].join('-');
    };
    
    // 格式化日期
    const formattedToday = formatDate(today);
    const formattedFirstDay = formatDate(firstDayOfMonth);
    
    console.log('今天日期:', formattedToday);
    console.log('本月第一天:', formattedFirstDay);
    
    // 设置日期选择器的值
    // 仅当元素存在且尚未设置值时才设置
    if ($('#date-from').length) {
        $('#date-from').val(formattedFirstDay);
        console.log('已设置开始日期:', $('#date-from').val());
    } else {
        console.error('未找到#date-from元素');
    }
    
    if ($('#date-to').length) {
        $('#date-to').val(formattedToday);
        console.log('已设置结束日期:', $('#date-to').val());
    } else {
        console.error('未找到#date-to元素');
    }
}

/**
 * 根据屏幕尺寸调整UI
 */
function adjustUIForScreenSize() {
    const windowWidth = $(window).width();
    
    // 根据屏幕宽度调整表格滚动提示
    if (windowWidth < 992 && $('.table-scroll-hint').length === 0) {
        $('.table-responsive').before('<div class="table-scroll-hint"><i class="fas fa-arrows-alt-h me-1"></i>左右滑动查看更多数据</div>');
    } else if (windowWidth >= 992) {
        $('.table-scroll-hint').remove();
    }
}

/**
 * 调整布局适应页面容器
 */
function adjustLayoutToContainer() {
    // 移除页面上的外部边距和内边距
    $('body').css({
        'margin': '0',
        'padding': '0',
        'overflow-x': 'hidden'
    });
    
    // 调整表格高度适应可用空间
    const windowHeight = $(window).height();
    const filterCardHeight = $('.filter-card').outerHeight(true);
    const tableHeaderHeight = $('.report-card .card-header').outerHeight(true);
    const paginationHeight = $('.pagination-area').outerHeight(true);
    
    // 计算表格容器的可用高度
    let availableHeight = windowHeight - filterCardHeight - tableHeaderHeight - paginationHeight - 20;
    availableHeight = Math.max(availableHeight, 300); // 确保最小高度
    
    // 设置表格容器的高度
    $('.table-container').css('height', availableHeight + 'px');
    
    // 添加调试日志
    console.log('窗口高度:', windowHeight, 
                '过滤区高度:', filterCardHeight, 
                '表头高度:', tableHeaderHeight, 
                '分页区高度:', paginationHeight, 
                '表格可用高度:', availableHeight);
}

/**
 * 增强的分页控件更新函数
 */
window.updatePaginationControls = function() {
    const pageInfo = window.pageInfo || {
        currentPage: 1,
        totalPages: 1,
        totalItems: 0
    };
    
    // 更新当前页和总页数
    $('#current-page').text(pageInfo.currentPage);
    $('#total-pages').text(pageInfo.totalPages);
    
    // 启用/禁用页码按钮
    $('#first-page, #prev-page').prop('disabled', pageInfo.currentPage <= 1);
    $('#last-page, #next-page').prop('disabled', pageInfo.currentPage >= pageInfo.totalPages);
    
    // 渲染页码
    renderPageNumbers(pageInfo.currentPage, pageInfo.totalPages);
};

// 加载日报数据
window.loadReportData = function(page = 1) {
    showLoading();
    
    const dateFrom = $('#date-from').val();
    const dateTo = $('#date-to').val();
    const channelName = $('#channel-name').val();
    const pageSize = $('#page-size-select').val() || 20;
    
    // 使用完整路径，确保请求能正确发送
    let url = `/daily_report_management/list/?page=${page}&page_size=${pageSize}`;
    if (dateFrom) url += `&date_from=${dateFrom}`;
    if (dateTo) url += `&date_to=${dateTo}`;
    if (channelName) url += `&channel_name=${encodeURIComponent(channelName)}`;
    
    console.log('正在从以下URL获取数据:', url);
    
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            console.log('接收到的数据:', data);
            if (data.code === 200) {
                // 更新分页信息
                window.pageInfo = {
                    currentPage: data.page,
                    pageSize: data.page_size,
                    totalPages: data.total_pages,
                    totalItems: data.total
                };
                
                // 更新分页控件
                updatePaginationControls();
                
                // 渲染数据
                renderReportData(data.data);
                
                // 添加动画效果
                $('.table tbody tr').each(function(index) {
                    $(this).css({
                        'opacity': 0,
                        'transform': 'translateY(10px)'
                    }).delay(index * 30).animate({
                        'opacity': 1,
                        'transform': 'translateY(0)'
                    }, 200);
                });
            } else {
                console.error('API返回错误:', data);
                showEmptyMessage('加载数据失败，请稍后重试');
            }
        },
        error: function(xhr, status, error) {
            console.error('获取数据时出错:', error);
            showEmptyMessage('网络错误，请检查连接');
        }
    });
};

// 分页跳转函数
window.goToPage = function(page) {
    loadReportData(page);
};

// 显示加载中
function showLoading() {
    $('#report-data').html(`
        <tr>
            <td colspan="18">
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <div class="mt-3 loading-text">加载中...</div>
                </div>
            </td>
        </tr>
    `);
}

// 显示空数据提示
function showEmptyMessage(message) {
    $('#report-data').html(`
        <tr>
            <td colspan="18">
                <div class="empty-message">
                    <i class="fas fa-info-circle me-2"></i>
                    ${message || '暂无数据'}
                </div>
            </td>
        </tr>
    `);
}

// 渲染页码
function renderPageNumbers(currentPage, totalPages) {
    const $pageNumbers = $('#page-numbers');
    $pageNumbers.empty();
    
    // 屏幕宽度决定显示页码数量
    const isSmallScreen = $(window).width() < 576;
    const pageButtonsToShow = isSmallScreen ? 3 : 5;
    
    let startPage = Math.max(1, currentPage - Math.floor(pageButtonsToShow / 2));
    let endPage = Math.min(totalPages, startPage + pageButtonsToShow - 1);
    
    if (endPage - startPage < pageButtonsToShow - 1) {
        startPage = Math.max(1, endPage - pageButtonsToShow + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const $pageButton = $('<button>')
            .addClass('page-btn')
            .text(i)
            .attr('title', `跳转到第${i}页`);
            
        if (i === currentPage) {
            $pageButton.addClass('active');
        }
        
        $pageButton.click(function() {
            goToPage(i);
        });
        
        $pageNumbers.append($pageButton);
    }
}

// 格式化优化师
function formatOptimizers(optimizers) {
    if (!optimizers || optimizers === '-') return '-';
    
    return optimizers.split(',').map(name => 
        `<span class="optimizer-name">${name.trim()}</span>`
    ).join(' ');
}

// 格式化成本，标记异常值
function formatCost(cost, isRegCost) {
    const costValue = parseFloat(cost);
    if (isNaN(costValue) || costValue === 0) return '-';
    
    let className = '';
    // 注册成本告警阈值
    if (isRegCost && costValue > 50) {
        className = 'text-danger';
    }
    // 首充成本告警阈值
    else if (!isRegCost && costValue > 200) {
        className = 'text-danger';
    }
    
    return `<span class="${className}">${costValue.toFixed(2)}</span>`;
}

// 格式化百分比
function formatPercent(value) {
    const percentValue = parseFloat(value);
    if (isNaN(percentValue) || percentValue === 0) return '-';
    
    let className = '';
    if (percentValue > 20) {
        className = 'text-success';
    } else if (percentValue < 5) {
        className = 'text-warning';
    }
    
    return `<span class="${className}">${percentValue.toFixed(2)}%</span>`;
}

// 格式化货币
function formatCurrency(value) {
    const numValue = parseFloat(value);
    if (isNaN(numValue) || numValue === 0) return '-';
    
    return numValue.toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// 渲染日报数据
window.renderReportData = function(reports) {
    const $tbody = $('#report-data');
    $tbody.empty();
    
    if (!reports || reports.length === 0) {
        showEmptyMessage();
        return;
    }
    
    reports.forEach((report, index) => {
        // 格式化数据
        const budget = report.budget ? formatCurrency(report.budget) : '-';
        
        // 预算说明可能很长，截断显示
        const budgetDescription = report.budget_description || '';
        const shortBudgetDesc = budgetDescription.length > 20 
            ? budgetDescription.substring(0, 20) + '...' 
            : budgetDescription;
        
        // 判断是否为偶数行
        const rowClass = index % 2 === 0 ? '' : 'table-row-alt';
        
        const $tr = $('<tr>').addClass(rowClass);
        
        $tr.html(`
            <td class="text-center row-number">${index + 1}</td>
            <td>${report.date}</td>
            <td>${report.channel_name}</td>
            <td>${formatOptimizers(report.optimizers)}</td>
            <td class="text-end metric-value">${formatCurrency(report.consumption)}</td>
            <td class="text-center">${report.registrations}</td>
            <td class="text-center">${report.first_deposits}</td>
            <td class="text-end">${formatCost(report.registration_cost, true)}</td>
            <td class="text-end">${formatCost(report.first_deposit_cost, false)}</td>
            <td class="text-end metric-value">${budget}</td>
            <td>${report.kpi || '-'}</td>
            <td class="text-center">${formatPercent(report.daily_recharge_rate)}</td>
            <td class="text-center">${formatPercent(report.retention_day2)}</td>
            <td class="text-center">${formatPercent(report.retention_day3)}</td>
            <td class="text-center">${formatPercent(report.retention_day4)}</td>
            <td class="text-center">${formatPercent(report.retention_day5)}</td>
            <td class="text-center">${formatPercent(report.retention_day7)}</td>
            <td title="${budgetDescription}">${shortBudgetDesc}</td>
        `);
        
        $tbody.append($tr);
    });
    
    console.log('数据渲染完成，共', reports.length, '条');
};