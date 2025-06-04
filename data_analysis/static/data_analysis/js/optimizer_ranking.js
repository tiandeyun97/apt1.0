// 全局变量
let rankingData = null;
let csrfToken = null;
let getDataUrl = null;
let projectSearchUrl = null;
let departmentSearchUrl = null;
let dailyDatePicker = null;
let monthlyDateRangePicker = null;
let charts = {}; // 存储所有图表实例
let selectedProject = null; // 存储选中的项目信息

// 格式化金额函数
function formatMoney(amount, decimal = 2) {
    return parseFloat(amount).toFixed(decimal).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// 格式化日期范围显示
function formatDateRange(startDate, endDate) {
    return `${startDate} 至 ${endDate}`;
}

// 加载部门列表
async function loadDepartmentList() {
    try {
        const response = await fetch(departmentSearchUrl, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('获取部门列表失败: ' + response.status);
        }
        
        const data = await response.json();
        console.log('获取到的部门列表:', data);
        
        // 填充每日标签页中的部门选择器
        const dailyDepartmentSelect = document.getElementById('daily-department-select');
        if (dailyDepartmentSelect && data.departments && data.departments.length > 0) {
            // 清空现有选项（保留第一个"全部部门"选项）
            while (dailyDepartmentSelect.options.length > 1) {
                dailyDepartmentSelect.remove(1);
            }
            
            // 添加部门选项
            data.departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.id;
                option.textContent = `${dept.name} (${dept.member_count}人)`;
                option.dataset.code = dept.code;
                dailyDepartmentSelect.appendChild(option);
            });
        }
        
        // 填充本月标签页中的部门选择器
        const monthlyDepartmentSelect = document.getElementById('monthly-department-select');
        if (monthlyDepartmentSelect && data.departments && data.departments.length > 0) {
            // 清空现有选项（保留第一个"全部部门"选项）
            while (monthlyDepartmentSelect.options.length > 1) {
                monthlyDepartmentSelect.remove(1);
            }
            
            // 添加部门选项
            data.departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.id;
                option.textContent = `${dept.name} (${dept.member_count}人)`;
                option.dataset.code = dept.code;
                monthlyDepartmentSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载部门列表错误:', error);
        showErrorMessage('加载部门列表失败: ' + error.message);
    }
}

