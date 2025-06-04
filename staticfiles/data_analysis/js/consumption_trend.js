// 全局变量
let chartData = null;
let charts = {}; // 存储图表实例
let csrfToken = null;
let getDataUrl = null;

// 格式化金额函数
function formatMoney(amount, decimal = 2) {
    return parseFloat(amount).toFixed(decimal).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// 格式化日期函数
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 显示统计数据
function displayStats(data, period) {
    const statsContainer = document.getElementById(`${period}-stats`);
    const loadingSpinner = document.getElementById(`${period}-stats-loading`);
    
    if (loadingSpinner) {
        loadingSpinner.style.display = 'none';
    }
    
    if (!statsContainer) {
        console.error(`统计容器未找到: ${period}-stats`);
        return;
    }
    
    // 清空容器 (保留loading元素)
    const loadingElement = statsContainer.querySelector('.loading-spinner');
    statsContainer.innerHTML = '';
    if (loadingElement) {
        loadingElement.style.display = 'none';
        statsContainer.appendChild(loadingElement);
    }
    
    // 统计项及图标
    const totalItems = [
        { title: '总消费', value: formatMoney(data[`${period}_total`].total_consumption) + ' 元', icon: 'fas fa-money-bill-wave' },
        { title: '总回流', value: formatMoney(data[`${period}_total`].total_return_flow) + ' 元', icon: 'fas fa-undo-alt' },
        { title: '实际总消费', value: formatMoney(data[`${period}_total`].total_actual_consumption) + ' 元', icon: 'fas fa-wallet' },
        { title: '平均注册成本', value: formatMoney(data[`${period}_total`].avg_registration_cost) + ' 元', icon: 'fas fa-user-plus' },
        { title: '平均首充成本', value: formatMoney(data[`${period}_total`].avg_first_deposit_cost) + ' 元', icon: 'fas fa-donate' }
    ];
    
    // 创建统计卡片
    totalItems.forEach(item => {
        const statCard = document.createElement('div');
        statCard.className = 'stat-card';
        statCard.innerHTML = `
            <div class="stat-title"><i class="${item.icon}"></i> ${item.title}</div>
            <div class="stat-value">${item.value}</div>
        `;
        statsContainer.appendChild(statCard);
    });
}

// 初始化消费趋势图表
function initConsumptionChart(data, period, elementId) {
    const chartDom = document.getElementById(elementId);
    if (!chartDom) {
        console.error(`图表容器未找到: ${elementId}`);
        return;
    }
    
    // 初始化ECharts实例
    const myChart = echarts.init(chartDom);
    charts[elementId] = myChart;
    
    // 数据处理
    const dates = data[`${period}_data`].map(item => item.date);
    const consumptionData = data[`${period}_data`].map(item => item.total_consumption);
    const returnFlowData = data[`${period}_data`].map(item => item.total_return_flow);
    const actualConsumptionData = data[`${period}_data`].map(item => item.total_actual_consumption);
    
    // 配置项
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function(params) {
                let result = params[0].name + '<br/>';
                params.forEach(param => {
                    result += `${param.marker} ${param.seriesName}: ${formatMoney(param.value)} 元<br/>`;
                });
                return result;
            }
        },
        legend: {
            data: ['消费', '回流', '实际消费'],
            bottom: 0
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: dates,
            axisLabel: {
                rotate: period === 'yearly' ? 0 : 30,
                interval: 'auto',
                formatter: function(value) {
                    // 对于月度视图，修改标签显示格式
                    if (period === 'yearly') {
                        return value.substring(5, 7) + '月'; // 只显示月份
                    } else {
                        return value.substring(5); // 只显示月-日部分
                    }
                }
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: '{value} 元'
            }
        },
        series: [
            {
                name: '消费',
                type: 'bar',
                barMaxWidth: period === 'yearly' ? 40 : 30,
                data: consumptionData,
                itemStyle: {
                    color: '#0d6efd'
                }
            },
            {
                name: '回流',
                type: 'bar',
                barMaxWidth: period === 'yearly' ? 40 : 30,
                data: returnFlowData,
                itemStyle: {
                    color: '#ffc107'
                }
            },
            {
                name: '实际消费',
                type: 'line',
                data: actualConsumptionData,
                smooth: true,
                itemStyle: {
                    color: '#198754'
                },
                lineStyle: {
                    width: 3,
                    type: 'solid'
                },
                symbol: 'circle',
                symbolSize: 8
            }
        ]
    };
    
    // 使用配置项和数据显示图表
    myChart.setOption(option);
}

