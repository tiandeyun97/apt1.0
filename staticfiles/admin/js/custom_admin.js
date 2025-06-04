// 等待DOM完全加载后执行
document.addEventListener('DOMContentLoaded', function() {
    // 适配VPN环境下的页面
    setupVpnCompatibility();
    
    // 增强表格交互功能
    enhanceTableInteraction();
    
    // 修复可能的CSRF问题
    ensureCSRFProtection();
});

/**
 * 设置兼容VPN环境的功能
 */
function setupVpnCompatibility() {
    // 修复静态资源路径问题
    fixStaticResourcePaths();
    
    // 调整请求头，确保跨域请求正常
    setupCORSHeaders();
}

/**
 * 修复静态资源路径问题
 */
function fixStaticResourcePaths() {
    // 获取所有图片元素
    const images = document.querySelectorAll('img');
    
    // 修复图片路径
    images.forEach(function(img) {
        // 如果图片未加载成功，尝试使用完整路径
        img.addEventListener('error', function() {
            // 提取路径最后部分（文件名）
            const srcParts = img.src.split('/');
            const filename = srcParts[srcParts.length - 1];
            
            // 尝试从静态资源目录加载
            img.src = `/static/admin/img/${filename}`;
        });
    });
}

/**
 * 设置CORS相关头信息
 */
function setupCORSHeaders() {
    // 对所有AJAX请求添加CORS头
    if (window.XMLHttpRequest) {
        const originalXhr = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            const xhr = new originalXhr();
            const originalOpen = xhr.open;
            
            xhr.open = function() {
                originalOpen.apply(xhr, arguments);
                
                // 设置请求头
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            };
            
            return xhr;
        };
    }
}

/**
 * 增强表格交互功能
 */
function enhanceTableInteraction() {
    // 获取所有表格
    const tables = document.querySelectorAll('.results');
    
    tables.forEach(function(table) {
        // 添加表格排序功能
        addTableSorting(table);
        
        // 添加表格过滤功能
        addTableFiltering(table);
    });
}

/**
 * 添加表格排序功能
 */
function addTableSorting(table) {
    // 获取表头
    const headers = table.querySelectorAll('thead th');
    
    headers.forEach(function(header) {
        // 排除不需要排序的列
        if (header.classList.contains('action-checkbox-column') ||
            header.classList.contains('no-sort')) {
            return;
        }
        
        // 添加排序指示器和点击事件
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(table, Array.from(headers).indexOf(header));
        });
    });
}

/**
 * 添加表格过滤功能
 */
function addTableFiltering(table) {
    // 实现简单的表格过滤功能
    const searchInput = document.querySelector('#searchbar input[name="q"]');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(function(row) {
                let found = false;
                
                // 检查每个单元格
                row.querySelectorAll('td').forEach(function(cell) {
                    if (cell.textContent.toLowerCase().includes(query)) {
                        found = true;
                    }
                });
                
                // 显示或隐藏行
                row.style.display = found ? '' : 'none';
            });
        });
    }
}

/**
 * 表格排序功能
 */
function sortTable(table, columnIndex) {
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const isAscending = table.getAttribute('data-sort-dir') !== 'asc';
    
    // 保存排序方向
    table.setAttribute('data-sort-dir', isAscending ? 'asc' : 'desc');
    
    // 排序行
    rows.sort(function(a, b) {
        const cellA = a.querySelectorAll('td')[columnIndex];
        const cellB = b.querySelectorAll('td')[columnIndex];
        
        if (!cellA || !cellB) return 0;
        
        const valueA = cellA.textContent.trim();
        const valueB = cellB.textContent.trim();
        
        // 检查是否为数字
        const isNumeric = !isNaN(parseFloat(valueA)) && !isNaN(parseFloat(valueB));
        
        if (isNumeric) {
            return isAscending ? 
                parseFloat(valueA) - parseFloat(valueB) : 
                parseFloat(valueB) - parseFloat(valueA);
        } else {
            return isAscending ? 
                valueA.localeCompare(valueB) : 
                valueB.localeCompare(valueA);
        }
    });
    
    // 重新插入排序后的行
    const tbody = table.querySelector('tbody');
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
}

/**
 * 确保CSRF保护
 */
function ensureCSRFProtection() {
    // 从cookie中获取CSRF令牌
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
    
    // 设置CSRF令牌为请求头
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) {
        // 对所有AJAX请求添加CSRF令牌
        if (window.XMLHttpRequest) {
            const originalXhr = window.XMLHttpRequest;
            window.XMLHttpRequest = function() {
                const xhr = new originalXhr();
                const originalOpen = xhr.open;
                
                xhr.open = function() {
                    originalOpen.apply(xhr, arguments);
                    
                    // 设置CSRF令牌
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                };
                
                return xhr;
            };
        }
    }
} 