// 格式化日期为YYYY-MM-DD
function formatDate(date) {
    if (!date) return '';
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

// 加载排名数据
async function fetchRankingData(params = {}) {
    try {
        // 构建查询参数
        const queryParams = new URLSearchParams(params).toString();
        const url = `${getDataUrl}${queryParams ? '?' + queryParams : ''}`;
        
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
        console.log('获取到的排名数据:', data);
        
        // 保存数据
        rankingData = data;
        
        // 更新界面
        updateRankingDisplay(data);
        
        return data;
    } catch (error) {
        console.error('获取排名数据错误:', error);
        
        // 显示错误消息
        showErrorMessage(error.message);
        
        return null;
    }
}

// 搜索项目
async function searchProjects(keyword) {
    if (!keyword || keyword.trim().length < 2) {
        return [];
    }
    
    try {
        const response = await fetch(`${projectSearchUrl}?keyword=${encodeURIComponent(keyword)}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('项目搜索失败：' + response.status);
        }
        
        const data = await response.json();
        return data.projects || [];
    } catch (error) {
        console.error('项目搜索错误:', error);
        return [];
    }
}

// 获取项目优化师排名数据
async function fetchProjectRankingData(projectId) {
    try {
        const params = {
            period: 'project',
            project_id: projectId
        };
        
        return await fetchRankingData(params);
    } catch (error) {
        console.error('获取项目排名数据错误:', error);
        showErrorMessage(error.message);
        return null;
    }
}

// 显示错误信息
function showErrorMessage(message) {
    // 清空所有图表并显示错误信息
    const chartIds = ['daily-ranking-chart', 'weekly-ranking-chart', 'monthly-ranking-chart', 
                     'daily-pie-chart', 'weekly-pie-chart', 'monthly-pie-chart',
                     'project-ranking-chart', 'project-pie-chart'];
    
    chartIds.forEach(chartId => {
        const chart = charts[chartId];
        if (chart) {
            chart.setOption({
                title: {
                    text: '错误: ' + message,
                    left: 'center',
                    top: 'center',
                    textStyle: {
                        color: '#e74c3c',
                        fontSize: 16
                    }
                }
            });
        }
    });
    
    // 清空统计卡片
    updateStatsCard('daily', {
        totalConsumption: 0,
        maxConsumption: 0,
        avgConsumption: 0
    });
    
    updateStatsCard('weekly', {
        totalConsumption: 0,
        maxConsumption: 0,
        avgConsumption: 0
    });
    
    updateStatsCard('monthly', {
        totalConsumption: 0,
        maxConsumption: 0,
        avgConsumption: 0
    });
    
    // 清空项目统计卡片
    updateProjectStatsCard({
        totalConsumption: 0,
        optimizerCount: 0,
        taskCount: 0
    });
}

// 更新排名显示
function updateRankingDisplay(data) {
    if (!data || !data.ranking_data) {
        showErrorMessage('返回的数据格式不完整');
        return;
    }
    
    const period = data.period;
    const chartId = `${period}-ranking-chart`;
    const pieChartId = `${period}-pie-chart`;
    
    if (period === 'project') {
        // 更新项目信息
        updateProjectInfo(data.project_info || {});
    }
    
    // 更新柱状图
    updateRankingChart(data.ranking_data, chartId, period, data.date_info);
    
    // 对所有周期都更新右侧统计和饼图
    // 计算统计数据
    const stats = calculateConsumptionStats(data.ranking_data);
    
    if (period === 'project') {
        // 更新项目统计卡片
        updateProjectStatsCard({
            totalConsumption: stats.totalConsumption,
            optimizerCount: data.ranking_data.length,
            taskCount: data.ranking_data.reduce((sum, item) => sum + (item.task_count || 0), 0)
        });
    } else {
        // 更新普通统计卡片
        updateStatsCard(period, stats);
    }
    
    // 更新饼图
    updatePieChart(data.ranking_data, pieChartId, period);
}

// 更新项目信息
function updateProjectInfo(projectInfo) {
    const projectNameElement = document.querySelector('#project-info .project-name');
    if (projectNameElement) {
        projectNameElement.textContent = projectInfo.name ? `项目：${projectInfo.name}` : '';
    }
    
    // 更新选中的项目名称
    const selectedProjectNameElement = document.getElementById('selected-project-name');
    if (selectedProjectNameElement) {
        selectedProjectNameElement.textContent = projectInfo.name || '暂未选择';
    }
}

// 更新项目统计卡片
function updateProjectStatsCard(stats) {
    document.getElementById('project-total-consumption').textContent = `${formatMoney(stats.totalConsumption)} 元`;
    document.getElementById('project-optimizer-count').textContent = `${stats.optimizerCount} 人`;
    document.getElementById('project-task-count').textContent = `${stats.taskCount} 个`;
}

// 计算消耗统计数据
function calculateConsumptionStats(rankingData) {
    if (!rankingData || rankingData.length === 0) {
        return {
            totalConsumption: 0,
            maxConsumption: 0,
            avgConsumption: 0
        };
    }
    
    // 计算总消耗
    const totalConsumption = rankingData.reduce((sum, item) => sum + parseFloat(item.total_actual_consumption || 0), 0);
    
    // 计算最高消耗
    const maxConsumption = Math.max(...rankingData.map(item => parseFloat(item.total_actual_consumption || 0)));
    
    // 计算平均消耗
    const avgConsumption = totalConsumption / rankingData.length;
    
    return {
        totalConsumption,
        maxConsumption,
        avgConsumption
    };
}

// 更新统计卡片
function updateStatsCard(period, stats) {
    document.getElementById(`${period}-total-consumption`).textContent = `${formatMoney(stats.totalConsumption)} 元`;
    document.getElementById(`${period}-max-consumption`).textContent = `${formatMoney(stats.maxConsumption)} 元`;
    document.getElementById(`${period}-avg-consumption`).textContent = `${formatMoney(stats.avgConsumption)} 元`;
}

// 更新饼图
function updatePieChart(rankingData, chartId, period) {
    // 获取或初始化图表
    let chart = charts[chartId];
    if (!chart) {
        chart = echarts.init(document.getElementById(chartId));
        charts[chartId] = chart;
    }
    
    // 如果没有数据
    if (!rankingData || rankingData.length === 0) {
        chart.setOption({
            title: {
                text: '暂无数据',
                left: 'center',
                top: 'center',
                textStyle: {
                    color: '#999',
                    fontSize: 14
                }
            }
        });
        return;
    }
    
    // 限制显示前10名数据
    let displayData = rankingData.slice(0, 10);
    
    // 准备饼图数据
    const pieData = displayData.map(item => {
        const name = item.is_manager ? `${item.nickname || item.username} (主管)` : (item.nickname || item.username);
        return {
            name: name,
            value: parseFloat(item.total_actual_consumption || 0),
            rank: item.rank,
            isManager: item.is_manager
        };
    });
    
    // 颜色配置
    const colors = [
        '#f1c40f', '#95a5a6', '#d35400',
        '#3498db', '#2ecc71', '#9b59b6', '#e74c3c', 
        '#1abc9c', '#34495e', '#f39c12'
    ];
    
    // 图表标题配置
    let titleText = '优化师消耗占比';
    
    // 图表配置
    const option = {
        title: {
            text: titleText,
            left: 'center',
            top: 0,
            textStyle: {
                fontSize: 14,
                fontWeight: 'bold'
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                const data = params.data;
                let html = `
                    <div>
                        <b>排名 ${data.rank}: ${data.name}</b><br/>
                `;
                
                // 如果是部门主管，添加标识
                if (data.isManager) {
                    html += `<span style="color:#e74c3c;font-weight:bold;">部门主管</span><br/>`;
                }
                
                html += `
                        <span>消耗: ${formatMoney(data.value)} 元</span><br/>
                        <span>占比: ${params.percent}%</span>
                    </div>
                `;
                return html;
            }
        },
        legend: {
            type: 'scroll',
            orient: 'vertical',
            right: 10,
            top: 40,
            bottom: 20,
            formatter: function(name) {
                const item = pieData.find(d => d.name === name);
                if (item) {
                    return `${item.rank}. ${name}`;
                }
                return name;
            }
        },
        series: [
            {
                name: '消耗占比',
                type: 'pie',
                radius: ['40%', '70%'],
                center: ['40%', '55%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 4,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: '14',
                        fontWeight: 'bold'
                    }
                },
                labelLine: {
                    show: false
                },
                data: pieData.map(item => {
                    // 为部门主管设置特殊颜色
                    if (item.isManager) {
                        return {
                            ...item,
                            itemStyle: {
                                color: '#e74c3c'  // 部门主管使用红色
                            }
                        };
                    }
                    return item;
                })
            }
        ],
        color: colors
    };
    
    // 设置图表配置
    chart.setOption(option);
    
    // 确保图表在显示后正确渲染
    setTimeout(() => {
        chart.resize();
    }, 100);
}

// 初始化排名图表
function initRankingChart(chartId) {
    const chartDom = document.getElementById(chartId);
    if (!chartDom) {
        console.error(`找不到图表容器: ${chartId}`);
        return null;
    }
    
    // 初始化ECharts实例
    const chart = echarts.init(chartDom);
    
    // 保存图表实例
    charts[chartId] = chart;
    
    return chart;
}

// 更新排名图表
function updateRankingChart(rankingData, chartId, period, dateInfo) {
    // 获取或初始化图表
    let chart = charts[chartId];
    if (!chart) {
        chart = initRankingChart(chartId);
        if (!chart) return;
    }
    
    // 如果没有数据
    if (!rankingData || rankingData.length === 0) {
        chart.setOption({
            title: {
                text: '暂无排名数据',
                left: 'center',
                top: 'center',
                textStyle: {
                    color: '#999',
                    fontSize: 16
                }
            }
        });
        return;
    }
    
    // 限制展示数据量，对月度报表显示更多数据
    let displayData;
    if (period === 'monthly') {
        displayData = rankingData.slice(0, 30); // 月度可显示30条数据
    } else {
        displayData = rankingData.slice(0, 10); // 其他为10条
    }
    
    // 根据优化师数量设置自适应高度
    const chartDom = document.getElementById(chartId);
    if (chartDom) {
        // 设置CSS变量保存优化师数量，用于CSS计算高度
        chartDom.style.setProperty('--optimizer-count', displayData.length);
        
        // 当优化师数量超过阈值时，添加特殊类以启用自适应高度
        if (displayData.length > 10) {
            chartDom.classList.add('many-optimizers');
        } else {
            chartDom.classList.remove('many-optimizers');
        }
    }
    
    // 准备数据
    const usernames = displayData.map(item => {
        // 标识部门主管
        if (item.is_manager) {
            return `${item.nickname || item.username} (主管)`;
        }
        return item.nickname || item.username;
    });
    const consumptionData = displayData.map(item => item.total_actual_consumption);
    const taskCountData = displayData.map(item => item.task_count);
    
    // 颜色配置
    const rankColors = [
        '#f1c40f', // 金色 - 第一名
        '#95a5a6', // 银色 - 第二名
        '#d35400', // 铜色 - 第三名
        '#3498db', '#2ecc71', '#9b59b6', '#e74c3c', '#1abc9c', '#34495e', '#f39c12' // 其他颜色
    ];
    
    // 根据数据量调整网格位置
    const gridBottom = displayData.length > 10 ? '5%' : '15%';
    
    // 图表标题配置
    let titleText = '';
    let subtitleText = '';
    
    switch (period) {
        case 'daily':
            titleText = '每日消耗排名图表';
            subtitleText = `日期: ${dateInfo?.start_date || ''}`;
            break;
        case 'weekly':
            titleText = '本周消耗排名图表';
            subtitleText = dateInfo ? `${formatDateRange(dateInfo.start_date, dateInfo.end_date)}` : '';
            break;
        case 'monthly':
            titleText = '本月消耗排名图表';
            subtitleText = dateInfo ? `${formatDateRange(dateInfo.start_date, dateInfo.end_date)}` : '';
            break;
        case 'project':
            titleText = '项目优化师消耗排名';
            subtitleText = selectedProject ? `项目: ${selectedProject.name}` : '';
            break;
        default:
            titleText = '消耗排名图表';
    }
    
    // 图表配置
    const option = {
        title: {
            text: titleText,
            subtext: subtitleText,
            left: 'center',
            top: 0,
            textStyle: {
                fontSize: 16,
                fontWeight: 'bold'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function(params) {
                const index = params[0].dataIndex;
                const data = displayData[index];
                
                let tooltipHtml = `
                    <div>
                        <b>排名 ${data.rank}: ${data.nickname || data.username}</b><br/>
                `;
                
                // 如果是部门主管，添加标识
                if (data.is_manager) {
                    tooltipHtml += `<span style="color:#e74c3c;font-weight:bold;">部门主管</span><br/>`;
                }
                
                tooltipHtml += `
                        <span>任务数量: ${data.task_count}</span><br/>
                        <span>总消耗: ${formatMoney(data.total_consumption)} 元</span><br/>
                        <span>总回流: ${formatMoney(data.total_return_flow)} 元</span><br/>
                        <span>实际消耗: ${formatMoney(data.total_actual_consumption)} 元</span>
                `;
                
                // 如果是项目排名或有部门信息，添加部门信息
                if ((period === 'project' || period === 'daily') && data.department) {
                    tooltipHtml += `<span>部门: ${data.department}</span><br/>`;
                }
                
                tooltipHtml += '</div>';
                return tooltipHtml;
            }
        },
        legend: {
            data: ['实际消耗', '任务数量'],
            bottom: 0
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: gridBottom,
            top: '60px',
            containLabel: true
        },
        xAxis: {
            type: 'value',
            name: '金额 (元)',
            axisLabel: {
                formatter: '{value} 元'
            }
        },
        yAxis: {
            type: 'category',
            data: usernames,
            axisLabel: {
                interval: 0,
                rotate: 0,
                formatter: function(value, index) {
                    // 显示排名 + 名称
                    return `${displayData[index].rank}. ${value}`;
                },
                rich: {
                    manager: {
                        color: '#e74c3c',
                        fontWeight: 'bold'
                    }
                }
            },
            axisTick: {
                alignWithLabel: true
            }
        },
        series: [
            {
                name: '实际消耗',
                type: 'bar',
                data: consumptionData.map((value, index) => {
                    // 为部门主管设置特殊颜色
                    const color = displayData[index].is_manager ? 
                        '#e74c3c' :  // 部门主管使用红色
                        (index < 3 ? rankColors[index] : (rankColors[3 + index % 7]));
                    
                    return {
                        value: value,
                        itemStyle: {
                            color: color
                        }
                    };
                }),
                label: {
                    show: true,
                    position: 'right',
                    formatter: '{c} 元'
                }
            },
            {
                name: '任务数量',
                type: 'scatter',
                yAxisIndex: 0,
                symbolSize: function(value) {
                    // 根据任务数量设置散点大小
                    return Math.max(value * 3, 10);
                },
                data: taskCountData.map((value, index) => {
                    // 将任务数量映射到x轴上的位置
                    const maxConsumption = Math.max(...consumptionData);
                    return [consumptionData[index] * 0.8, index];
                })
            }
        ]
    };
    
    // 设置图表配置
    chart.setOption(option);
    
    // 延迟执行resize以确保正确渲染
    setTimeout(() => {
        chart.resize();
    }, 50);
}

// 初始化项目搜索
function initProjectSearch() {
    const searchInput = document.getElementById('project-search-input');
    const searchResults = document.getElementById('project-search-results');
    
    if (!searchInput || !searchResults) return;
    
    // 输入搜索关键词时显示结果
    searchInput.addEventListener('input', async function() {
        const keyword = this.value.trim();
        
        if (keyword.length < 2) {
            searchResults.innerHTML = '';
            searchResults.style.display = 'none';
            return;
        }
        
        // 搜索项目
        const projects = await searchProjects(keyword);
        
        if (projects.length === 0) {
            searchResults.innerHTML = '<div class="project-search-item">没有找到匹配的项目</div>';
        } else {
            // 显示搜索结果
            searchResults.innerHTML = projects.map(project => 
                `<div class="project-search-item" data-id="${project.id}" data-name="${project.name}" data-media-channel="${project.media_channel}" data-task-type="${project.task_type}">
                    <div class="project-name">${project.name}</div>
                    <div class="project-info">${project.media_channel} - ${project.task_type}</div>
                </div>`
            ).join('');
            
            // 为每个结果项添加点击事件
            const resultItems = searchResults.querySelectorAll('.project-search-item');
            resultItems.forEach(item => {
                item.addEventListener('click', function() {
                    const projectId = this.getAttribute('data-id');
                    const projectName = this.getAttribute('data-name');
                    const mediaChannel = this.getAttribute('data-media-channel');
                    const taskType = this.getAttribute('data-task-type');
                    
                    // 选中项目
                    selectProject({
                        id: projectId,
                        name: projectName,
                        media_channel: mediaChannel,
                        task_type: taskType
                    });
                    
                    // 清空搜索框和结果
                    searchInput.value = '';
                    searchResults.style.display = 'none';
                });
            });
        }
        
        // 显示搜索结果
        searchResults.style.display = 'block';
    });
    
    // 点击外部区域时关闭搜索结果
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
            searchResults.style.display = 'none';
        }
    });
    
    // 输入框获取焦点，如果有内容则显示结果
    searchInput.addEventListener('focus', function() {
        if (this.value.trim().length >= 2) {
            searchResults.style.display = 'block';
        }
    });
}

// 选择项目
async function selectProject(project) {
    if (!project || !project.id) return;
    
    // 保存已选项目
    selectedProject = project;
    
    // 更新显示的项目名称和信息
    const selectedProjectNameElement = document.getElementById('selected-project-name');
    const selectedProjectInfoElement = document.getElementById('selected-project-info');
    if (selectedProjectNameElement) {
        selectedProjectNameElement.textContent = project.name;
    }
    if (selectedProjectInfoElement) {
        selectedProjectInfoElement.textContent = `${project.media_channel} - ${project.task_type}`;
    }
    
    // 加载项目排名数据
    await fetchProjectRankingData(project.id);
}

// 调整图表大小
function resizeAllCharts() {
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

// 初始化日期选择器
function initDatePickers() {
    // 初始化每日日期选择器
    dailyDatePicker = flatpickr('#daily-date-picker', {
        dateFormat: 'Y-m-d',
        maxDate: 'today',
        locale: 'zh',
        defaultDate: rankingData?.date_info?.yesterday || 'today',
        onChange: function(selectedDates, dateStr, instance) {
            console.log('选择的日期:', dateStr);
        }
    });
    
    // 初始化月度日期范围选择器
    monthlyDateRangePicker = flatpickr('#monthly-date-range-picker', {
        mode: 'range',
        dateFormat: 'Y-m-d',
        maxDate: 'today',
        locale: 'zh',
        defaultDate: [
            rankingData?.date_info?.start_date,
            rankingData?.date_info?.end_date
        ],
        onChange: function(selectedDates, dateStr, instance) {
            console.log('选择的日期范围:', dateStr);
        }
    });
}

// 初始化事件监听
function initEventListeners() {
    // 每日查询按钮
    document.getElementById('daily-search-btn').addEventListener('click', function() {
        const selectedDate = dailyDatePicker.selectedDates[0];
        if (!selectedDate) {
            alert('请选择日期');
            return;
        }
        
        const dateStr = selectedDate.toISOString().split('T')[0];
        const departmentId = document.getElementById('daily-department-select').value;
        
        const params = {
            period: 'daily',
            date: dateStr
        };
        
        // 如果选择了部门，添加部门参数
        if (departmentId) {
            params.department_id = departmentId;
        }
        
        fetchRankingData(params);
    });
    
    // 月度查询按钮
    document.getElementById('monthly-search-btn').addEventListener('click', function() {
        const selectedDates = monthlyDateRangePicker.selectedDates;
        if (selectedDates.length < 2) {
            alert('请选择完整的日期范围');
            return;
        }
        
        const startDate = selectedDates[0].toISOString().split('T')[0];
        const endDate = selectedDates[1].toISOString().split('T')[0];
        const departmentId = document.getElementById('monthly-department-select').value;
        
        const params = {
            period: 'monthly',
            start_date: startDate,
            end_date: endDate
        };
        
        // 如果选择了部门，添加部门参数
        if (departmentId) {
            params.department_id = departmentId;
        }
        
        fetchRankingData(params);
    });
    
    // 标签页切换事件
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', event => {
            // 获取当前活动的标签页
            const activeTabId = event.target.getAttribute('id');
            let period = '';
            
            // 根据标签页ID设置请求周期
            if (activeTabId === 'daily-tab') {
                period = 'daily';
            } else if (activeTabId === 'weekly-tab') {
                period = 'weekly';
            } else if (activeTabId === 'monthly-tab') {
                period = 'monthly';
            } else if (activeTabId === 'project-tab') {
                period = 'project';
                // 如果已选择项目，则加载项目数据
                if (selectedProject) {
                    fetchProjectRankingData(selectedProject.id);
                    return;
                }
            }
            
            if (period && period !== 'project') {
                fetchRankingData({ period });
            }
        });
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async function() {
    console.log('页面加载完成，开始初始化');
    
    // 获取CSRF令牌和数据URL
    csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    getDataUrl = document.getElementById('data-url').getAttribute('data-url');
    projectSearchUrl = document.getElementById('project-search-url').getAttribute('data-url');
    departmentSearchUrl = document.getElementById('department-search-url').getAttribute('data-url');
    
    // 首次加载默认数据 (每日排名)
    await fetchRankingData({ period: 'daily' });
    
    // 初始化日期选择器
    initDatePickers();
    
    // 初始化项目搜索
    initProjectSearch();
    
    // 初始化事件监听
    initEventListeners();
    
    // 监听窗口大小改变事件
    window.addEventListener('resize', function() {
        // 重新计算图表容器高度
        adjustChartContainersHeight();
        // 重绘所有图表
        resizeAllCharts();
    });
    
    // 监听标签页切换事件
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', event => {
            // 重新计算图表容器高度
            setTimeout(function() {
                adjustChartContainersHeight();
                resizeAllCharts();
            }, 50);
        });
    });
    
    // 初始调整所有图表容器高度
    adjustChartContainersHeight();
    
    // 加载部门列表
    await loadDepartmentList();
});

// 调整图表容器高度，确保左右两侧内容对齐
function adjustChartContainersHeight() {
    // 获取当前活动的标签页
    const activeTabPane = document.querySelector('.tab-pane.active');
    if (!activeTabPane) return;
    
    const leftChartContainer = activeTabPane.querySelector('.col-lg-8 .ranking-chart-container');
    const rightContent = activeTabPane.querySelector('.col-lg-4 .right-content');
    
    if (!leftChartContainer || !rightContent) return;
    
    // 获取左侧图表容器的高度
    const leftHeight = leftChartContainer.offsetHeight;
    
    // 设置右侧容器的最小高度与左侧一致
    rightContent.style.minHeight = `${leftHeight}px`;
    
    // 如果右侧有多个元素，平均分配高度
    const rightElements = rightContent.querySelectorAll('.stats-card-container, .ranking-chart-container');
    if (rightElements.length > 1) {
        const elementHeight = (leftHeight / rightElements.length) - 10; // 减去间距
        rightElements.forEach(el => {
            el.style.height = `${elementHeight}px`;
        });
    }
} 