// 初始化成本趋势图表
function initCostChart(data, period, elementId) {
    const chartDom = document.getElementById(elementId);
    if (!chartDom) {
        console.error(`图表容器未找到: ${elementId}`);
        return;
    }
    
    // 初始化ECharts实例
    const myChart = echarts.init(chartDom);
    charts[elementId] = myChart;
    
    // 数据处理
    const dates = data[`${period}_data`].map(item => item.date);
    const registrationCostData = data[`${period}_data`].map(item => item.avg_registration_cost);
    const firstDepositCostData = data[`${period}_data`].map(item => item.avg_first_deposit_cost);
    
    // 配置项
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'line'
            },
            formatter: function(params) {
                let result = params[0].name + '<br/>';
                params.forEach(param => {
                    result += `${param.marker} ${param.seriesName}: ${formatMoney(param.value)} 元<br/>`;
                });
                return result;
            }
        },
        legend: {
            data: ['注册成本', '首充成本'],
            bottom: 0
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: dates,
            axisLabel: {
                rotate: period === 'yearly' ? 0 : 30,
                interval: 'auto',
                formatter: function(value) {
                    // 对于月度视图，修改标签显示格式
                    if (period === 'yearly') {
                        return value.substring(5, 7) + '月'; // 只显示月份
                    } else {
                        return value.substring(5); // 只显示月-日部分
                    }
                }
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: '{value} 元'
            }
        },
        series: [
            {
                name: '注册成本',
                type: 'line',
                data: registrationCostData,
                smooth: true,
                itemStyle: {
                    color: '#dc3545'
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(220, 53, 69, 0.3)' },
                        { offset: 1, color: 'rgba(220, 53, 69, 0.1)' }
                    ])
                },
                symbol: 'circle',
                symbolSize: 8
            },
            {
                name: '首充成本',
                type: 'line',
                data: firstDepositCostData,
                smooth: true,
                itemStyle: {
                    color: '#fd7e14'
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(253, 126, 20, 0.3)' },
                        { offset: 1, color: 'rgba(253, 126, 20, 0.1)' }
                    ])
                },
                symbol: 'circle',
                symbolSize: 8
            }
        ]
    };
    
    // 使用配置项和数据显示图表
    myChart.setOption(option);
}

// 填充数据表格
function populateDataTable(data, period, tableId) {
    const table = document.getElementById(tableId);
    if (!table) {
        console.error(`表格未找到: ${tableId}`);
        return;
    }
    
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    
    data[`${period}_data`].forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.date}</td>
            <td>${formatMoney(item.total_consumption)} 元</td>
            <td>${formatMoney(item.total_return_flow)} 元</td>
            <td>${formatMoney(item.total_actual_consumption)} 元</td>
            <td>${formatMoney(item.avg_registration_cost)} 元</td>
            <td>${formatMoney(item.avg_first_deposit_cost)} 元</td>
        `;
        tbody.appendChild(row);
    });
}

// 生成消费趋势洞察
function generateInsights(data, period, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`洞察容器未找到: ${containerId}`);
        return;
    }
    
    // 清除加载指示器
    container.innerHTML = '';
    
    // 分析数据
    const periodData = data[`${period}_data`];
    const totalStats = data[`${period}_total`];
    
    if (periodData.length <= 0) {
        container.innerHTML = '<div class="alert alert-info">暂无足够数据进行分析</div>';
        return;
    }
    
    // 找出最高消费日
    let maxConsumptionDay = periodData[0];
    let minConsumptionDay = periodData[0];
    periodData.forEach(day => {
        if (day.total_consumption > maxConsumptionDay.total_consumption) {
            maxConsumptionDay = day;
        }
        if (day.total_consumption < minConsumptionDay.total_consumption) {
            minConsumptionDay = day;
        }
    });
    
    // 计算消费趋势
    let trend = '稳定';
    const first = periodData[0]?.total_consumption || 0;
    const last = periodData[periodData.length - 1]?.total_consumption || 0;
    const percentChange = first > 0 ? ((last - first) / first * 100) : 0;
    
    if (percentChange > 15) {
        trend = '显著上升';
    } else if (percentChange > 5) {
        trend = '小幅上升';
    } else if (percentChange < -15) {
        trend = '显著下降';
    } else if (percentChange < -5) {
        trend = '小幅下降';
    }
    
    // 创建洞察内容
    const insights = document.createElement('div');
    insights.className = 'insights';
    
    // 根据不同时间段调整洞察文本
    const periodText = period === 'yearly' ? '年度月度' : (period === 'month' ? '本月' : '本周');
    const timeUnitText = period === 'yearly' ? '月' : '日';
    
    insights.innerHTML = `
        <div class="row g-4">
            <div class="col-md-6">
                <div class="alert alert-primary">
                    <h6 class="alert-heading"><i class="fas fa-chart-line"></i> 消费趋势</h6>
                    <p>${periodText}消费趋势呈<strong>${trend}</strong>趋势，变化幅度约为 <strong>${Math.abs(percentChange).toFixed(1)}%</strong>。</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="alert alert-warning">
                    <h6 class="alert-heading"><i class="fas fa-calendar-day"></i> 高峰与低谷</h6>
                    <p>最高消费${timeUnitText}为 <strong>${maxConsumptionDay.date.substring(0, period === 'yearly' ? 7 : 10)}</strong>，消费 <strong>${formatMoney(maxConsumptionDay.total_consumption)}</strong> 元</p>
                    <p>最低消费${timeUnitText}为 <strong>${minConsumptionDay.date.substring(0, period === 'yearly' ? 7 : 10)}</strong>，消费 <strong>${formatMoney(minConsumptionDay.total_consumption)}</strong> 元</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="alert alert-success">
                    <h6 class="alert-heading"><i class="fas fa-calculator"></i> 平均数据</h6>
                    <p>平均每${timeUnitText}消费: <strong>${formatMoney(totalStats.total_consumption / periodData.length)}</strong> 元</p>
                    <p>平均注册成本: <strong>${formatMoney(totalStats.avg_registration_cost)}</strong> 元</p>
                    <p>平均首充成本: <strong>${formatMoney(totalStats.avg_first_deposit_cost)}</strong> 元</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="alert alert-info">
                    <h6 class="alert-heading"><i class="fas fa-lightbulb"></i> 优化建议</h6>
                    <p>根据数据分析，建议在消费效果良好的${timeUnitText}份增加投放，在注册成本较高的${timeUnitText}份调整策略。</p>
                    <p>回流占比${totalStats.total_return_flow > 0 ? '较高' : '较低'}，可${totalStats.total_return_flow > 0 ? '维持当前' : '调整'}投放策略。</p>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(insights);
}

