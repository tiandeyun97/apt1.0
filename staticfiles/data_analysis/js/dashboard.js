/**
 * 数据分析仪表盘JavaScript - Bootstrap版本
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化变量
    let trendData = null;
    let dailyData = null;
    let monthlyData = null;
    let currentTrendPeriod = 'this_week';
    let currentMonthlyIndex = 0;
    // 添加最大显示月份数量变量
    const MAX_MONTHS_TO_SHOW = 2;
    // 排名显示的优化师数量
    const TOP_OPTIMIZERS_TO_DISPLAY = 10;
    
    // 美化页面元素
    beautifyDashboard();
    
    // 初始化图表
    const trendChart = echarts.init(document.getElementById('trend-chart'));
    const dailyOptimizerChart = echarts.init(document.getElementById('daily-optimizer-chart'));
    const monthlyOptimizerChart = echarts.init(document.getElementById('monthly-optimizer-chart'));
    
    // 加载所有数据
    Promise.all([
        fetchConsumptionTrend(),
        fetchDailyConsumptionByOptimizer(),
        fetchMonthlyConsumptionByOptimizer()
    ]).then(() => {
        console.log('所有数据加载完成');
    }).catch(error => {
        console.error('加载数据时出错:', error);
    });
    
    // 监听窗口大小变化，调整图表尺寸
    window.addEventListener('resize', function() {
        trendChart.resize();
        dailyOptimizerChart.resize();
        monthlyOptimizerChart.resize();
    });
    
    // 设置趋势图时段选择器事件监听
    document.querySelectorAll('#trend-period-selector .btn').forEach(button => {
        button.addEventListener('click', function() {
            const period = this.getAttribute('data-period');
            setActiveButton(this);
            updateTrendChart(period);
        });
    });
    
    /**
     * 美化仪表盘
     */
    function beautifyDashboard() {
        // 添加卡片阴影和边框效果
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            card.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08)';
            card.style.borderRadius = '8px';
            card.style.border = '1px solid rgba(0, 0, 0, 0.05)';
        });
        
        // 美化标题
        const titles = document.querySelectorAll('.card-title');
        titles.forEach(title => {
            title.style.fontWeight = '600';
            title.style.color = '#2c3e50';
            title.style.fontSize = '1.1rem';
        });
        
        // 美化今日消耗卡片
        const todayCard = document.getElementById('today-consumption').parentNode;
        if (todayCard) {
            todayCard.style.background = 'linear-gradient(135deg, #3498db, #2980b9)';
            todayCard.style.color = 'white';
            
            const todayValue = document.getElementById('today-consumption');
            if (todayValue) {
                todayValue.style.fontSize = '1.8rem';
                todayValue.style.fontWeight = '700';
            }
        }
        
        // 美化按钮
        const buttons = document.querySelectorAll('.btn-outline-primary');
        buttons.forEach(button => {
            button.addEventListener('mouseover', function() {
                this.style.transition = 'all 0.3s ease';
            });
        });
    }
    
    /**
     * 设置活动按钮
     */
    function setActiveButton(element) {
        // 移除所有按钮的活动状态
        const buttons = element.parentNode.querySelectorAll('.btn');
        buttons.forEach(btn => {
            btn.classList.remove('active');
        });
        // 设置当前按钮为活动状态
        element.classList.add('active');
    }
    
    /**
     * 获取消耗趋势数据
     */
    function fetchConsumptionTrend() {
        return fetch(CONSUMPTION_TREND_API_URL)
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络响应不正常');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    trendData = data.data;
                    // 更新今日消耗
                    document.getElementById('today-consumption').textContent = 
                        formatCurrency(trendData.today);
                    // 更新趋势图
                    updateTrendChart(currentTrendPeriod);
                } else {
                    console.error('获取消耗趋势数据失败');
                }
            })
            .catch(error => {
                console.error('获取消耗趋势数据出错:', error);
            });
    }
    
    /**
     * 获取优化师每日消耗数据
     */
    function fetchDailyConsumptionByOptimizer() {
        return fetch(DAILY_CONSUMPTION_BY_OPTIMIZER_API_URL)
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络响应不正常');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    dailyData = data.data;
                    // 更新优化师每日消耗图表 - 显示前一天的数据（索引1）而不是当天
                    updateDailyOptimizerChart();
                } else {
                    console.error('获取优化师每日消耗数据失败');
                }
            })
            .catch(error => {
                console.error('获取优化师每日消耗数据出错:', error);
            });
    }
    
    /**
     * 获取优化师每月消耗数据
     */
    function fetchMonthlyConsumptionByOptimizer() {
        return fetch(MONTHLY_CONSUMPTION_BY_OPTIMIZER_API_URL)
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络响应不正常');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    monthlyData = data.data;
                    // 初始化月份选择器
                    initMonthlyDateSelector();
                    // 更新优化师每月消耗图表
                    updateMonthlyOptimizerChart(currentMonthlyIndex);
                } else {
                    console.error('获取优化师每月消耗数据失败');
                }
            })
            .catch(error => {
                console.error('获取优化师每月消耗数据出错:', error);
            });
    }
    
    /**
     * 初始化每月数据月份选择器
     */
    function initMonthlyDateSelector() {
        const selector = document.getElementById('monthly-date-selector');
        selector.innerHTML = '';
        
        // 仅显示最近的几个月
        const monthsToShow = Math.min(MAX_MONTHS_TO_SHOW, monthlyData.length);
        
        // 循环显示最近的N个月
        for (let i = 0; i < monthsToShow; i++) {
            const index = i;
            const item = monthlyData[index];
            
            const button = document.createElement('button');
            button.classList.add('btn', 'btn-outline-primary', 'btn-sm');
            if (index === currentMonthlyIndex) {
                button.classList.add('active');
            }
            button.setAttribute('data-index', index);
            button.textContent = formatMonth(item.month);
            
            button.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                setActiveButton(this);
                updateMonthlyOptimizerChart(index);
            });
            
            selector.appendChild(button);
        }
    }
    
    /**
     * 更新消耗趋势图表
     */
    function updateTrendChart(period) {
        currentTrendPeriod = period;
        
        if (!trendData) {
            return;
        }
        
        let chartData = [];
        let dateLabels = [];
        
        switch (period) {
            case 'this_week':
                chartData = trendData.this_week.map(item => item.value);
                dateLabels = trendData.this_week.map(item => formatDate(item.date));
                break;
            case 'this_month':
                chartData = trendData.this_month.map(item => item.value);
                dateLabels = trendData.this_month.map(item => formatDate(item.date));
                break;
            case 'last_month':
                chartData = trendData.last_month.map(item => item.value);
                dateLabels = trendData.last_month.map(item => formatDate(item.date));
                break;
        }
        
        const option = {
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    const data = params[0];
                    return `${data.name}<br/>${data.marker} 消耗: ${formatCurrency(data.value)}`;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                borderColor: '#eee',
                borderWidth: 1,
                textStyle: {
                    color: '#333'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: dateLabels,
                axisLabel: {
                    formatter: function(value) {
                        // 如果日期太多，只显示部分
                        if (dateLabels.length > 20) {
                            return value.substr(5);  // 只显示月-日
                        }
                        return value;
                    },
                    color: '#666'
                },
                axisLine: {
                    lineStyle: {
                        color: '#ddd'
                    }
                }
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    formatter: function(value) {
                        return formatCurrency(value, true);
                    },
                    color: '#666'
                },
                splitLine: {
                    lineStyle: {
                        color: '#eee'
                    }
                }
            },
            series: [{
                name: '消耗',
                type: 'line',
                smooth: true,
                data: chartData,
                symbol: 'circle',
                symbolSize: 6,
                itemStyle: {
                    color: '#3498db'
                },
                lineStyle: {
                    width: 3,
                    shadowColor: 'rgba(0, 0, 0, 0.1)',
                    shadowBlur: 10
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                        offset: 0,
                        color: 'rgba(52, 152, 219, 0.5)'
                    }, {
                        offset: 1,
                        color: 'rgba(52, 152, 219, 0.1)'
                    }])
                }
            }]
        };
        
        trendChart.setOption(option);
    }
    
    /**
     * 更新优化师每日消耗图表 - 显示前一天数据
     */
    function updateDailyOptimizerChart() {
        if (!dailyData || dailyData.length === 0) {
            return;
        }
        
        // 找到有数据的第一天（通常是前一天，索引1）
        let dataIndex = 1; // 默认显示前一天的数据
        
        // 如果前一天没有数据，寻找最近有数据的一天
        if (dataIndex < dailyData.length && (!dailyData[dataIndex].data || dailyData[dataIndex].data.length === 0)) {
            for (let i = 0; i < dailyData.length; i++) {
                if (dailyData[i].data && dailyData[i].data.length > 0) {
                    dataIndex = i;
                    break;
                }
            }
        }
        
        // 如果没有找到有数据的天，就显示第一天
        if (dataIndex >= dailyData.length) {
            dataIndex = 0;
        }
        
        const dayData = dailyData[dataIndex];
        
        // 按消耗金额从大到小排序
        const sortedData = [...dayData.data].sort((a, b) => b.value - a.value);
        
        // 限制显示TOP N名优化师
        const displayData = sortedData.slice(0, TOP_OPTIMIZERS_TO_DISPLAY);
        const names = displayData.map(item => item.name);
        const values = displayData.map(item => item.value);
        
        // 计算剩余的"其他"优化师总和
        let othersTotal = 0;
        if (sortedData.length > TOP_OPTIMIZERS_TO_DISPLAY) {
            for (let i = TOP_OPTIMIZERS_TO_DISPLAY; i < sortedData.length; i++) {
                othersTotal += sortedData[i].value;
            }
            
            if (othersTotal > 0) {
                names.push('其他');
                values.push(othersTotal);
            }
        }
        
        // 生成优美的颜色方案
        const colorScheme = generateColorScheme(names.length);
        
        const option = {
            title: {
                text: `${dayData.date} 总消耗: ${formatCurrency(dayData.total)}`,
                textStyle: {
                    fontSize: 14,
                    fontWeight: 'normal',
                    color: '#2c3e50'
                },
                left: 'center',
                top: 0,
                padding: [10, 0]
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                },
                formatter: function(params) {
                    const data = params[0];
                    const percent = ((data.value / dayData.total) * 100).toFixed(1);
                    return `${data.name}<br/>${data.marker} 消耗: ${formatCurrency(data.value)} (${percent}%)`;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                borderColor: '#eee',
                borderWidth: 1,
                textStyle: {
                    color: '#333'
                }
            },
            grid: {
                left: '3%',
                right: '8%',  // 增加右侧空间，以便显示标签
                bottom: '3%',
                top: 50,
                containLabel: true
            },
            xAxis: {
                type: 'value',
                axisLabel: {
                    formatter: function(value) {
                        return formatCurrency(value, true);
                    },
                    color: '#666'
                },
                axisLine: {
                    lineStyle: {
                        color: '#ddd'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#eee'
                    }
                }
            },
            yAxis: {
                type: 'category',
                data: names,
                axisLabel: {
                    interval: 0,
                    color: '#2c3e50',
                    fontWeight: 'bold'
                },
                axisLine: {
                    lineStyle: {
                        color: '#ddd'
                    }
                }
            },
            series: [{
                name: '消耗',
                type: 'bar',
                data: values,
                barWidth: '60%',
                itemStyle: {
                    color: function(params) {
                        return colorScheme[params.dataIndex % colorScheme.length];
                    },
                    borderRadius: [0, 4, 4, 0]
                },
                label: {
                    show: true,
                    position: 'right',
                    distance: 10,
                    formatter: function(params) {
                        const percent = ((params.value / dayData.total) * 100).toFixed(1);
                        return `${formatCurrency(params.value)} (${percent}%)`;
                    },
                    textStyle: {
                        color: '#666'
                    }
                }
            }]
        };
        
        dailyOptimizerChart.setOption(option);
    }
    
    /**
     * 更新优化师每月消耗图表
     */
    function updateMonthlyOptimizerChart(index) {
        currentMonthlyIndex = index;
        
        if (!monthlyData || !monthlyData[index]) {
            return;
        }
        
        const monthData = monthlyData[index];
        
        // 按消耗金额从大到小排序数据
        const sortedData = [...monthData.data].sort((a, b) => b.value - a.value);
        
        // 限制显示TOP N名优化师
        const displayData = sortedData.slice(0, TOP_OPTIMIZERS_TO_DISPLAY);
        const names = displayData.map(item => item.name);
        const values = displayData.map(item => item.value);
        
        // 计算剩余的"其他"优化师总和
        let othersTotal = 0;
        if (sortedData.length > TOP_OPTIMIZERS_TO_DISPLAY) {
            for (let i = TOP_OPTIMIZERS_TO_DISPLAY; i < sortedData.length; i++) {
                othersTotal += sortedData[i].value;
            }
            
            if (othersTotal > 0) {
                names.push('其他');
                values.push(othersTotal);
            }
        }
        
        // 计算总消耗
        const total = sortedData.reduce((sum, item) => sum + item.value, 0);
        
        // 生成优美的颜色方案
        const colorScheme = generateColorScheme(names.length);
        
        const option = {
            title: {
                text: `${formatMonth(monthData.month)} 总消耗: ${formatCurrency(total)}`,
                textStyle: {
                    fontSize: 14,
                    fontWeight: 'normal',
                    color: '#2c3e50'
                },
                left: 'center',
                top: 0,
                padding: [10, 0]
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                },
                formatter: function(params) {
                    const data = params[0];
                    const percent = ((data.value / total) * 100).toFixed(1);
                    return `${data.name}<br/>${data.marker} 消耗: ${formatCurrency(data.value)} (${percent}%)`;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                borderColor: '#eee',
                borderWidth: 1,
                textStyle: {
                    color: '#333'
                }
            },
            grid: {
                left: '3%',
                right: '8%', // 增加右侧空间，以便显示标签
                bottom: '3%',
                top: 50,
                containLabel: true
            },
            xAxis: {
                type: 'value',
                axisLabel: {
                    formatter: function(value) {
                        return formatCurrency(value, true);
                    },
                    color: '#666'
                },
                axisLine: {
                    lineStyle: {
                        color: '#ddd'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#eee'
                    }
                }
            },
            yAxis: {
                type: 'category',
                data: names,
                axisLabel: {
                    interval: 0,
                    color: '#2c3e50',
                    fontWeight: 'bold'
                },
                axisLine: {
                    lineStyle: {
                        color: '#ddd'
                    }
                }
            },
            series: [{
                name: '消耗',
                type: 'bar',
                data: values,
                barWidth: '60%',
                itemStyle: {
                    color: function(params) {
                        return colorScheme[params.dataIndex % colorScheme.length];
                    },
                    borderRadius: [0, 4, 4, 0]
                },
                label: {
                    show: true,
                    position: 'right',
                    distance: 10,
                    formatter: function(params) {
                        const percent = ((params.value / total) * 100).toFixed(1);
                        return `${formatCurrency(params.value)} (${percent}%)`;
                    },
                    textStyle: {
                        color: '#666'
                    }
                }
            }]
        };
        
        monthlyOptimizerChart.setOption(option);
    }
    
    /**
     * 生成优美的颜色方案
     */
    function generateColorScheme(count) {
        // 设计优美的颜色方案 - 不同于默认的Bootstrap颜色
        const baseColors = [
            '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', 
            '#1abc9c', '#d35400', '#34495e', '#16a085', '#c0392b',
            '#2980b9', '#27ae60', '#e67e22', '#8e44ad', '#2c3e50'
        ];
        
        // 如果颜色不够用，生成额外的颜色
        const colors = [...baseColors];
        
        if (count > colors.length) {
            // 生成额外的颜色 - 使用HSL来确保颜色的区分度
            for (let i = colors.length; i < count; i++) {
                const hue = (i * 137.5) % 360; // 黄金角分布
                const saturation = 70 + Math.random() * 20; // 70-90%
                const lightness = 45 + Math.random() * 10; // 45-55%
                colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
            }
        }
        
        return colors;
    }
    
    /**
     * 格式化货币
     */
    function formatCurrency(value, short = false) {
        if (short && value >= 10000) {
            return (value / 10000).toFixed(1) + '万';
        }
        return parseFloat(value).toLocaleString('zh-CN', { 
            style: 'currency', 
            currency: 'CNY',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    
    /**
     * 格式化日期
     */
    function formatDate(dateStr) {
        const date = new Date(dateStr);
        const month = date.getMonth() + 1;
        const day = date.getDate();
        return `${month}月${day}日`;
    }
    
    /**
     * 格式化月份
     */
    function formatMonth(monthStr) {
        const parts = monthStr.split('-');
        return `${parts[0]}年${parts[1]}月`;
    }
}); 