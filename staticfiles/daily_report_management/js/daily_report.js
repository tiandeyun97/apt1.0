// 等待DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 查询功能
    document.getElementById('filter-btn').addEventListener('click', function() {
        loadReportData();
    });
    
    // 重置查询
    document.getElementById('reset-btn').addEventListener('click', function() {
        document.getElementById('date-from').value = '';
        document.getElementById('date-to').value = '';
        document.getElementById('channel-name').value = '';
        loadReportData();
    });
    
    // 分页控件事件绑定
    document.getElementById('first-page').addEventListener('click', function() {
        goToPage(1);
    });
    
    document.getElementById('prev-page').addEventListener('click', function() {
        const currentPage = parseInt(document.getElementById('current-page').textContent);
        if (currentPage > 1) {
            goToPage(currentPage - 1);
        }
    });
    
    document.getElementById('next-page').addEventListener('click', function() {
        const currentPage = parseInt(document.getElementById('current-page').textContent);
        const totalPages = parseInt(document.getElementById('total-pages').textContent);
        if (currentPage < totalPages) {
            goToPage(currentPage + 1);
        }
    });
    
    document.getElementById('last-page').addEventListener('click', function() {
        const totalPages = parseInt(document.getElementById('total-pages').textContent);
        goToPage(totalPages);
    });
    
    document.getElementById('page-size-select').addEventListener('change', function() {
        goToPage(1);
    });
    
    // 分页跳转函数
    window.goToPage = function(page) {
        loadReportData(page);
    };
    
    // 加载日报数据
    window.loadReportData = function(page = 1) {
        showLoading();
        
        const dateFrom = document.getElementById('date-from').value;
        const dateTo = document.getElementById('date-to').value;
        const channelName = document.getElementById('channel-name').value;
        const pageSize = document.getElementById('page-size-select').value || 20;
        
        // 使用完整路径，确保请求能正确发送
        let url = `/daily_report_management/list/?page=${page}&page_size=${pageSize}`;
        if (dateFrom) url += `&date_from=${dateFrom}`;
        if (dateTo) url += `&date_to=${dateTo}`;
        if (channelName) url += `&channel_name=${encodeURIComponent(channelName)}`;
        
        console.log('Fetching data from URL:', url);
        
        fetch(url)
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Received data:', data);
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
                } else {
                    console.error('API返回错误:', data);
                    showEmptyMessage('加载数据失败，请稍后重试');
                }
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                showEmptyMessage('网络错误，请检查连接');
            });
    };
    
    // 显示加载中
    function showLoading() {
        const tbody = document.getElementById('report-data');
        tbody.innerHTML = `
            <tr>
                <td colspan="18">
                    <div class="loading">
                        <div class="loading-spinner"></div>
                    </div>
                </td>
            </tr>
        `;
    }
    
    // 显示空数据提示
    function showEmptyMessage(message) {
        const tbody = document.getElementById('report-data');
        tbody.innerHTML = `
            <tr>
                <td colspan="18">
                    <div class="empty-message">${message || '暂无数据'}</div>
                </td>
            </tr>
        `;
    }
    
    // 格式化百分比
    function formatPercent(value) {
        if (value === null || value === undefined || value === '') {
            return '-';
        }
        return parseFloat(value).toFixed(2) + '%';
    }
    
    // 格式化成本，并根据阈值设置颜色
    function formatCost(cost, isRegistration = true) {
        if (!cost || cost <= 0) {
            return '-';
        }
        
        const costValue = parseFloat(cost).toFixed(2);
        let colorClass = '';
        
        if (isRegistration) {
            // 注册成本阈值
            colorClass = parseFloat(cost) > 50 ? 'negative' : 'positive';
        } else {
            // 首充成本阈值
            colorClass = parseFloat(cost) > 200 ? 'negative' : 'positive';
        }
        
        return `<span class="metric-value ${colorClass}">${costValue}</span>`;
    }
    
    // 格式化优化师列表为徽章
    function formatOptimizers(optimizers) {
        if (!optimizers || optimizers === '-') {
            return '-';
        }
        
        const optimizerList = optimizers.split(', ');
        if (optimizerList.length === 0) {
            return '-';
        }
        
        // 创建一个容器来放置优化师名字
        let container = '<div class="optimizer-container">';
        
        // 将每个优化师名字添加到容器中
        optimizerList.forEach(optimizer => {
            if (optimizer.trim()) {
                container += `<span class="optimizer-badge">${optimizer.trim()}</span>`;
            }
        });
        
        container += '</div>';
        return container;
    }
    
    // 渲染日报数据
    function renderReportData(reports) {
        const tbody = document.getElementById('report-data');
        console.log('渲染数据，tbody元素存在:', !!tbody, '数据条数:', reports ? reports.length : 0);
        
        if (!tbody) {
            console.error('找不到#report-data元素!');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (!reports || reports.length === 0) {
            showEmptyMessage();
            return;
        }
        
        console.log('开始渲染数据行...');
        reports.forEach((report, index) => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-id', report.id);
            
            // 格式化数字
            const consumption = parseFloat(report.consumption).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            const budget = parseFloat(report.budget).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            
            // 处理预算说明的tooltip
            const budgetDescription = report.budget_description || '-';
            const shortBudgetDesc = budgetDescription.length > 20 ? budgetDescription.substring(0, 20) + '...' : budgetDescription;
            
            tr.innerHTML = `
                <td class="row-number"></td>
                <td>${report.date}</td>
                <td>${report.channel_name}</td>
                <td>${formatOptimizers(report.optimizers)}</td>
                <td class="metric-value">${consumption}</td>
                <td>${report.registrations}</td>
                <td>${report.first_deposits}</td>
                <td>${formatCost(report.registration_cost, true)}</td>
                <td>${formatCost(report.first_deposit_cost, false)}</td>
                <td class="metric-value">${budget}</td>
                <td>${report.kpi || '-'}</td>
                <td>${formatPercent(report.daily_recharge_rate)}</td>
                <td>${formatPercent(report.retention_day2)}</td>
                <td>${formatPercent(report.retention_day3)}</td>
                <td>${formatPercent(report.retention_day4)}</td>
                <td>${formatPercent(report.retention_day5)}</td>
                <td>${formatPercent(report.retention_day7)}</td>
                <td title="${budgetDescription}">${shortBudgetDesc}</td>
            `;
            tbody.appendChild(tr);
        });
        console.log('数据渲染完成，共', reports.length, '条');
    }
    
    // 渲染页码
    function renderPageNumbers(currentPage, totalPages) {
        const pageNumbersDiv = document.getElementById('page-numbers');
        pageNumbersDiv.innerHTML = '';
        
        // 确定要显示的页码范围
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const pageButton = document.createElement('button');
            pageButton.className = 'page-number' + (i === currentPage ? ' active' : '');
            pageButton.textContent = i;
            pageButton.addEventListener('click', function() {
                goToPage(i);
            });
            pageNumbersDiv.appendChild(pageButton);
        }
    }
    
    // 检查分页按钮状态
    function updatePaginationControls() {
        const { currentPage, totalPages } = window.pageInfo;
        
        document.getElementById('first-page').disabled = currentPage <= 1;
        document.getElementById('prev-page').disabled = currentPage <= 1;
        document.getElementById('next-page').disabled = currentPage >= totalPages;
        document.getElementById('last-page').disabled = currentPage >= totalPages;
        
        document.getElementById('current-page').textContent = currentPage;
        document.getElementById('total-pages').textContent = totalPages;
        
        renderPageNumbers(currentPage, totalPages);
    }
    
    // 获取CSRF Token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // 初始加载
    loadReportData();
}); 