// 初始化所有图表
function initAllCharts(data) {
    try {
        // 检查数据是否完整
        if (data.custom_data && data.custom_total) {
            // 处理自定义日期范围数据
            // 将自定义数据作为month数据进行展示
            data.month_data = data.custom_data;
            data.month_total = data.custom_total;
            
            // 初始化月份图表和洞察
            initConsumptionChart(data, 'month', 'monthConsumptionChart');
            initCostChart(data, 'month', 'monthCostChart');
            generateInsights(data, 'month', 'monthInsights');
            displayStats(data, 'month');
            
            // 隐藏月份部分的加载指示器
            document.querySelectorAll('#month-stats-loading, #monthInsights .loading-spinner').forEach(spinner => {
                spinner.style.display = 'none';
            });
            
            return;
        }
        
        // 常规数据流程
        if (!data || !data.week_data || !data.month_data || !data.yearly_data ||
            !data.week_total || !data.month_total || !data.yearly_total) {
            console.error('返回的数据格式不完整', data);
            throw new Error('返回的数据格式不完整');
        }
        
        // 保存数据到全局变量
        chartData = data;
        
        // 初始化趋势图表
        initConsumptionChart(data, 'week', 'weekConsumptionChart');
        initCostChart(data, 'week', 'weekCostChart');
        
        initConsumptionChart(data, 'month', 'monthConsumptionChart');
        initCostChart(data, 'month', 'monthCostChart');
        
        initConsumptionChart(data, 'yearly', 'yearlyConsumptionChart');
        initCostChart(data, 'yearly', 'yearlyCostChart');
        
        // 生成洞察
        generateInsights(data, 'week', 'weekInsights');
        generateInsights(data, 'month', 'monthInsights');
        generateInsights(data, 'yearly', 'yearlyInsights');
        
        // 显示统计数据
        displayStats(data, 'week');
        displayStats(data, 'month');
        displayStats(data, 'yearly');
        
        // 隐藏所有加载指示器
        document.querySelectorAll('.loading-spinner').forEach(spinner => {
            spinner.style.display = 'none';
        });
    } catch (error) {
        console.error('初始化图表错误:', error);
        document.querySelectorAll('.loading-spinner').forEach(spinner => {
            spinner.innerHTML = `<div class="alert alert-danger">图表初始化失败: ${error.message}</div>`;
        });
    }
}

// 获取数据并初始化图表
async function fetchDataAndInitCharts(params = {}) {
    try {
        // 显示所有加载指示器
        document.querySelectorAll('.loading-spinner').forEach(spinner => {
            spinner.style.display = 'block';
            spinner.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
            `;
        });
        
        // 构建URL查询参数
        let url = getDataUrl;
        if (Object.keys(params).length > 0) {
            const queryParams = new URLSearchParams(params);
            url = `${getDataUrl}?${queryParams.toString()}`;
        }
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('获取数据失败：' + response.status);
        }
        
        const data = await response.json();
        console.log('获取到的数据:', data);
        initAllCharts(data);
    } catch (error) {
        console.error('获取数据错误:', error);
        
        // 显示错误消息
        document.querySelectorAll('.loading-spinner').forEach(spinner => {
            spinner.innerHTML = `<div class="alert alert-danger">数据加载失败: ${error.message}</div>`;
        });
    }
}

// 调整图表大小
function resizeAllCharts() {
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

// 初始化日期范围选择器
function initDateRangePicker() {
    const monthDateRangePicker = document.getElementById('month-date-range-picker');
    
    if (!monthDateRangePicker) {
        console.error('月份日期选择器未找到');
        return;
    }
    
    // 获取本月的开始和结束日期（默认值）
    const today = new Date();
    const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
    const monthEnd = today;
    
    // 初始化日期范围选择器
    const picker = flatpickr(monthDateRangePicker, {
        mode: 'range',
        dateFormat: 'Y-m-d',
        locale: 'zh',
        maxDate: 'today',
        defaultDate: [monthStart, monthEnd],
        disableMobile: true,
        showMonths: 2,
        onChange: function(selectedDates, dateStr) {
            if (selectedDates.length === 2) {
                const startDate = selectedDates[0];
                const endDate = selectedDates[1];
                
                // 计算日期差
                const daysDiff = Math.round((endDate - startDate) / (1000 * 60 * 60 * 24));
                
                // 检查是否超过最大允许日期范围 (62天)
                if (daysDiff > 62) {
                    // 显示警告消息
                    const alertElement = document.createElement('div');
                    alertElement.className = 'alert alert-warning alert-dismissible fade show mt-2';
                    alertElement.role = 'alert';
                    alertElement.innerHTML = `
                        <i class="fas fa-exclamation-triangle"></i> 日期范围不能超过62天，请重新选择。
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    
                    // 将警告添加到选择器下方
                    const parentElement = monthDateRangePicker.parentElement;
                    
                    // 移除已存在的警告
                    const existingAlert = parentElement.querySelector('.alert');
                    if (existingAlert) {
                        parentElement.removeChild(existingAlert);
                    }
                    
                    parentElement.appendChild(alertElement);
                    
                    // 重置为默认日期
                    picker.setDate([monthStart, monthEnd]);
                }
            }
        }
    });
    
    // 设置本月为默认值（文本显示）
    monthDateRangePicker.value = `${formatDate(monthStart)} 至 ${formatDate(monthEnd)}`;
    
    // 绑定查询按钮点击事件
    const monthSearchBtn = document.getElementById('month-search-btn');
    if (monthSearchBtn) {
        monthSearchBtn.addEventListener('click', function() {
            // 获取选定的日期范围
            const dates = picker.selectedDates;
            
            if (dates.length === 2) {
                const startDate = formatDate(dates[0]);
                const endDate = formatDate(dates[1]);
                
                // 发送请求获取指定日期范围的数据
                fetchDataAndInitCharts({
                    period: 'custom',
                    start_date: startDate,
                    end_date: endDate
                });
            }
        });
    }
    
    // 绑定重置按钮点击事件
    const monthResetBtn = document.getElementById('month-reset-btn');
    if (monthResetBtn) {
        monthResetBtn.addEventListener('click', function() {
            // 重置为本月时间范围
            picker.setDate([monthStart, monthEnd]);
            
            // 重新获取数据
            fetchDataAndInitCharts();
        });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，开始获取数据');
    
    // 获取CSRF令牌和数据URL (这些会在HTML模板中设置)
    csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    getDataUrl = document.getElementById('data-url').getAttribute('data-url');
    
    // 初始化日期范围选择器
    initDateRangePicker();
    
    // 开始获取数据
    fetchDataAndInitCharts();
    
    // 监听窗口大小改变事件
    window.addEventListener('resize', resizeAllCharts);
    
    // 监听标签页切换事件
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', event => {
            // 获取当前活动的标签页
            const activeTab = event.target.getAttribute('id');
            console.log('切换到标签页:', activeTab);
            
            // 重绘当前标签页的图表
            setTimeout(resizeAllCharts, 50);
        });
    });
}); 